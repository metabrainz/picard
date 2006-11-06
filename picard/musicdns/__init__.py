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

try:
    from picard.musicdns import ofa
except ImportError:
    ofa = None
from picard.util import encode_filename


class OFA(object):
    
    def __init__(self):
        self._decoders = []
        try:
            from picard.musicdns import directshow
            self._decoders.append(directshow)
        except ImportError:
            pass
        try:
            from picard.musicdns import quicktime
            self._decoders.append(quicktime)
        except ImportError:
            pass
        try:
            from picard.musicdns import gstreamer
            self._decoders.append(gstreamer)
        except ImportError:
            pass
        if not self._decoders:
            self.log.warning(
                "No decoders found! Fingerprinting will be disabled.")

    def init(self):
        for decoder in self._decoders:
            decoder.init()
        
    def done(self):
        for decoder in self._decoders:
            decoder.done()

    def create_fingerprint(self, filename):
        """Decode the specified file and calculate a fingerprint."""
        if ofa is None:
            return None
        filename = encode_filename(filename)
        for decoder in self._decoders:
            result = decoder.decode(filename)
            if result:
                buffer, samples, sample_rate, stereo, duration = result
                fingerprint = ofa.create_print(buffer, samples, sample_rate, stereo)
                return (fingerprint, duration)
        return None
