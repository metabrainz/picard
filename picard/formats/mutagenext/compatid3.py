# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2005 Michael Urman
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

from mutagen.id3 import ID3, Frames, Frames_2_2, TextFrame


class TCMP(TextFrame):
    pass


class TSO2(TextFrame):
    pass


class TSOC(TextFrame):
    pass


class XDOR(TextFrame):
    pass


class XSOP(TextFrame):
    pass


class CompatID3(ID3):

    """
    Additional features over mutagen.id3.ID3:
     * iTunes' TCMP frame
     * Allow some v2.4 frames also in v2.3
    """

    PEDANTIC = False

    def __init__(self, *args, **kwargs):
        if args:
            known_frames = dict(Frames)
            known_frames.update(dict(Frames_2_2))
            known_frames["TCMP"] = TCMP
            known_frames["TSO2"] = TSO2
            known_frames["TSOC"] = TSOC
            known_frames["XDOR"] = XDOR
            known_frames["XSOP"] = XSOP
            kwargs["known_frames"] = known_frames
        super().__init__(*args, **kwargs)

    def update_to_v23(self):
        # leave TSOP, TSOA and TSOT even though they are officially defined
        # only in ID3v2.4, because most applications use them also in ID3v2.3
        frames = []
        for key in ["TSOP", "TSOA", "TSOT", "TSST"]:
            frames.extend(self.getall(key))
        super().update_to_v23()
        for frame in frames:
            self.add(frame)
