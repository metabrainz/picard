# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 The MusicBrainz Team
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
    QtWidgets,
)


class FixedRowHeightDelegate(QtWidgets.QStyledItemDelegate):
    """Size rows from the view's font and icon size rather than cell content.

    Uniform row heights copy the first row's height to all rows, so text needing a
    taller fallback font (e.g. U+200E with some fonts) would resize the whole view.
    """

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        widget = option.widget
        if widget is None:
            return size
        opt = QtWidgets.QStyleOptionViewItem(option)
        opt.features |= (
            QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDisplay
            | QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasDecoration
        )
        opt.text = 'Xg'
        height = (
            widget.style()
            .sizeFromContents(QtWidgets.QStyle.ContentsType.CT_ItemViewItem, opt, QtCore.QSize(), widget)
            .height()
        )
        fixed_size = index.data(QtCore.Qt.ItemDataRole.SizeHintRole)
        if isinstance(fixed_size, QtCore.QSize):
            height = max(height, fixed_size.height())
        size.setHeight(height)
        return size
