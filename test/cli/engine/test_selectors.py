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

from test.picardtestcase import PicardTestCase

from picard.cli.engine.selectors import (
    Segment,
    SelectorError,
    parse_selector,
    resolve_nodes,
    resolve_selector,
)


class ParseSelectorTest(PicardTestCase):
    def test_single_handle(self):
        terms = parse_selector('a1')
        self.assertEqual(1, len(terms))
        self.assertEqual(('a', 'ordinal', 1), (terms[0].prefix, terms[0].kind, terms[0].value))

    def test_type_wildcard(self):
        (term,) = parse_selector('c*')
        self.assertEqual(('c', 'wildcard', None), (term.prefix, term.kind, term.value))

    def test_universal_wildcard(self):
        (term,) = parse_selector('*')
        self.assertEqual(('', 'wildcard', None), (term.prefix, term.kind, term.value))

    def test_comma_union_with_spaces(self):
        terms = parse_selector('a1, c2 , f3')
        self.assertEqual(['a1', 'c2', 'f3'], [t.raw for t in terms])

    def test_token_list_is_a_union(self):
        # A command line splits "a1, c2 f3" into separate tokens.
        for tokens in (['a1,', 'c2', 'f3'], ['a1', 'c2', 'f3'], ['a1,c2', 'f3'], ['a1', ',c2,', 'f3']):
            with self.subTest(tokens=tokens):
                terms = parse_selector(tokens)
                self.assertEqual(['a1', 'c2', 'f3'], [t.raw for t in terms])

    def test_token_list_rejects_empty(self):
        with self.assertRaises(SelectorError):
            parse_selector([])

    def test_rejects_exclusion(self):
        with self.assertRaises(SelectorError):
            parse_selector('!a2')

    def test_range(self):
        (term,) = parse_selector('f1-12')
        self.assertEqual(('f', 'range', (1, 12)), (term.prefix, term.kind, term.value))

    def test_range_in_a_path(self):
        (term,) = parse_selector('c1.f2-5')
        self.assertEqual(Segment('f', 'range', (2, 5)), term.path[0])

    def test_rejects_malformed_reversed_and_oversized_ranges(self):
        for text in ('a1-', 'a-3', 'a1-b', 'a1-c3', 'a1--3', 'a0-3', 'a3-1', 'a1-99999', 'u1-3', '*-3'):
            with self.subTest(text=text), self.assertRaises(SelectorError):
                parse_selector(text)

    def test_one_element_range_is_a_range(self):
        (term,) = parse_selector('a2-2')
        self.assertEqual((2, 2), term.value)

    def test_rejects_unknown_prefix(self):
        with self.assertRaises(SelectorError):
            parse_selector('z1')

    def test_rejects_bare_ordinal(self):
        # Bare-ordinal sticky prefix is full-grammar, not the subset.
        with self.assertRaises(SelectorError):
            parse_selector('a1,2')

    def test_rejects_empty_term(self):
        with self.assertRaises(SelectorError):
            parse_selector('a1,,c2')

    def test_rejects_prefix_without_ordinal(self):
        with self.assertRaises(SelectorError):
            parse_selector('a')


class _FakeWorkspace:
    """Minimal enumerator source keyed by prefix."""

    def __init__(self, **by_prefix):
        self._by_prefix = {k: list(v) for k, v in by_prefix.items()}

    def enumerate_prefix(self, prefix):
        return list(self._by_prefix.get(prefix, ()))


def _registry(mapping):
    """A handle->entity resolver from a dict; missing handles resolve to None."""
    return lambda handle: mapping.get(handle)


class ResolveSelectorTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.a1, self.a2 = object(), object()
        self.c1 = object()
        self.f1, self.f2 = object(), object()
        self.handles = {'a1': self.a1, 'a2': self.a2, 'c1': self.c1, 'f1': self.f1, 'f2': self.f2}
        self.wks = _FakeWorkspace(a=[self.a1, self.a2], c=[self.c1], f=[self.f1, self.f2])

    def _resolve(self, text):
        return resolve_selector(text, _registry(self.handles), self.wks.enumerate_prefix)

    def test_single_handle_hit(self):
        entities, unresolved = self._resolve('a1')
        self.assertEqual([self.a1], entities)
        self.assertEqual([], unresolved)

    def test_single_handle_miss(self):
        entities, unresolved = self._resolve('a9')
        self.assertEqual([], entities)
        self.assertEqual(['a9'], unresolved)

    def test_range_gives_the_live_entities_in_order(self):
        entities, unresolved = self._resolve('f1-2,a1-2')
        self.assertEqual([self.f1, self.f2, self.a1, self.a2], entities)
        self.assertEqual([], unresolved)

    def test_range_skips_what_is_not_there(self):
        entities, unresolved = self._resolve('a1-9')
        self.assertEqual([self.a1, self.a2], entities)
        self.assertEqual([], unresolved)

    def test_range_that_matches_nothing_is_unresolved(self):
        entities, unresolved = self._resolve('a5-9')
        self.assertEqual([], entities)
        self.assertEqual(['a5-9'], unresolved)

    def test_range_overlapping_another_term_is_deduplicated(self):
        entities, _ = self._resolve('a2,a1-2')
        self.assertEqual([self.a2, self.a1], entities)

    def test_type_wildcard(self):
        entities, unresolved = self._resolve('a*')
        self.assertEqual([self.a1, self.a2], entities)
        self.assertEqual([], unresolved)

    def test_universal_wildcard_is_top_level(self):
        # f* ∪ c* ∪ a*, first-appearance order (f, then c, then a).
        entities, unresolved = self._resolve('*')
        self.assertEqual([self.f1, self.f2, self.c1, self.a1, self.a2], entities)
        self.assertEqual([], unresolved)

    def test_comma_union(self):
        entities, unresolved = self._resolve('a1,c1')
        self.assertEqual([self.a1, self.c1], entities)
        self.assertEqual([], unresolved)

    def test_union_dedupes_preserving_first_order(self):
        # a1 appears both explicitly and via a*; it must appear once, first.
        entities, _ = self._resolve('a1,a*')
        self.assertEqual([self.a1, self.a2], entities)

    def test_mixed_hit_and_miss(self):
        entities, unresolved = self._resolve('a1,a9,c1')
        self.assertEqual([self.a1, self.c1], entities)
        self.assertEqual(['a9'], unresolved)

    def test_resolved_empty_vs_unresolved(self):
        # Valid wildcard over an empty namespace: resolved-empty, NOT unresolved.
        wks = _FakeWorkspace(a=[])
        entities, unresolved = resolve_selector('a*', _registry({}), wks.enumerate_prefix)
        self.assertEqual([], entities)
        self.assertEqual([], unresolved)


class ParsePathTest(PicardTestCase):
    def test_path_segments(self):
        (term,) = parse_selector('a1.d2.t3')
        self.assertEqual(('a', 'ordinal', 1), (term.prefix, term.kind, term.value))
        self.assertEqual((Segment('d', 'ordinal', 2), Segment('t', 'ordinal', 3)), term.path)
        self.assertEqual('a1.d2.t3', term.raw)

    def test_wildcard_segments(self):
        (term,) = parse_selector('a*.t*')
        self.assertEqual('wildcard', term.kind)
        self.assertEqual((Segment('t', 'wildcard'),), term.path)

    def test_plain_term_has_no_path(self):
        (term,) = parse_selector('a1')
        self.assertEqual((), term.path)

    def test_singleton_segment_takes_no_number(self):
        (term,) = parse_selector('a1.u')
        self.assertEqual((Segment('u', 'single'),), term.path)

    def test_singleton_can_start_a_path(self):
        (term,) = parse_selector('u.f*')
        self.assertEqual(('u', 'single'), (term.prefix, term.kind))
        self.assertEqual((Segment('f', 'wildcard'),), term.path)

    def test_paths_in_a_union(self):
        terms = parse_selector('a1.t1, c2.f*')
        self.assertEqual(['a1.t1', 'c2.f*'], [t.raw for t in terms])

    def test_path_from_command_line_tokens(self):
        terms = parse_selector(['a1.t1,', 'c2.f*'])
        self.assertEqual(['a1.t1', 'c2.f*'], [t.raw for t in terms])

    def test_rejects_malformed_paths(self):
        for text in ('a1.', '.t1', 'a1..t1', 'a1.t', 'a1.x1', 'a.t1', 'a1.t1x', '*.f*', 'u1', 'u*', 'a1.u2'):
            with self.subTest(text=text):
                with self.assertRaises(SelectorError):
                    parse_selector(text)


class _FakeNavigator:
    """A tiny tree: albums hold tracks; ``d1`` is a view that finishes to its tracks."""

    def __init__(self):
        self.tracks = [object(), object(), object()]
        self.disc = object()
        self.steps = []

    def step(self, node, segment):
        self.steps.append((node, segment))
        if segment.prefix == 'u':
            return [self.disc]
        if segment.prefix == 'm':
            raise SelectorError("no such thing here")
        if segment.kind == 'wildcard':
            return list(self.tracks)
        if segment.kind == 'ordinal':
            return self.tracks[segment.value - 1 : segment.value]
        return []

    def finish(self, node):
        return list(self.tracks) if node is self.disc else [node]

    def segments(self, node):
        return ['t*']


class ResolvePathTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.a1 = object()
        self.nav = _FakeNavigator()
        self.handles = {'a1': self.a1}
        self.wks = _FakeWorkspace(a=[self.a1])

    def _resolve(self, text, navigator=True):
        return resolve_selector(
            text,
            _registry(self.handles),
            self.wks.enumerate_prefix,
            self.nav if navigator else None,
        )

    def test_ordinal_child(self):
        entities, unresolved = self._resolve('a1.t2')
        self.assertEqual([self.nav.tracks[1]], entities)
        self.assertEqual([], unresolved)
        self.assertEqual([(self.a1, Segment('t', 'ordinal', 2))], self.nav.steps)

    def test_wildcard_child(self):
        entities, _ = self._resolve('a1.t*')
        self.assertEqual(self.nav.tracks, entities)

    def test_wildcard_head_steps_from_every_match(self):
        self.wks = _FakeWorkspace(a=[self.a1, object()])
        self._resolve('a*.t1')
        self.assertEqual(2, len(self.nav.steps))

    def test_missing_ordinal_child_is_unresolved(self):
        entities, unresolved = self._resolve('a1.t9')
        self.assertEqual([], entities)
        self.assertEqual(['a1.t9'], unresolved)

    def test_missing_head_is_unresolved_without_walking(self):
        entities, unresolved = self._resolve('a9.t1')
        self.assertEqual([], entities)
        self.assertEqual(['a9.t1'], unresolved)
        self.assertEqual([], self.nav.steps)

    def test_wildcard_matching_nothing_is_not_unresolved(self):
        self.nav.tracks = []
        entities, unresolved = self._resolve('a1.t*')
        self.assertEqual([], entities)
        self.assertEqual([], unresolved)

    def test_singleton_head_starts_from_the_root(self):
        entities, _ = self._resolve('u.t*')
        self.assertEqual((None, Segment('u', 'single')), self.nav.steps[0])
        self.assertEqual(self.nav.tracks, entities)

    def test_finish_expands_views(self):
        entities, _ = self._resolve('a1.u')
        self.assertEqual(self.nav.tracks, entities)

    def test_results_are_deduplicated_across_terms(self):
        entities, _ = self._resolve('a1.t1,a1.t*')
        self.assertEqual(self.nav.tracks, entities)

    def test_paths_mix_with_plain_terms(self):
        entities, unresolved = self._resolve('a1,a1.t1,a9')
        self.assertEqual([self.a1, self.nav.tracks[0]], entities)
        self.assertEqual(['a9'], unresolved)

    def test_navigator_error_names_the_term(self):
        with self.assertRaises(SelectorError) as ctx:
            self._resolve('a1.m1')
        self.assertIn('a1.m1', str(ctx.exception))
        self.assertIn('no such thing here', str(ctx.exception))

    def test_path_without_navigator_is_an_error(self):
        for text in ('a1.t1', 'u'):
            with self.subTest(text=text):
                with self.assertRaises(SelectorError):
                    self._resolve(text, navigator=False)


class ResolveNodesTest(PicardTestCase):
    """resolve_nodes() stops short of finish(), so a view is not expanded."""

    def setUp(self):
        super().setUp()
        self.a1 = object()
        self.nav = _FakeNavigator()
        self.handles = {'a1': self.a1}
        self.wks = _FakeWorkspace(a=[self.a1])

    def _nodes(self, text):
        return resolve_nodes(text, _registry(self.handles), self.wks.enumerate_prefix, self.nav)

    def test_plain_handle(self):
        self.assertEqual([self.a1], self._nodes('a1'))

    def test_path_ends_at_the_view_not_its_members(self):
        self.assertEqual([self.nav.disc], self._nodes('a1.u'))

    def test_unresolved_term_gives_nothing(self):
        self.assertEqual([], self._nodes('a9'))
        self.assertEqual([], self._nodes('a1.t9'))

    def test_wildcard_head(self):
        self.assertEqual([self.a1], self._nodes('a*'))

    def test_only_a_single_term_is_accepted(self):
        with self.assertRaises(SelectorError):
            self._nodes('a1,a1.t1')

    def test_navigator_errors_are_reported(self):
        with self.assertRaises(SelectorError):
            self._nodes('a1.m1')
