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

from PyQt4 import QtCore

from picard.mbxml import release_to_metadata, media_formats_from_node
from picard.util import partial


class CollectedRelease(object):

    def __init__(self, id, collection, data=None, album=None):
        self.id = id
        if data:
            self.data = data
        elif album:
            self.data = {}
            m = album.metadata
            for k in ("album", "albumartist", "date", "releasecountry", "barcode"):
                self.data[k] = m[k]
            self.data["media"] = album.format_str
            self.data["totaltracks"] = album.tracks_str
        self.collection = collection
        self.pending = False
        self.item = None

    def column(self, column):
        if column == "title":
            return self.data["album"]
        else:
            return self.data.get(column, "")


class Collection(QtCore.QObject):

    def __init__(self, id, name, size):
        QtCore.QObject.__init__(self)
        self.id = id
        self.name = name
        self.pending = set()
        self.item = None
        self.releases = {}
        self.load(int(size))

    def load(self, size):
        offset = 0
        while size > offset:
            self.tagger.xmlws.get_collection(self.id, self._collection_request_finished, offset=offset)
            offset += 100

    def _collection_request_finished(self, document, reply, error):
        if error:
            self.log.error("%r", unicode(reply.errorString()))
            return
        release_list = document.metadata[0].collection[0].release_list[0]
        if release_list.count != "0":
            releases = []
            for node in release_list.release:
                m = {}
                release_to_metadata(node, m, self.config)
                m["media"] = media_formats_from_node(node.medium_list[0])
                m["totaltracks"] = " + ".join([med.track_list[0].count for med in node.medium_list[0].medium])
                release = CollectedRelease(node.id, self, data=m)
                self.releases[release.id] = release
                releases.append(release)
            self.item.add_releases(releases)

    def add_releases(self, release_map):
        ids = set(release_map.keys()) - self.pending
        if ids:
            self.pending.update(ids)
            releases = [release_map[id] for id in ids]
            for release in releases:
                release.collection = self
                self.releases[release.id] = release
            self.item.add_releases(releases)
            self.set_releases_pending(releases, True)
            self.tagger.xmlws.put_to_collection(self.id, ids, partial(self._add_finished, releases))

    def remove_releases(self, release_ids):
        ids = release_ids - self.pending
        if ids:
            try:
                releases = [self.releases[id] for id in ids]
            except KeyError:
                return
            self.pending.update(ids)
            self.set_releases_pending(releases, True)
            self.tagger.xmlws.delete_from_collection(self.id, ids, partial(self._remove_finished, releases))

    def set_releases_pending(self, releases, pending):
        for release in releases:
            if pending:
                self.pending.add(release.id)
            else:
                self.pending.remove(release.id)
            release.pending = pending
            release.item.update()

    def _add_finished(self, releases, document, reply, error):
        self.set_releases_pending(releases, False)
        if error:
            self.log.error("%r", unicode(reply.errorString()))
            self.item.remove_releases([self.releases.pop(r.id) for r in releases])

    def _remove_finished(self, releases, document, reply, error):
        self.set_releases_pending(releases, False)
        if not error:
            for r in releases:
                del self.releases[r.id]
            self.item.remove_releases(releases)
        else:
            self.log.error("%r", unicode(reply.errorString()))

    def column(self, column):
        if column == "title":
            size = len(self.releases)
            end = "releases" if size != 1 else "release"
            return "%s (%d %s)" % (self.name, size, end)
        return ""


class CollectionList(QtCore.QObject):

    def __init__(self, view):
        self.view = view
        self.load()

    def load(self):
        self.collections = []
        self.loaded = False
        if self.config.setting["username"] and self.config.setting["password"]:
            self.tagger.xmlws.get_collection_list(self._request_finished)
        else:
            self.view.set_message(N_("You must configure your MusicBrainz account information."))

    def _request_finished(self, document, reply, error):
        if error:
            self.tagger.window.set_statusbar_message(N_("Could not load user collections: %s"), unicode(reply.errorString()))
            self.view.set_message(N_("Error loading collections."))
            return
        collection_list = document.metadata[0].collection_list[0]
        if "collection" in collection_list.children:
            self.view.clear()
            for node in collection_list.collection:
                collection = Collection(node.id, node.name[0].text, node.release_list[0].count)
                self.collections.append(collection)
                self.view.add_collection(collection)
            self.loaded = True
        else:
            self.view.set_message(N_("You have no collections."))
