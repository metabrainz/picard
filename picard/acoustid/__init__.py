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

from PyQt5 import QtCore

from picard import (
    config,
    log,
)
from picard.acoustid.json_helpers import parse_recording
from picard.const import FPCALC_NAMES
from picard.const.sys import IS_FROZEN
from picard.util import (
    find_executable,
)


class AcoustIDClient(QtCore.QObject):

    def __init__(self):
        super().__init__()
        self._queue = deque()
        self._running = 0
        self._max_processes = 2

        # The second condition is checked because in case of a packaged build of picard
        # the temp directory that pyinstaller decompresses picard into changes on every
        # launch, thus we need to ignore the existing config values.
        if not config.setting["acoustid_fpcalc"] or IS_FROZEN:
            fpcalc_path = find_executable(*FPCALC_NAMES)
            if fpcalc_path:
                config.setting["acoustid_fpcalc"] = fpcalc_path

    def init(self):
        pass

    def done(self):
        pass

    def _on_lookup_finished(self, next_func, file, document, http, error):
        doc = {}
        if error:
            mparms = {
                'error': http.errorString(),
                'body': document,
                'filename': file.filename,
            }
            log.error(
                "AcoustID: Lookup network error for '%(filename)s': %(error)r, %(body)s" %
                mparms)
            self.tagger.window.set_statusbar_message(
                N_("AcoustID lookup network error for '%(filename)s'!"),
                mparms,
                echo=None
            )
        else:
            try:
                recording_list = doc['recordings'] = []
                status = document['status']
                if status == 'ok':
                    results = document['results']
                    if results:
                        result = results[0]
                        file.metadata['acoustid_id'] = result['id']
                        if 'recordings' in result and result['recordings']:
                            max_sources = max([r.get('sources', 1) for r in result['recordings']] + [1])
                            for recording in result['recordings']:
                                parsed_recording = parse_recording(recording)
                                if parsed_recording is not None:
                                    parsed_recording['score'] = recording.get('sources', 1) / max_sources * 100
                                    recording_list.append(parsed_recording)
                            log.debug("AcoustID: Lookup successful for '%s'", file.filename)
                else:
                    mparms = {
                        'error': document['error']['message'],
                        'filename': file.filename
                    }
                    log.error(
                        "AcoustID: Lookup error for '%(filename)s': %(error)r" %
                        mparms)
                    self.tagger.window.set_statusbar_message(
                        N_("AcoustID lookup failed for '%(filename)s'!"),
                        mparms,
                        echo=None
                    )
            except (AttributeError, KeyError, TypeError) as e:
                log.error("AcoustID: Error reading response", exc_info=True)
                error = e

        next_func(doc, http, error)

    def _lookup_fingerprint(self, next_func, filename, result=None, error=None):
        try:
            file = self.tagger.files[filename]
        except KeyError:
            # The file has been removed. do nothing
            return
        mparms = {
            'filename': file.filename
        }
        if not result:
            log.debug(
                "AcoustID: lookup returned no result for file '%(filename)s'" %
                mparms
            )
            self.tagger.window.set_statusbar_message(
                N_("AcoustID lookup returned no result for file '%(filename)s'"),
                mparms,
                echo=None
            )
            file.clear_pending()
            return
        log.debug(
            "AcoustID: looking up the fingerprint for file '%(filename)s'" %
            mparms
        )
        self.tagger.window.set_statusbar_message(
            N_("Looking up the fingerprint for file '%(filename)s' ..."),
            mparms,
            echo=None
        )
        params = dict(meta='recordings releasegroups releases tracks compress sources')
        if result[0] == 'fingerprint':
            fp_type, fingerprint, length = result
            file.acoustid_fingerprint = fingerprint
            file.acoustid_length = length
            self.tagger.acoustidmanager.add(file, None)
            params['fingerprint'] = fingerprint
            params['duration'] = str(length)
        else:
            fp_type, recordingid = result
            params['recordingid'] = recordingid
        self.tagger.acoustid_api.query_acoustid(partial(self._on_lookup_finished, next_func, file), **params)

    def _on_fpcalc_finished(self, next_func, file, exit_code, exit_status):
        process = self.sender()
        finished = process.property('picard_finished')
        if finished:
            return
        process.setProperty('picard_finished', True)
        result = None
        try:
            self._running -= 1
            self._run_next_task()
            process = self.sender()
            if exit_code == 0 and exit_status == 0:
                output = bytes(process.readAllStandardOutput()).decode()
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
                log.error(
                    "Fingerprint calculator failed exit code = %r, exit status = %r, error = %s",
                    exit_code,
                    exit_status,
                    process.errorString())
        finally:
            next_func(result)

    def _on_fpcalc_error(self, next_func, filename, error):
        process = self.sender()
        finished = process.property('picard_finished')
        if finished:
            return
        process.setProperty('picard_finished', True)
        try:
            self._running -= 1
            self._run_next_task()
            log.error("Fingerprint calculator failed error = %s (%r)", process.errorString(), error)
        finally:
            next_func(None)

    def _run_next_task(self):
        try:
            file, next_func = self._queue.popleft()
        except IndexError:
            return
        fpcalc = config.setting["acoustid_fpcalc"] or "fpcalc"
        self._running += 1
        process = QtCore.QProcess(self)
        process.setProperty('picard_finished', False)
        process.finished.connect(partial(self._on_fpcalc_finished, next_func, file))
        process.error.connect(partial(self._on_fpcalc_error, next_func, file))
        process.start(fpcalc, ["-length", "120", file.filename])
        log.debug("Starting fingerprint calculator %r %r", fpcalc, file.filename)

    def analyze(self, file, next_func):
        fpcalc_next = partial(self._lookup_fingerprint, next_func, file.filename)

        if not config.setting["ignore_existing_acoustid_fingerprints"]:
            # use cached fingerprint
            fingerprints = file.metadata.getall('acoustid_fingerprint')
            if fingerprints:
                length = int(file.metadata.length / 1000)
                fpcalc_next(result=('fingerprint', fingerprints[0], length))
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
