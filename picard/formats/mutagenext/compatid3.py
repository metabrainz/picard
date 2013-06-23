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

import struct
from struct import pack, unpack
import mutagen
from mutagen._util import insert_bytes
from mutagen.id3 import ID3, Frame, Frames, Frames_2_2, TextFrame, TORY, \
                        TYER, TIME, APIC, IPLS, TDAT, BitPaddedInt, MakeID3v1

class TCMP(TextFrame):
    pass

class TSO2(TextFrame):
    pass

class XDOR(TextFrame):
    pass

class XSOP(TextFrame):
    pass

class CompatID3(ID3):
    """
    Additional features over mutagen.id3.ID3:
     * ID3v2.3 writing
     * iTunes' TCMP frame
    """

    PEDANTIC = False

    def __init__(self, *args, **kwargs):
        self.unknown_frames = []
        if args:
            known_frames = dict(Frames)
            known_frames.update(dict(Frames_2_2))
            known_frames["TCMP"] = TCMP
            known_frames["TSO2"] = TSO2
            known_frames["XDOR"] = XDOR
            known_frames["XSOP"] = XSOP
            kwargs["known_frames"] = known_frames
        super(CompatID3, self).__init__(*args, **kwargs) 

    def save(self, filename=None, v1=1, v2=4):
        """Save changes to a file.

        If no filename is given, the one most recently loaded is used.

        Keyword arguments:
        v1 -- if 0, ID3v1 tags will be removed
              if 1, ID3v1 tags will be updated but not added
              if 2, ID3v1 tags will be created and/or updated
        v2 -- version of ID3v2 tags (3 or 4). By default Mutagen saves ID3v2.4
              tags. If you want to save ID3v2.3 tags, you must call method
              update_to_v23 before saving the file.

        The lack of a way to update only an ID3v1 tag is intentional.
        """

        # Sort frames by 'importance'
        order = ["TIT2", "TPE1", "TRCK", "TALB", "TPOS", "TDRC", "TCON"]
        order = dict(zip(order, range(len(order))))
        last = len(order)
        frames = self.items()
        frames.sort(lambda a, b: cmp(order.get(a[0][:4], last),
                                     order.get(b[0][:4], last)))

        framedata = [self.__save_frame(frame, v2) for (key, frame) in frames]
        framedata.extend([data for data in self.unknown_frames
                if len(data) > 10])
        if not framedata:
            try:
                self.delete(filename)
            except EnvironmentError, err:
                from errno import ENOENT
                if err.errno != ENOENT: raise
            return

        framedata = ''.join(framedata)
        framesize = len(framedata)

        if filename is None: filename = self.filename
        try: f = open(filename, 'rb+')
        except IOError, err:
            from errno import ENOENT
            if err.errno != ENOENT: raise
            f = open(filename, 'ab') # create, then reopen
            f = open(filename, 'rb+')
        try:
            idata = f.read(10)
            try: id3, vmaj, vrev, flags, insize = unpack('>3sBBB4s', idata)
            except struct.error: id3, insize = '', 0
            insize = BitPaddedInt(insize)
            if id3 != 'ID3': insize = -10

            if insize >= framesize: outsize = insize
            else: outsize = (framesize + 1023) & ~0x3FF
            framedata += '\x00' * (outsize - framesize)

            framesize = BitPaddedInt.to_str(outsize, width=4)
            flags = 0
            header = pack('>3sBBB4s', 'ID3', v2, 0, flags, framesize)
            data = header + framedata

            if (insize < outsize):
                insert_bytes(f, outsize-insize, insize+10)
            f.seek(0)
            f.write(data)

            try:
                f.seek(-128, 2)
            except IOError, err:
                from errno import EINVAL
                if err.errno != EINVAL: raise
                f.seek(0, 2) # ensure read won't get "TAG"

            if f.read(3) == "TAG":
                f.seek(-128, 2)
                if v1 > 0: f.write(MakeID3v1(self))
                else: f.truncate()
            elif v1 == 2:
                f.seek(0, 2)
                f.write(MakeID3v1(self))

        finally:
            f.close()

    def __save_frame(self, frame, v2):
        flags = 0
        if self.PEDANTIC and isinstance(frame, TextFrame):
            if len(str(frame)) == 0: return ''
        framedata = frame._writeData()
        if v2 == 3: bits=8
        else: bits=7
        datasize = BitPaddedInt.to_str(len(framedata), width=4, bits=bits)
        header = pack('>4s4sH', type(frame).__name__, datasize, flags)
        return header + framedata

    def update_to_v23(self, join_with="/"):
        """Convert older (and newer) tags into an ID3v2.3 tag.

        This updates incompatible ID3v2 frames to ID3v2.3 ones. If you
        intend to save tags as ID3v2.3, you must call this function
        at some point.
        """

        if self.version < (2,3,0): del self.unknown_frames[:]

        # TMCL, TIPL -> TIPL
        if "TIPL" in self or "TMCL" in self:
            people = []
            if "TIPL" in self:
                f = self.pop("TIPL")
                people.extend(f.people)
            if "TMCL" in self:
                f = self.pop("TMCL")
                people.extend(f.people)
            if "IPLS" not in self:
                self.add(IPLS(encoding=f.encoding, people=people))

        # TODO:
        #  * EQU2 -> EQUA
        #  * RVA2 -> RVAD 

        #  TDOR -> TORY
        if "TDOR" in self:
            f = self.pop("TDOR")
            if f.text:
                d = f.text[0]
                if d.year and "TORY" not in self:
                    self.add(TORY(encoding=f.encoding, text="%04d" % d.year))

        # TDRC -> TYER, TDAT, TIME
        if "TDRC" in self:
            f = self.pop("TDRC")
            if f.text:
                d = f.text[0]
                if d.year and "TYER" not in self:
                    self.add(TYER(encoding=f.encoding, text="%04d" % d.year))
                if d.month and d.day and "TDAT" not in self:
                    self.add(TDAT(encoding=f.encoding, text="%02d%02d" % (d.day, d.month)))
                if d.hour and d.minute and "TIME" not in self:
                    self.add(TIME(encoding=f.encoding, text="%02d%02d" % (d.hour, d.minute)))

        if "TCON" in self:
            self["TCON"].genres = self["TCON"].genres

        if self.version < (2, 3):
            # ID3v2.2 PIC frames are slightly different.
            pics = self.getall("APIC")
            mimes = { "PNG": "image/png", "JPG": "image/jpeg" }
            self.delall("APIC")
            for pic in pics:
                newpic = APIC(
                    encoding=pic.encoding, mime=mimes.get(pic.mime, pic.mime),
                    type=pic.type, desc=pic.desc, data=pic.data)
                self.add(newpic)

            # ID3v2.2 LNK frames are just way too different to upgrade.
            self.delall("LINK")

        # leave TSOP, TSOA and TSOT even though they are officially defined
        # only in ID3v2.4, because most applications use them also in ID3v2.3

        # New frames added in v2.4.
        for key in ["ASPI", "EQU2", "RVA2", "SEEK", "SIGN", "TDRL", "TDTG",
            "TMOO", "TPRO"]:
            if key in self: del(self[key])

        for frame in self.values():
            # ID3v2.3 doesn't support UTF-8 (and WMP can't read UTF-16 BE)
            if hasattr(frame, "encoding"):
                if frame.encoding > 1:
                    frame.encoding = 1
            # ID3v2.3 doesn't support multiple values
            if isinstance(frame, mutagen.id3.TextFrame):
                try:
                    frame.text = [join_with.join(frame.text)]
                except TypeError:
                    frame.text = frame.text[:1]
