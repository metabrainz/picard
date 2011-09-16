# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2011 Lukáš Lalinský
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

from collections import deque
from PyQt4 import QtCore
from picard.const import ACOUSTID_KEY
from picard.util import partial, call_next
from picard.webservice import XmlNode


class AcoustIDClient(QtCore.QObject):

    def __init__(self):
        QtCore.QObject.__init__(self)
        self._queue = deque()
        self._running = 0
        self._max_processes = 2

    def init(self):
        pass

    def done(self):
        pass

    def _on_lookup_finished(self, next, file, document, http, error):
        def make_artist_credit_node(parent, artists):
            artist_credit_el = parent.append_child('artist_credit')
            for i, artist in enumerate(artists):
                name_credit_el = artist_credit_el.append_child('name_credit')
                artist_el = name_credit_el.append_child('artist')
                artist_el.append_child('id').text = artist.id[0].text
                artist_el.append_child('name').text = artist.name[0].text
                artist_el.append_child('sort_name').text = artist.name[0].text
                if i > 0:
                    name_credit_el.attribs['joinphrase'] = '; '
            return artist_credit_el
        doc = XmlNode()
        metadata_el = doc.append_child('metadata')
        puid_el = metadata_el.append_child('puid')
        recording_list_el = puid_el.append_child('recording_list')
        seen = set()
        acoustid_id = None
        for result in document.response[0].results[0].children.get('result', []):
            if acoustid_id is None:
                acoustid_id = result.id[0].text
            for recording in result.recordings[0].recording:
                recording_id = recording.id[0].text
                if recording_id in seen:
                    continue
                seen.add(recording_id)
                recording_el = recording_list_el.append_child('recording')
                recording_el.attribs['id'] = recording_id
                recording_el.append_child('title').text = recording.title[0].text
                if 'duration' in recording.children:
                    recording_el.append_child('length').text = str(int(recording.duration[0].text) * 1000)
                make_artist_credit_node(recording_el, recording.artists[0].artist)
                release_list_el = recording_el.append_child('release_list')
                for release_group in recording.releasegroups[0].releasegroup:
                    for release in release_group.releases[0].release:
                        release_el = release_list_el.append_child('release')
                        release_el.attribs['id'] = release.id[0].text
                        if 'title' in release.children:
                            release_el.append_child('title').text = release.title[0].text
                        else:
                            release_el.append_child('title').text = release_group.title[0].text
                        if 'country' in release.children:
                            release_el.append_child('country').text = release.country[0].text
                        medium_list_el = release_el.append_child('medium_list')
                        medium_list_el.attribs['count'] = release.medium_count[0].text
                        for medium in release.mediums[0].medium:
                            medium_el = medium_list_el.append_child('medium')
                            track_list_el = medium_el.append_child('track_list')
                            track_list_el.attribs['count'] = medium.track_count[0].text
                            for track in medium.tracks[0].track:
                                track_el = track_list_el.append_child('track')
                                track_el.append_child('position').text = track.position[0].text
        if acoustid_id is not None:
            file.metadata['acoustid_id'] = acoustid_id
        next(doc, http, error)

    def _lookup_fingerprint(self, next, filename, result=None, error=None):
        try:
            file = self.tagger.files[filename]
        except KeyError:
            # The file has been removed. do nothing
            return
        self.tagger.window.set_statusbar_message(
            N_("Looking up the fingerprint for file %s..."), file.filename)
        params = dict(client=ACOUSTID_KEY, format='xml', meta='recordings releasegroups releases tracks compress')
        if result[0] == 'fingerprint':
            type, fingerprint, length = result
            params['fingerprint'] = fingerprint
            params['duration'] = str((file.metadata.length or 1000 * length) / 1000)
        else:
            type, trackid = result
            params['trackid'] = trackid
        self.tagger.xmlws.query_acoustid(partial(self._on_lookup_finished, next, file), **params)

    @call_next
    def _on_finished(self, next, filename, exit_code, exit_status):
        self._running -= 1
        self._run_next_task()
        process = self.sender()
        if exit_code == 0 and exit_status == 0:
            output = str(process.readAllStandardOutput())
            duration = None
            fingerprint = None
            for line in output.splitlines():
                parts = line.split('=', 1)
                if len(parts) != 2:
                    continue
                if parts[0] == 'DURATION':
                    duration = int(parts[1])
                elif parts[0] == 'FINGERPRINT':
                    fingerpring = parts[1]
            return 'fingerprint', fingerpring, duration

    def _run_next_task(self):
        try:
            file, next = self._queue.popleft()
        except IndexError:
            return
        fpcalc = self.config.setting["acoustid_fpcalc"] or "fpcalc"
        process = QtCore.QProcess(self)
        process.start(fpcalc, ["-length", "120", file.filename])
        process.finished.connect(next)
        self._running += 1

    def analyze(self, file, next):
        fpcalc_next = partial(self._lookup_fingerprint, next, file.filename)
        # return cached track IDs
        trackids = file.metadata.getall('acoustid_id')
        if trackids:
            fpcalc_next(result=('trackid', trackids[0]))
            return
        # use cached fingerprint
        fingerprints = file.metadata.getall('acoustid_fingerprint')
        if fingerprints:
            fpcalc_next(result=('fingerprint', fingerprints[0], 0))
            return
        # calculate the fingerprint
        callback = partial(self._on_finished, fpcalc_next, file.filename)
        task = (file, callback)
        self._queue.append(task)
        if self._running < self._max_processes:
            self._run_next_task()

    def stop_analyze(self, file):
        new_queue = deque()
        for task in self._queue:
            if task[0] != file:
                new_queue.appendleft(task)
        self._queue = new_queue

