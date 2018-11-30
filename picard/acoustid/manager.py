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

from functools import partial

from PyQt5 import QtCore

from picard import log
from picard.util import load_json


class Submission(object):

    def __init__(self, fingerprint, duration, orig_recordingid=None, recordingid=None, puid=None):
        self.fingerprint = fingerprint
        self.duration = duration
        self.puid = puid
        self.orig_recordingid = orig_recordingid
        self.recordingid = recordingid


class AcoustIDManager(QtCore.QObject):

    def __init__(self):
        super().__init__()
        self._fingerprints = {}

    def add(self, file, recordingid):
        if not hasattr(file, 'acoustid_fingerprint'):
            return
        if not hasattr(file, 'acoustid_length'):
            return
        puid = file.metadata['musicip_puid']
        self._fingerprints[file] = Submission(file.acoustid_fingerprint, file.acoustid_length, recordingid, recordingid, puid)
        self._check_unsubmitted()

    def update(self, file, recordingid):
        submission = self._fingerprints.get(file)
        if submission is None:
            return
        submission.recordingid = recordingid
        self._check_unsubmitted()

    def remove(self, file):
        if file in self._fingerprints:
            del self._fingerprints[file]
        self._check_unsubmitted()

    def _unsubmitted(self):
        for submission in self._fingerprints.values():
            if submission.recordingid and submission.orig_recordingid != submission.recordingid:
                yield submission

    def _check_unsubmitted(self):
        enabled = next(self._unsubmitted(), None) is not None
        self.tagger.window.enable_submit(enabled)

    def submit(self):
        fingerprints = list(self._unsubmitted())
        if not fingerprints:
            self._check_unsubmitted()
            return
        log.debug("AcoustID: submitting ...")
        self.tagger.window.set_statusbar_message(
            N_('Submitting AcoustIDs ...'),
            echo=None
        )
        self.tagger.acoustid_api.submit_acoustid_fingerprints(fingerprints,
            partial(self.__fingerprint_submission_finished, fingerprints))

    def __fingerprint_submission_finished(self, fingerprints, document, http, error):
        if error:
            try:
                error = load_json(document)
                message = error["error"]["message"]
            except BaseException:
                message = ""
            mparms = {
                'error': http.errorString(),
                'message': message
            }
            log.error(
                "AcoustID: submission failed with error '%(error)s': %(message)s" %
                mparms)
            self.tagger.window.set_statusbar_message(
                N_("AcoustID submission failed with error '%(error)s': %(message)s"),
                mparms,
                echo=None,
                timeout=3000
            )
        else:
            log.debug('AcoustID: successfully submitted')
            self.tagger.window.set_statusbar_message(
                N_('AcoustIDs successfully submitted.'),
                echo=None,
                timeout=3000
            )
            for submission in fingerprints:
                submission.orig_recordingid = submission.recordingid
            self._check_unsubmitted()
