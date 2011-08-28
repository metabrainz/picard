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

import glob
import os.path
import shutil
import sys
import re
import unicodedata
import traceback
from PyQt4 import QtCore
from picard.mbxml import artist_credit_from_node
from picard.metadata import Metadata
from picard.ui.item import Item
from picard.script import ScriptParser
from picard.similarity import similarity2
from picard.util import (
    call_next,
    decode_filename,
    encode_filename,
    make_short_filename,
    replace_win32_incompat,
    replace_non_ascii,
    sanitize_filename,
    partial,
    unaccent,
    format_time,
    LockableObject,
    pathcmp,
    mimetype
    )


class File(LockableObject, Item):

    __id_counter = 0
    @staticmethod
    def new_id():
        File.__id_counter += 1
        return File.__id_counter

    UNDEFINED = -1
    PENDING = 0
    NORMAL = 1
    CHANGED = 2
    ERROR = 3
    REMOVED = 4

    def __init__(self, filename):
        super(File, self).__init__()
        self.id = self.new_id()
        self.filename = filename
        self.base_filename = os.path.basename(filename)
        self._state = File.UNDEFINED
        self.state = File.PENDING
        self.error = None

        self.orig_metadata = Metadata()
        self.user_metadata = Metadata()
        self.metadata = self.user_metadata

        self.similarity = 1.0
        self.parent = None

        self.lookup_task = None

        self.comparison_weights = {"title": 13, "artist": 4, "album": 5,
            "length": 10, "totaltracks": 4, "releasetype": 20,
            "releasecountry": 2, "format": 2}

        self.item = None

    def __repr__(self):
        return '<File #%d %r>' % (self.id, self.base_filename)

    def load(self, next):
        self.tagger.load_queue.put((
            partial(self._load, self.filename),
            partial(self._loading_finished, next),
            QtCore.Qt.LowEventPriority + 1))

    @call_next
    def _loading_finished(self, next, result=None, error=None):
        if self.state != self.PENDING:
            return
        if error is not None:
            self.error = str(error)
            self.state = self.ERROR
        else:
            self.error = None
            self.state = self.NORMAL
            self._copy_metadata(result)
        self.update()
        return self

    def _copy_metadata(self, metadata):
        filename, extension = os.path.splitext(self.base_filename)
        self.metadata.copy(metadata)
        self.metadata['~extension'] = extension[1:].lower()
        if 'title' not in self.metadata:
            self.metadata['title'] = filename
        if 'tracknumber' not in self.metadata:
            match = re.match("(?:track)?\s*(?:no|nr)?\s*(\d+)", filename, re.I)
            if match:
                try:
                    tracknumber = int(match.group(1))
                except ValueError:
                    pass
                else:
                    self.metadata['tracknumber'] = str(tracknumber)
        self.orig_metadata.copy(self.metadata)

    def has_error(self):
        return self.state == File.ERROR

    def _load(self):
        """Load metadata from the file."""
        raise NotImplementedError

    def save(self, next, settings):
        self.set_pending()
        metadata = Metadata()
        metadata.copy(self.metadata)
        self.tagger.save_queue.put((
            partial(self._save_and_rename, self.filename, metadata, settings),
            partial(self._saving_finished, next),
            QtCore.Qt.LowEventPriority + 2))

    def _save_and_rename(self, old_filename, metadata, settings):
        """Save the metadata."""
        new_filename = old_filename
        if not settings["dont_write_tags"]:
            self._save(old_filename, metadata, settings)
        # Rename files
        if settings["rename_files"] or settings["move_files"]:
            new_filename = self._rename(old_filename, metadata, settings)
        # Move extra files (images, playlists, etc.)
        if settings["move_files"] and settings["move_additional_files"]:
            self._move_additional_files(old_filename, new_filename,
                                        settings)
        # Delete empty directories
        if settings["delete_empty_dirs"]:
            try:
                os.removedirs(encode_filename(os.path.dirname(old_filename)))
            except EnvironmentError:
                pass
        # Save cover art images
        if settings["save_images_to_files"]:
            self._save_images(new_filename, metadata, settings)
        return new_filename

    @call_next
    def _saving_finished(self, next, result=None, error=None):
        old_filename = new_filename = self.filename
        if error is not None:
            self.error = str(error)
            self.set_state(File.ERROR, update=True)
        else:
            self.filename = new_filename = result
            self.base_filename = os.path.basename(new_filename)
            length = self.orig_metadata.length
            temp_info = {}
            for info in ('~#bitrate', '~#sample_rate', '~#channels',
                         '~#bits_per_sample', '~format', '~extension'):
                temp_info[info] = self.orig_metadata[info]
            self.orig_metadata.copy(self.metadata)
            self.orig_metadata.length = length
            for k, v in temp_info.items():
                self.orig_metadata[k] = v
            self.metadata.changed = False
            self.error = None
            self.clear_pending()
        return self, old_filename, new_filename

    def _save(self, filename, metadata, settings):
        """Save the metadata."""
        raise NotImplementedError

    def _script_to_filename(self, format, file_metadata, settings):
        metadata = Metadata()
        metadata.copy(file_metadata)
        # make sure every metadata can safely be used in a path name
        for name in metadata.keys():
            if isinstance(metadata[name], basestring):
                metadata[name] = sanitize_filename(metadata[name])
        format = format.replace("\t", "").replace("\n", "")
        filename = ScriptParser().eval(format, metadata, self)
        # replace incompatible characters
        if settings["windows_compatible_filenames"] or sys.platform == "win32":
            filename = replace_win32_incompat(filename)
        if settings["ascii_filenames"]:
            if isinstance(filename, unicode):
                filename = unaccent(filename)
            filename = replace_non_ascii(filename)
        return filename

    def _make_filename(self, filename, metadata, settings):
        """Constructs file name based on metadata and file naming formats."""
        if settings["move_files"]:
            new_dirname = settings["move_files_to"]
            if not os.path.isabs(new_dirname):
                new_dirname = os.path.normpath(os.path.join(os.path.dirname(filename), new_dirname))
        else:
            new_dirname = os.path.dirname(filename)
        old_dirname = new_dirname
        new_filename, ext = os.path.splitext(os.path.basename(filename))

        if settings["rename_files"]:
            # expand the naming format
            format = settings['file_naming_format']
            if settings['use_va_format'] and metadata['compilation'] == '1':
                format = settings['va_file_naming_format']
            if len(format) > 0:
                new_filename = self._script_to_filename(format, metadata, settings)
                if not settings['move_files']:
                    new_filename = os.path.basename(new_filename)
                new_filename = make_short_filename(new_dirname, new_filename)
                # win32 compatibility fixes
                if settings['windows_compatible_filenames'] or sys.platform == 'win32':
                    new_filename = new_filename.replace('./', '_/').replace('.\\', '_\\')
                # replace . at the beginning of file and directory names
                new_filename = new_filename.replace('/.', '/_').replace('\\.', '\\_')
                if new_filename[0] == '.':
                    new_filename = '_' + new_filename[1:]
                # Fix for precomposed characters on OSX
	            if sys.platform == "darwin":
	                new_filename = unicodedata.normalize("NFD", new_filename)
        return os.path.realpath(os.path.join(new_dirname, new_filename + ext.lower()))

    def _rename(self, old_filename, metadata, settings):
        new_filename, ext = os.path.splitext(
            self._make_filename(old_filename, metadata, settings))
        if old_filename != new_filename + ext:
            new_dirname = os.path.dirname(new_filename)
            if not os.path.isdir(encode_filename(new_dirname)):
                os.makedirs(new_dirname)
            tmp_filename = new_filename
            i = 1
            while (not pathcmp(old_filename, new_filename + ext) and
                   os.path.exists(encode_filename(new_filename + ext))):
                new_filename = "%s (%d)" % (tmp_filename, i)
                i += 1
            new_filename = new_filename + ext
            self.log.debug("Moving file %r => %r", old_filename, new_filename)
            shutil.move(encode_filename(old_filename), encode_filename(new_filename))
            return new_filename
        else:
            return old_filename

    def _save_images(self, filename, metadata, settings):
        """Save the cover images to disk."""
        if not metadata.images:
            return
        overwrite = settings["save_images_overwrite"]
        image_filename = self._script_to_filename(
            settings["cover_image_filename"], metadata, settings)
        if not image_filename:
            image_filename = "cover"
        if os.path.isabs(image_filename):
            filename = image_filename
        else:
            filename = os.path.join(os.path.dirname(filename), image_filename)
        if settings['windows_compatible_filenames'] or sys.platform == 'win32':
            filename = filename.replace('./', '_/').replace('.\\', '_\\')
        filename = encode_filename(filename)
        i = 0
        for mime, data in metadata.images:
            image_filename = filename
            ext = mimetype.get_extension(mime, ".jpg")
            if i > 0:
                image_filename = "%s (%d)" % (filename, i)
            i += 1
            while os.path.exists(image_filename + ext) and not overwrite:
                if os.path.getsize(image_filename + ext) == len(data):
                    self.log.debug("Identical file size, not saving %r", image_filename)
                    break
                image_filename = "%s (%d)" % (filename, i)
                i += 1
            else:
                self.log.debug("Saving cover images to %r", image_filename)
                f = open(image_filename + ext, "wb")
                f.write(data)
                f.close()

    def _move_additional_files(self, old_filename, new_filename, settings):
        """Move extra files, like playlists..."""
        old_path = encode_filename(os.path.dirname(old_filename))
        new_path = encode_filename(os.path.dirname(new_filename))
        patterns = encode_filename(settings["move_additional_files_pattern"])
        patterns = filter(bool, [p.strip() for p in patterns.split()])
        files = []
        for pattern in patterns:
            # FIXME glob1 is not documented, maybe we need our own implemention?
            for old_file in glob.glob1(old_path, pattern):
                new_file = os.path.join(new_path, old_file)
                old_file = os.path.join(old_path, old_file)
                # FIXME we shouldn't do this from a thread!
                if self.tagger.get_file_by_filename(decode_filename(old_file)):
                    self.log.debug("File loaded in the tagger, not moving %r", old_file)
                    continue
                self.log.debug("Moving %r to %r", old_file, new_file)
                shutil.move(old_file, new_file)

    def move(self, parent):
        if parent == self.parent:
            return
        self.log.debug("Moving %r from %r to %r", self, self.parent, parent)
        self.clear_lookup_task()
        self.tagger._ofa.stop_analyze(self)
        old_parent = self.parent
        self.parent = parent
        old_parent.remove_file(self)
        parent.add_file(self)

    def is_saved(self):
        return self.similarity == 1.0 and self.state == File.NORMAL

    def update(self):
        for name, values in self.metadata.rawitems():
            if name.startswith('~'):
                continue
            if self.orig_metadata.getall(name) != values:
                self.similarity = self.orig_metadata.compare(self.metadata)
                if self.state in (File.CHANGED, File.NORMAL):
                    self.state = File.CHANGED
                break
        else:
            self.similarity = 1.0
            if self.state in (File.CHANGED, File.NORMAL):
                self.state = File.NORMAL
        if self.item:
            self.tagger.file_updated.emit(self)
        if self.parent:
            self.parent.update()

    def remove(self):
        if self.state == File.REMOVED:
            return
        self.state = File.REMOVED
        self.clear_lookup_task()
        self.tagger._ofa.stop_analyze(self)
        self.tagger.puidmanager.remove(self.metadata['musicip_puid'])
        del self.tagger.files[self.filename]

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

    def _info(self, metadata, file):
        if hasattr(file.info, 'length'):
            metadata.length = int(file.info.length * 1000)
        if hasattr(file.info, 'bitrate') and file.info.bitrate:
            metadata['~#bitrate'] = file.info.bitrate / 1000.0
        if hasattr(file.info, 'sample_rate') and file.info.sample_rate:
            metadata['~#sample_rate'] = file.info.sample_rate
        if hasattr(file.info, 'channels') and file.info.channels:
            metadata['~#channels'] = file.info.channels
        if hasattr(file.info, 'bits_per_sample') and file.info.bits_per_sample:
            metadata['~#bits_per_sample'] = file.info.bits_per_sample
        metadata['~format'] = self.__class__.__name__.replace('File', '')

    def get_state(self):
        return self._state

    # in order to significantly speed up performance, the number of pending
    #  files is cached
    num_pending_files = 0

    def set_state(self, state, update=False):
        if state != self._state:
            if state == File.PENDING:
                File.num_pending_files += 1
            elif self._state == File.PENDING:
                File.num_pending_files -= 1
        self._state = state
        if update:
            self.update()
        self.tagger.file_state_changed.emit(File.num_pending_files)

    state = property(get_state, set_state)

    def column(self, column):
        m = self.orig_metadata
        if column == '~length':
            return format_time(m.length)
        elif column == "title" and not m["title"]:
            return self.base_filename
        else:
            return m[column]

    def _compare_to_track(self, track):
        """
        Compare file metadata to a MusicBrainz track.

        Weigths:
          * title                = 13
          * artist name          = 4
          * release name         = 5
          * length               = 10
          * number of tracks     = 4
          * album type           = 20
          * release country      = 2
          * format               = 2

        """
        total = 0.0
        parts = []
        w = self.comparison_weights

        if 'title' in self.metadata:
            a = self.metadata['title']
            b = track.title[0].text
            parts.append((similarity2(a, b), w["title"]))
            total += w["title"]

        if 'artist' in self.metadata:
            a = self.metadata['artist']
            b = artist_credit_from_node(track.artist_credit[0], self.config)[0]
            parts.append((similarity2(a, b), w["artist"]))
            total += w["artist"]

        a = self.metadata.length
        if a > 0 and 'length' in track.children:
            b = int(track.length[0].text)
            score = 1.0 - min(abs(a - b), 30000) / 30000.0
            parts.append((score, w["length"]))
            total += w["length"]

        releases = []
        if "release_list" in track.children and "release" in track.release_list[0].children:
            releases = track.release_list[0].release

        if not releases:
            return (total, None)

        scores = []
        for release in releases:
            t, p = self.metadata.compare_to_release(release, w, self.config)
            total_ = total + t
            parts_ = list(parts) + p
            scores.append((reduce(lambda x, y: x + y[0] * y[1] / total_, parts_, 0.0), release.id))

        return max(scores, key=lambda x: x[0])

    def _lookup_finished(self, lookuptype, document, http, error):
        self.lookup_task = None

        if self.state == File.REMOVED:
            return

        try:
            m = document.metadata[0]
            if lookuptype == "metadata":
                tracks = m.recording_list[0].recording
            elif lookuptype == "puid":
                tracks = m.puid[0].recording_list[0].recording
            elif lookuptype == "trackid":
                tracks = m.recording
        except (AttributeError, IndexError):
            tracks = None

        # no matches
        if not tracks:
            self.tagger.window.set_statusbar_message(N_("No matching tracks for file %s"), self.filename, timeout=3000)
            self.clear_pending()
            return

        # multiple matches -- calculate similarities to each of them
        matches = []
        for track in tracks:
            score, release = self._compare_to_track(track)
            matches.append((score, track, release))
        matches.sort(reverse=True)
        #self.log.debug("Track matches: %r", matches)

        if lookuptype != 'puid':
            threshold = self.config.setting['file_lookup_threshold']
            if matches[0][0] < threshold:
                self.tagger.window.set_statusbar_message(N_("No matching tracks above the threshold for file %s"), self.filename, timeout=3000)
                self.clear_pending()
                return
        self.tagger.window.set_statusbar_message(N_("File %s identified!"), self.filename, timeout=3000)
        self.clear_pending()

        albumid = matches[0][2]
        track = matches[0][1]
        if lookuptype == 'puid':
            self.tagger.puidmanager.add(self.metadata['musicip_puid'], track.id)
        if albumid:
            self.tagger.move_file_to_track(self, albumid, track.id)
        else:
            self.tagger.move_file_to_nat(self, track.id, node=track)

    def lookup_puid(self, puid):
        """ Try to identify the file using the PUID. """
        self.tagger.window.set_statusbar_message(N_("Looking up the PUID for file %s..."), self.filename)
        self.clear_lookup_task()
        self.lookup_task = self.tagger.xmlws.lookup_puid(puid, partial(self._lookup_finished, 'puid'))

    def lookup_metadata(self):
        """ Try to identify the file using the existing metadata. """
        self.tagger.window.set_statusbar_message(N_("Looking up the metadata for file %s..."), self.filename)
        self.clear_lookup_task()
        self.lookup_task = self.tagger.xmlws.find_tracks(partial(self._lookup_finished, 'metadata'),
            track=self.metadata.get('title', ''),
            artist=self.metadata.get('artist', ''),
            release=self.metadata.get('album', ''),
            tnum=self.metadata.get('tracknumber', ''),
            tracks=self.metadata.get('totaltracks', ''),
            qdur=str(self.metadata.length / 2000),
            limit=25)

    def clear_lookup_task(self):
        if self.lookup_task:
            self.tagger.xmlws.remove_task(self.lookup_task)
            self.lookup_task = None

    def set_pending(self):
        if self.state == File.REMOVED:
            return
        self.state = File.PENDING
        self.update()

    def clear_pending(self):
        if self.state == File.PENDING:
            self.state = File.NORMAL
            self.update()

    def iterfiles(self, save=False):
        yield self

    def _get_tracknumber(self):
        try:
            return int(self.metadata["tracknumber"])
        except:
            return 0
    tracknumber = property(_get_tracknumber, doc="The track number as an int.")

    def _get_discnumber(self):
        try:
            return int(self.metadata["discnumber"])
        except:
            return 0
    discnumber = property(_get_discnumber, doc="The disc number as an int.")
