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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QMenu,
    QPushButton,
)

from picard.i18n import gettext as _


# Global registry of all translatable widget instances.
# Uses destroyed signal for cleanup instead of weakrefs (Qt objects
# may have their C++ side deleted while Python reference is alive).
_registry = set()


def _register(widget):
    """Register a translatable widget and connect cleanup on destroy."""
    _registry.add(widget)
    widget.destroyed.connect(lambda: _registry.discard(widget))


def retranslate_all():
    """Retranslate all live Translatable* instances in the registry."""
    for widget in list(_registry):
        widget.retranslateUi()


class TranslatableAction(QAction):
    """QAction subclass that supports dynamic retranslation.

    All text set via setText(), setToolTip(), and setStatusTip() is treated
    as untranslated source text (as marked with N_() at the call site).
    The source is stored and _() is applied immediately.

    Instances are auto-registered and retranslated by retranslate_all().
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Capture any text set via the constructor (PyQt6 sets it at C++ level,
        # bypassing our setText override). Store source and apply _().
        self._source_text = self.text()
        self._source_tool_tip = ''
        self._source_status_tip = ''
        self._source_icon_text = ''
        if self._source_text:
            super().setText(_(self._source_text))
        _register(self)

    def setText(self, text):
        self._source_text = text
        super().setText(_(text) if text else '')

    def setToolTip(self, text):
        self._source_tool_tip = text
        super().setToolTip(_(text) if text else '')

    def setStatusTip(self, text):
        self._source_status_tip = text
        super().setStatusTip(_(text) if text else '')

    def setIconText(self, text):
        self._source_icon_text = text
        super().setIconText(_(text) if text else '')

    def retranslateUi(self):
        """Re-apply _() to all stored source strings."""
        if self._source_text:
            super().setText(_(self._source_text))
        if self._source_tool_tip:
            super().setToolTip(_(self._source_tool_tip))
        if self._source_status_tip:
            super().setStatusTip(_(self._source_status_tip))
        if self._source_icon_text:
            super().setIconText(_(self._source_icon_text))


class TranslatableMenu(QMenu):
    """QMenu subclass that supports dynamic retranslation of its title.

    The title passed to the constructor or setTitle() is treated as an
    untranslated source string (as marked with N_() at the call site).
    The source is stored and _() is applied immediately.

    Instances are auto-registered and retranslated by retranslate_all().
    """

    def __init__(self, title='', parent=None):
        super().__init__(title, parent)
        self._source_title = self.title()
        if self._source_title:
            super().setTitle(_(self._source_title))
        _register(self)

    def setTitle(self, title):
        self._source_title = title
        super().setTitle(_(title) if title else '')

    def retranslateUi(self):
        """Re-apply _() to the stored source title."""
        if self._source_title:
            super().setTitle(_(self._source_title))


class TranslatablePushButton(QPushButton):
    """QPushButton subclass that supports dynamic retranslation.

    The text passed to the constructor or setText() is treated as an
    untranslated source string (as marked with N_() at the call site).
    The source is stored and _() is applied immediately.

    Instances are auto-registered and retranslated by retranslate_all().
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._source_text = self.text()
        self._source_tool_tip = ''
        if self._source_text:
            super().setText(_(self._source_text))
        _register(self)

    def setText(self, text):
        self._source_text = text
        super().setText(_(text) if text else '')

    def setToolTip(self, text):
        self._source_tool_tip = text
        super().setToolTip(_(text) if text else '')

    def retranslateUi(self):
        """Re-apply _() to stored source strings."""
        if self._source_text:
            super().setText(_(self._source_text))
        if self._source_tool_tip:
            super().setToolTip(_(self._source_tool_tip))
