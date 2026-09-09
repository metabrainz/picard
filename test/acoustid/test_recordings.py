# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2019-2020, 2023, 2026 Philipp Wolfer
# Copyright (C) 2020 Ray Bouchard
# Copyright (C) 2020-2022, 2025 Laurent Monin
# Copyright (C) 2021 Vladislav Karbovskii
# Copyright (C) 2021, 2025 Bob Swift
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


from test.picardtestcase import PicardTestCase

from picard.acoustid.recordings import (
    Recording,
    max_source_count,
    parse_recording_map,
)


class MaxSourceCountTest(PicardTestCase):
    def test_max_source_count(self):
        recordings = (
            Recording({}, sources=5),
            Recording({}, sources=13),
            Recording({}, sources=12),
        )
        self.assertEqual(13, max_source_count(recordings))

    def test_max_source_count_no_recordings(self):
        self.assertEqual(1, max_source_count([]))

    def test_max_source_count_smaller_1(self):
        recordings = (Recording({}, sources=0),)
        self.assertEqual(1, max_source_count(recordings))


class ParseRecordingMapTest(PicardTestCase):
    def test_parse_recording_map(self):
        recordings = {
            "cb127606-8e3d-4dcf-9902-69c7a9b59bc9": {
                "d12e0535-3b2f-4987-8b03-63d85ef57fdd": Recording(
                    {
                        "id": "d12e0535-3b2f-4987-8b03-63d85ef57fdd",
                    }
                ),
                "e8a313ee-b723-4b48-9395-6c8e026fc9e0": Recording(
                    {"id": "e8a313ee-b723-4b48-9395-6c8e026fc9e0"},
                    sources=4,
                    result_score=0.5,
                ),
            }
        }
        expected = [
            {
                "id": "d12e0535-3b2f-4987-8b03-63d85ef57fdd",
                "acoustid": "cb127606-8e3d-4dcf-9902-69c7a9b59bc9",
                "score": 25,
                "sources": 1,
            },
            {
                "id": "e8a313ee-b723-4b48-9395-6c8e026fc9e0",
                "acoustid": "cb127606-8e3d-4dcf-9902-69c7a9b59bc9",
                "score": 50,
                "sources": 4,
            },
        ]
        self.assertEqual(expected, list(parse_recording_map(recordings)))
