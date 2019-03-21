# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006 Lukáš Lalinský
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from collections import defaultdict
import fnmatch
from functools import partial
from operator import itemgetter
import os
import os.path
import re
import shutil
import unicodedata

from PyQt5 import QtCore

from picard import (
    PICARD_APP_NAME,
    config,
    log,
)
from picard.const import QUERY_LIMIT
from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)
from picard.metadata import Metadata
from picard.util import (
    decode_filename,
    format_time,
    pathcmp,
    thread,
    tracknum_from_filename,
)
from picard.util.filenaming import make_short_filename
from picard.util.scripttofilename import script_to_filename
from picard.util.tags import PRESERVED_TAGS

from picard.ui.item import Item


class File(QtCore.QObject, Item):

    metadata_images_changed = QtCore.pyqtSignal()

    NAME = None

    UNDEFINED = -1
    PENDING = 0
    NORMAL = 1
    CHANGED = 2
    ERROR = 3
    REMOVED = 4

    LOOKUP_METADATA = 1
    LOOKUP_ACOUSTID = 2

    comparison_weights = {
        "title": 13,
        "artist": 4,
        "album": 5,
        "length": 10,
        "totaltracks": 4,
        "releasetype": 20,
        "releasecountry": 2,
        "format": 2,
    }

    class PreserveTimesStatError(Exception):
        pass

    class PreserveTimesUtimeError(Exception):
        pass

    # in order to significantly speed up performance, the number of pending
    # files is cached, set @state.setter
    num_pending_files = 0

    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.base_filename = os.path.basename(filename)
        self._state = File.UNDEFINED
        self.state = File.PENDING
        self.error = None

        self.orig_metadata = Metadata()
        self.metadata = Metadata()

        self.similarity = 1.0
        self.parent = None

        self.lookup_task = None
        self.item = None

    def __repr__(self):
        return '<File %r>' % self.base_filename

    @property
    def new_metadata(self):
        return self.metadata

    def load(self, callback):
        thread.run_task(
            partial(self._load_check, self.filename),
            partial(self._loading_finished, callback),
            priority=1)

    def _load_check(self, filename):
        # Check that file has not been removed since thread was queued
        # Don't load if we are stopping.
        if self.state != File.PENDING:
            log.debug("File not loaded because it was removed: %r", self.filename)
            return None
        if self.tagger.stopping:
            log.debug("File not loaded because %s is stopping: %r", PICARD_APP_NAME, self.filename)
            return None
        return self._load(filename)

    def _load(self, filename):
        """Load metadata from the file."""
        raise NotImplementedError

    def _loading_finished(self, callback, result=None, error=None):
        if self.state != File.PENDING or self.tagger.stopping:
            return
        if error is not None:
            self.error = str(error)
            self.state = self.ERROR
            from picard.formats import supported_extensions
            file_name, file_extension = os.path.splitext(self.base_filename)
            if file_extension not in supported_extensions():
                self.remove()
                log.error('Unsupported media file %r wrongly loaded. Removing ...', self)
                return
        else:
            self.error = None
            self.state = self.NORMAL
            self._copy_loaded_metadata(result)
        self.update()
        callback(self)

    def _copy_loaded_metadata(self, metadata):
        filename, _ = os.path.splitext(self.base_filename)
        metadata['~length'] = format_time(metadata.length)
        if 'title' not in metadata:
            metadata['title'] = filename
        if 'tracknumber' not in metadata:
            tracknumber = tracknum_from_filename(self.base_filename)
            if tracknumber != -1:
                tracknumber = str(tracknumber)
                metadata['tracknumber'] = tracknumber
                if metadata['title'] == filename:
                    stripped_filename = filename.lstrip('0')
                    tnlen = len(tracknumber)
                    if stripped_filename[:tnlen] == tracknumber:
                        metadata['title'] = stripped_filename[tnlen:].lstrip()
        self.orig_metadata = metadata
        self.metadata.copy(metadata)

    def copy_metadata(self, metadata, preserve_deleted=True):
        acoustid = self.metadata["acoustid_id"]
        preserve = config.setting["preserved_tags"].strip()
        saved_metadata = {}

        for tag in re.split(r"\s*,\s*", preserve) + PRESERVED_TAGS:
            values = self.orig_metadata.getall(tag)
            if values:
                saved_metadata[tag] = values
        deleted_tags = self.metadata.deleted_tags
        self.metadata.copy(metadata)
        if preserve_deleted:
            for tag in deleted_tags:
                self.metadata.delete(tag)
        for tag, values in saved_metadata.items():
            self.metadata.set(tag, values)

        if acoustid and "acoustid_id" not in metadata.deleted_tags:
            self.metadata["acoustid_id"] = acoustid
        self.metadata_images_changed.emit()

    def keep_original_images(self):
        self.metadata.images = self.orig_metadata.images[:]
        self.update()
        self.metadata_images_changed.emit()

    def has_error(self):
        return self.state == File.ERROR

    def save(self):
        self.set_pending()
        metadata = Metadata()
        metadata.copy(self.metadata)
        thread.run_task(
            partial(self._save_and_rename, self.filename, metadata),
            self._saving_finished,
            priority=2,
            thread_pool=self.tagger.save_thread_pool)

    def _preserve_times(self, filename, func):
        """Save filename times before calling func, and set them again"""
        try:
            # https://docs.python.org/3/library/os.html#os.utime
            # Since Python 3.3, ns parameter is available
            # The best way to preserve exact times is to use the st_atime_ns and st_mtime_ns
            # fields from the os.stat() result object with the ns parameter to utime.
            st = os.stat(filename)
        except OSError as why:
            errmsg = "Couldn't read timestamps from %r: %s" % (filename, why)
            raise self.PreserveTimesStatError(errmsg) from None
            # if we can't read original times, don't call func and let caller handle this
        func()
        try:
            os.utime(filename, ns=(st.st_atime_ns, st.st_mtime_ns))
        except OSError as why:
            errmsg = "Couldn't preserve timestamps for %r: %s" % (filename, why)
            raise self.PreserveTimesUtimeError(errmsg) from None
        return (st.st_atime_ns, st.st_mtime_ns)

    def _save_and_rename(self, old_filename, metadata):
        """Save the metadata."""
        # Check that file has not been removed since thread was queued
        # Also don't save if we are stopping.
        if self.state == File.REMOVED:
            log.debug("File not saved because it was removed: %r", self.filename)
            return None
        if self.tagger.stopping:
            log.debug("File not saved because %s is stopping: %r", PICARD_APP_NAME, self.filename)
            return None
        new_filename = old_filename
        if not config.setting["dont_write_tags"]:
            save = partial(self._save, old_filename, metadata)
            if config.setting["preserve_timestamps"]:
                try:
                    self._preserve_times(old_filename, save)
                except self.PreserveTimesStatError as why:
                    log.warning(why)
                    # we didn't save the file yet, bail out
                    return None
                except self.FilePreserveTimesUtimeError as why:
                    log.warning(why)
            else:
                save()
        # Rename files
        if config.setting["rename_files"] or config.setting["move_files"]:
            new_filename = self._rename(old_filename, metadata)
        # Move extra files (images, playlists, etc.)
        if config.setting["move_files"] and config.setting["move_additional_files"]:
            self._move_additional_files(old_filename, new_filename)
        # Delete empty directories
        if config.setting["delete_empty_dirs"]:
            dirname = os.path.dirname(old_filename)
            try:
                self._rmdir(dirname)
                head, tail = os.path.split(dirname)
                if not tail:
                    head, tail = os.path.split(head)
                while head and tail:
                    try:
                        self._rmdir(head)
                    except BaseException:
                        break
                    head, tail = os.path.split(head)
            except EnvironmentError:
                pass
        # Save cover art images
        if config.setting["save_images_to_files"]:
            self._save_images(os.path.dirname(new_filename), metadata)
        return new_filename

    @staticmethod
    def _rmdir(path):
        junk_files = (".DS_Store", "desktop.ini", "Desktop.ini", "Thumbs.db")
        if not set(os.listdir(path)) - set(junk_files):
            shutil.rmtree(path, False)
        else:
            raise OSError

    def _saving_finished(self, result=None, error=None):
        # Handle file removed before save
        # Result is None if save was skipped
        if ((self.state == File.REMOVED or self.tagger.stopping)
                and result is None):
            return
        old_filename = new_filename = self.filename
        if error is not None:
            self.error = str(error)
            self.state = File.ERROR
        else:
            self.filename = new_filename = result
            self.base_filename = os.path.basename(new_filename)
            length = self.orig_metadata.length
            temp_info = {}
            for info in ('~bitrate', '~sample_rate', '~channels',
                         '~bits_per_sample', '~format'):
                temp_info[info] = self.orig_metadata[info]
            # Data is copied from New to Original because New may be
            # a subclass to handle id3v23
            if config.setting["clear_existing_tags"]:
                self.orig_metadata.copy(self.new_metadata)
            else:
                self.orig_metadata.update(self.new_metadata)
            # After saving deleted tags should no longer be marked deleted
            self.new_metadata.clear_deleted()
            self.orig_metadata.clear_deleted()
            self.orig_metadata.length = length
            self.orig_metadata['~length'] = format_time(length)
            for k, v in temp_info.items():
                self.orig_metadata[k] = v
            self.error = None
            self.clear_pending()
            self._add_path_to_metadata(self.orig_metadata)
            self.metadata_images_changed.emit()

        # Force update to ensure file status icon changes immediately after save
        self.update()

        if self.state != File.REMOVED:
            del self.tagger.files[old_filename]
            self.tagger.files[new_filename] = self

        if self.tagger.stopping:
            log.debug("Save of %r completed before stopping Picard", self.filename)

    def _save(self, filename, metadata):
        """Save the metadata."""
        raise NotImplementedError

    def _script_to_filename(self, naming_format, file_metadata, settings=None):
        if settings is None:
            settings = config.setting
        metadata = Metadata()
        if settings["clear_existing_tags"]:
            metadata.copy(file_metadata)
        else:
            metadata.copy(self.orig_metadata)
            metadata.update(file_metadata)
        return script_to_filename(naming_format, metadata, file=self, settings=settings)

    def _fixed_splitext(self, filename):
        # In case the filename is blank and only has the extension
        # the real extension is in new_filename and ext is blank
        new_filename, ext = os.path.splitext(filename)
        if ext == '' and new_filename.lower() in self.EXTENSIONS:
            ext = new_filename
            new_filename = ''
        return new_filename, ext

    def _format_filename(self, new_dirname, new_filename, metadata, settings):
        # TODO: tests !!
        new_filename, ext = self._fixed_splitext(new_filename)
        ext = ext.lower()
        new_filename = new_filename + ext

        # expand the naming format
        naming_format = settings['file_naming_format']
        if naming_format:
            new_filename = self._script_to_filename(naming_format, metadata, settings)
            # NOTE: the _script_to_filename strips the extension away
            new_filename = new_filename + ext
            if not settings['move_files']:
                new_filename = os.path.basename(new_filename)
            win_compat = IS_WIN or settings['windows_compatibility']
            new_filename = make_short_filename(new_dirname, new_filename,
                                               win_compat)
            # TODO: move following logic under util.filenaming
            # (and reconsider its necessity)
            # win32 compatibility fixes
            if win_compat:
                new_filename = new_filename.replace('./', '_/').replace('.\\', '_\\')
            # replace . at the beginning of file and directory names
            # FIXME: even on non-win platforms ???
            new_filename = new_filename.replace('/.', '/_').replace('\\.', '\\_')
            if new_filename.startswith('.'):
                new_filename = '_' + new_filename[1:]
            # Fix for precomposed characters on OSX
            if IS_MACOS:
                new_filename = unicodedata.normalize("NFD", new_filename)
        return new_filename

    def _make_filename(self, filename, metadata, settings=None):
        """Constructs file name based on metadata and file naming formats."""
        if settings is None:
            settings = config.setting
        if settings["move_files"]:
            new_dirname = settings["move_files_to"]
            if not os.path.isabs(new_dirname):
                new_dirname = os.path.normpath(os.path.join(os.path.dirname(filename), new_dirname))
        else:
            new_dirname = os.path.dirname(filename)
        new_filename = os.path.basename(filename)

        if settings["rename_files"]:
            new_filename = self._format_filename(new_dirname, new_filename, metadata, settings)

        new_path = os.path.join(new_dirname, new_filename)
        try:
            return os.path.realpath(new_path)
        except FileNotFoundError:
            # os.path.realpath can fail if cwd doesn't exist
            return new_path

    def _rename(self, old_filename, metadata):
        new_filename, ext = os.path.splitext(
            self._make_filename(old_filename, metadata))

        if old_filename == new_filename + ext:
            return old_filename

        new_dirname = os.path.dirname(new_filename)
        if not os.path.isdir(new_dirname):
            os.makedirs(new_dirname)
        tmp_filename = new_filename
        i = 1
        while (not pathcmp(old_filename, new_filename + ext)
               and os.path.exists(new_filename + ext)):
            new_filename = "%s (%d)" % (tmp_filename, i)
            i += 1
        new_filename = new_filename + ext
        log.debug("Moving file %r => %r", old_filename, new_filename)
        shutil.move(old_filename, new_filename)
        return new_filename

    def _save_images(self, dirname, metadata):
        """Save the cover images to disk."""
        if not metadata.images:
            return
        counters = defaultdict(lambda: 0)
        images = []
        if config.setting["caa_save_single_front_image"]:
            images = [metadata.images.get_front_image()]
        if not images:
            images = metadata.images
        for image in images:
            image.save(dirname, metadata, counters)

    def _move_additional_files(self, old_filename, new_filename):
        """Move extra files, like images, playlists..."""
        new_path = os.path.dirname(new_filename)
        old_path = os.path.dirname(old_filename)
        if new_path == old_path:
            # skip, same directory, nothing to move
            return
        patterns = config.setting["move_additional_files_pattern"]
        pattern_regexes = set()
        for pattern in patterns.split():
            pattern = pattern.strip()
            if not pattern:
                continue
            pattern_regex = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
            match_hidden = pattern.startswith('.')
            pattern_regexes.add((pattern_regex, match_hidden))
        if not pattern_regexes:
            return
        moves = set()
        try:
            # TODO: use with statement with python 3.6+
            for entry in os.scandir(old_path):
                is_hidden = entry.name.startswith('.')
                for pattern_regex, match_hidden in pattern_regexes:
                    if is_hidden and not match_hidden:
                        continue
                    if pattern_regex.match(entry.name):
                        new_file_path = os.path.join(new_path, entry.name)
                        moves.add((entry.path, new_file_path))
                        break  # we are done with this file
        except OSError as why:
            log.error("Failed to scan %r: %s", old_path, why)
            return

        for old_file_path, new_file_path in moves:
            # FIXME we shouldn't do this from a thread!
            if self.tagger.files.get(decode_filename(old_file_path)):
                log.debug("File loaded in the tagger, not moving %r", old_file_path)
                continue
            log.debug("Moving %r to %r", old_file_path, new_file_path)
            try:
                shutil.move(old_file_path, new_file_path)
            except OSError as why:
                log.error("Failed to move %r to %r: %s", old_file_path,
                          new_file_path, why)

    def remove(self, from_parent=True):
        if from_parent and self.parent:
            log.debug("Removing %r from %r", self, self.parent)
            self.parent.remove_file(self)
        self.tagger.acoustidmanager.remove(self)
        self.state = File.REMOVED

    def move(self, parent):
        if parent != self.parent:
            log.debug("Moving %r from %r to %r", self, self.parent, parent)
            self.clear_lookup_task()
            self.tagger._acoustid.stop_analyze(self)
            if self.parent:
                self.clear_pending()
                self.parent.remove_file(self)
            self.parent = parent
            self.parent.add_file(self)
            self._acoustid_update()

    def _move(self, parent):
        if parent != self.parent:
            log.debug("Moving %r from %r to %r", self, self.parent, parent)
            if self.parent:
                self.parent.remove_file(self)
            self.parent = parent
            self._acoustid_update()

    def _acoustid_update(self):
        recording_id = None
        if self.parent and hasattr(self.parent, 'orig_metadata'):
            recording_id = self.parent.orig_metadata['musicbrainz_recordingid']
        if not recording_id:
            recording_id = self.metadata['musicbrainz_recordingid']
        self.tagger.acoustidmanager.update(self, recording_id)

    @classmethod
    def supports_tag(cls, name):
        """Returns whether tag ``name`` can be saved to the file."""
        return True

    def is_saved(self):
        return self.similarity == 1.0 and self.state == File.NORMAL

    def update(self, signal=True):
        new_metadata = self.new_metadata
        names = set(new_metadata.keys())
        names.update(self.orig_metadata.keys())
        clear_existing_tags = config.setting["clear_existing_tags"]
        for name in names:
            if not name.startswith('~') and self.supports_tag(name):
                new_values = new_metadata.getall(name)
                if not (new_values or clear_existing_tags
                        or name in new_metadata.deleted_tags):
                    continue
                orig_values = self.orig_metadata.getall(name)
                if orig_values != new_values:
                    self.similarity = self.orig_metadata.compare(new_metadata)
                    if self.state == File.NORMAL:
                        self.state = File.CHANGED
                    break
        else:
            if (self.metadata.images
                    and self.orig_metadata.images != self.metadata.images):
                self.state = File.CHANGED
            else:
                self.similarity = 1.0
                if self.state == File.CHANGED:
                    self.state = File.NORMAL
        if signal:
            log.debug("Updating file %r", self)
            self.update_item()

    def can_save(self):
        """Return if this object can be saved."""
        return True

    def can_remove(self):
        """Return if this object can be removed."""
        return True

    def can_edit_tags(self):
        """Return if this object supports tag editing."""
        return True

    def can_analyze(self):
        """Return if this object can be fingerprinted."""
        return True

    def can_autotag(self):
        return True

    def can_refresh(self):
        return False

    def can_view_info(self):
        return True

    def _info(self, metadata, file):
        if hasattr(file.info, 'length'):
            metadata.length = int(file.info.length * 1000)
        if hasattr(file.info, 'bitrate') and file.info.bitrate:
            metadata['~bitrate'] = file.info.bitrate / 1000.0
        if hasattr(file.info, 'sample_rate') and file.info.sample_rate:
            metadata['~sample_rate'] = file.info.sample_rate
        if hasattr(file.info, 'channels') and file.info.channels:
            metadata['~channels'] = file.info.channels
        if hasattr(file.info, 'bits_per_sample') and file.info.bits_per_sample:
            metadata['~bits_per_sample'] = file.info.bits_per_sample
        if self.NAME:
            metadata['~format'] = self.NAME
        else:
            metadata['~format'] = self.__class__.__name__.replace('File', '')
        self._add_path_to_metadata(metadata)

    def _add_path_to_metadata(self, metadata):
        metadata['~dirname'] = os.path.dirname(self.filename)
        filename, extension = os.path.splitext(os.path.basename(self.filename))
        metadata['~filename'] = filename
        metadata['~extension'] = extension.lower()[1:]

    @property
    def state(self):
        """Current state of the File object"""
        return self._state

    @state.setter
    def state(self, state):
        if state == self._state:
            return
        if state == File.PENDING:
            File.num_pending_files += 1
            self.tagger.tagger_stats_changed.emit()
        elif self._state == File.PENDING:
            File.num_pending_files -= 1
            self.tagger.tagger_stats_changed.emit()
        self._state = state

    def column(self, column):
        m = self.metadata
        if column == "title" and not m["title"]:
            return self.base_filename
        return m[column]

    def _lookup_finished(self, lookuptype, document, http, error):
        self.lookup_task = None

        if self.state == File.REMOVED:
            return
        if error:
            log.error("Network error encountered during the lookup for %s. Error code: %s",
                      self.filename, error)
        try:
            tracks = document['recordings']
        except (KeyError, TypeError):
            tracks = None

        # no matches
        if not tracks:
            self.tagger.window.set_statusbar_message(
                N_("No matching tracks for file '%(filename)s'"),
                {'filename': self.filename},
                timeout=3000
            )
            self.clear_pending()
            return

        # multiple matches -- calculate similarities to each of them
        best_sim = -1
        for track in tracks:
            match = self.metadata.compare_to_track(track, self.comparison_weights)
            if match[0] > best_sim:
                best_match = match
                best_sim = best_match[0]
        sim, rg, release, track = best_match
        if lookuptype == File.LOOKUP_METADATA and sim < config.setting['file_lookup_threshold']:
            self.tagger.window.set_statusbar_message(
                N_("No matching tracks above the threshold for file '%(filename)s'"),
                {'filename': self.filename},
                timeout=3000
            )
            self.clear_pending()
            return

        self.tagger.window.set_statusbar_message(
            N_("File '%(filename)s' identified!"),
            {'filename': self.filename},
            timeout=3000
        )

        self.clear_pending()

        if lookuptype == File.LOOKUP_ACOUSTID:
            self.tagger.acoustidmanager.add(self, track['id'])
        if release:
            self.tagger.get_release_group_by_id(rg['id']).loaded_albums.add(release['id'])
            self.tagger.move_file_to_track(self, release['id'], track['id'])
        else:
            node = track if 'title' in track else None
            self.tagger.move_file_to_nat(self, track['id'], node=node)

    def lookup_metadata(self):
        """Try to identify the file using the existing metadata."""
        if self.lookup_task:
            return
        self.tagger.window.set_statusbar_message(
            N_("Looking up the metadata for file %(filename)s ..."),
            {'filename': self.filename}
        )
        self.clear_lookup_task()
        metadata = self.metadata
        self.set_pending()
        self.lookup_task = self.tagger.mb_api.find_tracks(
            partial(self._lookup_finished, File.LOOKUP_METADATA),
            track=metadata['title'],
            artist=metadata['artist'],
            release=metadata['album'],
            tnum=metadata['tracknumber'],
            tracks=metadata['totaltracks'],
            qdur=str(metadata.length // 2000),
            isrc=metadata['isrc'],
            limit=QUERY_LIMIT)

    def clear_lookup_task(self):
        if self.lookup_task:
            self.tagger.webservice.remove_task(self.lookup_task)
            self.lookup_task = None

    def set_pending(self):
        if self.state != File.REMOVED:
            self.state = File.PENDING
            self.update_item()

    def clear_pending(self):
        if self.state == File.PENDING:
            self.state = File.NORMAL
            self.update_item()

    def update_item(self):
        if self.item:
            self.item.update()

    def iterfiles(self, save=False):
        yield self

    @property
    def tracknumber(self):
        """The track number as an int."""
        try:
            return int(self.metadata["tracknumber"])
        except BaseException:
            return 0

    @property
    def discnumber(self):
        """The disc number as an int."""
        try:
            return int(self.metadata["discnumber"])
        except BaseException:
            return 0
