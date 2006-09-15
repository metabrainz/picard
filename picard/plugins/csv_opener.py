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
        self.orig_metadata["title"] = row[0].decode('utf-8', 'replace')
        self.orig_metadata["artist"] = row[1].decode('utf-8', 'replace')
        self.orig_metadata["date"] = row[2].decode('utf-8', 'replace')
        self.orig_metadata["album"] = row[3].decode('utf-8', 'replace')
        self.orig_metadata["tracknumber"] = row[4].decode('utf-8', 'replace')
        self.orig_metadata["~filename"] = self.base_filename
        self.orig_metadata["~#length"] = int(row[5])
        self.metadata.copy(self.orig_metadata)

class CsvOpener(Component):
    
    implements(IFileOpener)
    
    def get_supported_formats(self):
        return ((u".csv", u"CSV file with tags (for testing)"),)
        
    def can_open_file(self, filename):
        return filename[-4:].lower() == u".csv"

    def open_file(self, filename):
        import csv
        files = []
        f = csv.reader(file(filename))
        for row in f:
            files.append(CsvVirtualFile(row))
        return files

