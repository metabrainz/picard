# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008 Lukáš Lalinský
# Copyright (C) 2014 Sophist-UK
# Copyright (C) 2014, 2018 Laurent Monin
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
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


import uuid

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import config
from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)
from picard.util import restore_method


if IS_MACOS:
    FONT_FAMILY_MONOSPACE = 'Menlo'
elif IS_WIN:
    FONT_FAMILY_MONOSPACE = 'Consolas'
else:
    FONT_FAMILY_MONOSPACE = 'Monospace'


class PreserveGeometry:

    defaultsize = None
    autorestore = True

    def __init__(self):
        config.Option("persist", self.opt_name(), QtCore.QByteArray())
        if self.autorestore:
            self.restore_geometry()
        if getattr(self, 'finished', None):
            self.finished.connect(self.save_geometry)

    def opt_name(self):
        return 'geometry_' + self.__class__.__name__

    @restore_method
    def restore_geometry(self):
        geometry = config.persist[self.opt_name()]
        if not geometry.isNull():
            self.restoreGeometry(geometry)
        elif self.defaultsize:
            self.resize(self.defaultsize)

    def save_geometry(self):
        config.persist[self.opt_name()] = self.saveGeometry()


class SingletonDialog:
    _instance = None

    @classmethod
    def get_instance(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = cls(*args, **kwargs)
            cls._instance.finished.connect(cls._on_dialog_finished)
        return cls._instance

    @classmethod
    def show_instance(cls, *args, **kwargs):
        instance = cls.get_instance(*args, **kwargs)
        instance.show()
        instance.raise_()
        instance.activateWindow()
        return instance

    @classmethod
    def _on_dialog_finished(cls):
        cls._instance = None


class PicardDialog(QtWidgets.QDialog, PreserveGeometry):

    flags = QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint

    def __init__(self, parent=None):
        super().__init__(parent, self.flags)

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Close):
            self.close()
        else:
            super().keyPressEvent(event)


# With py3, QObjects are no longer hashable unless they have
# an explicit __hash__ implemented.
# See: http://python.6.x6.nabble.com/QTreeWidgetItem-is-not-hashable-in-Py3-td5212216.html
class HashableTreeWidgetItem(QtWidgets.QTreeWidgetItem):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = uuid.uuid4()

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(str(self.id))


class HashableListWidgetItem(QtWidgets.QListWidgetItem):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = uuid.uuid4()

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(str(self.id))
