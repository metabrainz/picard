# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2008, 2011 Lukáš Lalinský
# Copyright (C) 2008 Hendrik van Antwerpen
# Copyright (C) 2008 Will
# Copyright (C) 2010-2011, 2014, 2018-2021 Philipp Wolfer
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2012 Wieland Hoffmann
# Copyright (C) 2013-2015, 2018-2021 Laurent Monin
# Copyright (C) 2014, 2017 Sophist-UK
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Antonio Larrosa
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2020 Gabriel Ferreira
# Copyright (C) 2020 Ray Bouchard
# Copyright (C) 2021 Petit Minion
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
from enum import IntEnum
from heapq import (
    heappop,
    heappush,
)
import ntpath
from operator import attrgetter
import re

from PyQt5 import QtCore

from picard.config import get_config
from picard.const import QUERY_LIMIT
from picard.const.sys import IS_WIN
from picard.metadata import (
    Metadata,
    SimMatchRelease,
)
from picard.similarity import similarity
from picard.util import (
    album_artist_from_path,
    find_best_match,
    format_time,
    process_events_iter,
)
from picard.util.imagelist import (
    add_metadata_images,
    remove_metadata_images,
    update_metadata_images,
)
from picard.util.progresscheckpoints import ProgressCheckpoints

from picard.ui.item import (
    FileListItem,
    Item,
)


class FileList(QtCore.QObject, FileListItem):

    metadata_images_changed = QtCore.pyqtSignal()

    def __init__(self, files=None):
        QtCore.QObject.__init__(self)
        FileListItem.__init__(self, files)
        self.metadata = Metadata()
        self.orig_metadata = Metadata()
        if self.files and self.can_show_coverart:
            for file in self.files:
                file.metadata_images_changed.connect(self.update_metadata_images)
            update_metadata_images(self)

    def iterfiles(self, save=False):
        yield from self.files

    def update(self):
        pass

    @property
    def can_show_coverart(self):
        return True


class Cluster(FileList):

    # Weights for different elements when comparing a cluster to a release
    comparison_weights = {
        'album': 17,
        'albumartist': 6,
        'totaltracks': 5,
        'releasetype': 10,
        'releasecountry': 2,
        'format': 2,
        'date': 4,
    }

    def __init__(self, name, artist="", special=False, related_album=None, hide_if_empty=False):
        super().__init__()
        self.item = None
        self.metadata['album'] = name
        self.metadata['albumartist'] = artist
        self.metadata['totaltracks'] = 0
        self.special = special
        self.hide_if_empty = hide_if_empty
        self.related_album = related_album
        self.lookup_task = None

    def __repr__(self):
        if self.related_album:
            return '<Cluster %s %r>' % (
                self.related_album.id,
                self.related_album.metadata["album"] + '/' + self.metadata['album']
            )
        return '<Cluster %r>' % self.metadata['album']

    def __len__(self):
        return len(self.files)

    @property
    def album(self):
        return self.related_album

    def _update_related_album(self, added_files=None, removed_files=None):
        if self.related_album:
            if added_files:
                add_metadata_images(self.related_album, added_files)
            if removed_files:
                remove_metadata_images(self.related_album, removed_files)
            self.related_album.update()

    def add_files(self, files, new_album=True):
        added_files = set(files) - set(self.files)
        if not added_files:
            return
        for file in added_files:
            self.metadata.length += file.metadata.length
            file._move(self)
            file.update(signal=False)
            if self.can_show_coverart:
                file.metadata_images_changed.connect(self.update_metadata_images)
        added_files = sorted(added_files, key=attrgetter('discnumber', 'tracknumber', 'base_filename'))
        self.files.extend(added_files)
        self.metadata['totaltracks'] = len(self.files)
        if self.can_show_coverart:
            add_metadata_images(self, added_files)
        self.item.add_files(added_files)
        if new_album:
            self._update_related_album(added_files=added_files)

    def add_file(self, file, new_album=True):
        self.add_files([file], new_album=new_album)

    def remove_file(self, file, new_album=True):
        self.tagger.window.set_processing(True)
        self.metadata.length -= file.metadata.length
        self.files.remove(file)
        self.metadata['totaltracks'] = len(self.files)
        self.item.remove_file(file)
        if self.can_show_coverart:
            file.metadata_images_changed.disconnect(self.update_metadata_images)
            remove_metadata_images(self, [file])
        if new_album:
            self._update_related_album(removed_files=[file])
        self.tagger.window.set_processing(False)
        if not self.special and self.get_num_files() == 0:
            self.tagger.remove_cluster(self)

    def update(self):
        if self.item:
            self.item.update()

    def get_num_files(self):
        return len(self.files)

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

    def can_submit(self):
        return not self.special and self.files

    def is_album_like(self):
        return True

    def column(self, column):
        if column == 'title':
            return '%s (%d)' % (self.metadata['album'], len(self.files))
        elif self.special and column in {'~length', 'album', 'covercount'}:
            return ''
        elif column == '~length':
            return format_time(self.metadata.length)
        elif column == 'artist':
            return self.metadata['albumartist']
        elif column == 'tracknumber':
            return self.metadata['totaltracks']
        elif column == 'discnumber':
            return self.metadata['totaldiscs']
        elif column == 'covercount':
            return self.cover_art_description()
        return self.metadata[column]

    def _lookup_finished(self, document, http, error):
        self.lookup_task = None

        try:
            releases = document['releases']
        except (KeyError, TypeError):
            releases = None

        def statusbar(message):
            self.tagger.window.set_statusbar_message(
                message,
                {'album': self.metadata['album']},
                timeout=3000
            )

        best_match_release = None
        if releases:
            config = get_config()
            best_match_release = self._match_to_release(releases, threshold=config.setting['cluster_lookup_threshold'])

        if best_match_release:
            statusbar(N_("Cluster %(album)s identified!"))
            self.tagger.move_files_to_album(self.files, best_match_release['id'])
        else:
            statusbar(N_("No matching releases for cluster %(album)s"))

    def _match_to_release(self, releases, threshold=0):
        # multiple matches -- calculate similarities to each of them
        def candidates():
            for release in releases:
                match = self.metadata.compare_to_release(release, Cluster.comparison_weights)
                if match.similarity >= threshold:
                    yield match

        no_match = SimMatchRelease(similarity=-1, release=None)
        best_match = find_best_match(candidates, no_match)

        return best_match.result.release

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
    def cluster(files, threshold, tagger=None):
        config = get_config()
        win_compat = config.setting["windows_compatibility"] or IS_WIN
        artist_dict = ClusterDict()
        album_dict = ClusterDict()
        tracks = []
        num_files = len(files)

        # 10 evenly spaced indexes of files being clustered, used as checkpoints for every 10% progress
        status_update_steps = ProgressCheckpoints(num_files, 10)

        for i, file in process_events_iter(enumerate(files)):
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

            if tagger and status_update_steps.is_checkpoint(i):
                statusmsg = N_("Clustering - step %(step)d/3: %(cluster_type)s (%(update)d%%)")
                mparams = {
                    'step': ClusterType.METADATA.value,
                    'cluster_type': _(ClusterEngine.cluster_type_label(ClusterType.METADATA)),
                    'update': status_update_steps.progress(i),
                }
                tagger.window.set_statusbar_message(statusmsg, mparams)

        artist_cluster_engine = ClusterEngine(artist_dict, ClusterType.ARTIST)
        artist_cluster_engine.cluster(threshold, tagger)

        album_cluster_engine = ClusterEngine(album_dict, ClusterType.ALBUM)
        album_cluster_engine.cluster(threshold, tagger)

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


class UnclusteredFiles(Cluster):

    """Special cluster for 'Unmatched Files' which have not been clustered."""

    def __init__(self):
        super().__init__(_("Unclustered Files"), special=True)

    def add_files(self, files, new_album=True):
        super().add_files(files, new_album=new_album)
        self.tagger.window.enable_cluster(self.get_num_files() > 0)

    def remove_file(self, file, new_album=True):
        super().remove_file(file, new_album=new_album)
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
            yield from cluster.iterfiles(save)

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
            if token == '':  # nosec
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


class ClusterType(IntEnum):
    METADATA = 1
    ARTIST = 2
    ALBUM = 3


class ClusterEngine(object):
    CLUSTER_TYPE_LABELS = {
        ClusterType.METADATA: N_('Metadata Extraction'),
        ClusterType.ARTIST: N_('Artist'),
        ClusterType.ALBUM: N_('Album'),
    }

    def __init__(self, cluster_dict, cluster_type):
        # the cluster dictionary we're using
        self.cluster_dict = cluster_dict
        # keeps track of unique cluster index
        self.cluster_count = 0
        # Keeps track of the clusters we've created
        self.cluster_bins = {}
        # Index the word ids -> clusters
        self.index_id_cluster = {}
        self.cluster_type = cluster_type

    @staticmethod
    def cluster_type_label(cluster_type):
        return ClusterEngine.CLUSTER_TYPE_LABELS[cluster_type]

    def _cluster_type_label(self):
        return ClusterEngine.cluster_type_label(self.cluster_type)

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

    def cluster(self, threshold, tagger=None):
        # Keep the matches sorted in a heap
        heap = []
        num_files = self.cluster_dict.get_size()

        # 20 evenly spaced indexes of files being clustered, used as checkpoints for every 5% progress
        status_update_steps = ProgressCheckpoints(num_files, 20)

        for y in process_events_iter(range(num_files)):
            token_y = self.cluster_dict.get_token(y).lower()
            for x in range(y):
                if x != y:
                    token_x = self.cluster_dict.get_token(x).lower()
                    c = similarity(token_x, token_y)
                    if c >= threshold:
                        heappush(heap, ((1.0 - c), [x, y]))

            word, count = self.cluster_dict.get_word_and_count(y)
            if word and count > 1:
                self.cluster_bins[self.cluster_count] = [y]
                self.index_id_cluster[y] = self.cluster_count
                self.cluster_count = self.cluster_count + 1

            if tagger and status_update_steps.is_checkpoint(y):
                statusmsg = N_("Clustering - step %(step)d/3: %(cluster_type)s (%(update)d%%)")
                mparams = {
                    'step': self.cluster_type.value,
                    'cluster_type': _(self._cluster_type_label()),
                    'update': status_update_steps.progress(y),
                }
                tagger.window.set_statusbar_message(statusmsg, mparams)

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
