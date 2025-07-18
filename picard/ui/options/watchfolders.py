# -*- coding: utf-8 -*-
"""Watch Folder Options Page

Ermöglicht dem Benutzer, Verzeichnisse für die Ordner-Überwachung zu konfigurieren.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6 import QtCore, QtWidgets

from picard.config import get_config
from picard.extension_points.options_pages import register_options_page
from picard.i18n import gettext as _
from picard.ui.options import OptionsPage
import picard.options  # Stellt sicher, dass die Optionen-Definitionen (watch_folders_*) registriert sind


class WatchFolderOptionsPage(OptionsPage):
    NAME = "watch_folders"
    TITLE = _("Watch Folders")
    PARENT = None
    SORT_ORDER = 99  # weit unten einsortieren
    ACTIVE = True
    HELP_URL = "/config/watch_folders.html"

    OPTIONS = (
        ("watch_folders_paths", ["watch_folders_paths"]),
        ("watch_folders_autostart", ["watch_folders_autostart"]),
    )

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)

        self.layout = QtWidgets.QVBoxLayout(self)

        # Ordnerliste
        self.list_widget = QtWidgets.QListWidget(self)
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.layout.addWidget(self.list_widget)

        # Buttons Add / Remove
        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_add = QtWidgets.QPushButton(_("Add…"), self)
        self.btn_remove = QtWidgets.QPushButton(_("Remove"), self)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addStretch(1)
        self.layout.addLayout(btn_layout)

        # Auto-Start-Checkbox
        self.chk_autostart = QtWidgets.QCheckBox(_("Start watching on Picard startup"), self)
        self.layout.addWidget(self.chk_autostart)

        # Auto-Tagging-Checkbox
        self.chk_auto_tag = QtWidgets.QCheckBox(_("Automatically tag newly added files"), self)
        self.layout.addWidget(self.chk_auto_tag)

        # Auto-Save-Checkbox
        self.chk_auto_save = QtWidgets.QCheckBox(_("Automatically save after tagging"), self)
        self.layout.addWidget(self.chk_auto_save)
        self.layout.addStretch(1)

        # Signals
        self.btn_add.clicked.connect(self._add_folder)
        self.btn_remove.clicked.connect(self._remove_selected)

    # ------------------------------------------------------------------
    # OptionsPage API
    # ------------------------------------------------------------------

    def load(self):
        cfg = get_config()
        self.list_widget.clear()
        for p in cfg.setting["watch_folders_paths"]:
            self.list_widget.addItem(p)
        self.chk_autostart.setChecked(cfg.setting["watch_folders_autostart"])
        self.chk_auto_tag.setChecked(cfg.setting["watch_folders_auto_tag"])
        self.chk_auto_save.setChecked(cfg.setting["watch_folders_auto_save"])

    def save(self):
        cfg = get_config()
        paths = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        cfg.setting["watch_folders_paths"] = paths
        cfg.setting["watch_folders_autostart"] = self.chk_autostart.isChecked()
        cfg.setting["watch_folders_auto_tag"] = self.chk_auto_tag.isChecked()
        cfg.setting["watch_folders_auto_save"] = self.chk_auto_save.isChecked()

    def restore_defaults(self):
        self.list_widget.clear()
        self.chk_autostart.setChecked(True)
        self.chk_auto_tag.setChecked(True)
        self.chk_auto_save.setChecked(False)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _add_folder(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, _("Select Folder to Watch"))
        if path:
            path = str(Path(path).resolve())
            existing = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
            if path not in existing:
                self.list_widget.addItem(path)

    def _remove_selected(self):
        for item in self.list_widget.selectedItems():
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)


register_options_page(WatchFolderOptionsPage) 