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

import sys
from PyQt4 import QtCore
try:
    from picard.musicdns import ofa
except ImportError:
    ofa = None
from picard import version_string
from picard.const import MUSICDNS_KEY
from picard.util import encode_filename, partial, call_next


class OFA(QtCore.QObject):

    def __init__(self):
        QtCore.QObject.__init__(self)
        if not ofa:
            self.log.warning(
                "Libofa not found! Libofa Fingerprinting will be disabled.")
        self._decoders = []
        self._analyze_tasks = {}
        plugins = ["avcodec", "directshow", "quicktime", "gstreamer"]
        for name in plugins:
            try:
                decoder = getattr(__import__("picard.musicdns." + name).musicdns, name)
                self._decoders.append(decoder)
            except ImportError:
                pass
        if not self._decoders:
            self.log.warning(
                "No decoders found! Libofa Fingerprinting will be disabled.")

    def init(self):
        for decoder in self._decoders:
            decoder.init()

    def done(self):
        for decoder in self._decoders:
            decoder.done()

    def calculate_fingerprint(self, filename):
        """Decode the specified file and calculate a fingerprint."""
        if ofa is None:
            return None, 0
        filename = encode_filename(filename)
        if sys.platform == 'win32':
            filename = filename.encode('utf8', 'replace')
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

    @call_next
    def _lookup_finished(self, next, document, http, error):
        try:
            puid = document.metadata[0].track[0].puid_list[0].puid[0].id
        except (AttributeError, IndexError):
            return None
        # for some reason MusicDNS started to return these bogus PUIDs
        if puid == '00000000-0000-0000-0000-000000000000':
            return None
        return puid

    def _lookup_fingerprint(self, next, filename, result=None, error=None):
        try:
            file = self.tagger.files[filename]
            del self._analyze_tasks[file]
        except KeyError:
            # The file has been removed. do nothing
            return

        if result is None or result[0] is None or error is not None:
            next(file, result=None)
            return
        fingerprint, length = result
        self.tagger.window.set_statusbar_message(
            N_("Looking up the fingerprint for file %s..."), file.filename)
        self.tagger.xmlws.query_musicdns(partial(self._lookup_finished,
                                                 partial(next, file)),
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

    def analyze(self, file, next):
        # return cached PUID
        puids = file.metadata.getall('musicip_puid')
        if puids:
            next(result=puids[0])
            return
        # use cached fingerpring
        fingerprints = file.metadata.getall('musicip_fingerprint')
        if fingerprints:
            self._lookup_fingerprint(self.tagger.analyze_queue.next,
                file.filename, result=(fingerprints[0], 0))
            return
        # calculate fingerprint
        if ofa is not None:
            if file not in self._analyze_tasks:
                task = (partial(self.calculate_fingerprint, file.filename),
                        partial(self._lookup_fingerprint, self.tagger._lookup_puid, file.filename),
                        QtCore.Qt.LowEventPriority + 1)
                self._analyze_tasks[file] = task
                self.tagger.analyze_queue.put(task)
            return
        # no PUID
        next(result=None)

    def stop_analyze(self, file):
        try:
            task = self._analyze_tasks[file]
            self.tagger.analyze_queue.remove(task)
            del self._analyze_tasks[file]
        except:
            pass
