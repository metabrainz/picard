# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2007, 2011 Lukáš Lalinský
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2010, 2014-2015, 2018-2021 Philipp Wolfer
# Copyright (C) 2011 Chad Wilson
# Copyright (C) 2011 Wieland Hoffmann
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2014, 2017 Sophist-UK
# Copyright (C) 2014-2015, 2018-2019 Laurent Monin
# Copyright (C) 2016 Mark Trolley
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016 Suhas
# Copyright (C) 2017 Antonio Larrosa
# Copyright (C) 2017-2018 Sambhav Kothari
# Copyright (C) 2018 Calvin Walton
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2019 Joel Lintunen
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
from itertools import filterfalse
import re
import traceback

from PyQt5 import QtCore

from picard import log
from picard.config import get_config
from picard.const import (
    DATA_TRACK_TITLE,
    SILENCE_TRACK_TITLE,
    VARIOUS_ARTISTS_ID,
)
from picard.dataobj import DataObject
from picard.file import (
    run_file_post_addition_to_track_processors,
    run_file_post_removal_from_track_processors,
)
from picard.mbjson import recording_to_metadata
from picard.metadata import (
    Metadata,
    MultiMetadataProxy,
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
)
from picard.util.textencoding import asciipunct

from picard.ui.item import FileListItem


_TRANSLATE_TAGS = {
    "hip hop": "Hip-Hop",
    "synth-pop": "Synthpop",
    "electronica": "Electronic",
}


class TagGenreFilter:

    def __init__(self, filters):
        self.errors = dict()
        self.match_regexes = defaultdict(list)
        for lineno, line in enumerate(filters.splitlines()):
            line = line.strip()
            if line and line[0] in ('+', '-'):
                _list = line[0]
                remain = line[1:].strip()
                if not remain:
                    continue
                if len(remain) > 2 and remain[0] == '/' and remain[-1] == '/':
                    remain = remain[1:-1]
                    try:
                        regex_search = re.compile(remain, re.IGNORECASE)
                    except Exception as e:
                        log.error("Failed to compile regex /%s/: %s", remain, e)
                        self.errors[lineno] = str(e)
                        regex_search = None
                else:
                    # FIXME?: only support '*' (not '?' or '[abc]')
                    # replace multiple '*' by one
                    star = re.escape('*')
                    remain = re.sub(star + '+', '*', remain)
                    regex = '.*'.join([re.escape(x) for x in remain.split('*')])
                    regex_search = re.compile('^' + regex + '$', re.IGNORECASE)
                if regex_search:
                    self.match_regexes[_list].append(regex_search)

    def skip(self, tag):
        if not self.match_regexes:
            return False
        for regex in self.match_regexes['+']:
            if regex.search(tag):
                return False
        for regex in self.match_regexes['-']:
            if regex.search(tag):
                return True
        return False

    def filter(self, list_of_tags):
        return list(filterfalse(self.skip, list_of_tags))


class TrackArtist(DataObject):
    def __init__(self, ta_id):
        super().__init__(ta_id)


class Track(DataObject, FileListItem):

    metadata_images_changed = QtCore.pyqtSignal()

    def __init__(self, track_id, album=None):
        DataObject.__init__(self, track_id)
        FileListItem.__init__(self)
        self.metadata = Metadata()
        self.orig_metadata = Metadata()
        self.album = album
        self.num_linked_files = 0
        self.scripted_metadata = Metadata()
        self._track_artists = []

    def __repr__(self):
        return '<Track %s %r>' % (self.id, self.metadata["title"])

    @property
    def linked_files(self):
        """For backward compatibility with old code in plugins"""
        return self.files

    def add_file(self, file, new_album=True):
        if file not in self.files:
            track_will_expand = self.num_linked_files == 1
            self.files.append(file)
            self.num_linked_files += 1
        self.update_file_metadata(file)
        add_metadata_images(self, [file])
        self.album._add_file(self, file, new_album=new_album)
        file.metadata_images_changed.connect(self.update_metadata_images)
        run_file_post_addition_to_track_processors(self, file)
        if track_will_expand:
            # Files get expanded, ensure the existing item renders correctly
            self.files[0].update_item()

    def update_file_metadata(self, file):
        if file not in self.files:
            return
        # Run the scripts for the file to allow usage of
        # file specific metadata and variables
        config = get_config()
        if config.setting["clear_existing_tags"]:
            metadata = Metadata(self.orig_metadata)
            metadata_proxy = MultiMetadataProxy(metadata, file.metadata)
            self.run_scripts(metadata_proxy)
        else:
            metadata = Metadata(file.metadata)
            metadata.update(self.orig_metadata)
            self.run_scripts(metadata)
        # Apply changes to the track's metadata done manually after the scripts ran
        meta_diff = self.metadata.diff(self.scripted_metadata)
        metadata.update(meta_diff)
        # Images are not affected by scripting, always use the tracks current images
        metadata.images = self.metadata.images
        file.copy_metadata(metadata)
        file.update(signal=False)
        self.update()

    def remove_file(self, file, new_album=True):
        if file not in self.files:
            return
        self.files.remove(file)
        self.num_linked_files -= 1
        file.metadata_images_changed.disconnect(self.update_metadata_images)
        file.copy_metadata(file.orig_metadata, preserve_deleted=False)
        self.album._remove_file(self, file, new_album=new_album)
        remove_metadata_images(self, [file])
        run_file_post_removal_from_track_processors(self, file)
        self.update()
        if self.item.isSelected():
            self.tagger.window.refresh_metadatabox()

    @staticmethod
    def run_scripts(metadata):
        for s_name, s_text in enabled_tagger_scripts_texts():
            parser = ScriptParser()
            try:
                parser.eval(s_text, metadata)
            except ScriptError:
                log.exception("Failed to run tagger script %s on track", s_name)
            metadata.strip_whitespace()

    def update(self):
        if self.item:
            self.item.update()

    def is_linked(self):
        return self.num_linked_files > 0

    def can_save(self):
        """Return if this object can be saved."""
        for file in self.files:
            if file.can_save():
                return True
        return False

    def can_remove(self):
        """Return if this object can be removed."""
        for file in self.files:
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
        if column == 'covercount':
            return self.metadata._cover_art_description("yes")
        elif column in m:
            return m[column]
        elif self.num_linked_files == 1:
            return self.files[0].column(column)

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
        config = get_config()
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
        config = get_config()
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
        config = get_config()
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
        tag_filter = TagGenreFilter(config.setting['genres_filter'])
        genre = []
        for usage, name in taglist[:maxtags]:
            if tag_filter.skip(name):
                continue
            if usage < minusage:
                break
            name = _TRANSLATE_TAGS.get(name, name.title())
            genre.append(name)
        genre.sort()
        join_genres = config.setting['join_genres']
        if join_genres:
            genre = [join_genres.join(genre)]
        self.metadata['genre'] = genre


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
        self.metadata.copy(self.album.metadata, copy_images=False)
        self.status = _("[loading recording information]")
        self.clear_errors()
        self.loaded = False
        self.album.update(True)
        config = get_config()
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
                                           self._recording_request_finished,
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
            for file in self.files:
                self.update_file_metadata(file)
        except Exception:
            self._set_error(traceback.format_exc())

    def _set_error(self, error):
        self.error_append(error)
        self.status = _("[could not load recording %s]") % self.id
        self.album.update(True)

    def _parse_recording(self, recording):
        m = self.metadata
        recording_to_metadata(recording, m, self)
        self._customize_metadata()
        run_track_metadata_processors(self.album, m, recording)
        self.orig_metadata.copy(m)
        self.run_scripts(m)
        self.loaded = True
        self.status = None
        if self.callback:
            self.callback()
            self.callback = None
        self.album.update(True)

    def _customize_metadata(self):
        super()._customize_metadata()
        self.metadata['album'] = self.album.metadata['album']
        if self.metadata['~recording_firstreleasedate']:
            self.metadata['originaldate'] = self.metadata['~recording_firstreleasedate']
            self.metadata['originalyear'] = self.metadata['originaldate'][:4]

    def run_when_loaded(self, func):
        if self.loaded:
            func()
        else:
            self.callback = func
