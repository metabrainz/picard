# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013 Michael Wiencek
# Copyright (C) 2014 Lukáš Lalinský
# Copyright (C) 2014, 2017 Sophist-UK
# Copyright (C) 2014, 2017-2021, 2023-2024 Laurent Monin
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2019, 2021-2022, 2024 Philipp Wolfer
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


from collections.abc import Callable
from functools import partial
from typing import Any

from PyQt6.QtNetwork import QNetworkReply

from picard import (
    log,
    tagger_instance,
)
from picard.config import get_config
from picard.i18n import (
    N_,
    ngettext,
)
from picard.webservice import ReplyHandler
from picard.webservice.api_helpers import MBAPIHelper


user_collections: dict[str, 'Collection'] = {}


class Collection:
    def __init__(self, collection_id: str, mb_api: MBAPIHelper) -> None:
        self.tagger = tagger_instance()
        self.id = collection_id
        self.name = ''
        self.size = 0
        self.pending_releases: set[str] = set()
        self.releases: set[str] = set()
        self._mb_api = mb_api

    @property
    def size(self) -> int:
        return self._size

    @size.setter
    def size(self, value: int | str) -> None:
        self._size = int(value)

    def __repr__(self) -> str:
        return '<Collection %s (%s)>' % (self.name, self.id)

    def _modify(
        self,
        api_method: Callable[[str, list[str], ReplyHandler], None],
        success_handler: Callable[[set[str], Callable], None],
        releases: set[str],
        callback: Callable,
    ) -> None:
        releases -= self.pending_releases
        if releases:
            self.pending_releases |= releases
            when_done = partial(self._finished, success_handler, releases, callback)
            api_method(self.id, list(releases), when_done)

    def add_releases(self, releases: set[str], callback: Callable) -> None:
        api_method = self._mb_api.put_to_collection
        self._modify(api_method, self._success_add, set(releases), callback)

    def remove_releases(self, releases: set[str], callback: Callable) -> None:
        api_method = self._mb_api.delete_from_collection
        self._modify(api_method, self._success_remove, set(releases), callback)

    def _finished(
        self,
        success_handler: Callable[[set[str], Callable], None],
        releases: set[str],
        callback: Callable,
        document: Any,
        reply: QNetworkReply,
        error: QNetworkReply.NetworkError | Exception | None,
    ) -> None:
        self.pending_releases -= releases
        if not error:
            success_handler(releases, callback)
        else:
            self._error(reply)

    def _error(self, reply: QNetworkReply) -> None:
        self.tagger.window.set_statusbar_message(
            N_("Error while modifying collections: %(error)s"),
            {'error': reply.errorString()},
            echo=log.error,
        )

    def _success_add(self, releases: set[str], callback: Callable) -> None:
        count = len(releases)
        self.releases |= releases
        self.size += count
        status_msg = ngettext(
            'Added %(count)i release to collection "%(name)s"',
            'Added %(count)i releases to collection "%(name)s"',
            count,
        )
        debug_msg = 'Added %(count)i release(s) to collection "%(name)s"'
        self._success(count, callback, status_msg, debug_msg)

    def _success_remove(self, releases: set[str], callback: Callable) -> None:
        count = len(releases)
        self.releases -= releases
        self.size -= count
        status_msg = ngettext(
            'Removed %(count)i release from collection "%(name)s"',
            'Removed %(count)i releases from collection "%(name)s"',
            count,
        )
        debug_msg = 'Removed %(count)i release(s) from collection "%(name)s"'
        self._success(count, callback, status_msg, debug_msg)

    def _success(self, count: int, callback: Callable, status_msg: str, debug_msg: str) -> None:
        callback()
        mparms = {
            'count': count,
            'name': self.name,
        }
        log.debug(debug_msg % mparms)
        self.tagger.window.set_statusbar_message(
            status_msg,
            mparms,
            translate=None,
            echo=None,
        )


def get_user_collection(collection_id: str) -> Collection:
    collection = user_collections.get(collection_id)
    if collection is None:
        tagger = tagger_instance()
        collection = user_collections[collection_id] = Collection(collection_id, tagger.mb_api)
    return collection


def load_user_collections(callback: Callable | None = None) -> None:
    tagger = tagger_instance()

    def request_finished(document: dict[str, Any] | None, reply: Any, error: Any) -> None:
        if error:
            tagger.window.set_statusbar_message(
                N_("Error loading collections: %(error)s"),
                {'error': reply.errorString()},
                echo=log.error,
            )
            return
        if document and 'collections' in document:
            collection_list = document['collections']
            new_collections: set[str] = set()

            for node in collection_list:
                if node['entity-type'] != 'release':
                    continue
                col_id = node['id']
                new_collections.add(col_id)
                collection = get_user_collection(col_id)
                collection.name = node['name']
                collection.size = node['release-count']

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


def add_release_to_user_collections(release_node: dict[str, Any]) -> None:
    """Add album to collections"""
    # Check for empty collection list
    if 'collections' in release_node:
        release_id = release_node['id']
        config = get_config()
        username = config.persist['oauth_username'].lower()
        for node in release_node['collections']:
            if node['editor'].lower() == username:
                collection = get_user_collection(node['id'])
                collection.name = node['name']
                collection.size = node['release-count']

                collection.releases.add(release_id)
                log.debug("Adding release %r to %r", release_id, collection)
