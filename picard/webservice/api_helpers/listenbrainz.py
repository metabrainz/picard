# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Philipp Wolfer
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
from dataclasses import (
    asdict,
    dataclass,
)
import enum
import json
from typing import Any

from picard.const import LISTENBRAINZ_API_URL
from picard.webservice import (
    ReplyHandler,
    WebService,
)

from .apihelper import APIHelper


class ListenType(enum.Enum):
    SINGLE = 'single'
    PLAYING_NOW = 'playing_now'
    IMPORT = 'import'


@dataclass
class TrackMetadata:
    artist_name: str
    track_name: str
    release_name: str | None = None
    additional_info: dict[str, str | int | list[str]] | None = None


@dataclass
class ListenPayload:
    track_metadata: TrackMetadata
    listened_at: int | None = None


@dataclass
class ListenSubmission:
    listen_type: ListenType
    payload: list[ListenPayload]

    def as_json(self) -> str:
        data = asdict(self, dict_factory=_dict_factory_omit_none)
        return json.dumps(data, default=_json_serializer, sort_keys=True)


class ListenBrainzAPIHelper(APIHelper):
    def __init__(self, webservice: WebService):
        super().__init__(webservice, base_url=LISTENBRAINZ_API_URL)

    def submit_listen(self, user_token: str, submission: ListenSubmission, handler: ReplyHandler):
        headers = {
            'Authorization': f'Token {user_token}',
        }
        self.post('submit-listens', submission.as_json(), handler, mblogin=False, headers=headers)


def _json_serializer(obj: Any):
    if isinstance(obj, ListenType):
        return obj.value
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')


def _dict_factory_omit_none(items: list[tuple[str, Any]]) -> dict[str, Any]:
    return dict((k, v) for k, v in items if v is not None)
