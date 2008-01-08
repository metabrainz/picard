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
import traceback
from PyQt4 import QtCore
from picard.metadata import Metadata
from picard.ui.item import Item
from picard.script import ScriptParser
from picard.similarity import similarity2
from picard.util.thread import proxy_to_main
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
    )


class File(LockableObject, Item):

    __id_counter = 0
    @staticmethod
    def new_id():
        File.__id_counter += 1
        return File.__id_counter

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
        self.state = File.PENDING
        self.error = None

        self.orig_metadata = Metadata()
        self.user_metadata = Metadata()
        self.server_metadata = Metadata()
        self.saved_metadata = self.server_metadata
        self.metadata = self.user_metadata

        self.orig_metadata['title'] = os.path.basename(self.filename)

        self.user_metadata.copy(self.orig_metadata)
        self.server_metadata.copy(self.orig_metadata)

        self.similarity = 1.0
        self.parent = None

    def __repr__(self):
        return '<File #%d %r>' % (self.id, self.base_filename)

    def load(self, next, thread_pool):
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
        filename, extension = os.path.splitext(os.path.basename(self.filename))
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

    def save(self, next, thread_pool, settings):
        metadata = Metadata()
        metadata.copy(self.metadata)
        metadata.strip_whitespace()
        self.tagger.load_queue.put((
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
            self.state = File.ERROR
        else:
            self.error = None
            self.state = File.NORMAL
            self.filename = new_filename = result
            length = self.orig_metadata.length
            self.orig_metadata.copy(self.metadata)
            self.orig_metadata.length = length
            self.metadata.changed = False
        self.update()
        return self, old_filename, new_filename

    def _save(self, filename, metadata, settings):
        """Save the metadata."""
        raise NotImplementedError

    def _script_to_filename(self, format, file_metadata, settings):
        metadata = Metadata()
        metadata.copy(file_metadata)
        # replace incompatible characters
        for name in metadata.keys():
            value = metadata[name]
            if isinstance(value, basestring):
                value = sanitize_filename(value)
                if settings["windows_compatible_filenames"] or sys.platform == "win32":
                    value = replace_win32_incompat(value)
                if settings["ascii_filenames"]:
                    if isinstance(value, unicode):
                        value = unaccent(value)
                    value = replace_non_ascii(value)
                metadata[name] = value
        return ScriptParser().eval(format, metadata)

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
            if metadata['compilation'] == '1':
                format = settings['va_file_naming_format']
            else:
                format = settings['file_naming_format']
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

        return os.path.join(new_dirname, new_filename + ext.lower())

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
            ext = ".jpg" # FIXME
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

    def remove(self, from_parent=True):
        if from_parent and self.parent:
            self.log.debug("Removing %r from %r", self, self.parent)
            self.parent.remove_file(self)
        self.tagger.puidmanager.update(self.metadata['musicip_puid'], self.metadata['musicbrainz_trackid'])
        self.state = File.REMOVED

    def move(self, parent):
        if parent != self.parent:
            self.log.debug("Moving %r from %r to %r", self, self.parent, parent)
            if self.parent:
                self.clear_pending()
                self.parent.remove_file(self)
            self.parent = parent
            self.parent.add_file(self)
            self.tagger.puidmanager.update(self.metadata['musicip_puid'], self.metadata['musicbrainz_trackid'])

    def _move(self, parent):
        if parent != self.parent:
            self.log.debug("Moving %r from %r to %r", self, self.parent, parent)
            if self.parent:
                self.parent.remove_file(self)
            self.parent = parent
            self.tagger.puidmanager.update(self.metadata['musicip_puid'], self.metadata['musicbrainz_trackid'])

    def supports_tag(self, name):
        """Returns whether tag ``name`` can be saved to the file."""
        return True

    def is_saved(self):
        return self.similarity == 1.0 and self.state == File.NORMAL

    def update(self, signal=True):
        for name, values in self.metadata.rawitems():
            if not name.startswith('~') and self.supports_tag(name):
                if self.orig_metadata.getall(name) != values:
                    #print name, values, self.orig_metadata.getall(name)
                    self.similarity = self.orig_metadata.compare(self.metadata)
                    if self.state in (File.CHANGED, File.NORMAL):
                        self.state = File.CHANGED
                    break
        else:
            self.similarity = 1.0
            if self.state in (File.CHANGED, File.NORMAL):
                self.state = File.NORMAL
        if signal:
            self.log.debug("Updating file %r", self)
            self.parent.update_file(self)

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

    def can_refresh(self):
        return False

    def _info(self, metadata, file):
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

    def set_state(self, state, update=False):
        self._state = state
        if update:
            self.update()
        self.tagger.emit(QtCore.SIGNAL("file_state_changed"))

    state = property(get_state, set_state)

    def column(self, column):
        if column == '~length':
            return format_time(self.metadata.length), self.similarity
        else:
            return self.metadata[column], self.similarity

    def _compare_to_track(self, track):
        """
        Compare file metadata to a MusicBrainz track.

        Weigths:
          * title                = 13
          * artist name          = 3
          * release name         = 5
          * length               = 10
          * number of tracks     = 3

        """
        total = 0.0
        parts = []

        if 'title' in self.metadata:
            a = self.metadata['title']
            b = track.title[0].text
            parts.append((similarity2(a, b), 13))
            total += 13

        if 'artist' in self.metadata:
            a = self.metadata['artist']
            b = track.artist[0].name[0].text
            parts.append((similarity2(a, b), 4))
            total += 4

        if 'album' in self.metadata:
            a = self.metadata['album']
            b = track.release_list[0].release[0].title[0].text
            parts.append((similarity2(a, b), 5))
            total += 5

        a = self.metadata.length
        if a > 0 and 'duration' in track.children:
            b = int(track.duration[0].text)
            score = 1.0 - min(abs(a - b), 30000) / 30000.0
            parts.append((score, 10))
            total += 10

        track_list = track.release_list[0].release[0].track_list[0]
        if 'totaltracks' in self.metadata and 'count' in track_list.attribs:
            try:
                a = int(self.metadata['totaltracks'])
                b = int(track_list.count)
                if a > b:
                    score = 0.0
                elif a < b:
                    score = 0.3
                else:
                    score = 1.0
                parts.append((score, 4))
                total += 4
            except ValueError:
                pass

        return reduce(lambda x, y: x + y[0] * y[1] / total, parts, 0.0)

    def _lookup_finished(self, lookuptype, document, http, error):
        try:
            tracks = document.metadata[0].track_list[0].track
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
            matches.append((self._compare_to_track(track), track))
        matches.sort(reverse=True)
        self.log.debug("Track matches: %r", matches)

        if lookuptype == 'puid':
            threshold = self.config.setting['puid_lookup_threshold']
        else:
            threshold = self.config.setting['file_lookup_threshold']

        if matches[0][0] < threshold:
            self.tagger.window.set_statusbar_message(N_("No matching tracks for file %s"), self.filename, timeout=3000)
            self.clear_pending()
            return
        self.tagger.window.set_statusbar_message(N_("File %s identified!"), self.filename, timeout=3000)
        self.clear_pending()

        albumid = matches[0][1].release_list[0].release[0].id
        trackid = matches[0][1].id
        if lookuptype == 'puid':
            self.tagger.puidmanager.add(self.metadata['musicip_puid'], trackid)
        self.tagger.move_file_to_track(self, albumid, trackid)

    def lookup_puid(self, puid):
        """ Try to identify the file using the PUID. """
        self.tagger.window.set_statusbar_message(N_("Looking up the PUID for file %s..."), self.filename)
        self.tagger.xmlws.find_tracks(partial(self._lookup_finished, 'puid'), puid=puid)

    def lookup_metadata(self):
        """ Try to identify the file using the existing metadata. """
        self.tagger.window.set_statusbar_message(N_("Looking up the metadata for file %s..."), self.filename)
        self.tagger.xmlws.find_tracks(partial(self._lookup_finished, 'metadata'),
            track=self.metadata.get('title', ''),
            artist=self.metadata.get('artist', ''),
            release=self.metadata.get('album', ''),
            tnum=self.metadata.get('tracknumber', ''),
            tracks=self.metadata.get('totaltracks', ''),
            qdur=str(self.metadata.length / 2000),
            limit=7)

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
