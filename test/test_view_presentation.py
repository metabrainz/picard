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


from unittest.mock import (
    MagicMock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.view_presentation import (
    ViewPresentation,
    set_view_presentation_sink,
    view_presentation,
)


class ViewPresentationTest(PicardTestCase):
    def test_accessor_is_stable(self):
        self.assertIs(view_presentation(), view_presentation())
        self.assertIsInstance(view_presentation(), ViewPresentation)

    def test_bring_to_front_noop_without_sink(self):
        facade = ViewPresentation()
        self.assertFalse(facade.has_sink)
        # Must not raise when headless (no sink).
        facade.bring_to_front()

    def test_bring_to_front_forwards_to_sink(self):
        facade = ViewPresentation()
        sink = MagicMock()
        facade.set_sink(sink)
        self.assertTrue(facade.has_sink)
        facade.bring_to_front()
        sink.bring_tagger_front.assert_called_once_with()

    def test_set_sink_none_reverts_to_noop(self):
        self.addCleanup(set_view_presentation_sink, None)
        sink = MagicMock()
        set_view_presentation_sink(sink)
        self.assertTrue(view_presentation().has_sink)
        set_view_presentation_sink(None)
        self.assertFalse(view_presentation().has_sink)

    def test_remove_forwards_to_sink_with_selection(self):
        facade = ViewPresentation()
        sink = MagicMock()
        facade.set_sink(sink)
        objs = [object()]
        facade.remove(objs)
        sink.remove_with_selection.assert_called_once_with(objs)

    def test_remove_works_with_a_plain_protocol_sink(self):
        # Regression: a MagicMock sink accepts any attribute, which hid a real
        # AttributeError (the Tagger sink has no `panel`). Use a plain object
        # implementing exactly the sink protocol so a missing member fails.
        removed = []

        class PlainSink:
            def bring_tagger_front(self):
                pass

            def remove_with_selection(self, objects):
                removed.extend(objects)

        facade = ViewPresentation()
        facade.set_sink(PlainSink())
        objs = [object(), object()]
        facade.remove(objs)
        self.assertEqual(objs, removed)

    def test_tagger_satisfies_the_sink_protocol(self):
        # The real GUI sink must provide every protocol member.
        from picard.tagger import Tagger
        from picard.view_presentation import ViewPresentationSink

        for member in ('bring_tagger_front', 'remove_with_selection'):
            self.assertTrue(callable(getattr(Tagger, member, None)), member)
        self.assertTrue(hasattr(ViewPresentationSink, 'remove_with_selection'))

    def test_remove_falls_back_to_workspace_without_sink(self):
        facade = ViewPresentation()
        self.assertFalse(facade.has_sink)
        objs = [object()]
        with patch('picard.workspace.workspace') as mock_workspace:
            facade.remove(objs)
            mock_workspace.return_value.remove.assert_called_once_with(objs)
