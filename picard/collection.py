# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2013 Michael Wiencek
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

from functools import partial

from PyQt5 import QtCore

from picard import (
    config,
    log,
)

user_collections = {}


class Collection(QtCore.QObject):
    COLLECTION_ADD = 1
    COLLECTION_REMOVE = 2

    def __init__(self, collection_id, name, size):
        self.id = collection_id
        self.name = name
        self.pending = set()
        self.size = int(size)
        self.releases = set()
        mb_api = self.tagger.mb_api
        self.api_action = {
            self.COLLECTION_ADD: mb_api.put_to_collection,
            self.COLLECTION_REMOVE: mb_api.delete_from_collection,
        }

    def __repr__(self):
        return '<Collection %s (%s)>' % (self.name, self.id)

    def _modify(self, kind, ids, callback):
        ids -= self.pending
        if ids:
            self.pending |= ids
            when_done = partial(self._finished, kind, ids, callback)
            self.api_action[kind](self.id, list(ids), when_done)

    def add_releases(self, ids, callback):
        self._modify(self.COLLECTION_ADD, ids, callback)

    def remove_releases(self, ids, callback):
        self._modify(self.COLLECTION_REMOVE, ids, callback)

    def _finished(self, kind, ids, callback, document, reply, error):
        self.pending -= ids
        statusbar = self.tagger.window.set_statusbar_message
        if not error:
            count = len(ids)
            if kind == self.COLLECTION_ADD:
                self.releases |= ids
                self.size += count
                status_msg = ngettext(
                    'Added %(count)i release to collection "%(name)s"',
                    'Added %(count)i releases to collection "%(name)s"',
                    count)
                debug_msg = 'Added %(count)i releases to collection "%(name)s"'
            else:
                self.releases -= ids
                self.size -= count
                status_msg = ngettext(
                    'Removed %(count)i release from collection "%(name)s"',
                    'Removed %(count)i releases from collection "%(name)s"',
                    count)
                debug_msg = 'Removed %(count)i releases from collection "%(name)s"'
            callback()
            mparms = {'count': count, 'name': self.name}
            log.debug(debug_msg % mparms)
            statusbar(status_msg, mparms, translate=None, echo=None)
        else:
            statusbar(
                N_("Error while modifying collections: %(error)s"),
                {'error': reply.errorString()},
                echo=log.error
            )


def get_user_collection(collection_id, name, size, refresh=False):
    collection = user_collections.get(collection_id)
    if collection is None:
        collection = user_collections[collection_id] = Collection(collection_id, name, size)
    elif refresh:
        collection.name = name
        collection.size = size
    return collection


def load_user_collections(callback=None):
    tagger = QtCore.QObject.tagger

    def request_finished(document, reply, error):
        if error:
            tagger.window.set_statusbar_message(
                N_("Error loading collections: %(error)s"),
                {'error': reply.errorString()},
                echo=log.error
            )
            return
        if document and "collections" in document:
            collection_list = document['collections']
            new_collections = set()

            for node in collection_list:
                if node["entity-type"] != "release":
                    continue
                col_id = node['id']
                col_name = node['name']
                col_size = node['release-count']
                new_collections.add(col_id)
                collection = get_user_collection(col_id, col_name, col_size, refresh=True)

            # remove collections which aren't returned by the web service anymore
            old_collections = set(user_collections) - new_collections
            for collection_id in old_collections:
                del user_collections[collection_id]

            log.debug("User collections: %r", [(k, v.name) for k, v in user_collections.items()])
        if callback:
            callback()

    if tagger.webservice.oauth_manager.is_authorized():
        tagger.mb_api.get_collection_list(partial(request_finished))
    else:
        user_collections.clear()


def add_release_to_user_collections(release_node):
    """Add album to collections"""
    # Check for empy collection list
    if "collections" in release_node:
        release_id = release_node['id']
        username = config.persist["oauth_username"].lower()
        for node in release_node['collections']:
            if node['editor'].lower() == username:
                col_id = node['id']
                col_name = node['name']
                col_size = node['release-count']
                collection = get_user_collection(col_id, col_name, col_size)
                collection.releases.add(release_id)
                log.debug("Adding release %r to %r", release_id, collection)
