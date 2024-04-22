# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018 Sambhav Kothari
# Copyright (C) 2018, 2020-2024 Laurent Monin
# Copyright (C) 2022, 2024 Philipp Wolfer
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


from PySide6 import (
    QtCore,
    QtWidgets,
)


class CheckboxListItem(QtWidgets.QListWidgetItem):

    def __init__(self, text='', checked=False, parent=None):
        super().__init__(text, parent=parent)
        self.setFlags(self.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
        self.setCheckState(QtCore.Qt.CheckState.Checked if checked else QtCore.Qt.CheckState.Unchecked)

    @property
    def checked(self):
        return self.checkState() == QtCore.Qt.CheckState.Checked
