# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2020 Philipp Wolfer
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


from PyQt5 import (
    QtCore,
    QtWidgets,
)


class TristateSortHeaderView(QtWidgets.QHeaderView):
    """A QHeaderView implementation supporting tristate sorting.

    A column can either be sorted ascending, descending or not sorted. The view
    toggles through these states by clicking on a section header.
    """

    STATE_NONE = 0
    STATE_SECTION_MOVED_OR_RESIZED = 1

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)

        # Remember if resize / move event just happened
        self._section_moved_or_resized = False
        self.lock(False)

        def update_state(i, o, n):
            self._section_moved_or_resized = True

        self.sectionResized.connect(update_state)
        self.sectionMoved.connect(update_state)

    def mouseReleaseEvent(self, event):
        if self.is_locked:
            tooltip = _(
                "The table is locked. To enable sorting and column resizing\n"
                "unlock the table in the table header's context menu.")
            QtWidgets.QToolTip.showText(event.globalPos(), tooltip, self)
            return

        if event.button() == QtCore.Qt.LeftButton:
            index = self.logicalIndexAt(event.pos())
            if (index != -1 and index == self.sortIndicatorSection()
                and self.sortIndicatorOrder() == QtCore.Qt.DescendingOrder):
                # After a column was sorted descending we want to reset it
                # to no sorting state. But we need to call the parent
                # implementation of mouseReleaseEvent in order to handle
                # other events, such as column move and resize.
                # Disable clickable sections temporarily so the parent
                # implementation  will not do the normal click behavior.
                self.setSectionsClickable(False)
                self._section_moved_or_resized = False
                super().mouseReleaseEvent(event)
                self.setSectionsClickable(True)
                # Only treat this as an actual click if no move
                # or resize event occurred.
                if not self._section_moved_or_resized:
                    self.setSortIndicator(-1, self.sortIndicatorOrder())
                return
        # Normal handling of events
        super().mouseReleaseEvent(event)

    def lock(self, is_locked):
        self.is_locked = is_locked
        self.setSectionsClickable(not is_locked)
        self.setSectionsMovable(not is_locked)
        if is_locked:
            resize_mode = QtWidgets.QHeaderView.Fixed
        else:
            resize_mode = QtWidgets.QHeaderView.Interactive
        self.setSectionResizeMode(resize_mode)
