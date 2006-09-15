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

import re
from picard.api import IFileOpener
from picard.component import Component, implements
from picard.file import File

_whitespace_re = re.compile('\s', re.UNICODE)
_split_re = re.compile('\s*("[^"]*"|[^ ]+)\s*', re.UNICODE)

def msfToMs(msf):
    msf = msf.split(":")
    return ((int(msf[0]) * 60 + int(msf[1])) * 75 + int(msf[2])) * 1000 / 75   

class CuesheetTrack(list):

    def __init__(self, cuesheet, index):
        list.__init__(self)
        self.cuesheet = cuesheet
        self.index = index
    
    def find(self, prefix):
        return [i for i in self if tuple(i[:len(prefix)]) == tuple(prefix)]
    
    def getTrackNumber(self):
        return self.index
        
    def getLength(self):
        try:
            nextTrack = self.cuesheet.tracks[self.index+1]
            index0 = self.find((u"INDEX",u"01"))
            index1 = nextTrack.find((u"INDEX",u"01"))
            return msfToMs(index1[0][2]) - msfToMs(index0[0][2]) 
        except IndexError:
            return 0
        
    def getField(self, prefix):
        try:
            return self.find(prefix)[0][len(prefix)]
        except IndexError:
            return u""

    def getArtist(self):
        return self.getField((u"PERFORMER",))

    def getTitle(self):
        return self.getField((u"TITLE",))

    def setArtist(self, artist):
        found = False
        for item in self:
            if item[0] == u"PERFORMER":
                if not found:
                    item[1] = artist
                    found = True
                else:
                    del item
        if not found:
            self.append((u"PERFORMER", artist))
        
    artist = property(getArtist, setArtist)

class Cuesheet(object):
    
    def __init__(self, filename):
        self.filename = filename
        self.tracks = []
        
    def read(self):
        f = file(self.filename)
        self.parse(f.readlines())
        f.close()

    def unquote(self, string):
        if string.startswith('"'):
            if string.endswith('"'):
                return string[1:-1]
            else:
                return string[1:]
        return string
        
    def quote(self, string):
        if _whitespace_re.search(string):
            return '"' + string.replace('"', '\'') + '"'
        return string
        
    def parse(self, lines):
        track = CuesheetTrack(self, 0)
        self.tracks = [track]
        isUnicode = False
        for line in lines:
            # remove BOM
            if line.startswith('\xfe\xff'):
                isUnicode = True
                line = line[1:]
            # decode to unicode string
            line = line.strip()
            if isUnicode:
                line = line.decode('UTF-8', 'replace')
            else:
                line = line.decode('ISO-8859-1', 'replace')
            # parse the line
            split = [self.unquote(s) for s in _split_re.findall(line)]
            keyword = split[0].upper()
            if keyword == 'TRACK':
                trackNum = int(split[1])
                track = CuesheetTrack(self, trackNum)
                self.tracks.append(track)
            track.append(split)

    def write(self):
        lines = []
        for num, track in self.tracks.items():
            for line in track:
                indent = 0
                if num > 0:
                    if line[0] == "TRACK":
                        indent = 2 
                    elif line[0] != "FILE":
                        indent = 4
                line2 = u" ".join([self.quote(s) for s in line])
                lines.append(" " * indent + line2.encode("UTF-8"))
        return "\r\n".join(lines)

class CuesheetVirtualFile(File):
    
    def __init__(self, cuesheet, track):
        File.__init__(self, cuesheet.filename)
        self.cuesheet = cuesheet
        self.track = track
        self.orig_metadata["ARTIST"] = track.getArtist()
        self.orig_metadata["TITLE"] = track.getTitle()
        self.orig_metadata["ALBUM"] = cuesheet.tracks[0].getTitle()
        self.orig_metadata["ALBUMARTIST"] = cuesheet.tracks[0].getArtist()
        self.orig_metadata["TRACKNUMBER"] = str(track.getTrackNumber())
        self.orig_metadata["TOTALTRACKS"] = str(len(cuesheet.tracks) - 1)

        # Special tags
        self.orig_metadata["~filename"] = self.base_filename
        self.orig_metadata["~#length"] = track.getLength()

        self.metadata.copy(self.orig_metadata)

class CuesheetOpener(Component):
    
    implements(IFileOpener)
    
    def get_supported_formats(self):
        return ((u".cue", u"Cuesheet"),)
        
    def can_open_file(self, filename):
        return filename[-4:].lower() == u".cue"

    def open_file(self, filename):
        cuesheet = Cuesheet(filename)
        cuesheet.read()
        files = []
        for track in cuesheet.tracks[1:]:
            file = CuesheetVirtualFile(cuesheet, track)
            files.append(file)
        print files
        return files
        
if __name__ == "__main__":
    cue = Cuesheet("a.cue")
    cue.read()
    for num, track in cue.tracks.items():
        print num, track

    print "-------"
    print cue.write()
#    cue.tracks[0].setArtist(0)
    

