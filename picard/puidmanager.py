# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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
from musicbrainz2.webservice import Query
import picard

class PUIDManager(QtCore.QObject):

    def __init__(self):
        super(PUIDManager, self).__init__()
        self.__puids = {}

    def add(self, puid, trackid):
        """Add the PUID to the manager."""
        if puid:
            self.__puids[puid] = [trackid, trackid]
            self.__check_unsubmitted()

    def update(self, puid, trackid):
        """Update the PUID."""
        if puid:
            self.__puids[puid][1] = trackid
            self.__check_unsubmitted()

    def __unsubmitted(self):
        """Return the count of unsubmitted PUIDs."""
        for puid, (origtrackid, trackid) in self.__puids.iteritems():
            if trackid and origtrackid != trackid:
                yield puid, trackid

    def __check_unsubmitted(self):
        """Enable/disable the 'Submit PUIDs' action."""
        enabled = len(list(self.__unsubmitted())) > 0
        self.tagger.thread_assist.proxy_to_main(self.tagger.window.enable_submit, enabled)

    def submit(self):
        """Submit PUIDs to MusicBrainz."""
        puids = {}
        for puid, trackid in self.__unsubmitted():
            puids[trackid] = puid
        if puids:
            self.tagger.thread_assist.spawn(self.__submit_thread, puids)

    def __submit_thread(self, puids):
        self.tagger.set_statusbar_message(N_('Submitting PUIDs...'))
        clientid = 'MusicBrainz Picard-' + picard.version_string
        ws = self.tagger.get_web_service()
        q = Query(ws, clientId=clientid)
        try:
            q.submitPuids(puids)
        except Exception, e:
            self.tagger.set_statusbar_message(N_('PUIDs submission failed: %s'), str(e), timeout=3000)
        else:
            self.tagger.set_statusbar_message(N_('PUIDs successfully submitted!'), timeout=3000)
        self.tagger.thread_assist.proxy_to_main(self.__clear_puids, puids)

    def __clear_puids(self, puids):
        for puid in puids.values():
            del self.__puids[puid]
        self.__check_unsubmitted()
