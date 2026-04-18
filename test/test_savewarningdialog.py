# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 The MusicBrainz Team
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

from unittest.mock import patch

from test.picardtestcase import PicardTestCase

from picard import config

from picard.ui.savewarningdialog import SaveWarningDialog


class _DummySignal:
    def connect(self, _callback):
        return None


class _DummyCheckBox:
    def __init__(self, _text):
        self._checked = False
        self.toggled = _DummySignal()

    def setChecked(self, value):
        self._checked = value


class _DummyMessageBox:
    class Icon:
        Warning = 1

    class StandardButton:
        Ok = 1
        Cancel = 2

    def __init__(self, _parent):
        self._text = ""

    def setIcon(self, _icon):
        return None

    def setText(self, text):
        self._text = text

    def text(self):
        return self._text

    def setWindowTitle(self, _title):
        return None

    def setWindowModality(self, _modality):
        return None

    def setCheckBox(self, _checkbox):
        return None

    def setStandardButtons(self, _buttons):
        return None

    def setDefaultButton(self, _button):
        return None

    def exec(self):
        return self.StandardButton.Cancel


@patch("picard.ui.savewarningdialog.QtWidgets.QCheckBox", _DummyCheckBox)
@patch("picard.ui.savewarningdialog.QtWidgets.QMessageBox", _DummyMessageBox)
@patch("picard.ui.savewarningdialog.get_config", lambda: config.config)
class TestSaveWarningDialog(PicardTestCase):
    def setUp(self):
        super().setUp()

    def _set_default_config(self):
        config.setting["enable_tag_saving"] = False
        config.setting["rename_files"] = False
        config.setting["move_files"] = True
        config.setting["move_files_to"] = "/music/tagged"
        config.setting["move_additional_files"] = False
        config.setting["move_additional_files_pattern"] = "*.jpg *.pdf"

    def test_save_warning_dialog_displays_move_conflict_strategy_skip(self):
        self._set_default_config()
        config.setting["move_conflict_strategy"] = "skip"

        dialog = SaveWarningDialog(None, 2)

        self.assertIn("skip moving if destination file exists", dialog.msg.text())
        self.assertIn("/music/tagged", dialog.msg.text())

    def test_save_warning_dialog_displays_move_conflict_strategy_rename(self):
        self._set_default_config()
        config.setting["move_conflict_strategy"] = "rename"

        dialog = SaveWarningDialog(None, 2)

        self.assertIn("rename with a numeric suffix if destination file exists", dialog.msg.text())
        self.assertIn("/music/tagged", dialog.msg.text())

    def test_save_warning_dialog_displays_move_conflict_strategy_overwrite(self):
        self._set_default_config()
        config.setting["move_conflict_strategy"] = "overwrite"

        dialog = SaveWarningDialog(None, 2)

        self.assertIn("overwrite destination file if it exists", dialog.msg.text())
        self.assertIn("/music/tagged", dialog.msg.text())

    def test_save_warning_dialog_includes_additional_files_pattern(self):
        self._set_default_config()
        config.setting["rename_files"] = True
        config.setting["move_additional_files"] = True
        config.setting["move_conflict_strategy"] = "rename"

        dialog = SaveWarningDialog(None, 2)

        self.assertIn("configured file naming script", dialog.msg.text())
        self.assertIn("additional files matching pattern", dialog.msg.text())
        self.assertIn("rename with a numeric suffix if destination file exists", dialog.msg.text())
        self.assertIn("/music/tagged", dialog.msg.text())
        self.assertIn("*.jpg *.pdf", dialog.msg.text())

    def test_save_warning_dialog_additional_files_uses_skip_conflict_strategy(self):
        self._set_default_config()
        config.setting["move_conflict_strategy"] = "skip"
        config.setting["move_additional_files"] = True

        dialog = SaveWarningDialog(None, 2)

        self.assertIn("additional files matching pattern", dialog.msg.text())
        self.assertIn("skip moving if destination file exists", dialog.msg.text())

    def test_save_warning_dialog_additional_files_uses_rename_conflict_strategy(self):
        self._set_default_config()
        config.setting["move_conflict_strategy"] = "rename"
        config.setting["move_additional_files"] = True

        dialog = SaveWarningDialog(None, 2)

        self.assertIn("additional files matching pattern", dialog.msg.text())
        self.assertIn("rename with a numeric suffix if destination file exists", dialog.msg.text())

    def test_save_warning_dialog_additional_files_uses_overwrite_conflict_strategy(self):
        self._set_default_config()
        config.setting["move_conflict_strategy"] = "overwrite"
        config.setting["move_additional_files"] = True

        dialog = SaveWarningDialog(None, 2)

        self.assertIn("additional files matching pattern", dialog.msg.text())
        self.assertIn("overwrite destination file if it exists", dialog.msg.text())
