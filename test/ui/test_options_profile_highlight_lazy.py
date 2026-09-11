# Picard, the next-generation MusicBrainz tagger
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

from unittest.mock import MagicMock

from test.picardtestcase import PicardTestCase

from picard.ui.options.dialog import OptionsDialog


class TestSwitchPageHighlightsLazyPages(PicardTestCase):
    """PICARD-3436: options pages are instantiated/loaded lazily on first visit.

    The initial profile-highlight pass runs once from ``showEvent`` and only
    covers pages already loaded at that moment. A page displayed later via
    ``switch_page`` must therefore have its per-widget highlights applied when
    it is first shown, otherwise overridden settings appear highlighted only on
    the page that happened to be active when the dialog opened.

    These tests exercise ``OptionsDialog.switch_page`` as an unbound method
    against a lightweight stub so the full dialog widget does not need to be
    constructed.
    """

    def _make_dialog_stub(self, loaded=True):
        dialog = MagicMock()
        page = MagicMock()
        page.NAME = 'metadata'
        page.loaded = loaded
        item = MagicMock()
        dialog.ui.pages_tree.selectedItems.return_value = [item]
        dialog.item_to_page = {item: MagicMock(NAME='metadata')}
        dialog._load_page.return_value = page
        # Use the real method under test rather than the mock's auto-attr.
        dialog._highlight_page_options = MagicMock()
        return dialog, page

    def test_switch_page_highlights_loaded_page(self):
        dialog, page = self._make_dialog_stub(loaded=True)
        OptionsDialog.switch_page(dialog)
        dialog._highlight_page_options.assert_called_once_with(page)

    def test_switch_page_does_not_highlight_unloaded_page(self):
        # A page that failed to load must not be highlighted (its widgets are
        # not populated); highlighting is deferred until it is actually loaded.
        dialog, page = self._make_dialog_stub(loaded=False)
        OptionsDialog.switch_page(dialog)
        dialog._highlight_page_options.assert_not_called()

    def test_switch_page_no_selection_is_noop(self):
        dialog = MagicMock()
        dialog.ui.pages_tree.selectedItems.return_value = []
        dialog._highlight_page_options = MagicMock()
        OptionsDialog.switch_page(dialog)
        dialog._highlight_page_options.assert_not_called()
        dialog._load_page.assert_not_called()
