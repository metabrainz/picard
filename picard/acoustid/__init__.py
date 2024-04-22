# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2011 Lukáš Lalinský
# Copyright (C) 2017-2018 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2018-2021, 2023-2024 Laurent Monin
# Copyright (C) 2018-2024 Philipp Wolfer
# Copyright (C) 2023 Bob Swift
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


from collections import (
    deque,
    namedtuple,
)
from enum import IntEnum
from functools import partial
import json

from PySide6 import QtCore

from picard import log
from picard.acoustid.recordings import RecordingResolver
from picard.config import get_config
from picard.const import FPCALC_NAMES
from picard.const.defaults import DEFAULT_FPCALC_THREADS
from picard.const.sys import IS_WIN
from picard.file import File
from picard.i18n import N_
from picard.util import (
    find_executable,
    win_prefix_longpath,
)
from picard.webservice.api_helpers import AcoustIdAPIHelper


class FpcalcExit(IntEnum):
    # fpcalc returned successfully
    NOERROR = 0
    # fpcalc encountered errors during decoding, but could still generate a fingerprint
    DECODING_ERROR = 3


def get_score(node):
    try:
        return float(node.get('score', 1.0))
    except (TypeError, ValueError):
        return 1.0


def get_fpcalc(config=None):
    if not config:
        config = get_config()
    fpcalc_path = config.setting["acoustid_fpcalc"]
    if not fpcalc_path:
        fpcalc_path = find_fpcalc()
    return fpcalc_path or 'fpcalc'


def find_fpcalc():
    return find_executable(*FPCALC_NAMES)


AcoustIDTask = namedtuple('AcoustIDTask', ('file', 'next_func'))


class AcoustIDClient(QtCore.QObject):

    def __init__(self, acoustid_api: AcoustIdAPIHelper):
        super().__init__()
        self.tagger = QtCore.QCoreApplication.instance()
        self._queue = deque()
        self._running = 0
        self._acoustid_api = acoustid_api

    def init(self):
        pass

    def done(self):
        pass

    def get_max_processes(self):
        config = get_config()
        return config.setting['fpcalc_threads'] or DEFAULT_FPCALC_THREADS

    def _on_lookup_finished(self, task, document, http, error):
        if error:
            mparms = {
                'error': http.errorString(),
                'body': document,
                'filename': task.file.filename,
            }
            log.error(
                "AcoustID: Lookup network error for '%(filename)s': %(error)r, %(body)s" %
                mparms)
            self.tagger.window.set_statusbar_message(
                N_("AcoustID lookup network error for '%(filename)s'!"),
                mparms,
                echo=None
            )
            task.next_func({}, http, error)
        else:
            try:
                status = document['status']
                if status == 'ok':
                    resolver = RecordingResolver(
                        self._acoustid_api.webservice,
                        document,
                        callback=partial(self._on_recording_resolve_finish, task, document, http))
                    resolver.resolve()
                else:
                    mparms = {
                        'error': document['error']['message'],
                        'filename': task.file.filename
                    }
                    log.error(
                        "AcoustID: Lookup error for '%(filename)s': %(error)r" %
                        mparms)
                    self.tagger.window.set_statusbar_message(
                        N_("AcoustID lookup failed for '%(filename)s'!"),
                        mparms,
                        echo=None
                    )
                    task.next_func({}, http, error)
            except (AttributeError, KeyError, TypeError) as e:
                log.error("AcoustID: Error reading response", exc_info=True)
                task.next_func({}, http, e)

    def _on_recording_resolve_finish(self, task, document, http, result=None, error=None):
        recording_list = result
        if not recording_list:
            results = document.get('results')
            if results:
                # Set AcoustID in tags if there was no matching recording
                acoustid = results[0].get('id')
                task.file.metadata['acoustid_id'] = acoustid
                task.file.update()
                log.debug(
                    "AcoustID: Found no matching recordings for '%s',"
                    " setting acoustid_id tag to %r",
                    task.file.filename, acoustid
                )
        else:
            log.debug(
                "AcoustID: Lookup successful for '%s' (recordings: %d)",
                task.file.filename,
                len(recording_list)
            )
        task.next_func({'recordings': recording_list}, http, error)

    def _lookup_fingerprint(self, task, result=None, error=None):
        if task.file.state == File.REMOVED:
            log.debug("File %r was removed", task.file)
            return
        mparms = {
            'filename': task.file.filename
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
            task.file.clear_pending()
            return
        log.debug(
            "AcoustID: looking up the fingerprint for file '%(filename)s'" %
            mparms
        )
        self.tagger.window.set_statusbar_message(
            N_("Looking up the fingerprint for file '%(filename)s' …"),
            mparms,
            echo=None
        )
        params = dict(meta='recordings releasegroups releases tracks compress sources')
        if result[0] == 'fingerprint':
            fp_type, fingerprint, length = result
            params['fingerprint'] = fingerprint
            params['duration'] = str(length)
        else:
            fp_type, recordingid = result
            params['recordingid'] = recordingid
        self._acoustid_api.query_acoustid(partial(self._on_lookup_finished, task), **params)

    def _on_fpcalc_finished(self, task, exit_code, exit_status):
        process = self.sender()
        finished = process.property('picard_finished')
        if finished:
            return
        process.setProperty('picard_finished', True)
        result = None
        try:
            self._running -= 1
            self._run_next_task()
            # fpcalc returns the exit code 3 in case of decoding errors that
            # still allowed it to calculate a result.
            if exit_code in {FpcalcExit.NOERROR, FpcalcExit.DECODING_ERROR} and exit_status == QtCore.QProcess.ExitStatus.NormalExit:
                if exit_code == FpcalcExit.DECODING_ERROR:
                    error = bytes(process.readAllStandardError()).decode()
                    log.warning("fpcalc non-critical decoding errors for %s: %s", task.file, error)
                output = bytes(process.readAllStandardOutput()).decode()
                jsondata = json.loads(output)
                # Use only integer part of duration, floats are not allowed in lookup
                duration = int(jsondata.get('duration'))
                fingerprint = jsondata.get('fingerprint')
                if fingerprint and duration:
                    result = 'fingerprint', fingerprint, duration
            else:
                log.error(
                    "Fingerprint calculator failed exit code = %r, exit status = %r, error = %s",
                    exit_code,
                    exit_status,
                    process.errorString())
        except (json.decoder.JSONDecodeError, UnicodeDecodeError, ValueError):
            log.error("Error reading fingerprint calculator output", exc_info=True)
        finally:
            if result and result[0] == 'fingerprint':
                fp_type, fingerprint, length = result
                # Only set the fingerprint if it was calculated without
                # decoding errors. Otherwise fingerprints for broken files
                # might get submitted.
                if exit_code == FpcalcExit.NOERROR:
                    task.file.set_acoustid_fingerprint(fingerprint, length)
            task.next_func(result)

    def _on_fpcalc_error(self, task, error):
        process = self.sender()
        finished = process.property('picard_finished')
        if finished:
            return
        process.setProperty('picard_finished', True)
        try:
            self._running -= 1
            self._run_next_task()
            log.error(
                "Fingerprint calculator failed error= %s (%r) program=%r arguments=%r",
                process.errorString(), error, process.program(), process.arguments()
            )
        finally:
            task.next_func(None)

    def _run_next_task(self):
        try:
            task = self._queue.popleft()
        except IndexError:
            return
        if task.file.state == File.REMOVED:
            log.debug("File %r was removed", task.file)
            return
        self._running += 1
        process = QtCore.QProcess(self)
        process.setProperty('picard_finished', False)
        process.finished.connect(partial(self._on_fpcalc_finished, task))
        process.errorOccurred.connect(partial(self._on_fpcalc_error, task))
        file_path = task.file.filename
        # On Windows fpcalc.exe does not handle long paths, even if system wide
        # long path support is enabled. Ensure the path is properly prefixed.
        if IS_WIN:
            file_path = win_prefix_longpath(file_path)
        process.start(self._fpcalc, ['-json', '-length', '120', file_path])
        log.debug("Starting fingerprint calculator %r %r", self._fpcalc, task.file.filename)

    def analyze(self, file, next_func):
        fpcalc_next = partial(self._lookup_fingerprint, AcoustIDTask(file, next_func))
        task = AcoustIDTask(file, fpcalc_next)

        config = get_config()
        fingerprint = task.file.acoustid_fingerprint
        if not fingerprint and not config.setting['ignore_existing_acoustid_fingerprints']:
            # use cached fingerprint from file metadata
            fingerprints = task.file.metadata.getall('acoustid_fingerprint')
            if fingerprints:
                fingerprint = fingerprints[0]
                task.file.set_acoustid_fingerprint(fingerprint)

        # If the fingerprint already exists skip calling fpcalc
        if fingerprint:
            length = task.file.acoustid_length
            fpcalc_next(result=('fingerprint', fingerprint, length))
            return

        # calculate the fingerprint
        self._fingerprint(task)

    def _fingerprint(self, task):
        if task.file.state == File.REMOVED:
            log.debug("File %r was removed", task.file)
            return
        self._queue.append(task)
        self._fpcalc = get_fpcalc()
        if self._running < self.get_max_processes():
            self._run_next_task()

    def fingerprint(self, file, next_func):
        self._fingerprint(AcoustIDTask(file, next_func))

    def stop_analyze(self, file):
        new_queue = deque()
        for task in self._queue:
            if task.file != file and task.file.state != File.REMOVED:
                new_queue.appendleft(task)
        self._queue = new_queue
