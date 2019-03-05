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
import traceback

from PyQt5 import QtCore

from picard import (
    config,
    log,
)
from picard.const import (
    DATA_TRACK_TITLE,
    SILENCE_TRACK_TITLE,
    VARIOUS_ARTISTS_ID,
)
from picard.dataobj import DataObject
from picard.mbjson import recording_to_metadata
from picard.metadata import (
    Metadata,
    run_track_metadata_processors,
)
from picard.script import (
    ScriptError,
    ScriptParser,
    enabled_tagger_scripts_texts,
)
from picard.util.imagelist import (
    add_metadata_images,
    remove_metadata_images,
    update_metadata_images,
)
from picard.util.textencoding import asciipunct

from picard.ui.item import Item

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
        self.error = None
        self._track_artists = []

    def __repr__(self):
        return '<Track %s %r>' % (self.id, self.metadata["title"])

    def add_file(self, file):
        if file not in self.linked_files:
            self.linked_files.append(file)
            self.num_linked_files += 1
        self.update_file_metadata(file)
        add_metadata_images(self, [file])
        self.album._add_file(self, file)
        file.metadata_images_changed.connect(self.update_orig_metadata_images)

    def update_file_metadata(self, file):
        if file not in self.linked_files:
            return
        file.copy_metadata(self.metadata)
        file.metadata['~extension'] = file.orig_metadata['~extension']
        file.update(signal=False)
        self.update()

    def remove_file(self, file):
        if file not in self.linked_files:
            return
        self.linked_files.remove(file)
        self.num_linked_files -= 1
        file.copy_metadata(file.orig_metadata, preserve_deleted=False)
        file.metadata_images_changed.disconnect(self.update_orig_metadata_images)
        self.album._remove_file(self, file)
        remove_metadata_images(self, [file])
        self.update()

    def update(self):
        if self.item:
            self.item.update()

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

        if config.setting['use_genres']:
            self._convert_folksonomy_tags_to_genre()

        # Convert Unicode punctuation
        if config.setting['convert_punctuation']:
            tm.apply_func(asciipunct)

    def _convert_folksonomy_tags_to_genre(self):
        # Combine release and track tags
        tags = dict(self.genres)
        self.merge_genres(tags, self.album.genres)
        if self.album.release_group:
            self.merge_genres(tags, self.album.release_group.genres)
        if not tags and config.setting['artists_genres']:
            # For compilations use each track's artists to look up tags
            if self.metadata['musicbrainz_albumartistid'] == VARIOUS_ARTISTS_ID:
                for artist in self._track_artists:
                    self.merge_genres(tags, artist.genres)
            else:
                for artist in self.album.get_album_artists():
                    self.merge_genres(tags, artist.genres)
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
        maxtags = config.setting['max_genres']
        minusage = config.setting['min_genre_usage']
        ignore_genres = self._get_ignored_folksonomy_tags()
        genre = []
        for usage, name in taglist[:maxtags]:
            if name.lower() in ignore_genres:
                continue
            if usage < minusage:
                break
            name = _TRANSLATE_TAGS.get(name, name.title())
            genre.append(name)
        join_genres = config.setting['join_genres']
        if join_genres:
            genre = [join_genres.join(genre)]
        self.metadata['genre'] = genre

    def _get_ignored_folksonomy_tags(self):
        tags = []
        ignore_genres = config.setting['ignore_genres']
        if ignore_genres:
            tags = [s.strip().lower() for s in ignore_genres.split(',')]
        return tags

    def update_orig_metadata_images(self):
        update_metadata_images(self)

    def keep_original_images(self):
        for file in self.linked_files:
            file.keep_original_images()
        self.update_orig_metadata_images()
        if self.linked_files:
            self.metadata.images = self.orig_metadata.images[:]
        else:
            self.metadata.images = []
        self.update()


class NonAlbumTrack(Track):

    def __init__(self, nat_id):
        super().__init__(nat_id, self.tagger.nats)
        self.callback = None
        self.loaded = False
        self.status = None

    def can_refresh(self):
        return True

    def column(self, column):
        if column == "title":
            if self.status is not None:
                return self.status
            else:
                return self.metadata['title']
        return super().column(column)

    def load(self, priority=False, refresh=False):
        self.metadata.copy(self.album.metadata)
        self.status = _("[loading recording information]")
        self.error = None
        self.loaded = False
        self.album.update(True)
        mblogin = False
        inc = ["artist-credits", "artists", "aliases"]
        if config.setting["track_ars"]:
            inc += ["artist-rels", "url-rels", "recording-rels",
                    "work-rels", "work-level-rels"]
        mblogin = self.set_genre_inc_params(inc) or mblogin
        if config.setting["enable_ratings"]:
            mblogin = True
            inc += ["user-ratings"]
        self.tagger.mb_api.get_track_by_id(self.id,
                                           partial(self._recording_request_finished),
                                           inc, mblogin=mblogin,
                                           priority=priority,
                                           refresh=refresh)

    def can_remove(self):
        return True

    def _recording_request_finished(self, recording, http, error):
        if error:
            self._set_error(http.errorString())
            return
        try:
            self._parse_recording(recording)
            for file in self.linked_files:
                self.update_file_metadata(file)
        except Exception:
            self._set_error(traceback.format_exc())

    def _set_error(self, error):
        log.error("%r", error)
        self.status = _("[could not load recording %s]") % self.id
        self.error = error
        self.album.update(True)

    def _parse_recording(self, recording):
        m = self.metadata
        recording_to_metadata(recording, m, self)
        self.orig_metadata.copy(m)
        self._customize_metadata()
        run_track_metadata_processors(self.album, m, None, recording)
        for s_name, s_text in enabled_tagger_scripts_texts():
            parser = ScriptParser()
            try:
                parser.eval(s_text, m)
            except ScriptError:
                log.exception("Failed to run tagger script %s on track", s_name)
            m.strip_whitespace()

        self.loaded = True
        self.status = None
        if self.callback:
            self.callback()
            self.callback = None
        self.album.update(True)

    def _customize_metadata(self):
        super()._customize_metadata()
        self.metadata['album'] = self.album.metadata['album']

    def run_when_loaded(self, func):
        if self.loaded:
            func()
        else:
            self.callback = func
