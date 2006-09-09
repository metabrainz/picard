# ***** BEGIN LICENSE BLOCK *****
# Version: RCSL 1.0/RPSL 1.0/GPL 2.0
#
# Portions Copyright (c) 1995-2002 RealNetworks, Inc. All Rights Reserved.
# Portions Copyright (c) 2004 Robert Kaye. All Rights Reserved.
#
# The contents of this file, and the files included with this file, are
# subject to the current version of the RealNetworks Public Source License
# Version 1.0 (the "RPSL") available at
# http://www.helixcommunity.org/content/rpsl unless you have licensed
# the file under the RealNetworks Community Source License Version 1.0
# (the "RCSL") available at http://www.helixcommunity.org/content/rcsl,
# in which case the RCSL will apply. You may also obtain the license terms
# directly from RealNetworks.  You may not use this file except in
# compliance with the RPSL or, if you have a valid RCSL with RealNetworks
# applicable to this file, the RCSL.  Please see the applicable RPSL or
# RCSL for the rights, obligations and limitations governing use of the
# contents of the file.
#
# This file is part of the Helix DNA Technology. RealNetworks is the
# developer of the Original Code and owns the copyrights in the portions
# it created.
#
# This file, and the files included with this file, is distributed and made
# available on an 'AS IS' basis, WITHOUT WARRANTY OF ANY KIND, EITHER
# EXPRESS OR IMPLIED, AND REALNETWORKS HEREBY DISCLAIMS ALL SUCH WARRANTIES,
# INCLUDING WITHOUT LIMITATION, ANY WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE, QUIET ENJOYMENT OR NON-INFRINGEMENT.
#
# Technology Compatibility Kit Test Suite(s) Location:
#    http://www.helixcommunity.org/content/tck
#
# --------------------------------------------------------------------
#
# picard is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# picard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with picard; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Contributor(s):
#   Robert Kaye
#
#
# ***** END LICENSE BLOCK *****

import sys, urllib, webbrowser, os
from os.path import basename
import launch

class FileLookup(launch.Launch):
    
    def __init__(self, parent, server, port, localPort):
        launch.Launch.__init__(self, parent)
        self.server = server
        self.localPort = int(localPort)
        self.port = port

    def _encode(self, text):
        return urllib.quote(text.encode('UTF-8', 'replace'))

    def discLookup(self, url):
        return self.launch("%s&tport=%d" % (url, self.localPort))

    def _lookup(self, type_, id_):
        url = "http://%s:%d/%s/%s.html?tport=%d" % (
            self._encode(self.server),
            self.port,
            type_,
            id_,
            self.localPort)
        return self.launch(url)

    def trackLookup(self, trackId):
        return self._lookup('track', trackId)

    def albumLookup(self, albumId):
        return self._lookup('album', albumId)

    def artistLookup(self, artistId):
        return self._lookup('artist', artistId)

    def _search(self, type_, query):
        url = "http://%s:%d/search/textsearch.html?limit=25&type=%s&query=%s&tport=%d" % (
            self._encode(self.server),
            self.port,
            type_, 
            self._encode(query),
            self.localPort)
        return self.launch(url)

    def artistSearch(self, query):
        return self._search('artist', query)

    def albumSearch(self, query):
        return self._search('release', query)

    def trackSearch(self, query):
        return self._search('track', query)

    def tagLookup(self, artist, release, track, trackNum, duration, filename, puid):
        url = "http://%s:%d/taglookup.html?tport=%d&artist=%s&release=%s&track=%s&tracknum=%s&duration=%s&filename=%s&puid=%s" % (
            self._encode(self.server),
            self.port,
            self.localPort,
            self._encode(artist),
            self._encode(release),
            self._encode(track),
            trackNum,
            duration,
            self._encode(basename(filename)),
            self._encode(puid))
        return self.launch(url)
