# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2004 Robert Kaye
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
from picard.album import Album
from picard.artist import Artist

class UnmatchedFiles(Album):
    
    def __init__(self):
        self._origName = u"Unmatched Files (%d)"
        Album.__init__(self, u"[unmatched files]", self._origName)

    def addUnmatchedFile(self, file):
        self.name = self._origName % (self.numUnmatchedFiles + 1) 
        Album.addUnmatchedFile(self, file)
        
    def removeFile(self, file):
        self.name = self._origName % (self.numUnmatchedFiles - 1) 
        Album.removeFile(self, file)
        
        
class Clusters(Album):
    pass

class AlbumManager(QtCore.QObject):
    
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.albums = []
        self.unmatchedFiles = UnmatchedFiles()
        self.clusters = Clusters(u"[clusters]", u"Clusters")
        
    def load(self, albumId):
        albumId = unicode(albumId)
        album = Album(albumId, "[loading album information]", None)
        self.albums.append(album)
        self.emit(QtCore.SIGNAL("albumAdded"), album)
        self.tagger.worker.loadAlbum(album)
        #album.load()

    def getAlbumById(self, id):
        for album in self.albums:
            if album.id == id:
                return album
        return None

    def getNumAlbums(self):
        return len(self.albums)

