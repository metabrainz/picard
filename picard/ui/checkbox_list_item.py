# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018 Sambhav Kothari
# Copyright (C) 2018, 2020-2022 Laurent Monin
# Copyright (C) 2022 Philipp Wolfer
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


from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QListWidgetItem


class CheckboxListItem(QListWidgetItem):

    def __init__(self, text='', checked=False, data=None):
        super().__init__()
        self.setText(text)
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        self.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self.data = data

    @property
    def checked(self):
        return self.checkState() == Qt.CheckState.Checked
