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

    def test_render_writes_the_minted_handles_as_ranges(self):
        out, buf = _output()
        render_result(self._lookup_result(30), out)
        minted = [line for line in buf.getvalue().splitlines() if line.startswith('minted:')]
        self.assertEqual(['minted: a1, m1-30'], minted)

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


def _color_output():
    buf = io.StringIO()
    return CliOutput(stdout=buf, stderr=buf, color=True), buf


class RenderColorTest(PicardTestCase):
    GREEN = CliOutput.GREEN
    YELLOW = CliOutput.YELLOW
    RED = CliOutput.RED

    def _render(self, item):
        out, buf = _color_output()
        render_result(EngineResult(items=[item]), out)
        return buf.getvalue()

    def test_status_is_colored_by_meaning(self):
        for status, code in (
            ('matched', self.GREEN),
            ('pending', self.YELLOW),
            ('load_failed', self.RED),
            ('listed', CliOutput.DIM),
        ):
            with self.subTest(status=status):
                self.assertIn(f'{code}{status}{CliOutput.RESET}', self._render(EngineItemResult('a1', status)))

    def test_error_value_is_red(self):
        text = self._render(EngineItemResult('a1', 'error', {'error': 'boom'}))
        self.assertIn(f'{self.RED}error=boom{CliOutput.RESET}', text)

    def test_tag_diffs_are_colored(self):
        rows = [
            {'tag': 'a', 'orig': 'x', 'new': 'y', 'status': 'changed'},
            {'tag': 'b', 'orig': '', 'new': 'n', 'status': 'added'},
            {'tag': 'c', 'orig': 'o', 'new': '', 'status': 'removed'},
        ]
        text = self._render(EngineItemResult('a1', 'listed', {'tags': rows}))
        self.assertIn(f'{CliOutput.DIM}x{CliOutput.RESET}', text)
        self.assertIn(f'{self.GREEN}y{CliOutput.RESET}', text)
        self.assertIn(f'{self.GREEN}+ n{CliOutput.RESET}', text)
        self.assertIn(f'{self.RED}- o{CliOutput.RESET}', text)

    def test_candidate_score_is_graded_and_applied_mark_is_green(self):
        cands = [
            {'handle': 'm1', 'title': 'A', 'similarity': 0.95, 'applied': True},
            {'handle': 'm2', 'title': 'B', 'similarity': 0.75},
            {'handle': 'm3', 'title': 'C', 'similarity': 0.2},
        ]
        text = self._render(EngineItemResult('c1', 'matched', {'candidates': cands}))
        self.assertIn(f'{self.GREEN}0.95{CliOutput.RESET}', text)
        self.assertIn(f'{self.YELLOW}0.75{CliOutput.RESET}', text)
        self.assertIn(f'{self.RED}0.2{CliOutput.RESET}', text)
        self.assertIn(f'{self.GREEN}{CliOutput.BOLD}*{CliOutput.RESET}', text)

    def test_current_version_mark_is_green(self):
        versions = [{'handle': 'v1', 'title': 'A', 'current': True}]
        text = self._render(EngineItemResult('a1', 'listed', {'versions': versions}))
        self.assertIn(f'{self.GREEN}{CliOutput.BOLD}*{CliOutput.RESET}', text)

    def test_title_and_artist_values_are_bold(self):
        text = self._render(EngineItemResult('f1', 'added', {'title': 'Gypsy', 'artist': 'Uriah Heep'}))
        self.assertIn(f'title={CliOutput.BOLD}Gypsy{CliOutput.RESET}', text)
        self.assertIn(f'artist={CliOutput.BOLD}Uriah Heep{CliOutput.RESET}', text)

    def test_candidate_and_version_titles_are_bold(self):
        cands = [{'handle': 'm1', 'title': 'Release A'}]
        versions = [{'handle': 'v1', 'title': 'Release B'}]
        text = self._render(EngineItemResult('c1', 'matched', {'candidates': cands, 'versions': versions}))
        self.assertIn(f'{CliOutput.BOLD}Release A{CliOutput.RESET}', text)
        self.assertIn(f'{CliOutput.BOLD}Release B{CliOutput.RESET}', text)

    def test_mb_references_are_colored_in_summaries_candidates_and_messages(self):
        mbid = '0bad6e23-1234-4abc-8def-0123456789ab'
        colored = f'{CliOutput.CYAN}release{CliOutput.RESET}:{CliOutput.DIM}{mbid}{CliOutput.RESET}'
        item = EngineItemResult(
            'a1',
            'loaded',
            {
                'entity_type': 'release',
                'mbid': mbid,
                'candidates': [dict(handle='m1', entity_type='release', mbid=mbid)],
            },
        )
        out, buf = _color_output()
        render_result(EngineResult(items=[item], message=f'loaded release:{mbid}'), out)
        self.assertEqual(3, buf.getvalue().count(colored))

    def test_bare_mbid_in_an_error_is_dimmed(self):
        mbid = '0bad6e23-1234-4abc-8def-0123456789ab'
        out, buf = _color_output()
        render_result(EngineResult.failure(f'not found: {mbid}'), out)
        self.assertIn(f'{CliOutput.DIM}{mbid}{CliOutput.RESET}', buf.getvalue())


class CompactMintedTest(PicardTestCase):
    def _minted(self, mints):
        out, buf = _output()
        render_result(EngineResult(mints=mints), out)
        return buf.getvalue().strip()

    def test_consecutive_handles_are_a_range(self):
        mints = ['f1', 'f2', 'f3', 'f4', 'f5', 'c1', 'c2', 'a1', 'a3']
        self.assertEqual('minted: f1-5, c1-2, a1, a3', self._minted(mints))

    def test_only_handles_that_follow_each_other_are_joined(self):
        self.assertEqual('minted: f1-2, f4, f6-7', self._minted(['f1', 'f2', 'f4', 'f6', 'f7']))
        self.assertEqual('minted: f2, f1', self._minted(['f2', 'f1']))

    def test_the_prefix_must_be_the_same(self):
        self.assertEqual('minted: a1, c2, a3', self._minted(['a1', 'c2', 'a3']))

    def test_a_lookup_listing_stays_short(self):
        mints = ['a1', *(f'm{n}' for n in range(1, 51))]
        self.assertEqual('minted: a1, m1-50', self._minted(mints))

    def test_many_terms_are_cut_and_counted(self):
        mints = [f'f{n}' for n in range(1, 60, 2)]  # 30 handles, none consecutive
        text = self._minted(mints)
        self.assertTrue(text.startswith('minted: f1, f3, f5'))
        self.assertTrue(text.endswith('… (+18 more)'), text)

    def test_a_handle_without_a_number_is_kept(self):
        self.assertEqual('minted: x, f1-2', self._minted(['x', 'f1', 'f2']))
