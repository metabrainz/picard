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
from picard.mbxml import artist_credit_from_node, media_formats_from_node
from picard.album import Album
from picard.webservice import XmlNode
from picard.util import partial


class CollectionList(QtCore.QObject):

    def __init__(self, view):
        QtCore.QObject.__init__(self)
        self.view = view
        self.collections = {}
        self.releases = {}
        self.loading = False
        self.loaded = False

    def release_from_obj(self, obj):
        self.releases.setdefault(obj.id, CollectionRelease(obj))
        return self.releases[obj.id]

    def _parse_collection_list(self, document):
        collection_list = document.metadata[0].collection_list[0]
        collections = collection_list.collection

        for collection in collections:
            id = collection.id
            name = collection.name[0].text
            count = int(collection.release_list[0].count)
            self.collections[id] = Collection(id, name, count, self)

    def _collection_list_request_finished(self, document, reply, error):
        if error:
            self.log.error("%r", unicode(reply.errorString()))
            self.view.window.show_collections_action.setChecked(False)
            self.view.window.collections_panel.hide()
        else:
            self._parse_collection_list(document)
            self.view.add_collections(self.collections)
            self.loading = False
            self.loaded = True

    def load(self):
        self.collections = {}
        self.releases = {}
        self.loading = True
        self.loaded = False
        self.tagger.xmlws.get_collection_list(self._collection_list_request_finished)


class Collection(QtCore.QObject):

    def __init__(self, id, name, count, list):
        self.id = id
        self.name = name
        self.count = count
        self.release_ids = set()
        self.pending_adds = set()
        self.pending_removes = set()
        self.collection_list = list
        self.widget = None
        self.release_widgets = {}
        self.load()

    def _add_release_ids(self, ids):
        self.release_ids.update(ids)
        self.count += len(ids)

    def _remove_release_ids(self, ids):
        self.release_ids.difference_update(ids)
        self.count -= len(ids)

    def add_releases(self, releases):
        ids = releases.keys()
        self._add_release_ids(ids)
        self.pending_adds.update(ids)
        not_pending = {}
        for id, release in releases.iteritems():
            if id not in self.pending_removes:
                not_pending[id] = release
            self.collection_list.releases.setdefault(id, release)
        self.collection_list.view.add_releases(not_pending, self, pending=True)
        self.tagger.xmlws.put_to_collection(self.id, ids, partial(self._add_request_finished, ids))

    def remove_releases(self, ids):
        self._remove_release_ids(ids)
        self.pending_removes.update(ids)
        self.color_pending_releases(ids, True)
        self.tagger.xmlws.delete_from_collection(self.id, ids, partial(self._remove_request_finished, ids))

    def load(self):
        self.tagger.xmlws.get_collection(self.id, self._collection_request_finished)

    def _add_request_finished(self, ids, document, reply, error):
        self.pending_adds.difference_update(ids)
        if error:
            self.log.error("%r", unicode(reply.errorString()))
            self._remove_release_ids(ids)
            self.collection_list.view.remove_releases(ids, self)
        else:
            self.widget.update_text()
            self.color_pending_releases(ids, False)

    def _remove_request_finished(self, ids, document, reply, error):
        self.pending_removes.difference_update(ids)
        if error:
            self.log.error("%r", unicode(reply.errorString()))
            self._add_release_ids(ids)
            self.color_pending_releases(ids, False)
        else:
            ids = set(ids) - self.pending_adds
            self.collection_list.view.remove_releases(ids, self)

    def color_pending_releases(self, ids, pending):
        if not pending:
            ids = set(ids) - self.pending_adds - self.pending_removes
        for id in ids:
            self.release_widgets[id].color_pending(pending)

    def _collection_request_finished(self, document, reply, error):
        if error:
            self.log.error("%r", unicode(reply.errorString()))
        else:
            self._parse_collection(document)
            self.widget.update_text()

    def _parse_collection(self, document):
        collection = document.metadata[0].collection[0]
        self.name = collection.name[0].text
        release_list = collection.release_list[0]
        releases = {}
        if release_list.count != "0":
            release_nodes = release_list.release
            for node in release_nodes:
                releases[node.id] = self.collection_list.release_from_obj(node)
                self.release_ids.add(node.id)
        self.collection_list.releases.update(releases)
        self.collection_list.view.add_releases(releases, self)


class CollectionRelease(QtCore.QObject):

    def __init__(self, obj):
        self.id = obj.id
        self.reference_count = 0
        if isinstance(obj, XmlNode):
            self._metadata_from_node(obj)
        elif isinstance(obj, Album):
            self._metadata_from_album(obj)

    def _metadata_from_node(self, node):
        title = node.title[0].text
        artist = artist_credit_from_node(node.artist_credit[0], self.config)[0]
        format = media_formats_from_node(node.medium_list[0])
        tracks = " + ".join([m.track_list[0].count for m in node.medium_list[0].medium])
        date = node.date[0].text if "date" in node.children else ""
        country = node.country[0].text if "country" in node.children else ""
        barcode = node.barcode[0].text if "barcode" in node.children else ""
        self.columns = (title, artist, format, tracks, date, country, barcode)

    def _metadata_from_album(self, album):
        m = album.metadata
        title = m["album"]
        artist = m["albumartist"]
        format = album.format_str
        tracks = album.tracks_str
        date = m["date"]
        country = m["releasecountry"]
        barcode = m["barcode"]
        self.columns = (title, artist, format, tracks, date, country, barcode)
