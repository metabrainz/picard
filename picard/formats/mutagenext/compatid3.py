# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2005 Michael Urman
# Copyright (C) 2006-2008, 2011-2012 Lukáš Lalinský
# Copyright (C) 2013-2014 Sophist-UK
# Copyright (C) 2013-2014, 2018, 2020 Laurent Monin
# Copyright (C) 2014, 2018-2020 Philipp Wolfer
# Copyright (C) 2016 Christoph Reiter
# Copyright (C) 2016 Ville Skyttä
# Copyright (C) 2017 Sambhav Kothari
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


from mutagen.id3 import (
    ID3,
    Frames,
    Frames_2_2,
    TextFrame,
)


try:
    from mutagen.id3 import GRP1
except ImportError:
    class GRP1(TextFrame):
        pass


class XSOP(TextFrame):
    pass


known_frames = dict(Frames)
known_frames.update(dict(Frames_2_2))
known_frames["GRP1"] = GRP1  # Available since mutagen >= 1.38
known_frames["XSOP"] = XSOP


class CompatID3(ID3):

    """
    Additional features over mutagen.id3.ID3:
     * Allow some v2.4 frames also in v2.3
    """

    PEDANTIC = False

    def __init__(self, *args, **kwargs):
        if args:
            kwargs["known_frames"] = known_frames
        super().__init__(*args, **kwargs)

    def update_to_v23(self):
        update_to_v23(self)


def update_to_v23(tags):
    # leave TSOP, TSOA and TSOT even though they are officially defined
    # only in ID3v2.4, because most applications use them also in ID3v2.3
    frames = []
    for key in ["TSOP", "TSOA", "TSOT", "TSST"]:
        frames.extend(tags.getall(key))
    ID3.update_to_v23(tags)
    for frame in frames:
        tags.add(frame)
