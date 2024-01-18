# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008 Lukáš Lalinský
# Copyright (C) 2014 Sophist-UK
# Copyright (C) 2014, 2018, 2020-2024 Laurent Monin
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2019-2023 Philipp Wolfer
# Copyright (C) 2021 Bob Swift
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

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import log
from picard.config import (
    Option,
    get_config,
)
from picard.const import DOCS_BASE_URL
from picard.const.sys import (
    IS_HAIKU,
    IS_MACOS,
    IS_WIN,
)
from picard.util import (
    restore_method,
    webbrowser2,
)


if IS_MACOS:
    FONT_FAMILY_MONOSPACE = 'Menlo'
elif IS_WIN:
    FONT_FAMILY_MONOSPACE = 'Consolas'
elif IS_HAIKU:
    FONT_FAMILY_MONOSPACE = 'Noto Sans Mono'
else:
    FONT_FAMILY_MONOSPACE = 'Monospace'


class PreserveGeometry:

    defaultsize = None

    def __init__(self):
        Option.add_if_missing('persist', self.opt_name(), QtCore.QByteArray())
        Option.add_if_missing('persist', self.splitters_name(), {})
        if getattr(self, 'finished', None):
            self.finished.connect(self.save_geometry)

    def opt_name(self):
        return 'geometry_' + self.__class__.__name__

    def splitters_name(self):
        return 'splitters_' + self.__class__.__name__

    def _get_lineage(self, widget):
        """Try to develop a unique lineage / ancestry to identify the specified widget.
        Args:
            widget (QtWidget): Widget to process.
        Returns:
            generator: full ancestry for the specified widget.
        """
        parent = widget.parent()
        if parent:
            yield from self._get_lineage(parent)

        yield widget.objectName() if widget.objectName() else widget.__class__.__name__

    def _get_name(self, widget):
        """Return the name of the widget.

        Args:
            widget (QtWidget): Widget to process.

        Returns:
            str: The name of the widget or the lineage if there is no name assigned.
        """
        name = widget.objectName()
        if not name:
            name = '.'.join(self._get_lineage(widget))
            log.debug("Splitter does not have objectName(): %s", name)
        return name

    @property
    def _get_splitters(self):
        try:
            return {
                self._get_name(splitter): splitter
                for splitter in self.findChildren(QtWidgets.QSplitter)
            }
        except AttributeError:
            return {}

    @restore_method
    def restore_geometry(self):
        config = get_config()
        geometry = config.persist[self.opt_name()]
        if not geometry.isNull():
            self.restoreGeometry(geometry)
        elif self.defaultsize:
            self.resize(self.defaultsize)
        splitters = config.persist[self.splitters_name()]
        seen = set()
        for name, splitter in self._get_splitters.items():
            if name in splitters:
                splitter.restoreState(splitters[name])
                seen.add(name)
        # remove unused saved states that don't match any existing splitter names
        for name in set(splitters) - seen:
            del config.persist[self.splitters_name()][name]

    def save_geometry(self):
        config = get_config()
        config.persist[self.opt_name()] = self.saveGeometry()
        config.persist[self.splitters_name()] = {
            name: bytearray(splitter.saveState())
            for name, splitter in self._get_splitters.items()
        }


class SingletonDialog:
    _instance = None

    @classmethod
    def get_instance(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = cls(*args, **kwargs)
            cls._instance.destroyed.connect(cls._on_dialog_destroyed)
        return cls._instance

    @classmethod
    def show_instance(cls, *args, **kwargs):
        instance = cls.get_instance(*args, **kwargs)
        # Get the current parent
        if hasattr(instance, 'parent'):
            if callable(instance.parent):
                parent = instance.parent()
            else:
                parent = instance.parent
        else:
            parent = None
        # Update parent if changed
        if 'parent' in kwargs and parent != kwargs['parent']:
            instance.setParent(kwargs['parent'])
        instance.show()
        instance.raise_()
        instance.activateWindow()
        return instance

    @classmethod
    def _on_dialog_destroyed(cls):
        cls._instance = None


class PicardDialog(QtWidgets.QDialog, PreserveGeometry):

    help_url = None
    flags = QtCore.Qt.WindowType.WindowSystemMenuHint | QtCore.Qt.WindowType.WindowTitleHint | QtCore.Qt.WindowType.WindowCloseButtonHint
    ready_for_display = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent, self.flags)
        self.__shown = False
        self.ready_for_display.connect(self.restore_geometry)

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.StandardKey.Close):
            self.close()
        elif event.matches(QtGui.QKeySequence.StandardKey.HelpContents) and self.help_url:
            self.show_help()
        else:
            super().keyPressEvent(event)

    def showEvent(self, event):
        if not self.__shown:
            self.ready_for_display.emit()
            self.__shown = True
        return super().showEvent(event)

    def show_help(self):
        if self.help_url:
            url = self.help_url
            if url.startswith('/'):
                url = DOCS_BASE_URL + url
            webbrowser2.open(url)


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
