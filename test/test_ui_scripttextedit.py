# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 prsdx
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

from PyQt6.QtGui import (
    QTextCursor,
    QTextDocument,
)

from test.picardtestcase import PicardTestCase

from picard import config
from picard.tags.docs import display_tag_tooltip

from picard.ui.widgets.scripttextedit import ScriptTextEdit


class ScriptTextEditTooltipTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        config.setting['enable_tagger_scripts'] = False
        config.setting['tagger_scripts'] = []
        config.persist['script_editor_wordwrap'] = False
        config.persist['script_editor_tooltips'] = True
        self.editor = ScriptTextEdit(None)
        self.addCleanup(self.editor.deleteLater)

    def test_tooltip_at_closing_percent(self):
        doc = QTextDocument()
        text = "%artist% %title%"
        doc.setPlainText(text)
        self.editor.setDocument(doc)

        expected_artist = display_tag_tooltip("artist")
        self.assertIsNotNone(expected_artist)

        # Positions 0 through 7 (closing '%') should all resolve to artist tooltip
        for pos in range(8):
            cursor = QTextCursor(doc)
            cursor.setPosition(pos)
            tooltip = self.editor.get_tooltip_at_cursor(cursor)
            self.assertEqual(tooltip, expected_artist)

        expected_title = display_tag_tooltip("title")
        self.assertIsNotNone(expected_title)
        # Position 8 is a space
        cursor = QTextCursor(doc)
        cursor.setPosition(8)
        self.assertIsNone(self.editor.get_tooltip_at_cursor(cursor))

        # Positions 9 through 15 (closing '%') should all resolve to title tooltip
        for pos in range(9, 16):
            cursor = QTextCursor(doc)
            cursor.setPosition(pos)
            tooltip = self.editor.get_tooltip_at_cursor(cursor)
            self.assertEqual(tooltip, expected_title)

    def test_tooltip_lone_symbols(self):
        doc = QTextDocument()
        text = "hello % world $ foo"
        doc.setPlainText(text)
        self.editor.setDocument(doc)

        # Ensure lone '%' and lone '$' do not produce any tooltip
        for pos in range(len(text) + 1):
            cursor = QTextCursor(doc)
            cursor.setPosition(pos)
            tooltip = self.editor.get_tooltip_at_cursor(cursor)
            self.assertIsNone(tooltip)
