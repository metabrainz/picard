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
from picard import version_string
from picard.const import MUSICDNS_KEY
from picard.util import encode_filename, partial
from picard.util.thread import proxy_to_main


class OFA(QtCore.QObject):

    def __init__(self):
        QtCore.QObject.__init__(self)
        if not ofa:
            self.log.warning(
                "Libofa not found! Fingerprinting will be disabled.")
        self._decoders = []
        plugins = ["avcodec", "directshow", "quicktime", "gstreamer"]
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
            return None, 0
        filename = encode_filename(filename)
        for decoder in self._decoders:
            self.log.debug("Decoding using %r...", decoder.__name__)
            try:
                result = decoder.decode(filename)
            except Exception:
                continue
            self.log.debug("Fingerprinting...")
            if result:
                buffer, samples, sample_rate, stereo, duration = result
                fingerprint = ofa.create_print(buffer, samples, sample_rate, stereo)
                return fingerprint, duration
        return None, 0

    def _lookup_finished(self, handler, file, document, http, error):
        try:
            puid = document.metadata[0].track[0].puid_list[0].puid[0].id
        except (AttributeError, IndexError):
            puid = None
        # for some reason MusicDNS started to return these bogus PUIDs
        if puid == '00000000-0000-0000-0000-000000000000':
            puid = None
        handler(file, puid)

    def _lookup_fingerprint(self, file, fingerprint, handler, length=0):
        if file.state != file.PENDING:
            handler(file, None)
            return
        self.tagger.window.set_statusbar_message(N_("Looking up the fingerprint for file %s..."), file.filename)
        self.tagger.xmlws.query_musicdns(partial(self._lookup_finished, handler, file),
            rmt='0',
            lkt='1',
            cid=MUSICDNS_KEY,
            cvr="MusicBrainz Picard-%s" % version_string,
            fpt=fingerprint,
            dur=str(file.metadata.length or length),
            brt=str(file.metadata.get("~#bitrate", 0)),
            fmt=file.metadata["~format"],
            art=file.metadata["artist"],
            ttl=file.metadata["title"],
            alb=file.metadata["album"],
            tnm=file.metadata["tracknumber"],
            gnr=file.metadata["genre"],
            yrr=file.metadata["date"][:4])

    def _create_fingerprint(self, file, handler):
        if file.state != file.PENDING:
            handler(file, None)
            return
        self.tagger.window.set_statusbar_message(N_("Creating fingerprint for file %s..."), file.filename)
        filename = encode_filename(file.filename)
        fingerprint = None
        for decoder in self._decoders:
            self.log.debug("Decoding using %r...", decoder.__name__)
            try:
                result = decoder.decode(filename)
            except Exception:
                continue
            if result:
                self.log.debug("Fingerprinting...")
                buffer, samples, sample_rate, stereo, duration = result
                fingerprint = ofa.create_print(buffer, samples, sample_rate, stereo)
                if fingerprint:
                    proxy_to_main(self._lookup_fingerprint, file, fingerprint, handler, duration)
                    return
                else:
                    break
        proxy_to_main(handler, file, None)

    def analyze(self, file, handler):
        if 'musicip_puid' in file.metadata:
            handler(file, file.metadata.getall('musicip_puid')[0])
        else:
            if 'musicip_fingerprint' in file.metadata:
                fingerprint = file.metadata.getall('musicip_fingerprint')[0]
                self._lookup_fingerprint(file, fingerprint, handler)
            elif ofa is not None:
                self.tagger.analyze_thread.add_task(self._create_fingerprint, file, handler)
            else:
                handler(file, None)
