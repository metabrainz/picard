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

from functools import partial
from PyQt5 import QtCore
from picard import config, log
from picard.metadata import Metadata, run_track_metadata_processors
from picard.dataobj import DataObject
from picard.util.textencoding import asciipunct
from picard.mbjson import recording_to_metadata
from picard.script import ScriptParser, enabled_tagger_scripts_texts
from picard.const import VARIOUS_ARTISTS_ID, SILENCE_TRACK_TITLE, DATA_TRACK_TITLE
from picard.ui.item import Item
from picard.util.imagelist import update_metadata_images
import traceback


_TRANSLATE_TAGS = {
    "hip hop": "Hip-Hop",
    "synth-pop": "Synthpop",
    "electronica": "Electronic",
}


class TrackArtist(DataObject):
    def __init__(self, ta_id):
        super().__init__(ta_id)


class Track(DataObject, Item):

    metadata_images_changed = QtCore.pyqtSignal()

    def __init__(self, track_id, album=None):
        DataObject.__init__(self, track_id)
        self.album = album
        self.linked_files = []
        self.num_linked_files = 0
        self.metadata = Metadata()
        self.orig_metadata = Metadata()
        self._track_artists = []

    def __repr__(self):
        return '<Track %s %r>' % (self.id, self.metadata["title"])

    def add_file(self, file):
        if file not in self.linked_files:
            self.linked_files.append(file)
            self.num_linked_files += 1
        self.album._add_file(self, file)
        self.update_file_metadata(file)
        file.metadata_images_changed.connect(self.update_orig_metadata_images)

    def update_file_metadata(self, file):
        if file not in self.linked_files:
            return
        file.copy_metadata(self.orig_metadata)
        file.metadata['~extension'] = file.orig_metadata['~extension']
        self.metadata.copy(file.metadata)

        # Re-run tagger scripts with updated metadata
        for s_name, s_text in enabled_tagger_scripts_texts():
            parser = ScriptParser()
            try:
                parser.eval(s_text, file.metadata)
                parser.eval(s_text, self.metadata)
            except:
                log.exception("Failed to run tagger script %s on file", s_name)
            file.metadata.strip_whitespace()
            self.metadata.strip_whitespace()

        file.metadata.changed = True
        file.update(signal=False)
        self.update()

    def remove_file(self, file):
        if file not in self.linked_files:
            return
        self.linked_files.remove(file)
        self.num_linked_files -= 1
        file.copy_metadata(file.orig_metadata)
        self.album._remove_file(self, file)
        file.metadata_images_changed.disconnect(self.update_orig_metadata_images)

        if self.num_linked_files > 0:
            self.metadata.copy(self.linked_files[-1].orig_metadata)
        else:
            self.metadata.copy(self.orig_metadata)

        # Restore to non-associated state
        for s_name, s_text in enabled_tagger_scripts_texts():
            parser = ScriptParser()
            try:
                parser.eval(s_text, self.metadata)
            except:
                log.exception("Failed to run tagger script %s on track", s_name)
            self.metadata.strip_whitespace()

        self.update()

    def update(self):
        if self.item:
            self.item.update()
        self.update_orig_metadata_images()

    def iterfiles(self, save=False):
        for file in self.linked_files:
            yield file

    def is_linked(self):
        return self.num_linked_files > 0

    def can_save(self):
        """Return if this object can be saved."""
        for file in self.linked_files:
            if file.can_save():
                return True
        return False

    def can_remove(self):
        """Return if this object can be removed."""
        for file in self.linked_files:
            if file.can_remove():
                return True
        return False

    def can_edit_tags(self):
        """Return if this object supports tag editing."""
        return True

    def can_view_info(self):
        return self.num_linked_files == 1 or self.metadata.images

    def column(self, column):
        m = self.metadata
        if column == 'title':
            prefix = "%s-" % m['discnumber'] if m['discnumber'] and m['totaldiscs'] != "1" else ""
            return "%s%s  %s" % (prefix, m['tracknumber'].zfill(2), m['title'])
        return m[column]

    def is_video(self):
        return self.metadata['~video'] == '1'

    def is_pregap(self):
        return self.metadata['~pregap'] == '1'

    def is_data(self):
        return self.metadata['~datatrack'] == '1'

    def is_silence(self):
        return self.metadata['~silence'] == '1'

    def is_complete(self):
        return self.ignored_for_completeness() or self.num_linked_files == 1

    def ignored_for_completeness(self):
        if (config.setting['completeness_ignore_videos'] and self.is_video()) \
            or (config.setting['completeness_ignore_pregap'] and self.is_pregap()) \
            or (config.setting['completeness_ignore_data'] and self.is_data()) \
            or (config.setting['completeness_ignore_silence'] and self.is_silence()):
            return True
        return False

    def append_track_artist(self, ta_id):
        """Append artist id to the list of track artists
        and return an TrackArtist instance"""
        track_artist = TrackArtist(ta_id)
        self._track_artists.append(track_artist)
        return track_artist

    def _customize_metadata(self):
        tm = self.metadata

        # Custom VA name
        if tm['musicbrainz_artistid'] == VARIOUS_ARTISTS_ID:
            tm['artistsort'] = tm['artist'] = config.setting['va_name']

        if tm['title'] == DATA_TRACK_TITLE:
            tm['~datatrack'] = '1'

        if tm['title'] == SILENCE_TRACK_TITLE:
            tm['~silence'] = '1'

        if config.setting['folksonomy_tags']:
            self._convert_folksonomy_tags_to_genre()

        # Convert Unicode punctuation
        if config.setting['convert_punctuation']:
            tm.apply_func(asciipunct)

    def _convert_folksonomy_tags_to_genre(self):
        # Combine release and track tags
        tags = dict(self.folksonomy_tags)
        self.merge_folksonomy_tags(tags, self.album.folksonomy_tags)
        if self.album.release_group:
            self.merge_folksonomy_tags(tags, self.album.release_group.folksonomy_tags)
        if not tags and config.setting['artists_tags']:
            # For compilations use each track's artists to look up tags
            if self.metadata['musicbrainz_albumartistid'] == VARIOUS_ARTISTS_ID:
                for artist in self._track_artists:
                    self.merge_folksonomy_tags(tags, artist.folksonomy_tags)
            else:
                for artist in self.album.get_album_artists():
                    self.merge_folksonomy_tags(tags, artist.folksonomy_tags)
        # Ignore tags with zero or lower score
        tags = dict((name, count) for name, count in tags.items() if count > 0)
        if not tags:
            return
        # Convert counts to values from 0 to 100
        maxcount = max(tags.values())
        taglist = []
        for name, count in tags.items():
            taglist.append((100 * count // maxcount, name))
        taglist.sort(reverse=True)
        # And generate the genre metadata tag
        maxtags = config.setting['max_tags']
        minusage = config.setting['min_tag_usage']
        ignore_tags = self._get_ignored_folksonomy_tags()
        genre = []
        for usage, name in taglist[:maxtags]:
            if name.lower() in ignore_tags:
                continue
            if usage < minusage:
                break
            name = _TRANSLATE_TAGS.get(name, name.title())
            genre.append(name)
        join_tags = config.setting['join_tags']
        if join_tags:
            genre = [join_tags.join(genre)]
        self.metadata['genre'] = genre

    def _get_ignored_folksonomy_tags(self):
        tags = []
        ignore_tags = config.setting['ignore_tags']
        if ignore_tags:
            tags = [s.strip().lower() for s in ignore_tags.split(',')]
        return tags

    def update_orig_metadata_images(self):
        update_metadata_images(self)

    def keep_original_images(self):
        for file in self.linked_files:
            file.keep_original_images()
        if self.linked_files:
            self.update_orig_metadata_images()
            self.metadata.images = self.orig_metadata.images[:]
        else:
            self.metadata.images = []
        self.update()


class NonAlbumTrack(Track):

    def __init__(self, nat_id):
        super().__init__(nat_id, self.tagger.nats)
        self.callback = None
        self.loaded = False

    def can_refresh(self):
        return True

    def column(self, column):
        if column == "title":
            return self.metadata["title"]
        return super().column(column)

    def load(self, priority=False, refresh=False):
        self.metadata.copy(self.album.metadata)
        self.metadata["title"] = "[loading track information]"
        self.loaded = False
        self.tagger.nats.update(True)
        mblogin = False
        inc = ["artist-credits", "artists", "aliases"]
        if config.setting["track_ars"]:
            inc += ["artist-rels", "url-rels", "recording-rels",
                    "work-rels", "work-level-rels"]
        if config.setting["folksonomy_tags"]:
            if config.setting["only_my_tags"]:
                mblogin = True
                inc += ["user-tags"]
            else:
                inc += ["tags"]
        if config.setting["enable_ratings"]:
            mblogin = True
            inc += ["user-ratings"]
        self.tagger.mb_api.get_track_by_id(self.id,
                                          partial(self._recording_request_finished),
                                          inc, mblogin=mblogin,
                                          priority=priority,
                                          refresh=refresh)

    def _recording_request_finished(self, recording, http, error):
        if error:
            log.error("%r", http.errorString())
            return
        try:
            self._parse_recording(recording)
            for file in self.linked_files:
                self.update_file_metadata(file)
        except Exception:
            log.error(traceback.format_exc())

    def _parse_recording(self, recording):
        m = self.metadata
        recording_to_metadata(recording, m, self)
        self._customize_metadata()
        run_track_metadata_processors(self.album, m, None, recording)
        self.orig_metadata.copy(m)

        self.loaded = True
        if self.callback:
            self.callback()
            self.callback = None
        self.tagger.nats.update(True)

    def run_when_loaded(self, func):
        if self.loaded:
            func()
        else:
            self.callback = func
