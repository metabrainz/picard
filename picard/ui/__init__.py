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
# Copyright (C) 2021, 2025 Bob Swift
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


import os
import uuid

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import (
    log,
    tagger_instance,
)
from picard.config import (
    Option,
    get_config,
)
from picard.const.sys import (
    IS_HAIKU,
    IS_MACOS,
    IS_WIN,
)
from picard.i18n import gettext as _
from picard.util import (
    get_url,
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


def modal_options():
    """Whether the Options dialog should use modal behavior.

    On macOS, Options must be WindowModal because NonModal dialogs can get
    lost behind the main window with no way to recover. On other platforms,
    Options uses NonModal + disabled MainWindow, which allows utility windows
    (LogView, Script Editor) to remain interactive.

    Can be overridden with the PICARD_MODAL_OPTIONS environment variable
    (set to '1' to force modal, '0' to force non-modal).

    Returns True for modal behavior, False for non-modal + disabled parent.
    """
    override = os.environ.get('PICARD_MODAL_OPTIONS')
    if override is not None:
        return override == '1'
    return IS_MACOS


class PreserveGeometry:
    defaultsize = None

    def __init__(self, *args, **kwargs):
        Option.add_if_missing('persist', self.opt_name(), QtCore.QByteArray())
        Option.add_if_missing('persist', self.splitters_name(), {})
        self._geometry_initialized = False
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
            return {self._get_name(splitter): splitter for splitter in self.findChildren(QtWidgets.QSplitter)}
        except AttributeError:
            return {}

    @restore_method
    def restore_geometry(self):
        self._geometry_initialized = True
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
        if not self._geometry_initialized:
            return
        geometry = self.saveGeometry()
        if not geometry:
            return
        config = get_config()
        config.persist[self.opt_name()] = geometry
        config.persist[self.splitters_name()] = {
            name: bytearray(splitter.saveState()) for name, splitter in self._get_splitters.items()
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
    flags = (
        QtCore.Qt.WindowType.WindowSystemMenuHint
        | QtCore.Qt.WindowType.WindowTitleHint
        | QtCore.Qt.WindowType.WindowCloseButtonHint
    )
    # Default modality: WindowModal when a parent is given, NonModal otherwise.
    # Subclasses can override this with an explicit Qt.WindowModality value to
    # opt out of the automatic behaviour, e.g.:
    #   modality = QtCore.Qt.WindowModality.NonModal   # keep non-modal despite having a parent
    #   modality = QtCore.Qt.WindowModality.ApplicationModal  # force app-modal (rare)
    # Set to None to use the automatic parent-based logic (the default).
    modality = None
    ready_for_display = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent, f=self.flags)
        self.tagger = tagger_instance()
        self.__shown = False
        self.ready_for_display.connect(self.restore_geometry)
        if self.modality is not None:
            self.setWindowModality(self.modality)
        elif parent is not None:
            self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        if parent is None:
            self._register_parentless()

    _parentless_instances: list['PicardDialog'] = []

    def _register_parentless(self):
        self._parentless_instances.append(self)

    @classmethod
    def close_all_parentless(cls):
        """Close all parentless dialogs. Called on application quit."""
        for dialog in cls._parentless_instances:
            log.debug("Closing parentless dialog %s on quit", type(dialog).__name__)
            dialog.close()
        cls._parentless_instances.clear()

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

    def _show_with_modality(self, modality):
        self.setWindowModality(modality)
        self.show()
        self.raise_()
        self.activateWindow()

    def show_modal(self):
        """Show this dialog as window-modal and bring it to the front.

        Sets WindowModal modality (blocking only the parent window), then
        shows, raises, and activates the dialog. Use this instead of exec()
        when you want non-blocking modal behaviour, or instead of a bare
        show() when the dialog must block its parent.
        """
        self._show_with_modality(QtCore.Qt.WindowModality.WindowModal)

    def show_nonmodal(self):
        """Show this dialog as non-modal and bring it to the front.

        Clears any modality so the dialog does not block any window, then
        shows, raises, and activates it. Use this for persistent utility
        windows (log viewer, documentation, etc.) that should stay open
        alongside the rest of the UI.
        """
        self._show_with_modality(QtCore.Qt.WindowModality.NonModal)

    def set_window_title(self, title: str) -> None:
        """Set window title, appending the app name for parentless windows.

        Parentless windows appear as separate entries in the taskbar, so the
        app name suffix helps identify them. Parented dialogs are already
        visually associated with their parent and don't need it.
        """
        if not self.parent():
            title = _("%s — MusicBrainz Picard") % title
        self.setWindowTitle(title)

    def show_help(self, help_url=None):
        url = help_url or self.help_url
        if url:
            webbrowser2.open(get_url(url))


# With py3, QObjects are no longer hashable unless they have
# an explicit __hash__ implemented.
# See: http://python.6.x6.nabble.com/QTreeWidgetItem-is-not-hashable-in-Py3-td5212216.html
class HashableItem:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__id = uuid.uuid4()
        self.__hash = hash(self.__id)

    def __eq__(self, other):
        return self.__id == other.__id

    def __hash__(self):
        return self.__hash


class HashableTreeWidgetItem(HashableItem, QtWidgets.QTreeWidgetItem):
    pass


class HashableListWidgetItem(HashableItem, QtWidgets.QListWidgetItem):
    pass
