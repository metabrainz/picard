#
# Copyright (C) 2026 Laurent Monin
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

import json

from test.picardtestcase import (
    PicardTestCase,
    load_test_json,
)

from picard.cli.engine.candidates import Candidate
from picard.matching import SimMatchRelease


class CandidateTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.release = load_test_json('release.json')

    def _candidate(self, similarity=0.9, applied=False):
        return Candidate(SimMatchRelease(similarity=similarity, release=self.release), applied=applied)

    def test_release_id_and_similarity(self):
        c = self._candidate(similarity=0.87)
        self.assertEqual(self.release['id'], c.release_id)
        self.assertEqual(0.87, c.similarity)

    def test_describe_projection(self):
        c = self._candidate(similarity=0.1234, applied=True)
        data = c.describe()
        self.assertEqual(self.release['id'], data['mbid'])
        self.assertIn('title', data)
        self.assertEqual(0.1234, data['similarity'])
        self.assertTrue(data['applied'])
        # Entity type is always present (MB vocabulary); a lookup candidate is
        # a release, so the reference is release:<mbid>.
        self.assertEqual('release', data['entity_type'])
        # Must be JSON-serializable (MCP / cross-process).
        json.dumps(data)

    def test_describe_includes_entity_type_even_with_none_release(self):
        c = Candidate(SimMatchRelease(similarity=-1, release=None))
        data = c.describe()
        self.assertEqual('release', data['entity_type'])

    def test_describe_handles_none_release(self):
        c = Candidate(SimMatchRelease(similarity=-1, release=None))
        data = c.describe()
        self.assertFalse(data.get('applied'))
        json.dumps(data)
