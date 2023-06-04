# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Matthias Friedrich
# Copyright (C) 2007-2008 Lukáš Lalinský
# Copyright (C) 2008 Robert Kaye
# Copyright (C) 2009, 2013, 2018-2023 Philipp Wolfer
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2013 Johannes Dewender
# Copyright (C) 2013 Sebastian Ramacher
# Copyright (C) 2013 Wieland Hoffmann
# Copyright (C) 2013, 2018-2021 Laurent Monin
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
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


import traceback

from PyQt5 import QtCore

from picard import log
from picard.util.mbserver import build_submission_url

from picard.ui.cdlookup import CDLookupDialog


try:
    # use python-libdiscid (http://pythonhosted.org/python-libdiscid/)
    from libdiscid.compat import discid
except ImportError:
    try:
        # use python-discid (http://python-discid.readthedocs.org/en/latest/)
        import discid
    except (ImportError, OSError):
        discid = None


class Disc(QtCore.QObject):

    def __init__(self, id=None):
        super().__init__()
        self.id = id
        self.mcn = None
        self.tracks = 0
        self.toc_string = None

    def read(self, device=None):
        if device is None:
            device = discid.get_default_device()
        log.debug("Reading CD using device: %r", device)
        try:
            disc = discid.read(device, features=['mcn'])
            self._set_disc_details(disc)
        except discid.DiscError as e:
            log.error("Error while reading %r: %s", device, e)
            raise

    def put(self, toc):
        log.debug("Generating disc ID using TOC: %r", toc)
        try:
            first, last, sectors, *offsets = toc
            disc = discid.put(first, last, sectors, offsets)
            self._set_disc_details(disc)
        except discid.TOCError as e:
            log.error("Error while processing TOC %r: %s", toc, e)
            raise
        except ValueError as e:
            log.error("Error while processing TOC %r: %s", toc, e)
            raise discid.TOCError(e)

    def _set_disc_details(self, disc):
        self.id = disc.id
        self.mcn = disc.mcn
        self.tracks = len(disc.tracks)
        self.toc_string = disc.toc_string
        log.debug("Read disc ID %s with MCN %s", self.id, self.mcn)

    @property
    def submission_url(self):
        if self.id and self.tracks and self.toc_string:
            return build_submission_url('/cdtoc/attach', query_args={
                'id': self.id,
                'tracks': self.tracks,
                'toc': self.toc_string.replace(' ', '+'),
            })
        else:
            return None

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
