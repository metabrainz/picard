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

from functools import partial

from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard.config import get_config
from picard.i18n import gettext as _


class TutorialTip(QtWidgets.QFrame):
    """A non-modal tooltip-style widget anchored near a target widget."""

    closed = QtCore.pyqtSignal()
    disabled = QtCore.pyqtSignal()

    def __init__(self, text, doc_url=None, parent=None):
        super().__init__(parent=parent)
        self.setWindowFlags(QtCore.Qt.WindowType.ToolTip)
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setStyleSheet("TutorialTip { background: palette(window); border: 1px solid palette(mid); padding: 8px; }")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

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
            link.setOpenExternalLinks(True)
            layout.addWidget(link)

        button_layout = QtWidgets.QHBoxLayout()
        disable_button = QtWidgets.QPushButton(_("Don't show tips again"))
        disable_button.clicked.connect(self._on_disable)
        button_layout.addWidget(disable_button)
        button_layout.addStretch()
        close_button = QtWidgets.QPushButton(_("Got it"))
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

    def _on_disable(self):
        self.disabled.emit()
        self.close()

    def show_at_widget(self, widget):
        self.adjustSize()
        pos = widget.mapToGlobal(QtCore.QPoint(0, widget.height()))
        # Keep on screen
        screen = widget.screen()
        if screen:
            screen_rect = screen.availableGeometry()
            if pos.x() + self.width() > screen_rect.right():
                pos.setX(screen_rect.right() - self.width())
            if pos.y() + self.height() > screen_rect.bottom():
                pos = widget.mapToGlobal(QtCore.QPoint(0, -self.height()))
        self.move(pos)
        self.show()

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


class TutorialManager:
    """Manages contextual tutorial tips shown once to new users."""

    def __init__(self, window):
        self._window = window
        self._active_tip = None

    def should_show(self, step_id):
        config = get_config()
        if config.persist['tutorial_disabled']:
            return False
        return step_id not in config.persist['tutorial_steps_shown']

    def mark_shown(self, step_id):
        config = get_config()
        shown = config.persist['tutorial_steps_shown']
        if step_id not in shown:
            shown.append(step_id)
            config.persist['tutorial_steps_shown'] = shown

    def disable(self):
        config = get_config()
        config.persist['tutorial_disabled'] = True

    def show_tip(self, step_id, widget, text, doc_url=None):
        if not self.should_show(step_id):
            return
        self._close_active_tip()
        tip = TutorialTip(text, doc_url=doc_url, parent=self._window)
        tip.closed.connect(partial(self.mark_shown, step_id))
        tip.closed.connect(partial(self._on_tip_closed, tip))
        tip.disabled.connect(self.disable)
        self._active_tip = tip
        tip.show_at_widget(widget)

    def _close_active_tip(self):
        if self._active_tip:
            self._active_tip.close()
            self._active_tip = None

    def _on_tip_closed(self, tip):
        if self._active_tip is tip:
            self._active_tip = None
