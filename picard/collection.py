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
from picard.util import partial


class CollectionList(QtCore.QObject):

    def __init__(self, view):
        QtCore.QObject.__init__(self)
        self.view = view
        self.collections = {}
        self.loaded = False

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
            self.loaded = True

    def load(self):
        self.collections = {}
        self.loaded = False
        self.tagger.xmlws.get_collection_list(self._collection_list_request_finished)


class Collection(QtCore.QObject):

    def __init__(self, id, name, count, list):
        self.id = id
        self.name = name
        self.count = count
        self.releases = set()
        self.pending_adds = set()
        self.pending_removes = set()
        self.collection_list = list
        self.widget = None
        self.release_widgets = {}
        self.load()

    def _add_releases(self, ids):
        self.releases.update(ids)
        self.count += len(ids)

    def _remove_releases(self, ids):
        self.releases.difference_update(ids)
        self.count -= len(ids)

    def add_releases(self, releases):
        ids = releases.keys()
        self._add_releases(ids)
        self.pending_adds.update(ids)
        self.collection_list.view.add_releases(releases, self, pending=True)
        self.tagger.xmlws.put_to_collection(self.id, ids, partial(self._add_request_finished, ids))

    def remove_releases(self, ids):
        self._remove_releases(ids)
        self.pending_removes.update(ids)
        self.color_pending_releases(ids, True)
        self.tagger.xmlws.delete_from_collection(self.id, ids, partial(self._remove_request_finished, ids))

    def load(self):
        self.tagger.xmlws.get_collection(self.id, self._collection_request_finished)

    def _add_request_finished(self, ids, document, reply, error):
        self.pending_adds.difference_update(ids)
        if error:
            self.log.error("%r", unicode(reply.errorString()))
            self._remove_releases(ids)
            self.collection_list.view.remove_releases(ids, self)
        else:
            self.widget.update_text()
            self.color_pending_releases(ids, False)

    def _remove_request_finished(self, ids, document, reply, error):
        self.pending_removes.difference_update(ids)
        if error:
            self.log.error("%r", unicode(reply.errorString()))
            self._add_releases(ids)
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
                title = node.title[0].text
                date = node.date[0].text if "date" in node.children else ""
                country = node.country[0].text if "country" in node.children else ""
                barcode = node.barcode[0].text if "barcode" in node.children else ""
                release = (title, date, country, barcode)
                releases[node.id] = release
                self.releases.add(node.id)
        self.collection_list.view.add_releases(releases, self)
