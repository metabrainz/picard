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
try:
    from picard.musicdns import ofa
except ImportError:
    ofa = None
from picard.util import encode_filename


class OFA(QtCore.QObject):

    def __init__(self):
        QtCore.QObject.__init__(self)
        self._decoders = []
        plugins = ["directshow", "avcodec", "quicktime", "gstreamer"]
        for name in plugins:
            try:
                decoder = getattr(__import__("picard.musicdns." + name).musicdns, name)
                self._decoders.append(decoder)
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
            self.log.debug("Decoding using %s...", decoder.__name__)
            try:
                result = decoder.decode(filename)
            except Exception:
                continue
            self.log.debug("Fingerprinting...")
            if result:
                buffer, samples, sample_rate, stereo, duration = result
                fingerprint = ofa.create_print(buffer, samples, sample_rate, stereo)
                return (fingerprint, duration)
        return None
