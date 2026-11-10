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

import io
import re

from test.picardtestcase import PicardTestCase

from picard.cli.engine.render import render_result
from picard.cli.engine.result import (
    EngineItemResult,
    EngineResult,
)
from picard.cli.output import CliOutput


def _output():
    buf = io.StringIO()
    return CliOutput(stdout=buf, stderr=buf, color=False), buf


class RenderResultTest(PicardTestCase):
    def test_render_items_with_handles(self):
        out, buf = _output()
        result = EngineResult(
            items=[EngineItemResult('a1', 'matched', {'title': 'OK Computer'})],
            mints=['a1'],
        )
        render_result(result, out)
        text = buf.getvalue()
        self.assertIn('a1', text)
        self.assertIn('matched', text)
        self.assertIn('OK Computer', text)
        self.assertIn('minted', text)

    def test_render_shows_the_path_after_the_handle(self):
        out, buf = _output()
        result = EngineResult(items=[EngineItemResult('t7', 'listed', {'title': 'Airbag'}, path='a1.d2.t3')])
        render_result(result, out)
        self.assertIn('t7  a1.d2.t3  listed', buf.getvalue())

    def test_render_without_a_path_is_unchanged(self):
        out, buf = _output()
        render_result(EngineResult(items=[EngineItemResult('a1', 'listed')]), out)
        self.assertEqual('a1  listed\n', buf.getvalue())

    @staticmethod
    def _lookup_result(count, applied=0):
        candidates = [
            {'handle': f'm{n}', 'title': f'Release {n}', 'similarity': 1 / n, 'applied': n - 1 == applied}
            for n in range(1, count + 1)
        ]
        return EngineResult(
            items=[EngineItemResult('c1', 'matched', {'candidates': candidates})],
            mints=['a1', *(f'm{n}' for n in range(1, count + 1))],
        )

    def test_render_shows_only_the_best_candidates_and_says_how_to_see_the_rest(self):
        out, buf = _output()
        render_result(self._lookup_result(25), out)
        candidates = self._candidate_lines(buf)
        self.assertEqual(10, len(candidates))
        self.assertIn('m10 ', candidates[-1])
        self.assertIn('15 more: ls c1.m*', buf.getvalue())

    @staticmethod
    def _candidate_lines(buf):
        """The lines listing a candidate (indented, unlike the minted and 'more' lines)."""
        return [line for line in buf.getvalue().splitlines() if re.match(r'^ {4}[* ] m\d+ ', line)]

    def test_render_shows_all_candidates_when_there_are_few(self):
        out, buf = _output()
        render_result(self._lookup_result(10), out)
        self.assertIn('m10 ', buf.getvalue())
        self.assertNotIn('more:', buf.getvalue())

    def test_render_always_shows_the_applied_candidate(self):
        out, buf = _output()
        render_result(self._lookup_result(25, applied=19), out)  # m20 was applied
        candidates = self._candidate_lines(buf)
        self.assertEqual(11, len(candidates))
        self.assertIn('* m20', candidates[-1])
        self.assertIn('14 more', buf.getvalue())

    def test_render_shortens_the_list_of_minted_handles(self):
        out, buf = _output()
        render_result(self._lookup_result(30), out)
        minted = [line for line in buf.getvalue().splitlines() if line.startswith('minted:')]
        self.assertEqual(1, len(minted))
        self.assertIn('a1, m1, m2', minted[0])
        self.assertIn('(+19 more)', minted[0])
        self.assertNotIn('m30', minted[0])

    def test_render_indents_items_by_depth(self):
        out, buf = _output()
        result = EngineResult(
            items=[
                EngineItemResult('a1', 'album', {'title': 'OK Computer', 'depth': 0}),
                EngineItemResult('t1', 'track', {'title': 'Airbag', 'depth': 1}),
                EngineItemResult('f1', 'file', {'filename': 'airbag.flac', 'depth': 2}),
            ],
        )
        render_result(result, out)
        lines = buf.getvalue().splitlines()
        album_line = next(line for line in lines if 'a1' in line)
        track_line = next(line for line in lines if 't1' in line)
        file_line = next(line for line in lines if 'f1' in line)
        # Deeper items are indented further than shallower ones.
        self.assertEqual(0, len(album_line) - len(album_line.lstrip()))
        self.assertLess(
            len(album_line) - len(album_line.lstrip()),
            len(track_line) - len(track_line.lstrip()),
        )
        self.assertLess(
            len(track_line) - len(track_line.lstrip()),
            len(file_line) - len(file_line.lstrip()),
        )
        # depth is structural, not surfaced as a data field.
        self.assertNotIn('depth=', buf.getvalue())

    def test_render_item_shows_type_mbid(self):
        out, buf = _output()
        result = EngineResult(
            items=[
                EngineItemResult(
                    'a1',
                    'listed',
                    {'entity_type': 'release', 'mbid': 'rel-123', 'title': 'OK Computer'},
                )
            ],
        )
        render_result(result, out)
        self.assertIn('release:rel-123', buf.getvalue())

    def test_render_failure(self):
        out, buf = _output()
        render_result(EngineResult.failure('boom', unresolved=['a9']), out)
        text = buf.getvalue()
        self.assertIn('boom', text)
        self.assertIn('a9', text)

    def test_render_candidates_marks_applied(self):
        out, buf = _output()
        result = EngineResult(
            items=[
                EngineItemResult(
                    'c1',
                    'matched',
                    {
                        'candidates': [
                            {
                                'handle': 'm1',
                                'entity_type': 'release',
                                'mbid': 'rel-abc',
                                'title': 'Best',
                                'similarity': 0.9,
                                'applied': True,
                            },
                            {'handle': 'm2', 'title': 'Other', 'similarity': 0.5},
                        ]
                    },
                )
            ],
        )
        render_result(result, out)
        text = buf.getvalue()
        self.assertIn('m1', text)
        self.assertIn('Best', text)
        self.assertIn('release:rel-abc', text)
        self.assertIn('* ', text)  # applied marker

    def test_render_empty(self):
        out, buf = _output()
        render_result(EngineResult(), out)
        self.assertIn('(nothing)', buf.getvalue())
