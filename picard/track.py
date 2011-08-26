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
from picard.metadata import Metadata
from picard.dataobj import DataObject
from picard.ui.item import Item
from picard.util import format_time, translate_artist, asciipunct, partial
from picard.mbxml import recording_to_metadata
from picard.script import ScriptParser
from picard.const import VARIOUS_ARTISTS_ID
import string
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
        self.metadata = Metadata()
        self.item = None

    def __repr__(self):
        return '<Track %s %r>' % (self.id, self.metadata["title"])

    def add_file(self, file):
        if file in self.linked_files:
            return
        self.linked_files.append(file)
        self.album._files += 1
        self.album.update(update_tracks=False)
        self.update_file(file)

    def remove_file(self, file):
        self.linked_files.remove(file)
        file.metadata.copy(file.orig_metadata)
        self.album._files -= 1
        self.update()

    def update_file(self, file):
        file.metadata.copy(self.metadata)
        puid = file.orig_metadata["musicip_puid"]
        if puid:
            file.metadata["musicip_puid"] = puid
            self.tagger.puidmanager.update(puid, self.id)
        file.metadata["~extension"] = file.orig_metadata["~extension"]
        file.metadata.changed = True
        file.update()

    def update(self):
        self.item.update()
        self.album.update(update_tracks=False)

    def remove(self):
        for file in list(self.linked_files):
            self.remove_file(file)
            file.remove()
        if self.linked_files > 1:
            self.item.clear_rows()
        self.linked_files = []
        self.update()

    def iterfiles(self, save=False):
        for file in self.linked_files:
            yield file

    def is_linked(self):
        return len(self.linked_files) > 0

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
        for file in self.linked_files:
            if file.can_edit_tags():
                return True
        return False

    def column(self, column):
        m = self.metadata
        if column == 'title':
            return u"%s  %s" % (m['tracknumber'].zfill(2), m['title'])
        elif column == '~length':
            return format_time(m.length)
        else:
            return m[column]

    def _customize_metadata(self, ignore_tags=None):
        tm = self.metadata

        # 'Translate' artist name
        if self.config.setting['translate_artist_names']:
            tm['artist'] = translate_artist(tm['artist'], tm['artistsort'])

        # Custom VA name
        if tm['musicbrainz_artistid'] == VARIOUS_ARTISTS_ID:
            tm['artistsort'] = tm['artist'] = self.config.setting['va_name']

        if self.config.setting['folksonomy_tags']:
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
            ignore_tags = self.config.setting["ignore_tags"]
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

            tm['genre'] = genre

        # Convert Unicode punctuation
        if self.config.setting['convert_punctuation']:
            tm.apply_func(asciipunct)


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
            return u"%s" % self.metadata["title"]
        else:
            return super(NonAlbumTrack, self).column(column)

    def load(self):
        inc = ["artist-credits"]
        mblogin = False
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
                self.update_file(file)
        except:
            self.log.error(traceback.format_exc())

    def _parse_recording(self, recording):
        recording_to_metadata(recording, self, self.config)
        if self.config.setting["enable_tagger_script"]:
            script = self.config.setting["tagger_script"]
            parser = ScriptParser()
        else:
            script = parser = None
        self._customize_metadata()
        self.loaded = True
        if self.callback:
            self.callback()
        self.tagger.nats.update(True)

    def run_when_loaded(self, func):
        if self.loaded:
            func()
        else:
            self.callback = func
