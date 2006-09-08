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

from picard.api import IFileOpener
from picard.component import Component, implements
from picard.file import File

class CsvVirtualFile(File):

    def __init__(self, row):
        File.__init__(self, unicode(row[6], 'utf-8', 'replace'))
        self.localMetadata["title"] = row[0].decode('utf-8', 'replace')
        self.localMetadata["artist"] = row[1].decode('utf-8', 'replace')
        self.localMetadata["date"] = row[2].decode('utf-8', 'replace')
        self.localMetadata["album"] = row[3].decode('utf-8', 'replace')
        self.localMetadata["tracknumber"] = row[4].decode('utf-8', 'replace')
        self.localMetadata["~filename"] = self.baseFileName
        self.localMetadata["~#length"] = int(row[5])
        self.metadata.copy(self.localMetadata)
        self.audioProperties.length = int(row[5])

class CsvOpener(Component):
    
    implements(IFileOpener)
    
    def getSupportedFormats(self):
        return ((u".csv", u"CSV file with tags (for testing)"),)
        
    def canOpenFile(self, fileName):
        return fileName[-4:].lower() == u".csv"

    def openFile(self, fileName):
        import csv
        files = []
        f = csv.reader(file(fileName))
        for row in f:
            files.append(CsvVirtualFile(row))
        return files

