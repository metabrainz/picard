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

from collections import (
    defaultdict,
    deque,
    namedtuple,
)
from typing import (
    Dict,
    List,
)

from PyQt5.QtNetwork import QNetworkReply

from picard.acoustid.json_helpers import (
    parse_recording,
    recording_has_metadata,
)
from picard.webservice import WebService
from picard.webservice.api_helpers import MBAPIHelper


# Only do extra lookup for recordings without metadata, if they have at least
# this percentage of sources compared to the recording with most sources.
SOURCE_THRESHOLD_NO_METADATA = 0.25

# Load max. this number of recordings without metadata per AcoustID
MAX_NO_METADATA_RECORDINGS = 3


class Recording:
    recording: dict
    result_score: float
    sources: int

    def __init__(self, recording, result_score=1.0, sources=1):
        self.recording = recording
        self.result_score = result_score
        self.sources = sources


IncompleteRecording = namedtuple('Recording', 'mbid acoustid result_score sources')


class RecordingResolver:
    """Given an AcoustID lookup result returns a list of MB recordings.
    The recordings are either directly taken from the AcoustID result or, if the
    results return only the MBID without metadata, loaded via the MB web service.
    """

    _recording_map: Dict[str, Dict[str, Recording]]

    def __init__(self, ws: WebService, doc: dict, callback: callable) -> None:
        self._mbapi = MBAPIHelper(ws)
        self._doc = doc
        self._callback = callback
        self._recording_map = defaultdict(dict)
        self._recording_cache = dict()
        self._missing_metadata = deque()

    def resolve(self) -> None:
        results = self._doc.get('results') or []
        incomplete_counts = defaultdict(lambda: 0)
        for result in results:
            recordings = result.get('recordings') or []
            result_score = get_score(result)
            acoustid = result.get('id')
            max_sources = max_source_count_raw_recording(recordings)
            for recording in sorted(recordings, key=lambda r: r.get('sources', 1), reverse=True):
                mbid = recording.get('id')
                sources = recording.get('sources', 1)
                if recording_has_metadata(recording):
                    mb_recording = parse_recording(recording)
                    self._recording_cache[mbid] = mb_recording
                    self._recording_map[acoustid][recording['id']] = Recording(
                        recording=mb_recording,
                        result_score=result_score,
                        sources=sources,
                    )
                else:
                    if (sources / max_sources > SOURCE_THRESHOLD_NO_METADATA
                        and incomplete_counts[acoustid] < MAX_NO_METADATA_RECORDINGS):
                        self._missing_metadata.append(IncompleteRecording(
                            mbid=mbid,
                            acoustid=acoustid,
                            result_score=result_score,
                            sources=sources,
                        ))
                        incomplete_counts[acoustid] += 1

        if self._missing_metadata:
            self._load_recordings()
        else:
            self._send_results()

    def _load_recordings(self):
        if not self._missing_metadata:
            self._send_results()
            return

        mbid = self._missing_metadata[0].mbid
        if mbid in self._recording_cache:
            mb_recording = self._recording_cache[mbid]
            self._recording_request_finished(mb_recording, None, None)
        else:
            self._mbapi.get_track_by_id(
                self._missing_metadata[0].mbid,
                self._recording_request_finished,
                inc=('artists', 'release-groups', 'releases', 'media'),
            )

    def _recording_request_finished(self, mb_recording, http, error):
        recording = self._missing_metadata.popleft()
        if error:
            if error == QNetworkReply.NetworkError.ContentNotFoundError:
                # Recording does not exist, ignore and move on
                self._load_recordings()
            else:
                self._send_results(error)
            return

        mbid = mb_recording.get('id')
        recording_dict = self._recording_map[recording.acoustid]
        if mbid:
            self._recording_cache[mbid] = mb_recording
            if mbid not in recording_dict:
                recording_dict[mbid] = Recording(
                    recording=mb_recording,
                    result_score=recording.result_score,
                    sources=recording.sources,
                )
            else:
                recording_dict[mbid].sources += recording.sources
        self._load_recordings()

    def _send_results(self, error=None):
        self._callback(list(parse_recording_map(self._recording_map)), error)


def get_score(node):
    try:
        return float(node.get('score', 1.0))
    except (TypeError, ValueError):
        return 1.0


def parse_recording_map(recording_map: Dict[str, Dict[str, Recording]]):
    for acoustid, recordings in recording_map.items():
        recording_list = recordings.values()
        max_sources = max_source_count(recording_list)
        for recording in recording_list:
            parsed_recording = recording.recording
            if parsed_recording is not None:
                # Calculate a score based on result score and sources for this
                # recording relative to other recordings in this result
                score = min(recording.sources / max_sources, 1.0) * 100
                parsed_recording['score'] = score * recording.result_score
                parsed_recording['acoustid'] = acoustid
                parsed_recording['sources'] = recording.sources
            yield parsed_recording


def max_source_count(recordings: List[Recording]):
    """Given a list of recordings return the highest number of sources.
    This ignores recordings without metadata.
    """
    sources = {r.sources for r in recordings}
    sources.add(1)
    return max(sources)


def max_source_count_raw_recording(recordings: List[dict]):
    """Given a list of recordings return the highest number of sources.
    This ignores recordings without metadata.
    """
    sources = {r.get('sources', 1) for r in recordings}
    sources.add(1)
    return max(sources)
