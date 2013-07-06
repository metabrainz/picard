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
from PyQt4 import QtCore
from picard import config


user_collections = {}


class Collection(QtCore.QObject):

    def __init__(self, id, name, size):
        self.id = id
        self.name = name
        self.pending = set()
        self.size = int(size)
        self.releases = set()

    def add_releases(self, ids, callback):
        ids = ids - self.pending
        if ids:
            self.pending.update(ids)
            self.tagger.xmlws.put_to_collection(self.id, list(ids),
                partial(self._add_finished, ids, callback))

    def remove_releases(self, ids, callback):
        ids = ids - self.pending
        if ids:
            self.pending.update(ids)
            self.tagger.xmlws.delete_from_collection(self.id, list(ids),
                partial(self._remove_finished, ids, callback))

    def _add_finished(self, ids, callback, document, reply, error):
        self.pending.difference_update(ids)
        if not error:
            count = len(ids)
            self.releases.update(ids)
            self.size += count
            callback()

            self.tagger.window.set_statusbar_message(
                ungettext('Added %i release to collection "%s"',
                    'Added %i releases to collection "%s"', count) % (count, self.name))

    def _remove_finished(self, ids, callback, document, reply, error):
        self.pending.difference_update(ids)
        if not error:
            count = len(ids)
            self.releases.difference_update(ids)
            self.size -= count
            callback()

            self.tagger.window.set_statusbar_message(
                ungettext('Removed %i release from collection "%s"',
                    'Removed %i releases from collection "%s"', count) % (count, self.name))


def load_user_collections(callback=None):
    tagger = QtCore.QObject.tagger

    def request_finished(document, reply, error):
        if error:
            tagger.window.set_statusbar_message(_("Error loading collections: %s"), unicode(reply.errorString()))
            return
        collection_list = document.metadata[0].collection_list[0]
        if "collection" in collection_list.children:
            new_collections = set()

            for node in collection_list.collection:
                new_collections.add(node.id)
                collection = user_collections.get(node.id)
                if collection is None:
                    user_collections[node.id] = Collection(node.id, node.name[0].text, node.release_list[0].count)
                else:
                    collection.name = node.name[0].text
                    collection.size = int(node.release_list[0].count)

            for id in set(user_collections.iterkeys()) - new_collections:
                del user_collections[id]

        if callback:
            callback()

    if config.setting["username"] and config.setting["password"]:
        tagger.xmlws.get_collection_list(partial(request_finished))
