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

from collections import defaultdict
from heapq import (
    heappop,
    heappush,
)
import ntpath
from operator import itemgetter
import re

from PyQt5 import QtCore

from picard import config
from picard.const import QUERY_LIMIT
from picard.const.sys import IS_WIN
from picard.metadata import Metadata
from picard.similarity import similarity
from picard.util import (
    album_artist_from_path,
    format_time,
)
from picard.util.imagelist import (
    add_metadata_images,
    remove_metadata_images,
    update_metadata_images,
)

from picard.ui.item import Item


class Cluster(QtCore.QObject, Item):

    # Weights for different elements when comparing a cluster to a release
    comparison_weights = {
        'album': 17,
        'albumartist': 6,
        'totaltracks': 5,
        'releasecountry': 2,
        'format': 2,
    }

    def __init__(self, name, artist="", special=False, related_album=None, hide_if_empty=False):
        QtCore.QObject.__init__(self)
        self.item = None
        self.metadata = Metadata()
        self.metadata['album'] = name
        self.metadata['albumartist'] = artist
        self.metadata['totaltracks'] = 0
        self.special = special
        self.hide_if_empty = hide_if_empty
        self.related_album = related_album
        self.files = []
        self.lookup_task = None

    def __repr__(self):
        if self.related_album:
            return '<Cluster %s %r>' % (
                self.related_album.id,
                self.related_album.metadata[u"album"] + '/' + self.metadata['album']
            )
        return '<Cluster %r>' % self.metadata['album']

    def __len__(self):
        return len(self.files)

    def _update_related_album(self, added_files=None, removed_files=None):
        if self.related_album:
            if added_files:
                add_metadata_images(self.related_album, added_files)
            if removed_files:
                remove_metadata_images(self.related_album, removed_files)
            self.related_album.update()

    def add_files(self, files):
        for file in files:
            self.metadata.length += file.metadata.length
            file._move(self)
            file.update(signal=False)
            if self.can_show_coverart:
                file.metadata_images_changed.connect(self.update_metadata_images)
        self.files.extend(files)
        self.metadata['totaltracks'] = len(self.files)
        self.item.add_files(files)
        if self.can_show_coverart:
            add_metadata_images(self, files)
        self._update_related_album(added_files=files)

    def add_file(self, file):
        self.add_files([file])

    def remove_file(self, file):
        self.metadata.length -= file.metadata.length
        self.files.remove(file)
        self.metadata['totaltracks'] = len(self.files)
        self.item.remove_file(file)
        if not self.special and self.get_num_files() == 0:
            self.tagger.remove_cluster(self)
        if self.can_show_coverart:
            file.metadata_images_changed.disconnect(self.update_metadata_images)
            remove_metadata_images(self, [file])
        self._update_related_album(removed_files=[file])

    def update(self):
        if self.item:
            self.item.update()

    def get_num_files(self):
        return len(self.files)

    def iterfiles(self, save=False):
        for file in self.files:
            yield file

    def can_save(self):
        """Return if this object can be saved."""
        if self.files:
            return True
        else:
            return False

    def can_remove(self):
        """Return if this object can be removed."""
        return not self.special

    def can_edit_tags(self):
        """Return if this object supports tag editing."""
        return True

    def can_analyze(self):
        """Return if this object can be fingerprinted."""
        return any([_file.can_analyze() for _file in self.files])

    def can_autotag(self):
        return True

    def can_refresh(self):
        return False

    def can_browser_lookup(self):
        return not self.special

    def can_view_info(self):
        if self.files:
            return True
        else:
            return False

    def is_album_like(self):
        return True

    def column(self, column):
        if column == 'title':
            return '%s (%d)' % (self.metadata['album'], len(self.files))
        elif (column == '~length' and self.special) or column == 'album':
            return ''
        elif column == '~length':
            return format_time(self.metadata.length)
        elif column == 'artist':
            return self.metadata['albumartist']
        return self.metadata[column]

    def _lookup_finished(self, document, http, error):
        self.lookup_task = None

        try:
            releases = document['releases']
        except (KeyError, TypeError):
            releases = None

        mparms = {
            'album': self.metadata['album']
        }

        # no matches
        if not releases:
            self.tagger.window.set_statusbar_message(
                N_("No matching releases for cluster %(album)s"),
                mparms,
                timeout=3000
            )
            return

        # multiple matches -- calculate similarities to each of them
        match = sorted((self.metadata.compare_to_release(
            release, Cluster.comparison_weights) for release in releases),
            reverse=True, key=itemgetter(0))[0]

        if match[0] < config.setting['cluster_lookup_threshold']:
            self.tagger.window.set_statusbar_message(
                N_("No matching releases for cluster %(album)s"),
                mparms,
                timeout=3000
            )
            return
        self.tagger.window.set_statusbar_message(
            N_("Cluster %(album)s identified!"),
            mparms,
            timeout=3000
        )
        self.tagger.move_files_to_album(self.files, match[1]['id'])

    def lookup_metadata(self):
        """Try to identify the cluster using the existing metadata."""
        if self.lookup_task:
            return
        self.tagger.window.set_statusbar_message(
            N_("Looking up the metadata for cluster %(album)s..."),
            {'album': self.metadata['album']}
        )
        self.lookup_task = self.tagger.mb_api.find_releases(self._lookup_finished,
            artist=self.metadata['albumartist'],
            release=self.metadata['album'],
            tracks=str(len(self.files)),
            limit=QUERY_LIMIT)

    def clear_lookup_task(self):
        if self.lookup_task:
            self.tagger.webservice.remove_task(self.lookup_task)
            self.lookup_task = None

    @staticmethod
    def cluster(files, threshold):
        win_compat = config.setting["windows_compatibility"] or IS_WIN
        artist_dict = ClusterDict()
        album_dict = ClusterDict()
        tracks = []
        for file in files:
            artist = file.metadata["albumartist"] or file.metadata["artist"]
            album = file.metadata["album"]
            # Improve clustering from directory structure if no existing tags
            # Only used for grouping and to provide cluster title / artist - not added to file tags.
            if win_compat:
                filename = ntpath.splitdrive(file.filename)[1]
            else:
                filename = file.filename
            album, artist = album_artist_from_path(filename, album, artist)
            # For each track, record the index of the artist and album within the clusters
            tracks.append((artist_dict.add(artist), album_dict.add(album)))

        artist_cluster_engine = ClusterEngine(artist_dict)
        artist_cluster_engine.cluster(threshold)

        album_cluster_engine = ClusterEngine(album_dict)
        album_cluster_engine.cluster(threshold)

        # Arrange tracks into albums
        albums = {}
        for i, track in enumerate(tracks):
            cluster = album_cluster_engine.get_cluster_from_id(track[1])
            if cluster is not None:
                albums.setdefault(cluster, []).append(i)

        # Now determine the most prominent names in the cluster and build the
        # final cluster list
        for album_id, album in albums.items():
            album_name = album_cluster_engine.get_cluster_title(album_id)

            artist_max = 0
            artist_id = None
            artist_hist = {}
            for track_id in album:
                cluster = artist_cluster_engine.get_cluster_from_id(tracks[track_id][0])
                if cluster is not None:
                    cnt = artist_hist.get(cluster, 0) + 1
                    if cnt > artist_max:
                        artist_max = cnt
                        artist_id = cluster
                    artist_hist[cluster] = cnt

            if artist_id is None:
                artist_name = "Various Artists"
            else:
                artist_name = artist_cluster_engine.get_cluster_title(artist_id)

            yield album_name, artist_name, (files[i] for i in album)

    def update_metadata_images(self):
        if self.can_show_coverart:
            update_metadata_images(self)


class UnclusteredFiles(Cluster):

    """Special cluster for 'Unmatched Files' which have no PUID and have not been clustered."""

    def __init__(self):
        super().__init__(_("Unclustered Files"), special=True)

    def add_files(self, files):
        super().add_files(files)
        self.tagger.window.enable_cluster(self.get_num_files() > 0)

    def add_file(self, file):
        super().add_file(file)
        self.tagger.window.enable_cluster(self.get_num_files() > 0)

    def remove_file(self, file):
        super().remove_file(file)
        self.tagger.window.enable_cluster(self.get_num_files() > 0)

    def lookup_metadata(self):
        self.tagger.autotag(self.files)

    def can_edit_tags(self):
        return False

    def can_autotag(self):
        return len(self.files) > 0

    def can_view_info(self):
        return False

    def can_remove(self):
        return len(self.files) > 0

    @property
    def can_show_coverart(self):
        return False


class ClusterList(list, Item):

    """A list of clusters."""

    def __init__(self):
        super().__init__()

    def __hash__(self):
        return id(self)

    def iterfiles(self, save=False):
        for cluster in self:
            for file in cluster.iterfiles(save):
                yield file

    def can_save(self):
        return len(self) > 0

    def can_analyze(self):
        return any([cluster.can_analyze() for cluster in self])

    def can_autotag(self):
        return len(self) > 0

    def can_browser_lookup(self):
        return False

    def lookup_metadata(self):
        for cluster in self:
            cluster.lookup_metadata()


class ClusterDict(object):

    def __init__(self):
        # word -> id index
        self.words = defaultdict(lambda: (-1, 0))
        # id -> word, token index
        self.ids = defaultdict(lambda: (None, None))
        # counter for new id generation
        self.id = 0
        self.regexp = re.compile(r'\W', re.UNICODE)
        self.spaces = re.compile(r'\s', re.UNICODE)

    def get_size(self):
        return self.id

    def tokenize(self, word):
        word = word.lower()
        token = self.regexp.sub('', word)
        return token if token else self.spaces.sub('', word)

    def add(self, word):
        """
        Add a new entry to the cluster if it does not exist. If it
        does exist, increment the count. Return the index of the word
        in the dictionary or -1 is the word is empty.
        """

        if word == '':
            return -1

        index, count = self.words[word]
        if index == -1:
            token = self.tokenize(word)
            if token == '':
                return -1
            index = self.id
            self.ids[index] = (word, token)
            self.id = self.id + 1
        self.words[word] = (index, count + 1)

        return index

    def get_word(self, index):
        word, token = self.ids[index]
        return word

    def get_token(self, index):
        word, token = self.ids[index]
        return token

    def get_word_and_count(self, index):
        word, unused = self.ids[index]
        unused, count = self.words[word]
        return word, count


class ClusterEngine(object):

    def __init__(self, cluster_dict):
        # the cluster dictionary we're using
        self.cluster_dict = cluster_dict
        # keeps track of unique cluster index
        self.cluster_count = 0
        # Keeps track of the clusters we've created
        self.cluster_bins = {}
        # Index the word ids -> clusters
        self.index_id_cluster = {}

    def get_cluster_from_id(self, clusterid):
        return self.index_id_cluster.get(clusterid)

    def get_cluster_title(self, cluster):

        if cluster < 0:
            return ""

        cluster_max = 0
        maxWord = ''
        for cluster_bin in self.cluster_bins[cluster]:
            word, count = self.cluster_dict.get_word_and_count(cluster_bin)
            if count >= cluster_max:
                maxWord = word
                cluster_max = count

        return maxWord

    def cluster(self, threshold):

        # Keep the matches sorted in a heap
        heap = []

        for y in range(self.cluster_dict.get_size()):
            token_y = self.cluster_dict.get_token(y).lower()
            for x in range(y):
                if x != y:
                    token_x = self.cluster_dict.get_token(x).lower()
                    c = similarity(token_x, token_y)
                    if c >= threshold:
                        heappush(heap, ((1.0 - c), [x, y]))
            QtCore.QCoreApplication.processEvents()

        for i in range(self.cluster_dict.get_size()):
            word, count = self.cluster_dict.get_word_and_count(i)
            if word and count > 1:
                self.cluster_bins[self.cluster_count] = [i]
                self.index_id_cluster[i] = self.cluster_count
                self.cluster_count = self.cluster_count + 1

        for i in range(len(heap)):
            c, pair = heappop(heap)
            c = 1.0 - c

            try:
                match0 = self.index_id_cluster[pair[0]]
            except BaseException:
                match0 = -1

            try:
                match1 = self.index_id_cluster[pair[1]]
            except BaseException:
                match1 = -1

            # if neither item is in a cluster, make a new cluster
            if match0 == -1 and match1 == -1:
                self.cluster_bins[self.cluster_count] = [pair[0], pair[1]]
                self.index_id_cluster[pair[0]] = self.cluster_count
                self.index_id_cluster[pair[1]] = self.cluster_count
                self.cluster_count = self.cluster_count + 1
                continue

            # If cluster0 is in a bin, stick the other match into that bin
            if match0 >= 0 and match1 < 0:
                self.cluster_bins[match0].append(pair[1])
                self.index_id_cluster[pair[1]] = match0
                continue

            # If cluster1 is in a bin, stick the other match into that bin
            if match1 >= 0 and match0 < 0:
                self.cluster_bins[match1].append(pair[0])
                self.index_id_cluster[pair[0]] = match1
                continue

            # If both matches are already in two different clusters, merge the clusters
            if match1 != match0:
                self.cluster_bins[match0].extend(self.cluster_bins[match1])
                for match in self.cluster_bins[match1]:
                    self.index_id_cluster[match] = match0
                del self.cluster_bins[match1]

    def can_refresh(self):
        return False
