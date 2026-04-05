# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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

from __future__ import annotations

from functools import partial

from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard.config import get_config
from picard.i18n import gettext as _


class TutorialTip(QtWidgets.QDialog):
    """A non-modal dialog for tutorial tips, positioned near a target widget."""

    disabled = QtCore.pyqtSignal()

    def __init__(self, text: str, doc_url: str | None = None, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.setWindowTitle(_("Picard Tutorial"))

        layout = QtWidgets.QVBoxLayout(self)

        label = QtWidgets.QLabel(text)
        label.setWordWrap(True)
        label.setOpenExternalLinks(True)
        layout.addWidget(label)

        if doc_url:
            link = QtWidgets.QLabel(
                '<a href="{url}">{text}</a>'.format(
                    url=doc_url,
                    text=_("Learn more…"),
                )
            )
            link.setToolTip(doc_url)
            link.setOpenExternalLinks(True)
            layout.addWidget(link)

        button_layout = QtWidgets.QHBoxLayout()
        disable_button = QtWidgets.QPushButton(_("Don't show tips again"))
        disable_button.clicked.connect(self._on_disable)
        button_layout.addWidget(disable_button)
        button_layout.addStretch()
        close_button = QtWidgets.QPushButton(_("Got it"))
        close_button.setDefault(True)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

    def _on_disable(self) -> None:
        self.disabled.emit()
        self.accept()

    def show_near_widget(self, widget: QtWidgets.QWidget) -> None:
        self.adjustSize()
        pos = widget.mapToGlobal(QtCore.QPoint(0, widget.height()))
        screen = widget.screen()
        if screen:
            screen_rect = screen.availableGeometry()
            if pos.x() + self.width() > screen_rect.right():
                pos.setX(screen_rect.right() - self.width())
            if pos.y() + self.height() > screen_rect.bottom():
                pos = widget.mapToGlobal(QtCore.QPoint(0, -self.height()))
        self.move(pos)
        self.show()


class TutorialManager:
    """Manages contextual tutorial tips shown once to new users."""

    def __init__(self, window: QtWidgets.QMainWindow):
        self._window = window
        self._active_tip: TutorialTip | None = None

    def should_show(self, step_id: str) -> bool:
        config = get_config()
        if config.persist['tutorial_disabled']:
            return False
        return step_id not in config.persist['tutorial_steps_shown']

    def mark_shown(self, step_id: str) -> None:
        config = get_config()
        shown = config.persist['tutorial_steps_shown']
        if step_id not in shown:
            shown.append(step_id)
            config.persist['tutorial_steps_shown'] = shown

    def disable(self) -> None:
        config = get_config()
        config.persist['tutorial_disabled'] = True

    def show_tip(self, step_id: str, widget: QtWidgets.QWidget, text: str, doc_url: str | None = None) -> bool:
        if not self.should_show(step_id):
            return False
        self._close_active_tip()
        tip = TutorialTip(text, doc_url=doc_url, parent=self._window)
        tip.finished.connect(partial(self.mark_shown, step_id))
        tip.finished.connect(partial(self._on_tip_closed, tip))
        tip.disabled.connect(self.disable)
        self._active_tip = tip
        tip.show_near_widget(widget)
        return True

    def _close_active_tip(self) -> None:
        if self._active_tip:
            self._active_tip.close()
            self._active_tip = None

    def _on_tip_closed(self, tip: TutorialTip, _result: int | None = None) -> None:
        if self._active_tip is tip:
            self._active_tip = None
