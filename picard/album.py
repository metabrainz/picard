# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2007 Lukáš Lalinský
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

import traceback
from PyQt4 import QtCore
from picard.metadata import Metadata, run_album_metadata_processors, run_track_metadata_processors
from picard.dataobj import DataObject
from picard.track import Track
from picard.script import ScriptParser
from picard.ui.item import Item
from picard.util import format_time, partial, translate_artist
from picard.cluster import Cluster
from picard.mbxml import release_to_metadata, track_to_metadata


VARIOUS_ARTISTS_ID = '89ad4ac3-39f7-470e-963a-56509c546377'


_TRANSLATE_TAGS = {
    "hip hop": u"Hip-Hop",
    "synth-pop": u"Synthpop",
    "electronica": u"Electronic",
}


class ReleaseEvent(object):

    ATTRS = ['date', 'releasecountry', 'label', 'barcode', 'catalognumber', 'format']

    def __init__(self):
        for attr in self.ATTRS:
            setattr(self, attr, None)

    def to_metadata(self, m):
        for attr in self.ATTRS:
            val = getattr(self, attr)
            if val is not None:
                m[attr] = val
            else:
                try: del m[attr]
                except KeyError: pass


class Album(DataObject, Item):

    def __init__(self, id, catalognumber=None):
        DataObject.__init__(self, id)
        self.metadata = Metadata()
        self.unmatched_files = Cluster(_("Unmatched Files"), special=2)
        self.tracks = []
        self.loaded = False
        self._files = 0
        self._requests = 0
        self._catalognumber = catalognumber
        self.current_release_event = None
        self.release_events = []

    def __repr__(self):
        return '<Album %s %r>' % (self.id, self.metadata[u"album"])

    def iterfiles(self, save=False):
        for track in self.tracks:
            for file in track.iterfiles():
                yield file
        if not save:
            for file in self.unmatched_files.iterfiles():
                yield file

    def _convert_folksonomy_tags_to_genre(self, track):
        # Combine release and track tags
        tags = dict(self.folksonomy_tags)
        for name, count in track.folksonomy_tags:
            tags.setdefault(name, 0)
            tags[name] += count
        if not tags:
            return
        # Convert counts to values from 0 to 100
        maxcount = max(tags.values())
        taglist = []
        for name, count in tags.items():
            taglist.append((100 * maxcount / count, name))
        taglist.sort(reverse=True)
        # And generate the genre metadata tag
        maxtags = self.config.setting['max_tags']
        minusage = self.config.setting['min_tag_usage']
        genre = []
        for usage, name in taglist[:maxtags]:
            if usage < minusage:
                break
            name = _TRANSLATE_TAGS.get(name, name.title())
            genre.append(name)
        join_tags = self.config.setting['join_tags']
        if join_tags:
            genre = [join_tags.join(genre)]
        track.metadata['genre'] = genre

    def _parse_release(self, document):
        self.log.debug("Loading release %r", self.id)

        # Get release metadata
        m = self._new_metadata
        m.length = 0
        release_node = document.metadata[0].release[0]
        self.release_events = []
        release_to_metadata(release_node, m, config=self.config, album=self)

        self.current_release_event = None
        for rel in self.release_events:
            if self._catalognumber and rel.catalognumber == self._catalognumber:
                self.current_release_event = rel
                break
        else:
            if self.release_events:
                preferred_events = [rel for rel in self.release_events
                                    if rel.releasecountry == self.config.setting["preferred_release_country"]]
                if preferred_events:
                    self.current_release_event = preferred_events[0]
                else:
                    self.current_release_event = self.release_events[0]
        if self.current_release_event:
            self.current_release_event.to_metadata(m)

        # 'Translate' artist name
        if self.config.setting['translate_artist_names']:
            m['albumartist'] = m['artist'] = translate_artist(m['artist'], m['artistsort'])

        # Custom VA name
        if m['musicbrainz_artistid'] == VARIOUS_ARTISTS_ID:
            m['albumartistsort'] = m['artistsort'] = m['albumartist'] = m['artist'] = self.config.setting['va_name']

        # Album metadata plugins
        try:
            run_album_metadata_processors(self, m, release_node)
        except:
            self.log.error(traceback.format_exc())

        # Prepare parser for user's script
        if self.config.setting["enable_tagger_script"]:
            script = self.config.setting["tagger_script"]
            parser = ScriptParser()
        else:
            script = None

        # Strip leading/trailing whitespace
        m.strip_whitespace()

        artists = set()
        for i, node in enumerate(release_node.track_list[0].track):
            t = Track(node.attribs['id'], self)
            self._new_tracks.append(t)

            # Get track metadata
            tm = t.metadata
            tm.copy(m)
            tm['tracknumber'] = str(i + 1)
            track_to_metadata(node, tm, config=self.config, track=t)
            artists.add(tm['musicbrainz_artistid'])
            m.length += tm.length

            # 'Translate' artist name
            if self.config.setting['translate_artist_names']:
                tm['artist'] = translate_artist(tm['artist'], tm['artistsort'])

            # Custom VA name
            if tm['musicbrainz_artistid'] == VARIOUS_ARTISTS_ID:
                tm['artistsort'] = tm['artist'] = self.config.setting['va_name']

            if self.config.setting['folksonomy_tags']:
                self._convert_folksonomy_tags_to_genre(t)

            # Track metadata plugins
            try:
                run_track_metadata_processors(self, tm, release_node, node)
            except:
                self.log.error(traceback.format_exc())

        if len(artists) > 1:
            for t in self._new_tracks:
                t.metadata['compilation'] = '1'

        if script:
            for track in self._new_tracks:
                # Run TaggerScript
                try:
                    parser.eval(script, track.metadata)
                except:
                    self.log.error(traceback.format_exc())
                # Strip leading/trailing whitespace
                track.metadata.strip_whitespace()

    def _release_request_finished(self, document, http, error):
        try:
            if error:
                self.log.error("%r", unicode(http.errorString()))
            else:
                try:
                    self._parse_release(document)
                except:
                    error = True
                    self.log.error(traceback.format_exc())
        finally:
            self._requests -= 1
            self._finalize_loading(error)

    def _finalize_loading(self, error):
        if error:
            self.metadata.clear()
            self.metadata['album'] = _("[couldn't load album %s]") % self.id
            del self._new_metadata
            del self._new_tracks
            self.update()
        else:
            if not self._requests:
                for old_track, new_track in zip(self.tracks, self._new_tracks):
                    if old_track.linked_file:
                        new_track.linked_file = old_track.linked_file
                        new_track.linked_file.parent = new_track
                        new_track.linked_file.metadata.copy(new_track.metadata)
                        new_track.linked_file.update(signal=False)
                for track in self.tracks[len(self._new_tracks):]:
                    if track.linked_file:
                        track.linked_file.move(self.unmatched_files)
                self.metadata = self._new_metadata
                self.tracks = self._new_tracks
                del self._new_metadata
                del self._new_tracks
                self.loaded = True
                self.update()
                self.tagger.window.set_statusbar_message('Album %s loaded', self.id, timeout=3000)
                self.match_files(self.unmatched_files.files)

    def load(self, force=False):
        if self._requests:
            self.log.info("Not reloading, some requests are still active.")
            return
        self.tagger.window.set_statusbar_message('Loading album %s...', self.id)
        self.loaded = False
        self.metadata.clear()
        self.metadata['album'] = _("[loading album information]")
        self.update()
        self._new_metadata = Metadata()
        self._new_tracks = []
        self._requests = 1
        inc = ['tracks', 'puids', 'artist', 'release-events', 'labels']
        if self.config.setting['release_ars'] or self.config.setting['track_ars']:
            inc += ['artist-rels', 'url-rels']
            if self.config.setting['track_ars']:
                inc += ['track-level-rels']
        if self.config.setting['folksonomy_tags']:
            inc += ['tags']
        self.tagger.xmlws.get_release_by_id(self.id, self._release_request_finished, inc=inc)

    def update(self, update_tracks=True):
        self.tagger.emit(QtCore.SIGNAL("album_updated"), self, update_tracks)

    def _add_file(self, track, file):
        self._files += 1
        self.update(False)

    def _remove_file(self, track, file):
        self._files -= 1
        self.update(False)

    def match_files(self, files):
        """Match files on tracks on this album, based on metadata similarity."""
        matches = []
        #print "Files:"
        #print [file.metadata for file in files]
        #print "Tracks:"
        #print [track.metadata for track in self.tracks]
        for file in files:
            trackid = file.metadata['musicbrainz_trackid']
            for track in self.tracks:
                if trackid == track.metadata['musicbrainz_trackid']:
                    matches.append((2.0, file, track))
                    break
                sim = track.metadata.compare(file.orig_metadata)
                matches.append((sim, file, track))
        matches.sort(reverse=True)
        #for sim, file, track in matches:
        #    print sim, file.metadata["title"], track.metadata["title"]
        matched = {}
        for sim, file, track in matches:
            if sim < self.config.setting['track_matching_threshold']:
                break
            if file in matched or track in matched.values():
                continue
            if track.linked_file and sim < track.linked_file.similarity:
                continue
            matched[file] = track
        unmatched = [f for f in files if f not in matched]
        for file, track in matched.items():
            file.move(track)
        for file in unmatched:
            file.move(self.unmatched_files)

    def match_file(self, file, trackid=None):
        """Match the file on a track on this album, based on trackid or metadata similarity."""
        if trackid is not None:
            for track in self.tracks:
                if track.metadata['musicbrainz_trackid'] == trackid:
                    file.move(track)
                    return
        self.match_files([file])

    def can_save(self):
        return self._files > 0

    def can_remove(self):
        return True

    def can_edit_tags(self):
        return False

    def can_analyze(self):
        return False

    def can_refresh(self):
        return True

    def get_num_unmatched_files(self):
        return len(self.unmatched_files.files)

    def get_num_unsaved_files(self):
        return len([track for track in self.tracks
                    if track.linked_file and not track.linked_file.is_saved()])

    def column(self, column):
        if column == 'title':
            if self.tracks:
                text = u'%s\u200E (%d/%d' % (self.metadata['album'], self._files, len(self.tracks))
                unmatched = self.get_num_unmatched_files()
                if unmatched:
                    text += '; %d?' % (unmatched,)
                unsaved = self.get_num_unsaved_files()
                if unsaved:
                    text += '; %d*' % (unsaved,)
                return text + ')'
            else:
                return self.metadata['album']
        elif column == '~length':
            length = self.metadata.length
            if length:
                return format_time(length)
            else:
                return ''
        elif column == 'artist':
            return self.metadata['albumartist']
        else:
            return ''

    def set_current_release_event(self, rel):
        self.current_release_event = rel
        if self.current_release_event:
            self.current_release_event.to_metadata(self.metadata)
            self.update(update_tracks=False)
            for track in self.tracks:
                self.current_release_event.to_metadata(track.metadata)
                if track.linked_file:
                    self.current_release_event.to_metadata(track.linked_file.metadata)
                    track.linked_file.update()
                else:
                    track.update()

    def add_release_event(self, date=None, releasecountry=None, label=None, barcode=None, catalognumber=None, format=None):
        rel = ReleaseEvent()
        rel.date = date
        rel.releasecountry = releasecountry
        rel.label = label
        rel.barcode = barcode
        rel.catalognumber = catalognumber
        rel.format = format
        self.release_events.append(rel)
        return rel
