# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2023 Philipp Wolfer
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

from picard.acoustid.json_helpers import (
    max_source_count,
    parse_recording,
)
from picard.webservice import WebService
from picard.webservice.api_helpers import MBAPIHelper


class RecordingResolver:

    def __init__(self, ws: WebService) -> None:
        self.mbapi = MBAPIHelper(ws)

    def resolve(self, doc: dict, callback: callable) -> None:
        recording_map = {}
        results = doc.get('results') or []
        for result in results:
            recordings = result.get('recordings') or []
            max_sources = max_source_count(recordings)
            result_score = get_score(result)
            for recording in recordings:
                parsed_recording = parse_recording(recording)
                if parsed_recording is not None:
                    # Calculate a score based on result score and sources for this
                    # recording relative to other recordings in this result
                    score = min(recording.get('sources', 1) / max_sources, 1.0) * 100
                    parsed_recording['score'] = score * result_score
                    parsed_recording['acoustid'] = result.get('id')
                    recording_map[parsed_recording['id']] = parsed_recording

        # TODO: Load recording details for recordings without metadata
        callback(recording_map.values())


def get_score(node):
    try:
        return float(node.get('score', 1.0))
    except (TypeError, ValueError):
        return 1.0
