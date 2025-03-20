# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2012-2014, 2017, 2019 Wieland Hoffmann
# Copyright (C) 2013-2014, 2018-2025 Laurent Monin
# Copyright (C) 2014, 2017, 2020 Sophist-UK
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017-2019 Antonio Larrosa
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2018-2024 Philipp Wolfer
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 Suryansh Shakya
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

from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard.i18n import gettext as _


class ArtworkCoverWidget(QtWidgets.QWidget):
    """A QWidget that can be added to artwork column cell of ArtworkTable."""

    SIZE = 170

    def __init__(self, pixmap=None, text=None, size=None, parent=None):
        super().__init__(parent=parent)
        layout = QtWidgets.QVBoxLayout()

        if pixmap is not None:
            if size is None:
                size = self.SIZE
            image_label = QtWidgets.QLabel()
            image_label.setPixmap(pixmap.scaled(size, size,
                                                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                                QtCore.Qt.TransformationMode.SmoothTransformation))
            image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(image_label)

        if text is not None:
            text_label = QtWidgets.QLabel()
            text_label.setText(text)
            text_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            text_label.setWordWrap(True)
            layout.addWidget(text_label)

        self.setLayout(layout)


class ArtworkTable(QtWidgets.QTableWidget):
    H_SIZE = 200
    V_SIZE = 230

    NUM_ROWS = 0
    NUM_COLS = 3

    _columns = {}
    _labels = ()
    _tooltips = {}
    artwork_columns = ()

    def __init__(self, parent=None):
        super().__init__(self.NUM_ROWS, self.NUM_COLS, parent=parent)

        h_header = self.horizontalHeader()
        h_header.setDefaultSectionSize(self.H_SIZE)
        h_header.setStretchLastSection(True)

        v_header = self.verticalHeader()
        v_header.setDefaultSectionSize(self.V_SIZE)

        self.setHorizontalHeaderLabels(self._labels)
        for colname, index in self._columns.items():
            self.horizontalHeaderItem(index).setToolTip(self._tooltips.get(colname, None))

    def get_column_index(self, name):
        return self._columns[name]


class ArtworkTableSimple(ArtworkTable):
    TYPE_COLUMN_SIZE = 140

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setColumnWidth(self.get_column_index('type'), self.TYPE_COLUMN_SIZE)


class ArtworkTableNew(ArtworkTableSimple):
    _columns = {
        'type': 0,
        'new': 1,
        'external': 2,
    }

    artwork_columns = ('new', 'external',)
    _labels = (_("Type"), _("New Embedded"), _("New Exported"),)
    _tooltips = {
        'new': _("New cover art embedded into tags"),
        'external': _("New cover art saved as a separate file"),
    }


class ArtworkTableOriginal(ArtworkTableSimple):
    NUM_COLS = 2

    _columns = {
        'type': 0,
        'new': 1,
    }

    artwork_columns = ('new',)
    _labels = (_("Type"), _("Existing Cover"))
    _tooltips = {
        'new': _("Existing cover art already embedded into tags"),
    }


class ArtworkTableExisting(ArtworkTable):
    NUM_COLS = 4

    _columns = {
        'orig': 0,
        'type': 1,
        'new': 2,
        'external': 3,
    }

    artwork_columns = ('orig', 'new', 'external',)
    _labels = (_("Existing Cover"), _("Type"), _("New Embedded"), _("New Exported"),)
    _tooltips = {
        'orig': _("Existing cover art already embedded into tags"),
        'new': _("New cover art embedded into tags"),
        'external': _("New cover art saved as a separate file"),
    }
