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


class Submission(object):

    def __init__(self, fingerprint, duration, orig_trackid=None, trackid=None, puid=None):
        self.fingerprint = fingerprint
        self.duration = duration
        self.puid = puid
        self.orig_trackid = orig_trackid
        self.trackid = trackid


class AcoustIDManager(QtCore.QObject):

    def __init__(self):
        QtCore.QObject.__init__(self)
        self._fingerprints = {}

    def add(self, file, trackid):
        if not hasattr(file, 'acoustid_fingerprint'):
            return
        if not hasattr(file, 'acoustid_length'):
            return
        puid = file.metadata['musicip_puid']
        self._fingerprints[file] = Submission(file.acoustid_fingerprint, file.acoustid_length, trackid, trackid, puid)
        self._check_unsubmitted()

    def update(self, file, trackid):
        submission = self._fingerprints.get(file)
        if submission is None:
            return
        submission.trackid = trackid
        self._check_unsubmitted()

    def remove(self, file):
        if file in self._fingerprints:
            del self._fingerprints[file]
        self._check_unsubmitted()

    def _unsubmitted(self):
        for submission in self._fingerprints.itervalues():
            if submission.trackid and submission.orig_trackid != submission.trackid:
                yield submission

    def _check_unsubmitted(self):
        enabled = False
        for submission in self._unsubmitted():
            enabled = True
            break
        self.tagger.window.enable_submit(enabled)

    def submit(self):
        fingerprints = list(self._unsubmitted())
        if not fingerprints:
            self._check_unsubmitted()
            return
        self.tagger.window.set_statusbar_message(N_('Submitting AcoustIDs...'))
        self.tagger.xmlws.submit_acoustid_fingerprints(fingerprints, partial(self.__fingerprint_submission_finished, fingerprints))

    def __fingerprint_submission_finished(self, fingerprints, document, http, error):
        if error:
            self.tagger.window.set_statusbar_message(N_('AcoustID submission failed: %s'), error, timeout=3000)
        else:
            self.tagger.window.set_statusbar_message(N_('AcoustIDs successfully submitted!'), timeout=3000)
            for submission in fingerprints:
                submission.orig_trackid = submission.trackid
            self._check_unsubmitted()

