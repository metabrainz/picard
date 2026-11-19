# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Nabhag Sorathiya
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

from PyQt6 import (
    QtCore,
    QtGui,
)

from test.picardtestcase import PicardTestCase

from picard.ui.widgets.wrappingcheckbox import WrappingCheckBox


class WrappingCheckBoxTest(PicardTestCase):
    def test_has_height_for_width(self):
        cb = WrappingCheckBox("Short text")
        self.assertTrue(cb.hasHeightForWidth())

    def test_height_for_width_increases_when_wrapping(self):
        long_text = (
            "Afficher une fenêtre de confirmation de sortie pour les changements non enregistrés dans les balises"
        )
        cb = WrappingCheckBox(long_text)
        h_wide = cb.heightForWidth(800)
        h_narrow = cb.heightForWidth(200)
        self.assertGreater(h_narrow, h_wide)

    def test_empty_text_height(self):
        cb = WrappingCheckBox("")
        self.assertGreater(cb.heightForWidth(200), 0)

    def test_minimum_size_hint(self):
        cb = WrappingCheckBox("Some text")
        min_size = cb.minimumSizeHint()
        self.assertGreater(min_size.width(), 0)
        self.assertGreater(min_size.height(), 0)

    def test_set_text_updates_geometry(self):
        cb = WrappingCheckBox("Short")
        cb.resize(200, 20)
        cb.setText(
            "A very long text that definitely needs to wrap onto several lines in order to fit in two hundred pixels"
        )
        self.assertGreater(cb.minimumHeight(), 20)

    def test_paint_event_ltr_and_rtl(self):
        long_text = "Afficher une boîte de dialogue de confirmation lors de l'enregistrement des fichiers"
        cb = WrappingCheckBox(long_text)
        cb.resize(250, cb.heightForWidth(250))

        # LTR: indicator is on the left (x == 0), text starts after indicator
        ind_ltr, text_ltr, align_ltr = cb._layout_rects(250)
        self.assertEqual(ind_ltr.left(), 0)
        self.assertGreater(text_ltr.left(), 0)
        self.assertEqual(align_ltr, QtCore.Qt.AlignmentFlag.AlignLeft)

        # RTL: indicator is on the right, text starts at left edge
        cb.setLayoutDirection(QtCore.Qt.LayoutDirection.RightToLeft)
        ind_rtl, text_rtl, align_rtl = cb._layout_rects(250)
        self.assertGreater(ind_rtl.left(), 0)
        self.assertEqual(text_rtl.left(), 0)
        self.assertEqual(align_rtl, QtCore.Qt.AlignmentFlag.AlignRight)

    def test_resize_updates_height(self):
        long_text = "Afficher une boîte de dialogue de confirmation lors de l'enregistrement des fichiers"
        cb = WrappingCheckBox(long_text)
        expected_height = cb.heightForWidth(200)
        event = QtGui.QResizeEvent(QtCore.QSize(200, 20), QtCore.QSize(640, 480))
        cb.resize(200, 20)
        cb.resizeEvent(event)
        self.assertEqual(cb.minimumHeight(), expected_height)
