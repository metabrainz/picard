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

from PyQt4 import QtCore
from picard.metadata import Metadata, run_track_metadata_processors
from picard.dataobj import DataObject
from picard.util import format_time, asciipunct, partial
from picard.mbxml import recording_to_metadata
from picard.script import ScriptParser
from picard.const import VARIOUS_ARTISTS_ID
from picard.ui.item import Item
import traceback


_TRANSLATE_TAGS = {
    "hip hop": u"Hip-Hop",
    "synth-pop": u"Synthpop",
    "electronica": u"Electronic",
}


class Track(DataObject, Item):

    def __init__(self, id, album=None):
        DataObject.__init__(self, id)
        self.album = album
        self.linked_files = []
        self.num_linked_files = 0
        self.metadata = Metadata()
        self.extra_file_tags = {}

    def __repr__(self):
        return '<Track %s %r>' % (self.id, self.metadata["title"])

    def add_file(self, file):
        if file not in self.linked_files:
            self.linked_files.append(file)
            self.num_linked_files += 1
        self.album._add_file(self, file)
        self.update_file_metadata(file)

    def update_file_metadata(self, file):
        if file not in self.linked_files:
            return
        self.extra_file_tags[file.id] = {}
        for tag in ['musicip_puid', 'acoustid_id']:
            self.metadata[tag] = file.metadata[tag]
            self.extra_file_tags[file.id][tag] = file.metadata[tag]
        file.metadata.copy(self.metadata)
        file.metadata['~extension'] = file.orig_metadata['~extension']
        file.metadata.changed = True
        file.update(signal=False)
        self.update()

    def remove_file(self, file):
        if file not in self.linked_files:
            return
        self.linked_files.remove(file)
        self.num_linked_files -= 1
        file.metadata.copy(file.orig_metadata)
        file_tags = self.extra_file_tags.pop(file.id)
        for k, v in file_tags.items():
            file.metadata[k] = v
            if k in self.metadata:
                del self.metadata[k]
        self.album._remove_file(self, file)
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
        return self.num_linked_files == 1

    def column(self, column):
        m = self.metadata
        if column == 'title':
            prefix = "%s-" % m['discnumber'] if m['totaldiscs'] != "1" else ""
            return u"%s%s  %s" % (prefix, m['tracknumber'].zfill(2), m['title'])
        return m[column]

    def _customize_metadata(self):
        tm = self.metadata

        # Custom VA name
        if tm['musicbrainz_artistid'] == VARIOUS_ARTISTS_ID:
            tm['artistsort'] = tm['artist'] = self.config.setting['va_name']

        if self.config.setting['folksonomy_tags']:
            self._convert_folksonomy_tags_to_genre()

        # Convert Unicode punctuation
        if self.config.setting['convert_punctuation']:
            tm.apply_func(asciipunct)

    def _convert_folksonomy_tags_to_genre(self):
        # Combine release and track tags
        tags = dict(self.folksonomy_tags)
        for name, count in self.album.folksonomy_tags.iteritems():
            tags.setdefault(name, 0)
            tags[name] += count
        if not tags:
            return
        # Convert counts to values from 0 to 100
        maxcount = max(tags.values())
        taglist = []
        for name, count in tags.items():
            taglist.append((100 * count / maxcount, name))
        taglist.sort(reverse=True)
        # And generate the genre metadata tag
        maxtags = self.config.setting['max_tags']
        minusage = self.config.setting['min_tag_usage']
        ignore_tags = self.config.setting['ignore_tags']
        genre = []
        for usage, name in taglist[:maxtags]:
            if name in ignore_tags:
                continue
            if usage < minusage:
                break
            name = _TRANSLATE_TAGS.get(name, name.title())
            genre.append(name)
        join_tags = self.config.setting['join_tags']
        if join_tags:
            genre = [join_tags.join(genre)]
        self.metadata['genre'] = genre


class NonAlbumTrack(Track):

    def __init__(self, id):
        super(NonAlbumTrack, self).__init__(id, self.tagger.nats)
        self.metadata.copy(self.album.metadata)
        self.metadata["title"] = "[loading track information]"
        self.callback = None
        self.loaded = False

    def can_refresh(self):
        return True

    def column(self, column):
        if column == "title":
            return self.metadata["title"]
        return Track.column(self, column)

    def load(self):
        inc = ["artist-credits", "artists", "aliases"]
        mblogin = False
        if self.config.setting["track_ars"]:
            inc += ["artist-rels", "url-rels", "recording-rels", "work-rels", "work-level-rels"]
        if self.config.setting["folksonomy_tags"]:
            if self.config.setting["only_my_tags"]:
                mblogin = True
                inc += ["user-tags"]
            else:
                inc += ["tags"]
        if self.config.setting["enable_ratings"]:
            mblogin = True
            inc += ["user-ratings"]
        self.tagger.xmlws.get_track_by_id(self.id, partial(self._recording_request_finished), inc, mblogin=mblogin)

    def _recording_request_finished(self, document, http, error):
        if error:
            self.log.error("%r", unicode(http.errorString()))
            return
        try:
            recording = document.metadata[0].recording[0]
            self._parse_recording(recording)
            for file in self.linked_files:
                self.update_file_metadata(file)
        except:
            self.log.error(traceback.format_exc())

    def _parse_recording(self, recording):
        recording_to_metadata(recording, self, self.config)
        self._customize_metadata()
        m = self.metadata
        run_track_metadata_processors(self.album, m, None, recording)
        if self.config.setting["enable_tagger_script"]:
            script = self.config.setting["tagger_script"]
            if script:
                parser = ScriptParser()
                try:
                    parser.eval(script, m)
                except:
                    self.log.error(traceback.format_exc())
                m.strip_whitespace()
        self.loaded = True
        if self.callback:
            self.callback()
        self.tagger.nats.update(True)

    def run_when_loaded(self, func):
        if self.loaded:
            func()
        else:
            self.callback = func
