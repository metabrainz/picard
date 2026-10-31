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

"""Regression tests for PICARD-3536 (and the related focus crash PICARD-3479).

Picard shows ``WindowModal`` dialogs parented to the main window. ``WindowModal``
blocks only the parent window (PICARD-3302), but on macOS such a dialog is
rendered as a native Cocoa sheet. Tearing that sheet down while the parent
window's key-window/focus state is unstable (at startup, or on app refocus)
crashes inside the Cocoa platform plugin.

The fix adds the ``Window`` flag on macOS so the dialog renders as a standalone
window instead of a sheet, while keeping ``WindowModal`` modality. This is
applied centrally in the ``PicardDialog`` base class and via the
``set_windowmodal_safe()`` helper for the few dialogs that are not
``PicardDialog`` subclasses.

These tests assert that invariant without requiring the native crash to be
reproduced (which can only happen on a real macOS/Cocoa stack).
"""

from unittest.mock import Mock

from PyQt6 import QtCore, QtWidgets

import pytest

import picard.ui as picard_ui
from picard.ui import (
    PicardDialog,
    set_windowmodal_safe,
)


def _is_window_flag_set(widget):
    return bool(widget.windowFlags() & QtCore.Qt.WindowType.Window)


@pytest.fixture
def fake_tagger(monkeypatch):
    """Provide a dummy Tagger so PicardDialog/SetupWizard can be constructed."""
    tagger = Mock()
    tagger.autoupdate_enabled = True
    tagger.get_plugin_manager.return_value = None
    tagger.window = Mock()
    monkeypatch.setattr(picard_ui, "tagger_instance", lambda: tagger)
    return tagger


# --- set_windowmodal_safe --------------------------------------------------


def test_set_windowmodal_safe_sets_window_modality(qapp, monkeypatch):
    # Modality must be WindowModal on every platform (PICARD-3302).
    monkeypatch.setattr(picard_ui, "IS_MACOS", False)
    msg = QtWidgets.QMessageBox()
    set_windowmodal_safe(msg)
    assert msg.windowModality() == QtCore.Qt.WindowModality.WindowModal


def test_set_windowmodal_safe_touches_flags_only_on_macos(qapp, monkeypatch):
    # The Window flag is only (re)applied on macOS; on other platforms the
    # plain WindowModal behaviour is left untouched. Spying on setWindowFlags
    # makes the platform branch observable regardless of the default flags a
    # dialog already carries.
    for is_macos, expected in ((True, True), (False, False)):
        monkeypatch.setattr(picard_ui, "IS_MACOS", is_macos)
        msg = QtWidgets.QMessageBox()
        called = False
        original = msg.setWindowFlags

        def _spy(flags, _orig=original):
            nonlocal called
            called = True
            return _orig(flags)

        monkeypatch.setattr(msg, "setWindowFlags", _spy)
        set_windowmodal_safe(msg)
        assert called is expected
        assert msg.windowModality() == QtCore.Qt.WindowModality.WindowModal


# --- PicardDialog base class -----------------------------------------------


def test_picarddialog_parented_is_windowmodal(qapp, monkeypatch, fake_tagger):
    # End-to-end: a parented PicardDialog ends up WindowModal (PICARD-3302).
    parent = QtWidgets.QWidget()
    dialog = PicardDialog(parent=parent)
    assert dialog.windowModality() == QtCore.Qt.WindowModality.WindowModal


def test_picarddialog_parented_applies_sheet_workaround(qapp, monkeypatch, fake_tagger):
    # A parented PicardDialog is WindowModal, so it must route through the
    # macOS sheet workaround (PICARD-3536 / -3479).
    calls = []
    monkeypatch.setattr(picard_ui, "set_windowmodal_safe", lambda w: calls.append(w))
    parent = QtWidgets.QWidget()
    dialog = PicardDialog(parent=parent)
    assert calls == [dialog]


def test_picarddialog_parentless_skips_sheet_workaround(qapp, monkeypatch, fake_tagger):
    # A parentless PicardDialog stays non-modal; the sheet workaround (and the
    # forced modality) must not be applied.
    calls = []
    monkeypatch.setattr(picard_ui, "set_windowmodal_safe", lambda w: calls.append(w))
    dialog = PicardDialog(parent=None)
    assert dialog.windowModality() != QtCore.Qt.WindowModality.WindowModal
    assert calls == []


def test_picarddialog_explicit_nonmodal_skips_sheet_workaround(qapp, monkeypatch, fake_tagger):
    # A subclass that opts out via modality = NonModal must not be forced into
    # the sheet workaround even when parented.
    calls = []
    monkeypatch.setattr(picard_ui, "set_windowmodal_safe", lambda w: calls.append(w))
    monkeypatch.setattr(PicardDialog, "modality", QtCore.Qt.WindowModality.NonModal)
    parent = QtWidgets.QWidget()
    dialog = PicardDialog(parent=parent)
    assert dialog.windowModality() == QtCore.Qt.WindowModality.NonModal
    assert calls == []


# --- Concrete startup/save dialogs -----------------------------------------


def test_new_user_dialog_uses_sheet_safe_modality(qapp, monkeypatch):
    # NewUserDialog must route its message box through set_windowmodal_safe.
    import picard.ui.newuserdialog as newuserdialog_mod

    seen = []
    real = newuserdialog_mod.set_windowmodal_safe

    def _spy(widget):
        seen.append(widget)
        return real(widget)

    monkeypatch.setattr(newuserdialog_mod, "set_windowmodal_safe", _spy)
    dialog = newuserdialog_mod.NewUserDialog(None)
    assert seen == [dialog.msg]
    assert dialog.msg.windowModality() == QtCore.Qt.WindowModality.WindowModal


def test_setup_wizard_uses_sheet_safe_modality(qapp, monkeypatch, fake_tagger):
    import picard.ui.setupwizard as setupwizard_mod

    monkeypatch.setattr(setupwizard_mod, "tagger_instance", lambda: fake_tagger)
    seen = []
    real = setupwizard_mod.set_windowmodal_safe

    def _spy(widget):
        seen.append(widget)
        return real(widget)

    monkeypatch.setattr(setupwizard_mod, "set_windowmodal_safe", _spy)
    wizard = setupwizard_mod.SetupWizard()
    try:
        assert seen == [wizard]
        assert wizard.windowModality() == QtCore.Qt.WindowModality.WindowModal
    finally:
        wizard.close()
