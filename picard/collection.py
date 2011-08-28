# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2011 Michael Wiencek
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

from uuid import UUID
from math import ceil

from PyQt4 import QtCore

from picard.mbxml import release_to_metadata
from picard.metadata import Metadata
from picard.util import partial


class Release:

    def __init__(self, id, metadata):
        self.id = id
        self._uuid_int = UUID(id).int
        self.metadata = metadata

    def __hash__(self):
        return self._uuid_int

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
        return hash(self) != hash(other)


class CollectedRelease:

    def __init__(self, release, collection):
        self.release = release
        self.collection = collection
        self.item = None

    def update(self):
        pass

    def column(self, column):
        m = self.release.metadata
        if column == "title":
            return m["album"]
        else:
            return m[column]


class Collection(QtCore.QObject):

    def __init__(self, id, name, count):
        QtCore.QObject.__init__(self)
        self.id = id
        self.name = name
        self.count = int(count)
        self.releases = set()
        self.pending = set()
        self.item = None
        self.collected_releases = {}
        self.load()

    def load(self):
        offset = 0
        self._requests = int(ceil(self.count / 100.0))
        while self.count > offset:
            self.tagger.xmlws.get_collection(self.id, self._collection_request_finished, offset=offset)
            offset += 100

    def _collection_request_finished(self, document, reply, error):
        if error:
            self.log.error("%r", unicode(reply.errorString()))
            return
        release_list = document.metadata[0].collection[0].release_list[0]
        if release_list.count != "0":
            for node in release_list.release:
                m = Metadata()
                release_to_metadata(node, m)
                release = Release(node.id, m)
                self.releases.add(release)
            self.tagger.releases_added_to_collection.emit(self.releases, self, False)
        if not self._requests:
            self.update()
            del self._requests
        else:
            self._requests -= 1

    def add_releases(self, releases):
        releases.difference_update(self.pending)
        if releases:
            self.count += len(releases)
            self.releases.update(releases)
            self.pending.update(releases)
            self.tagger.releases_added_to_collection.emit(releases, self, True)
            ids = [release.id for release in releases]
            func = partial(self._add_finished, releases)
            self.tagger.xmlws.put_to_collection(self.id, ids, func)

    def remove_releases(self, releases):
        releases.difference_update(self.pending)
        if releases:
            self.releases.difference_update(releases)
            self.pending.update(releases)
            self.tagger.releases_updated.emit(releases, True)
            ids = [release.id for release in releases]
            func = partial(self._remove_finished, releases)
            self.tagger.xmlws.delete_from_collection(self.id, ids, func)

    def _add_finished(self, releases, document, reply, error):
        self.pending.difference_update(releases)
        if not error:
            self.tagger.releases_updated.emit(releases)
        else:
            self.log.error("%r", unicode(reply.errorString()))
            self.releases.difference_update(releases)
            self.tagger.releases_removed_from_collection.emit(releases, self)

    def _remove_finished(self, releases, document, reply, error):
        self.pending.difference_update(releases)
        if not error:
            self.count -= len(releases)
            self.tagger.releases_removed_from_collection.emit(releases, self)
        else:
            self.log.error("%r", unicode(reply.errorString()))
            self.releases.update(releases)

    def update(self, pending=False):
        self.tagger.collection_updated.emit(self, pending)

    def column(self, column):
        if column == "title":
            end = "releases" if self.count != 1 else "release"
            return "%s (%d %s)" % (self.name, self.count, end)
        return ""
