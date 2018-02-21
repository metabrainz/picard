# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2006 Matthias Friedrich
# Copyright (C) 2013 Laurent Monin
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

try:
    # use python-libdiscid (http://pythonhosted.org/python-libdiscid/)
    from libdiscid.compat import discid
except ImportError:
    try:
        # use python-discid (http://python-discid.readthedocs.org/en/latest/)
        import discid
    except ImportError:
        discid = None

import traceback
from PyQt5 import QtCore
from picard import log
from picard.ui.cdlookup import CDLookupDialog


class Disc(QtCore.QObject):

    def __init__(self):
        super().__init__()
        self.id = None
        self.submission_url = None

    def read(self, device=None):
        if device is None:
            device = discid.get_default_device()
        log.debug("Reading CD using device: %r", device)
        try:
            disc = discid.read(device)
            self.id = disc.id
            self.submission_url = disc.submission_url
        except discid.disc.DiscError as e:
            log.error("Error while reading %r: %s" % (device, str(e)))
            raise

    def lookup(self):
        self.tagger.mb_api.lookup_discid(self.id, self._lookup_finished)

    def _lookup_finished(self, document, http, error):
        self.tagger.restore_cursor()
        releases = []
        if error:
            log.error("%r", http.errorString())
        else:
            try:
                releases = document['releases']
            except (AttributeError, IndexError):
                log.error(traceback.format_exc())

        dialog = CDLookupDialog(releases, self, parent=self.tagger.window)
        dialog.exec_()


if discid is not None:
    discid_version = "discid %s, %s" % (discid.__version__,
                                        discid.LIBDISCID_VERSION_STRING)
else:
    discid_version = None
