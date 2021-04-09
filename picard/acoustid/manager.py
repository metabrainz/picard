# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2011 Lukáš Lalinský
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018 Laurent Monin
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2020 Philipp Wolfer
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
        self.attempts = 0

    def __len__(self):
        # payload approximation
        # it is based on actual measures, as an example:
        # with no puid, 2 fingerprints total size of 7501 bytes, post body was 7719 bytes (including all fields)
        # so that's an overhead of ~3%
        # we use 10% here, to be safe
        return int((len(self.fingerprint) + len(self.puid)) * 1.1)

    def is_submitted(self):
        return not self.recordingid or self.orig_recordingid == self.recordingid


class AcoustIDManager(QtCore.QObject):

    # AcoustID has a post limit of around 1 MB.
    MAX_PAYLOAD = 1000000
    # Limit each submission to N attempts
    MAX_ATTEMPTS = 5
    # In case of Payload Too Large error, batch size is reduced by this factor
    # and a retry occurs
    BATCH_SIZE_REDUCTION_FACTOR = 0.7

    def __init__(self, acoustid_api):
        super().__init__()
        self._submissions = {}
        self._acoustid_api = acoustid_api

    def add(self, file, recordingid):
        if not file.acoustid_fingerprint or not file.acoustid_length:
            return
        puid = file.metadata['musicip_puid']
        self._submissions[file] = Submission(file.acoustid_fingerprint, file.acoustid_length, recordingid, recordingid, puid)
        self._check_unsubmitted()

    def update(self, file, recordingid):
        submission = self._submissions.get(file)
        if submission is None:
            return
        submission.recordingid = recordingid
        self._check_unsubmitted()

    def remove(self, file):
        if file in self._submissions:
            del self._submissions[file]
        self._check_unsubmitted()

    def is_submitted(self, file):
        submission = self._submissions.get(file)
        if submission:
            return submission.is_submitted()
        return True

    def _unsubmitted(self, reset=False):
        for file, submission in self._submissions.items():
            if not submission.is_submitted():
                if reset:
                    submission.attempts = 0
                yield (file, submission)

    def _check_unsubmitted(self):
        enabled = next(self._unsubmitted(), None) is not None
        self.tagger.window.enable_submit(enabled)

    def submit(self):
        self.max_batch_size = self.MAX_PAYLOAD
        submissions = list(self._unsubmitted(reset=True))
        if not submissions:
            self._check_unsubmitted()
            return
        log.debug("AcoustID: submitting total of %d fingerprints...", len(submissions))
        self._batch_submit(submissions)

    def _batch(self, submissions):
        batch = []
        remaining = []
        batch_size = 0
        max_attempts = self.MAX_ATTEMPTS
        for file, submission in submissions:
            if submission.attempts < max_attempts:
                batch_size += len(submission)
                if batch_size < self.max_batch_size:
                    submission.attempts += 1
                    batch.append((file, submission))
                    continue
                else:
                    # force appending the rest to remaining if we reach max_batch_size
                    max_attempts = 0
            remaining.append((file, submission))
        return batch, remaining

    def _batch_submit(self, submissions, errors=None):
        if not submissions:  # All fingerprints submitted, nothing to do
            if errors:
                log_msg = N_("AcoustID submission finished, but not all fingerprints have been submitted")
            else:
                log_msg = N_("AcoustID submission finished successfully")
            log.debug(log_msg)
            self.tagger.window.set_statusbar_message(
                log_msg, echo=None, timeout=3000)
            self._check_unsubmitted()
            return

        batch, submissions = self._batch(submissions)

        if not batch:
            if self.max_batch_size == 0:
                log_msg = N_("AcoustID submission failed permanently, maximum batch size reduced to zero")
            else:
                log_msg = N_("AcoustID submission failed permanently, probably too many retries")
            log.error(log_msg)
            self.tagger.window.set_statusbar_message(
                log_msg, echo=None, timeout=3000)
            self._check_unsubmitted()
            return

        log.debug("AcoustID: submitting batch of %d fingerprints (%d remaining)...",
            len(batch), len(submissions))
        self.tagger.window.set_statusbar_message(
            N_('Submitting AcoustIDs ...'),
            echo=None
        )
        if not errors:
            errors = []
        self._acoustid_api.submit_acoustid_fingerprints(
            [submission for file_, submission in batch],
            partial(self._batch_submit_finished, submissions, batch, errors)
        )

    def _batch_submit_finished(self, submissions, batch, previous_errors, document, http, error):
        if error:
            # re-add batched items to remaining list
            submissions.extend(batch)

            response_code = self._acoustid_api.webservice.http_response_code(http)
            if response_code == 413:
                self.max_batch_size = int(self.max_batch_size * self.BATCH_SIZE_REDUCTION_FACTOR)
                log.warn("AcoustID: payload too large, batch size reduced to %d", self.max_batch_size)
            else:
                try:
                    errordoc = load_json(document)
                    message = errordoc["error"]["message"]
                except BaseException:
                    message = ""
                mparms = {
                    'error': http.errorString(),
                    'message': message
                }
                previous_errors.append(mparms)
                log_msg = N_("AcoustID submission failed with error '%(error)s': %(message)s")
                log.error(log_msg, mparms)
                self.tagger.window.set_statusbar_message(
                    log_msg, mparms, echo=None, timeout=3000)
        else:
            log.debug('AcoustID: %d fingerprints successfully submitted', len(batch))
            for file, submission in batch:
                submission.orig_recordingid = submission.recordingid
                file.update()
            self._check_unsubmitted()
        self._batch_submit(submissions, previous_errors)
