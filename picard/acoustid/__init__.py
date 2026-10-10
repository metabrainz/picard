# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2011 Lukáš Lalinský
# Copyright (C) 2017-2018 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2018-2021, 2023-2026 Laurent Monin
# Copyright (C) 2018-2026 Philipp Wolfer
# Copyright (C) 2023, 2025 Bob Swift
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from collections import namedtuple
from enum import IntEnum
from functools import partial
import json

from PyQt6 import QtCore

from picard import (
    log,
    tagger_instance,
)
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
from picard.util.externalcommand import ExternalCommandRunner
from picard.webservice.api_helpers import AcoustIdAPIHelper


class FpcalcExit(IntEnum):
    # fpcalc returned successfully
    NOERROR = 0
    # fpcalc encountered errors during decoding, but could still generate a fingerprint
    DECODING_ERROR = 3


# Safety-net timeout (seconds) for a single fpcalc invocation. fpcalc scans a
# limited amount of audio and normally finishes within seconds; this generous
# value only catches a genuinely stuck process without failing slow but
# legitimate scans (large files, slow or networked storage).
FPCALC_TIMEOUT = 120.0


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
        self.tagger = tagger_instance()
        self._acoustid_api = acoustid_api
        self._fpcalc_runner = ExternalCommandRunner(max_concurrent=self.get_max_processes(), parent=self)

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
            log.error("AcoustID: Lookup network error for '%(filename)s': %(error)r, %(body)s" % mparms)
            self.tagger.window.set_statusbar_message(
                N_('AcoustID lookup network error for "%(filename)s"!'),
                mparms,
                echo=None,
            )
            task.next_func({}, http, error)
        else:
            try:
                status = document['status']
                if status == 'ok':
                    resolver = RecordingResolver(
                        self._acoustid_api.webservice,
                        document,
                        callback=partial(self._on_recording_resolve_finish, task, document, http),
                    )
                    resolver.resolve()
                else:
                    mparms = {
                        'error': document['error']['message'],
                        'filename': task.file.filename,
                    }
                    log.error("AcoustID: Lookup error for '%(filename)s': %(error)r" % mparms)
                    self.tagger.window.set_statusbar_message(
                        N_('AcoustID lookup failed for "%(filename)s"!'),
                        mparms,
                        echo=None,
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
                    "AcoustID: Found no matching recordings for '%s', setting acoustid_id tag to %r",
                    task.file.filename,
                    acoustid,
                )
        else:
            log.debug(
                "AcoustID: Lookup successful for '%s' (recordings: %d)",
                task.file.filename,
                len(recording_list),
            )
        task.next_func({'recordings': recording_list}, http, error)

    def _lookup_fingerprint(self, task, result=None, error=None):
        if task.file.state == File.State.REMOVED:
            log.debug("File %r was removed", task.file)
            return
        mparms = {
            'filename': task.file.filename,
        }
        if not result:
            log.debug("AcoustID: lookup returned no result for file '%(filename)s'" % mparms)
            self.tagger.window.set_statusbar_message(
                N_('AcoustID lookup returned no result for file "%(filename)s"'),
                mparms,
                echo=None,
            )
            task.file.clear_pending()
            return
        log.debug("AcoustID: looking up the fingerprint for file '%(filename)s'" % mparms)
        self.tagger.window.set_statusbar_message(
            N_('Looking up the fingerprint for file "%(filename)s" …'),
            mparms,
            echo=None,
        )
        params = {'meta': 'recordings releasegroups releases tracks compress sources'}
        if result[0] == 'fingerprint':
            fp_type, fingerprint, length = result
            params['fingerprint'] = fingerprint
            params['duration'] = str(length)
        else:
            fp_type, recordingid = result
            params['recordingid'] = recordingid
        self._acoustid_api.query_acoustid(partial(self._on_lookup_finished, task), **params)

    def _on_fpcalc_success(self, task, result):
        # fpcalc returns the exit code 3 in case of decoding errors that
        # still allowed it to calculate a result (ok_returncodes below).
        if result.returncode == FpcalcExit.DECODING_ERROR:
            log.warning(
                "fpcalc non-critical decoding errors for %s: %s",
                task.file,
                result.stderr.strip(),
            )
        fp_result = None
        try:
            jsondata = json.loads(result.stdout)
            # Use only integer part of duration, floats are not allowed in lookup
            duration = int(jsondata.get('duration'))
            fingerprint = jsondata.get('fingerprint')
            if fingerprint and duration:
                fp_result = 'fingerprint', fingerprint, duration
        except (json.decoder.JSONDecodeError, UnicodeDecodeError, ValueError):
            log.error("Error reading fingerprint calculator output", exc_info=True)
        finally:
            if fp_result is not None:
                _fp_type, fingerprint, length = fp_result
                # Only set the fingerprint if it was calculated without
                # decoding errors. Otherwise fingerprints for broken files
                # might get submitted.
                if result.returncode == FpcalcExit.NOERROR:
                    task.file.set_acoustid_fingerprint(fingerprint, length)
            task.next_func(fp_result)

    def _on_fpcalc_error(self, task, error):
        log.error(
            "Fingerprint calculator failed: %s (code=%r) args=%r",
            error,
            error.returncode,
            error.args_list,
        )
        task.next_func(None)

    def _run_fpcalc(self, task):
        if task.file.state == File.State.REMOVED:
            log.debug("File %r was removed", task.file)
            return
        file_path = task.file.filename
        # On Windows fpcalc.exe does not handle long paths, even if system wide
        # long path support is enabled. Ensure the path is properly prefixed.
        if IS_WIN:
            file_path = win_prefix_longpath(file_path)
        self._fpcalc_runner.set_max_concurrent(self.get_max_processes())
        self._fpcalc_runner.run(
            [self._fpcalc, '-json', '-length', '120', file_path],
            partial(self._on_fpcalc_success, task),
            partial(self._on_fpcalc_error, task),
            ok_returncodes=(FpcalcExit.DECODING_ERROR,),
            timeout=FPCALC_TIMEOUT,
            key=task.file,
        )
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
        if task.file.state == File.State.REMOVED:
            log.debug("File %r was removed", task.file)
            return
        self._fpcalc = get_fpcalc()
        self._run_fpcalc(task)

    def fingerprint(self, file, next_func):
        self._fingerprint(AcoustIDTask(file, next_func))

    def stop_analyze(self, file):
        self._fpcalc_runner.cancel(lambda key: key == file or getattr(key, 'state', None) == File.State.REMOVED)
