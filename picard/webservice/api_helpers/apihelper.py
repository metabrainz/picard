# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018, 2020-2021, 2023-2024 Laurent Monin
# Copyright (C) 2018-2023, 2026 Philipp Wolfer
# Copyright (C) 2026 metaisfacil
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.

from PyQt6.QtCore import QUrl

from picard.webservice import (
    ReplyHandler,
    WebService,
)


class APIHelper:
    _base_url: QUrl | None = None

    def __init__(self, webservice: WebService, base_url: QUrl | str | None = None):
        self._webservice = webservice
        if base_url is not None:
            self.base_url = base_url

    @property
    def base_url(self) -> QUrl:
        if self._base_url is None:
            raise ValueError("base_url undefined")
        return self._base_url

    @base_url.setter
    def base_url(self, url: QUrl | str) -> None:
        if not isinstance(url, QUrl):
            url = QUrl(url)
        self._base_url = url

    @property
    def webservice(self) -> WebService:
        return self._webservice

    def url_from_path(self, path: str) -> QUrl:
        url = QUrl(self.base_url)
        url.setPath(url.path() + path)
        return url

    def get(self, path: str, handler: ReplyHandler, **kwargs):
        kwargs['url'] = self.url_from_path(path)
        kwargs['handler'] = handler
        return self._webservice.get_url(**kwargs)

    def post(self, path: str, data: str | None, handler: ReplyHandler, **kwargs):
        kwargs['url'] = self.url_from_path(path)
        kwargs['handler'] = handler
        kwargs['data'] = data
        kwargs['mblogin'] = kwargs.get('mblogin', True)
        return self._webservice.post_url(**kwargs)

    def put(self, path: str, data: str | None, handler: ReplyHandler, **kwargs):
        kwargs['url'] = self.url_from_path(path)
        kwargs['handler'] = handler
        kwargs['data'] = data
        kwargs['priority'] = kwargs.get('priority', True)
        kwargs['mblogin'] = kwargs.get('mblogin', True)
        return self._webservice.put_url(**kwargs)

    def delete(self, path: str, handler: ReplyHandler, **kwargs):
        kwargs['url'] = self.url_from_path(path)
        kwargs['handler'] = handler
        kwargs['priority'] = kwargs.get('priority', True)
        kwargs['mblogin'] = kwargs.get('mblogin', True)
        return self._webservice.delete_url(**kwargs)
