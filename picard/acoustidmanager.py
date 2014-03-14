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
from PyQt4 import QtCore
from picard import config

class Submission(object):

    def __init__(self, fingerprint, duration, orig_recordingid=None, recordingid=None, puid=None):
        self.fingerprint = fingerprint
        self.duration = duration
        self.puid = puid
        self.orig_recordingid = orig_recordingid
        self.recordingid = recordingid


class AcoustIDManager(QtCore.QObject):

    def __init__(self):
        QtCore.QObject.__init__(self)
        self._fingerprints = {}
        self._submitting = False

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
        for submission in self._fingerprints.itervalues():
            if submission.recordingid and submission.orig_recordingid != submission.recordingid:
                yield submission

    def is_unsubmitted(self):
        for submission in self._unsubmitted():
            return True
        return False

    def _check_unsubmitted(self):
        self.tagger.window.enable_submit(self.is_unsubmitted())

    def submit(self):
        fingerprints = list(self._unsubmitted())
        if not fingerprints:
            self._check_unsubmitted()
            return
        if self._submitting:
            return
        self._submitting = True
        self.tagger.window.set_statusbar_message(N_('Submitting AcoustIDs...'))
        self.tagger.xmlws.submit_acoustid_fingerprints(fingerprints, partial(self.__fingerprint_submission_finished, fingerprints))

    def __fingerprint_submission_finished(self, fingerprints, document, http, error):
        self._submitting = True
        if error:
            self.tagger.window.set_statusbar_message(N_('AcoustID submission failed: %s'), error, timeout=3000)
        else:
            self.tagger.window.set_statusbar_message(N_('AcoustIDs successfully submitted!'), timeout=3000)
            for submission in fingerprints:
                submission.orig_recordingid = submission.recordingid
            self._check_unsubmitted()

    def check_auto_submit(self):
        if self.tagger.acoustid.num_analyzing() == 0 and self.tagger.xmlws.num_pending_web_requests == 0:
            self.auto_submit()

    def auto_submit(self):
        if config.setting["auto_submit"]:
            self.submit()

