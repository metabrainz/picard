# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
# Copyright (C) 2026 Bob Swift
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
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
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
        text = self.text()
        if not text:
            return ind_h

        avail_width = max(20, width - ind_w - spacing)
        rect = self.fontMetrics().boundingRect(
            QtCore.QRect(0, 0, avail_width, 0),
            QtCore.Qt.TextFlag.TextWordWrap | QtCore.Qt.TextFlag.TextShowMnemonic,
            text,
        )
        return max(ind_h, rect.height() + 4)

    def sizeHint(self) -> QtCore.QSize:
        hint = super().sizeHint()
        if self.width() > 0:
            return QtCore.QSize(hint.width(), self.heightForWidth(self.width()))
        return hint

    def minimumSizeHint(self) -> QtCore.QSize:
        opt, style, ind_w, spacing, ind_h = self._get_metrics()
        return QtCore.QSize(ind_w + spacing + 30, ind_h)

    def setText(self, text: str) -> None:
        super().setText(text)
        if self.width() > 0:
            self.setMinimumHeight(self.heightForWidth(self.width()))
        self.updateGeometry()

    def resizeEvent(self, a0: QtGui.QResizeEvent | None) -> None:
        super().resizeEvent(a0)
        width = self.width()
        if width > 0:
            self.setMinimumHeight(self.heightForWidth(width))

    def paintEvent(self, a0: QtGui.QPaintEvent | None) -> None:
        opt, style, ind_w, spacing, ind_h = self._get_metrics()
        full_text = opt.text

        painter = QtWidgets.QStylePainter(self)

        fm = self.fontMetrics()
        line_h = fm.height()
        ind_y = max(0, (line_h - ind_h) // 2)

        is_rtl = self.isRightToLeft()
        avail_width = max(20, self.width() - ind_w - spacing)

        if is_rtl:
            opt.rect = QtCore.QRect(self.width() - ind_w, ind_y, ind_w, ind_h)
            text_rect = QtCore.QRect(0, 0, avail_width, self.height())
            align_flag = QtCore.Qt.AlignmentFlag.AlignRight
        else:
            opt.rect = QtCore.QRect(0, ind_y, ind_w, ind_h)
            text_rect = QtCore.QRect(ind_w + spacing, 0, avail_width, self.height())
            align_flag = QtCore.Qt.AlignmentFlag.AlignLeft

        opt.text = ""
        style.drawPrimitive(QtWidgets.QStyle.PrimitiveElement.PE_IndicatorCheckBox, opt, painter, self)

        if opt.state & QtWidgets.QStyle.StateFlag.State_HasFocus:
            focus_opt = QtWidgets.QStyleOptionFocusRect()
            focus_opt.rect = self.rect()
            focus_opt.state = opt.state
            style.drawPrimitive(QtWidgets.QStyle.PrimitiveElement.PE_FrameFocusRect, focus_opt, painter, self)

        flags = (
            QtCore.Qt.TextFlag.TextWordWrap
            | QtCore.Qt.TextFlag.TextShowMnemonic
            | QtCore.Qt.AlignmentFlag.AlignTop
            | align_flag
        )
        painter.drawItemText(
            text_rect,
            flags,
            self.palette(),
            self.isEnabled(),
            full_text,
            QtGui.QPalette.ColorRole.WindowText,
        )
