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

from picard.musicdns import ofa


_decoders = []


def init(tagger):
    """Initialize the decoders."""
    # DirectShow
    try:
        from picard.musicdns import directshow
        _decoders.append(directshow)
    except ImportError:
        tagger.log.info("DirectShow decoder not found")
    # QuickTime
    try:
        from picard.musicdns import quicktime
        _decoders.append(quicktime)
    except ImportError:
        tagger.log.info("QuickTime decoder not found")
    # GStreamer
    try:
        from picard.musicdns import gstreamer
        _decoders.append(gstreamer)
    except ImportError:
        tagger.log.info("GStreamer decoder not found")
    # Check if we have at least one decoder
    if not _decoders:
        tagger.log.warning("No decoders found! "
                           "Fingerprinting will be disabled")


def create_fingerprint(filename):
    """Decode the specified file and calculate a fingerprint."""
    # TODO: init/done should be called only once, but the *must* be called
    #       from the same thread as we call decode.
    for decoder in _decoders:
        decoder.init()
        result = decoder.decode(filename)
        decoder.done()
        if result:
            buffer, samples, sample_rate, stereo, duration = result
            fingerprint = ofa.create_print(buffer, samples, sample_rate, stereo)
            return (fingerprint, duration)
    return None
