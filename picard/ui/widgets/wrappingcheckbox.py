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
    QtWidgets,
)


class WrappingCheckBox(QtWidgets.QCheckBox):
    """A QCheckBox that word-wraps its text onto multiple lines.

    Standard QCheckBox in Qt does not support word wrapping. When displayed
    in narrow dialogs or with long translated texts (e.g. in French), the text
    is normally clipped at the right margin.

    This subclass calculates height for width, dynamically updates its minimum
    height on resize, and renders its label with Qt.TextFlag.TextWordWrap
    while keeping the check indicator aligned with the first line of text.

    Note: Designed for text checkboxes in options dialogs. It does not
    render icons set via setIcon(), and keyboard shortcut underlines
    follow the platform's SH_UnderlineShortcut style hint.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )

    def _get_metrics(self):
        opt = QtWidgets.QStyleOptionButton()
        self.initStyleOption(opt)
        style = self.style()
        ind_w = style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_IndicatorWidth, opt, self)
        spacing = style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_CheckBoxLabelSpacing, opt, self)
        ind_h = style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_IndicatorHeight, opt, self)
        return opt, style, ind_w, spacing, ind_h

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        opt, style, ind_w, spacing, ind_h = self._get_metrics()
        _VERTICAL_PADDING = 4
        text = self.text()
        if not text:
            return ind_h

        avail_width = max(20, width - ind_w - spacing)
        rect = self.fontMetrics().boundingRect(
            QtCore.QRect(0, 0, avail_width, 0),
            QtCore.Qt.TextFlag.TextWordWrap | QtCore.Qt.TextFlag.TextShowMnemonic,
            text,
        )
        return max(ind_h, rect.height() + _VERTICAL_PADDING)

    def minimumSizeHint(self) -> QtCore.QSize:
        opt, style, ind_w, spacing, ind_h = self._get_metrics()
        _MIN_TEXT_WIDTH = 120  # Minimum readable text column width (~15-20 chars)
        return QtCore.QSize(ind_w + spacing + _MIN_TEXT_WIDTH, ind_h)

    def setText(self, text: str) -> None:
        super().setText(text)
        if self.width() > 0:
            self.setMinimumHeight(self.heightForWidth(self.width()))
        self.updateGeometry()

    def resizeEvent(self, a0: QtGui.QResizeEvent | None) -> None:
        super().resizeEvent(a0)
        width = self.width()
        if width > 0:
            # QScrollArea ignores heightForWidth when sizing its viewport content.
            # Pin minimumHeight on resize so the scroll area allocates enough vertical space.
            new_h = self.heightForWidth(width)
            if new_h != self.minimumHeight():
                self.setMinimumHeight(new_h)

    def _layout_rects(self, width: int):
        opt, style, ind_w, spacing, ind_h = self._get_metrics()
        fm = self.fontMetrics()
        line_h = fm.height()
        ind_y = max(0, (line_h - ind_h) // 2)
        avail_width = max(20, width - ind_w - spacing)

        if self.isRightToLeft():
            ind_rect = QtCore.QRect(width - ind_w, ind_y, ind_w, ind_h)
            text_rect = QtCore.QRect(0, 0, avail_width, self.height())
            align_flag = QtCore.Qt.AlignmentFlag.AlignRight
        else:
            ind_rect = QtCore.QRect(0, ind_y, ind_w, ind_h)
            text_rect = QtCore.QRect(ind_w + spacing, 0, avail_width, self.height())
            align_flag = QtCore.Qt.AlignmentFlag.AlignLeft
        return ind_rect, text_rect, align_flag

    def paintEvent(self, a0: QtGui.QPaintEvent | None) -> None:
        opt, style, ind_w, spacing, ind_h = self._get_metrics()
        full_text = opt.text

        painter = QtWidgets.QStylePainter(self)
        ind_rect, text_rect, align_flag = self._layout_rects(self.width())

        opt.rect = ind_rect
        opt.text = ""
        style.drawPrimitive(QtWidgets.QStyle.PrimitiveElement.PE_IndicatorCheckBox, opt, painter, self)

        if opt.state & QtWidgets.QStyle.StateFlag.State_HasFocus:
            focus_opt = QtWidgets.QStyleOptionFocusRect()
            focus_opt.rect = text_rect
            focus_opt.state = opt.state
            style.drawPrimitive(QtWidgets.QStyle.PrimitiveElement.PE_FrameFocusRect, focus_opt, painter, self)

        show_mnemonic = not style.styleHint(QtWidgets.QStyle.StyleHint.SH_UnderlineShortcut, opt, self) or bool(
            opt.state & QtWidgets.QStyle.StateFlag.State_KeyboardAccelerator
        )

        mnemonic_flag = QtCore.Qt.TextFlag.TextShowMnemonic if show_mnemonic else QtCore.Qt.TextFlag.TextHideMnemonic

        flags = QtCore.Qt.TextFlag.TextWordWrap | mnemonic_flag | QtCore.Qt.AlignmentFlag.AlignTop | align_flag
        painter.drawItemText(
            text_rect,
            flags,
            self.palette(),
            self.isEnabled(),
            full_text,
            QtGui.QPalette.ColorRole.WindowText,
        )
