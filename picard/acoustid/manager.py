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

    # AcoustID has a post limit of around 1 MB. With the data submitted by
    # Picard this is roughly around 250 fingerprints. Submit a few less to have
    # some leeway.
    BATCH_SUBMIT_COUNT = 240

    def __init__(self, acoustid_api):
        super().__init__()
        self._fingerprints = {}
        self._acoustid_api = acoustid_api

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

    def is_submitted(self, file):
        submission = self._fingerprints.get(file)
        if submission:
            return not submission.recordingid or submission.orig_recordingid == submission.recordingid
        return True

    def _unsubmitted(self):
        for file, submission in self._fingerprints.items():
            if submission.recordingid and submission.orig_recordingid != submission.recordingid:
                yield (file, submission)

    def _check_unsubmitted(self):
        enabled = next(self._unsubmitted(), None) is not None
        self.tagger.window.enable_submit(enabled)

    def submit(self):
        submissions = list(self._unsubmitted())
        if not submissions:
            self._check_unsubmitted()
            return
        log.debug("AcoustID: submitting total of %d fingerprints...", len(submissions))
        self._batch_submit(submissions)

    def _batch_submit(self, submissions):
        if not submissions:  # All fingerprints submitted, nothing to do
            log.debug("AcoustID: submitted all fingerprints")
            self.tagger.window.set_statusbar_message(
                N_('AcoustIDs successfully submitted.'),
                echo=None,
                timeout=3000
            )
            self._check_unsubmitted()
            return
        submission_batch = submissions[:self.BATCH_SUBMIT_COUNT]
        submissions = submissions[self.BATCH_SUBMIT_COUNT:]
        fingerprints = [fingerprint for file_, fingerprint in submission_batch]
        log.debug("AcoustID: submitting batch of %d fingerprints (%d remaining)...",
            len(submission_batch), len(submissions))
        self.tagger.window.set_statusbar_message(
            N_('Submitting AcoustIDs ...'),
            echo=None
        )
        next_func = partial(self._batch_submit, submissions)
        self._acoustid_api.submit_acoustid_fingerprints(fingerprints,
            partial(self._batch_submit_finished, submission_batch, next_func))

    def _batch_submit_finished(self, submissions, next_func, document, http, error):
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
            log.debug('AcoustID: %d fingerprints successfully submitted', len(submissions))
            for file, submission in submissions:
                submission.orig_recordingid = submission.recordingid
                file.update()
            self._check_unsubmitted()
        next_func()
