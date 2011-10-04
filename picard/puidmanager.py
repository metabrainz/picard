# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006-2007 Lukáš Lalinský
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

from PyQt4 import QtCore
from picard.util import partial

class PUIDManager(QtCore.QObject):

    def __init__(self):
        QtCore.QObject.__init__(self)
        self.__puids = {}
        self.__matches = {}

    def add(self, puid, trackid):
        """Add a PUID to the manager."""
        if puid:
            self.__puids[puid] = (trackid, trackid)
            self.__check_unsubmitted()

    def update(self, puid, trackid):
        """Update the PUID."""
        if puid:
            self.__puids[puid] = (self.__puids.get(puid, (None, None))[0], trackid)
            self.__check_unsubmitted()

    def remove(self, puid):
        try: del self.__puids[puid]
        except KeyError: pass

    def __unsubmitted(self):
        """Return the count of unsubmitted PUIDs."""
        for puid, (origtrackid, trackid) in self.__puids.iteritems():
            if trackid and origtrackid != trackid:
                yield puid, trackid

    def __check_unsubmitted(self):
        """Enable/disable the 'Submit PUIDs' action."""
        enabled = len(list(self.__unsubmitted())) > 0
        self.tagger.window.enable_submit(enabled)

    def submit(self):
        """Submit PUIDs to MusicBrainz."""
        puids = {}
        for puid, trackid in self.__unsubmitted():
            puids[trackid] = puid
        self.tagger.window.set_statusbar_message(N_('Submitting PUIDs...'))
        self.tagger.xmlws.submit_puids(puids, partial(self.__puid_submission_finished, puids))

    def __puid_submission_finished(self, puids, document, http, error):
        if error:
            #error_str = unicode(http.errorString())
            self.tagger.window.set_statusbar_message(N_('PUIDs submission failed: %d'), error, timeout=3000)
        else:
            self.tagger.window.set_statusbar_message(N_('PUIDs successfully submitted!'), timeout=3000)
            for puid in puids.values():
                try:
                    self.__puids[puid] = (self.__puids[puid][1], self.__puids[puid][1])
                except KeyError:
                    pass
            self.__check_unsubmitted()

    def add_match(self, puid, trackid):
        self.__matches.setdefault(puid, []).append(trackid)

    def lookup(self, puid):
        return self.__matches.get(puid, [])

