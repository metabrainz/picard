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

class CoverArtArchive:
    # list of types from http://musicbrainz.org/doc/Cover_Art/Types
# take care of the order of declaration
    CAATYPES = [
        ("front", N_("Front"),
         N_("<p>The Album cover, this is the front of the packaging of an "
           "audio recording (or in the case of a digital release the image "
           "associated with it in a digital media store).</p>")),
        ("back", N_("Back"),
         N_("<p>The back of the package of an audio recording, this will "
           "often contain the track listing, barcode and copyright "
           "information.</p>")),
        ("booklet", N_("Booklet"),
         N_("<p>A small book or group of pages inserted into the compact "
           "disc or DVD jewel case or the equivalent packaging for vinyl "
           "records and cassettes. Digital releases sometimes include a "
           "booklet in a digital file (usually PDF). Booklets often "
           "contain liner notes, song lyrics and/or photographs of "
           "the artist or band.</p>")),
        ("medium", N_("Medium"),
         N_("<p>The medium contains the audio recording, for a compact "
           "disc release it is the compact disc itself, similarly for "
           "a vinyl release it is the vinyl disc itself, etc..</p>")),
        ("tray", N_("Tray"),
         N_("<p>The image behind or on the tray containing the medium. "
           "For jewel cases, this is usually printed on the other side "
           "of the piece of paper with the back image.</p>")),
        ("obi", N_("Obi"),
         N_("<p>An obi is a strip of paper around the spine (or "
           "occasionally one of the other edges of the packaging).</p>")),
        ("spine", N_("Spine"),
         N_("<p>A spine is the edge of the package of an audio recording, "
           "it is often the only part visible when recordings are stacked "
           "or stored in a shelf. For compact discs the spine is usually "
           "part of the back cover scan, and should not be uploaded "
           "separately.</p>")),
        ("track", N_("Track"),
         N_("<p>Digital releases sometimes have cover art associated with "
           "each individual track of a release (typically embedded in the "
           ".mp3 files), use this type for images associated with "
           "individual tracks.</p>")),
        ("sticker", N_("Sticker"),
         N_("<p>A sticker is an adhesive piece of paper, that is attached "
           "to the plastic film or enclosed inside the packaging.</p>")),
        ("other", N_("Other"),
         N_("<p>Anything which doesn't fit in the types defined above.</p>")),
        ("unknown", N_("Unknown"), # pseudo type, used for the no type case
         N_("<p>Images for which no type was set.</p>")),
    ]

    CAATYPES_SEP = ' '  #separator to use when joining/splitting list of types

    CAATYPE_TO_NAME = dict([(e[0], e[1]) for e in CAATYPES])

    @staticmethod
    def types2str(types, sep=','):
        l = []
        for t in types:
            l.append(_(CoverArtArchive.CAATYPE_TO_NAME[t]))
        return sep.join(l)
