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

import re
from heapq import heappush, heappop 
from PyQt4 import QtCore
from picard.metadata import Metadata
from picard.similarity import similarity

class Cluster(QtCore.QObject):

    def __init__(self, name, artist="", special=False):
        QtCore.QObject.__init__(self)
        self.metadata = Metadata()
        self.metadata["album"] = name
        self.metadata["artist"] = artist
        self.metadata["~#length"] = 0
        self.special = special
        self.name = name
        self.artist = artist
        self.files = []

    def __str__(self):
        return '<Cluster "%s">' % (self.name.decode("UTF-8"))

    def add_file(self, file):
        self.metadata["~#length"] += file.metadata.get("~#length", 0)
        self.files.append(file)
        index = self.index_of_file(file)
        self.emit(QtCore.SIGNAL("fileAdded"), self, file, index)

    def remove_file(self, file):
        self.metadata["~#length"] -= file.metadata.get("~#length", 0)
        index = self.index_of_file(file)
        self.files.remove(file)
        self.emit(QtCore.SIGNAL("fileRemoved"), self, file, index)
        if not self.special and self.get_num_files() == 0:
            self.tagger.remove_cluster(self) 

    def get_num_files(self):
        return len(self.files)

    def index_of_file(self, file):
        return self.files.index(file)

    def can_save(self):
        """Return if this object can be saved."""
        if self.files:
            return True
        else:
            return False

    def can_remove(self):
        """Return if this object can be removed."""
        return True

    def can_edit_tags(self):
        """Return if this object supports tag editing."""
        return False

    def can_analyze(self):
        """Return if this object can be fingerprinted."""
        return False


class ClusterDict(object):
   
    def __init__(self):
        # word -> id index
        self.words = {}
        # id -> word, token index
        self.ids = {}
        # counter for new id generation
        self.id = 0
        self.regexp = re.compile(ur'\W', re.UNICODE)

    def getSize(self):
        return self.id

    def tokenize(self, word):
        return self.regexp.sub(u'', word.lower())

    def add(self, word):
        if word == u'': 
           return -1
       
        token = self.tokenize(word)
        if token == u'': 
           return -1

        try:
           index, count = self.words[word]
           self.words[word] = (index, count + 1)
        except KeyError:
           index = self.id
           self.words[word] = (self.id, 1)
           self.ids[index] = (word, token)
           self.id = self.id + 1

        return index

    def getWord(self, index):
        word = None
        try:
            word, token = self.ids[index]
        except KeyError:
            pass
        return word

    def getToken(self, index):
        token = None;
        try:
            word, token = self.ids[index]
        except KeyError:
            pass
        return token

    def getWordAndCount(self, index):
        word = None
        count = 0
        try:
           word, token = self.ids[index]
           index, count = self.words[word]
        except KeyError:
           pass
        return word, count 


class ClusterEngine(object):

    def __init__(self, clusterDict):
        # the cluster dictionary we're using
        self.clusterDict = clusterDict
        # keeps track of unique cluster index
        self.clusterCount = 0
        # Keeps track of the clusters we've created
        self.clusterBins = {}
        # Index the word ids -> clusters
        self.idClusterIndex = {}

    def getClusterFromId(self, id):
        return self.idClusterIndex.get(id)

    def printCluster(self, cluster):
        if cluster < 0: 
            print "[no such cluster]"
            return

        bin = self.clusterBins[cluster]
        print cluster, " -> ", ", ".join([("'" + self.clusterDict.getWord(i) + "'") for i in bin])

    def getClusterTitle(self, cluster):

        if cluster < 0: 
            return ""

        max = 0 
        maxWord = u''
        for id in self.clusterBins[cluster]:
            word, count = self.clusterDict.getWordAndCount(id)
            if count >= max:
                maxWord = word
                max = count

        return maxWord

    def cluster(self, threshold):

        # keep the matches sorted in a heap
        heap = []

        for y in xrange(self.clusterDict.getSize()):
            for x in xrange(y):
                if x != y:
                    c = similarity(self.clusterDict.getToken(x).lower(), 
                                   self.clusterDict.getToken(y).lower())
                    #print "'%s' - '%s' = %f" % (
                    #    self.clusterDict.getToken(x).encode('utf-8', 'replace').lower(),  
                    #    self.clusterDict.getToken(y).encode('utf-8', 'replace').lower(), c)

                    if c >= threshold:
                        heappush(heap, ((1.0 - c), [x, y]))

        for i in xrange(self.clusterDict.getSize()):
            word, count = self.clusterDict.getWordAndCount(i)
            if word and count > 1:
                self.clusterBins[self.clusterCount] = [ i ]
                self.idClusterIndex[i] = self.clusterCount
                self.clusterCount = self.clusterCount + 1
                #print "init ",
                #self.printCluster(self.clusterCount - 1)

        for i in xrange(len(heap)):
            c, pair = heappop(heap)
            c = 1.0 - c

            try: 
                match0 = self.idClusterIndex[pair[0]]
            except:
                match0 = -1

            try: 
                match1 = self.idClusterIndex[pair[1]]
            except:
                match1 = -1

            # if neither item is in a cluster, make a new cluster
            if match0 == -1 and match1 == -1:
                self.clusterBins[self.clusterCount] = [pair[0], pair[1]]
                self.idClusterIndex[pair[0]] = self.clusterCount
                self.idClusterIndex[pair[1]] = self.clusterCount
                self.clusterCount = self.clusterCount + 1
                #print "new ",
                #self.printCluster(self.clusterCount - 1)
                continue

            # If cluster0 is in a bin, stick the other match into that bin
            if match0 >= 0 and match1 < 0:
                self.clusterBins[match0].append(pair[1]) 
                self.idClusterIndex[pair[1]] = match0
                #print "add '%s' to cluster " % (self.clusterDict.getWord(pair[0])), 
                #self.printCluster(match0)
                continue
               
            # If cluster1 is in a bin, stick the other match into that bin
            if match1 >= 0 and match0 < 0:
                self.clusterBins[match1].append(pair[0]) 
                self.idClusterIndex[pair[0]] = match1
                #print "add '%s' to cluster " % (self.clusterDict.getWord(pair[1])),
                #self.printCluster(match0)
                continue

            # If both matches are already in two different clusters, merge the clusters
            if match1 != match0:
                self.clusterBins[match0].extend(self.clusterBins[match1])
                for match in self.clusterBins[match1]:
                    self.idClusterIndex[match] = match0
                #print "col cluster %d into cluster" % (match1),
                #self.printCluster(match0)
                del self.clusterBins[match1]

        return self.clusterBins 


class FileClusterEngine(object):
   
    def cluster(self, files, threshold):

        artistDict = ClusterDict()
        albumDict = ClusterDict()
        artists = {}
        albums = {}
        tracks = []

        for file in files:
            tracks.append({'file': file, 
                           'artistIndex': artistDict.add(file.metadata["artist"]),
                           'albumIndex': albumDict.add(file.metadata["album"])
                           })

        artistClusterEngine = ClusterEngine(artistDict)
        artistCluster = artistClusterEngine.cluster(threshold)

        albumClusterEngine = ClusterEngine(albumDict)
        albumCluster = albumClusterEngine.cluster(threshold) 

        # Arrange tracks into albums
        for i in xrange(len(tracks)):
            cluster = albumClusterEngine.getClusterFromId(
                  tracks[i]['albumIndex'])
            if cluster is not None:
                albums.setdefault(cluster, []).append(i)

        # Arrange tracks into artist groups
        for i in xrange(len(tracks)):
            cluster = artistClusterEngine.getClusterFromId(
               tracks[i]['artistIndex'])
            if cluster is not None:
                artists.setdefault(cluster, []).append(i)

        #print "Artists:"
        #for artist in artists.keys():
        #    print artistClusterEngine.getClusterTitle(artist).encode('utf-8', 'replace')

        # Now determine the most prominent names in the cluster and build the final cluster list
        for album in albums.keys():

            albumName = albumClusterEngine.getClusterTitle(album)

            artistHist = {}
            fileList = []
            for track in albums[album]:
                cluster = artistClusterEngine.getClusterFromId(tracks[track]['artistIndex'])
                fileList.append(tracks[track]['file'])
                try:
                    artistHist[cluster] += 1
                except KeyError:
                    artistHist[cluster] = 1

            if len(artistHist.keys()) == 1 and artistHist.keys()[0] is None:
                artistName = u"Various Artists"
            else:
                res = map(None, artistHist.values(), artistHist.keys())
                res.sort()
                res.reverse()
                artistName = artistClusterEngine.getClusterTitle(res[0][1])

            yield albumName, artistName, fileList
