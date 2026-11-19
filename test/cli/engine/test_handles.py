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

import gc

from test.picardtestcase import PicardTestCase

from picard.cli.engine.handles import HandleRegistry


class _Entity:
    """A weak-referenceable stand-in entity carrying its handle prefix."""

    def __init__(self, kind):
        self.kind = kind


def _classifier(entity):
    return getattr(entity, 'kind', None)


class HandleRegistryTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.reg = HandleRegistry(_classifier)

    def test_mint_assigns_prefixed_ordinal(self):
        f = _Entity('f')
        self.assertEqual('f1', self.reg.handle_for(f))

    def test_same_entity_returns_same_handle(self):
        f = _Entity('f')
        h1 = self.reg.handle_for(f)
        h2 = self.reg.handle_for(f)
        self.assertEqual(h1, h2)

    def test_counters_are_per_prefix(self):
        f1, f2 = _Entity('f'), _Entity('f')
        a1 = _Entity('a')
        self.assertEqual('f1', self.reg.handle_for(f1))
        self.assertEqual('f2', self.reg.handle_for(f2))
        self.assertEqual('a1', self.reg.handle_for(a1))

    def test_resolve_roundtrip(self):
        a = _Entity('a')
        h = self.reg.handle_for(a)
        self.assertIs(self.reg.resolve(h), a)
        self.assertIsNotNone(self.reg.resolve(h))

    def test_resolve_unknown_is_none(self):
        self.assertIsNone(self.reg.resolve('a99'))

    def test_ordinals_are_not_reused_after_drop(self):
        # Keep strong refs so they are not collected; "removal" here is only
        # about ordinal allocation, which must keep climbing.
        entities = [_Entity('a') for _ in range(3)]
        handles = [self.reg.handle_for(e) for e in entities]
        self.assertEqual(['a1', 'a2', 'a3'], handles)
        # Drop the middle entity's strong ref and force collection.
        dropped_handle = handles[1]
        del entities[1]
        gc.collect()
        self.assertIsNone(self.reg.resolve(dropped_handle))  # expired
        # A newly minted entity must NOT reuse a2.
        new = _Entity('a')
        self.assertEqual('a4', self.reg.handle_for(new))

    def test_handle_expires_when_entity_collected(self):
        a = _Entity('a')
        h = self.reg.handle_for(a)
        self.assertIsNotNone(self.reg.resolve(h))
        del a
        gc.collect()
        self.assertIsNone(self.reg.resolve(h))

    def test_unclassifiable_entity_raises(self):
        with self.assertRaises(ValueError):
            self.reg.handle_for(_Entity(None))


class MintMarkTest(PicardTestCase):
    def test_minted_since_a_mark_are_the_handles_minted_after_it(self):
        reg = HandleRegistry(_classifier)
        first = _Entity('f')
        reg.handle_for(first)
        mark = reg.mint_mark()
        second, third = _Entity('f'), _Entity('c')
        reg.handle_for(second)
        reg.handle_for(first)  # not minted again
        reg.handle_for(third)
        self.assertEqual(['f2', 'c1'], reg.minted_since(mark))
        self.assertEqual([], reg.minted_since(reg.mint_mark()))


class RemintTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.reg = HandleRegistry(_classifier)

    def test_a_kind_with_no_entity_left_starts_again_from_one(self):
        files = [_Entity('f') for _ in range(3)]
        self.assertEqual(['f1', 'f2', 'f3'], [self.reg.handle_for(f) for f in files])
        del files
        gc.collect()
        self.assertEqual(0, self.reg.remint('f'))
        self.assertEqual('f1', self.reg.handle_for(_kept := _Entity('f')))
        self.assertIs(_kept, self.reg.resolve('f1'))

    def test_a_kind_with_live_entities_is_left_as_it_is(self):
        kept = _Entity('f')
        self.reg.handle_for(_Entity('f'))
        self.reg.handle_for(kept)
        self.assertEqual(1, self.reg.remint('f'))
        self.assertEqual('f2', self.reg.handle_for(kept))
        self.assertEqual('f3', self.reg.handle_for(_kept := _Entity('f')))
        self.assertIs(_kept, self.reg.resolve('f3'))

    def test_only_the_kind_asked_is_reminted(self):
        cluster = _Entity('c')
        self.reg.handle_for(cluster)
        self.reg.handle_for(_Entity('f'))
        gc.collect()
        self.assertEqual(0, self.reg.remint('f'))
        self.assertEqual('c2', self.reg.handle_for(_kept := _Entity('c')))
        self.assertEqual('c1', self.reg.handle_for(cluster))

    def test_a_kind_never_minted_is_reminted_to_nothing(self):
        self.assertEqual(0, self.reg.remint('a'))
        self.assertEqual('a1', self.reg.handle_for(_kept := _Entity('a')))
