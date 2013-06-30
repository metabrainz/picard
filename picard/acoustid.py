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
from functools import partial
from PyQt4 import QtCore
from picard import config, log
from picard.const import ACOUSTID_KEY, FPCALC_NAMES
from picard.util import call_next, find_executable
from picard.webservice import XmlNode


class AcoustIDClient(QtCore.QObject):

    def __init__(self):
        QtCore.QObject.__init__(self)
        self._queue = deque()
        self._running = 0
        self._max_processes = 2

        if not config.setting["acoustid_fpcalc"]:
            fpcalc_path = find_executable(*FPCALC_NAMES)
            if fpcalc_path:
                config.setting["acoustid_fpcalc"] = fpcalc_path

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

        def parse_recording(recording):
            if 'title' not in recording.children: # we have no metadata for this recording
                return
            recording_id = recording.id[0].text
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
                    release_group_el = release_el.append_child('release_group')
                    release_group_el.attribs['id'] = release_group.id[0].text
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

        doc = XmlNode()
        metadata_el = doc.append_child('metadata')
        acoustid_el = metadata_el.append_child('acoustid')
        recording_list_el = acoustid_el.append_child('recording_list')

        status = document.response[0].status[0].text
        if status == 'ok':
            results = document.response[0].results[0].children.get('result')
            if results:
                result = results[0]
                file.metadata['acoustid_id'] = result.id[0].text
                if 'recordings' in result.children:
                    for recording in result.recordings[0].recording:
                        parse_recording(recording)
        else:
            error_message = document.response[0].error[0].message[0].text
            log.error("Fingerprint lookup failed: %r", error_message)

        next(doc, http, error)

    def _lookup_fingerprint(self, next, filename, result=None, error=None):
        try:
            file = self.tagger.files[filename]
        except KeyError:
            # The file has been removed. do nothing
            return
        if not result:
            self.tagger.window.set_statusbar_message(N_("Could not find AcoustID for file %s"), file.filename)
            file.clear_pending()
            return
        self.tagger.window.set_statusbar_message(
            N_("Looking up the fingerprint for file %s..."), file.filename)
        params = dict(meta='recordings releasegroups releases tracks compress')
        if result[0] == 'fingerprint':
            type, fingerprint, length = result
            file.acoustid_fingerprint = fingerprint
            file.acoustid_length = length
            self.tagger.acoustidmanager.add(file, None)
            params['fingerprint'] = fingerprint
            params['duration'] = str(length)
        else:
            type, trackid = result
            params['trackid'] = trackid
        self.tagger.xmlws.query_acoustid(partial(self._on_lookup_finished, next, file), **params)

    def _on_fpcalc_finished(self, next, file, exit_code, exit_status):
        process = self.sender()
        finished = process.property('picard_finished').toBool()
        if finished:
            return
        process.setProperty('picard_finished', QtCore.QVariant(True))
        result = None
        try:
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
                        fingerprint = parts[1]
                if fingerprint and duration:
                    result = 'fingerprint', fingerprint, duration
            else:
                log.error("Fingerprint calculator failed exit code = %r, exit status = %r, error = %s", exit_code, exit_status, unicode(process.errorString()))
        finally:
            next(result)

    def _on_fpcalc_error(self, next, filename, error):
        process = self.sender()
        finished = process.property('picard_finished').toBool()
        if finished:
            return
        process.setProperty('picard_finished', QtCore.QVariant(True))
        try:
            self._running -= 1
            self._run_next_task()
            log.error("Fingerprint calculator failed error = %s (%r)", unicode(process.errorString()), error)
        finally:
            next(None)

    def _run_next_task(self):
        try:
            file, next = self._queue.popleft()
        except IndexError:
            return
        fpcalc = config.setting["acoustid_fpcalc"] or "fpcalc"
        self._running += 1
        process = QtCore.QProcess(self)
        process.setProperty('picard_finished', QtCore.QVariant(False))
        process.finished.connect(partial(self._on_fpcalc_finished, next, file))
        process.error.connect(partial(self._on_fpcalc_error, next, file))
        process.start(fpcalc, ["-length", "120", file.filename])
        log.debug("Starting fingerprint calculator %r %r", fpcalc, file.filename)

    def analyze(self, file, next):
        fpcalc_next = partial(self._lookup_fingerprint, next, file.filename)
        # use cached fingerprint
        fingerprints = file.metadata.getall('acoustid_fingerprint')
        if fingerprints:
            fpcalc_next(result=('fingerprint', fingerprints[0], 0))
            return
        # calculate the fingerprint
        task = (file, fpcalc_next)
        self._queue.append(task)
        if self._running < self._max_processes:
            self._run_next_task()

    def stop_analyze(self, file):
        new_queue = deque()
        for task in self._queue:
            if task[0] != file:
                new_queue.appendleft(task)
        self._queue = new_queue

