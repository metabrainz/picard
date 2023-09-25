# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2008, 2011 Lukáš Lalinský
# Copyright (C) 2008 Hendrik van Antwerpen
# Copyright (C) 2008 Will
# Copyright (C) 2010-2011, 2014, 2018-2022 Philipp Wolfer
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


from collections import (
    Counter,
    defaultdict,
)
from operator import attrgetter
import re

from PyQt5 import QtCore

from picard.config import get_config
from picard.file import File
from picard.metadata import (
    Metadata,
    SimMatchRelease,
)
from picard.util import (
    album_artist_from_path,
    find_best_match,
    format_time,
)
from picard.util.imagelist import (
    add_metadata_images,
    remove_metadata_images,
    update_metadata_images,
)

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

    def update(self, signal=True):
        pass

    @property
    def can_show_coverart(self):
        return True


class Cluster(FileList):

    # Weights for different elements when comparing a cluster to a release
    comparison_weights = {
        'album': 17,
        'albumartist': 6,
        'totalalbumtracks': 5,
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
                self.related_album.metadata['album'] + '/' + self.metadata['album']
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
        self.update(signal=False)
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
        self.update(signal=False)
        self.item.remove_file(file)
        if self.can_show_coverart:
            file.metadata_images_changed.disconnect(self.update_metadata_images)
            remove_metadata_images(self, [file])
        if new_album:
            self._update_related_album(removed_files=[file])
        self.tagger.window.set_processing(False)
        if not self.special and self.get_num_files() == 0:
            self.tagger.remove_cluster(self)

    def update(self, signal=True):
        self.metadata['~totalalbumtracks'] = self.metadata['totaltracks'] = len(self.files)
        if signal and self.item:
            self.item.update()

    def get_num_files(self):
        return len(self.files)

    def can_save(self):
        """Return if this object can be saved."""
        return bool(self.files)

    def can_remove(self):
        """Return if this object can be removed."""
        return not self.special

    def can_edit_tags(self):
        """Return if this object supports tag editing."""
        return True

    def can_analyze(self):
        """Return if this object can be fingerprinted."""
        return any(_file.can_analyze() for _file in self.files)

    def can_autotag(self):
        return True

    def can_refresh(self):
        return False

    def can_browser_lookup(self):
        return not self.special

    def can_view_info(self):
        return bool(self.files)

    def can_submit(self):
        return not self.special and bool(self.files)

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
        best_match = find_best_match(candidates(), no_match)
        return best_match.result.release

    def lookup_metadata(self):
        """Try to identify the cluster using the existing metadata."""
        if self.lookup_task:
            return
        self.tagger.window.set_statusbar_message(
            N_("Looking up the metadata for cluster %(album)s…"),
            {'album': self.metadata['album']}
        )
        config = get_config()
        self.lookup_task = self.tagger.mb_api.find_releases(self._lookup_finished,
            artist=self.metadata['albumartist'],
            release=self.metadata['album'],
            tracks=str(len(self.files)),
            limit=config.setting['query_limit'])

    def clear_lookup_task(self):
        if self.lookup_task:
            self.tagger.webservice.remove_task(self.lookup_task)
            self.lookup_task = None

    @staticmethod
    def cluster(files):
        """Group the provided files into clusters, based on album tag in metadata.

        Args:
            files: List of File objects.

        Yields:
            FileCluster objects
        """
        config = get_config()
        various_artists = config.setting['va_name']

        cluster_list = defaultdict(FileCluster)
        for file in files:
            artist = file.metadata['albumartist'] or file.metadata['artist']
            album = file.metadata['album']

            # Improve clustering from directory structure if no existing tags
            # Only used for grouping and to provide cluster title / artist - not added to file tags.
            album, artist = album_artist_from_path(file.filename, album, artist)

            token = tokenize(album)
            if token:
                cluster_list[token].add(album, artist or various_artists, file)

        yield from cluster_list.values()


class UnclusteredFiles(Cluster):

    """Special cluster for 'Unmatched Files' which have not been clustered."""

    def __init__(self):
        super().__init__(_("Unclustered Files"), special=True)

    def add_files(self, files, new_album=True):
        super().add_files(files, new_album=new_album)
        self.tagger.window.enable_cluster(bool(self.files))

    def remove_file(self, file, new_album=True):
        super().remove_file(file, new_album=new_album)
        self.tagger.window.enable_cluster(bool(self.files))

    def lookup_metadata(self):
        self.tagger.autotag(self.files)

    def can_edit_tags(self):
        return False

    def can_autotag(self):
        return bool(self.files)

    def can_view_info(self):
        return False

    def can_remove(self):
        return bool(self.files)

    @property
    def can_show_coverart(self):
        return False


class ClusterList(list, Item):

    """A list of clusters."""

    def __init__(self):
        super().__init__()

    def __hash__(self):
        return id(self)

    def __bool__(self):
        # An existing Item object should not be considered False, even if it
        # is based on a list.
        return True

    def iterfiles(self, save=False):
        for cluster in self:
            yield from cluster.iterfiles(save)

    def can_save(self):
        return len(self) > 0

    def can_analyze(self):
        return any(cluster.can_analyze() for cluster in self)

    def can_autotag(self):
        return len(self) > 0

    def can_browser_lookup(self):
        return False

    def lookup_metadata(self):
        for cluster in self:
            cluster.lookup_metadata()


class FileCluster:
    def __init__(self):
        self._files = []
        self._artist_counts = Counter()
        self._artists = defaultdict(Counter)
        self._titles = Counter()

    def add(self, album, artist, file):
        self._files.append(file)
        token = tokenize(artist)
        self._artist_counts[token] += 1
        self._artists[token][artist] += 1
        self._titles[album] += 1

    @property
    def files(self):
        yield from (file for file in self._files if file.state != File.REMOVED)

    @property
    def artist(self):
        tokenized_artist = self._artist_counts.most_common(1)[0][0]
        candidates = self._artists[tokenized_artist]
        return candidates.most_common(1)[0][0]

    @property
    def title(self):
        # Find the most common title
        return self._titles.most_common(1)[0][0]


_re_non_alphanum = re.compile(r'\W', re.UNICODE)
_re_spaces = re.compile(r'\s', re.UNICODE)


def tokenize(word):
    word = word.lower()
    token = _re_non_alphanum.sub('', word)
    return token if token else _re_spaces.sub('', word)
