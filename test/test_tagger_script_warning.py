# Picard, the next-generation MusicBrainz tagger
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <https://www.gnu.org/licenses/>.

from types import SimpleNamespace
from unittest.mock import Mock, patch

from PyQt6 import QtCore, QtWidgets

from picard.config import Config
from picard.script import iter_unknown_script_functions
from picard.session.session_loader import ConfigurationManager
from picard.tagger import Tagger

import pytest

from picard.ui.mainwindow import MainWindow


def test_no_warning_for_valid_scripts():
    tagger = Mock()
    tagger._unknown_script_errors = set()
    with (
        patch('picard.tagger.iter_unknown_script_functions', return_value=[]),
        patch('picard.tagger.QtWidgets.QMessageBox') as message,
    ):
        Tagger.warn_about_unknown_script_functions(tagger, None)
    message.assert_not_called()


@pytest.mark.parametrize(
    'button_text, page',
    [
        ('Close', None),
        ('Scripting', 'scripting'),
        ('File Naming', 'filerenaming'),
        ('Cover Art', 'cover'),
        ('Plugins', 'plugins'),
    ],
)
def test_single_warning_with_options(qapp, button_text, page):
    class Window(QtWidgets.QWidget):
        def __init__(self):
            super().__init__()
            self.show_options = Mock()

    window = Window()
    tagger = Mock(spec=Tagger)
    tagger.window = window
    tagger._unknown_script_errors = set()
    errors = [
        ('scripting', '<My Script>', '$missingone'),
        ('scripting', 'Other Script', '$missingtwo'),
        ('filerenaming', 'File naming script', '$missingthree'),
        ('cover', 'Cover art naming script', '$missingfour'),
    ]
    dialogs = []

    def dismiss_dialog():
        dialog = qapp.activeModalWidget()
        if isinstance(dialog, QtWidgets.QMessageBox):
            dialogs.append(
                (dialog.informativeText(), dialog.textFormat(), [button.text() for button in dialog.buttons()])
            )
            button = dialog.button(QtWidgets.QMessageBox.StandardButton.Close)
            if page:
                button = next((button for button in dialog.buttons() if button.text() == button_text), button)
            button.click()

    with patch('picard.tagger.iter_unknown_script_functions', return_value=errors):
        QtCore.QTimer.singleShot(0, dismiss_dialog)
        Tagger.warn_about_unknown_script_functions(tagger, None)

    assert len(dialogs) == 1
    text, format_, buttons = dialogs[0]
    assert '<My Script>: $missingone' in text
    assert 'Other Script: $missingtwo' in text
    assert 'File naming script: $missingthree' in text
    assert 'Cover art naming script: $missingfour' in text
    assert format_ == QtCore.Qt.TextFormat.PlainText
    for title in ('Scripting', 'File Naming', 'Cover Art', 'Plugins'):
        assert buttons.count(title) == 1
    if page:
        window.show_options.assert_called_once_with(page)
    else:
        window.show_options.assert_not_called()


def test_warning_runs_after_plugin_initialization():
    tagger = Mock()
    manager = tagger.get_plugin_manager.return_value
    manager.init_plugins.return_value = []
    manager._init_failed_plugins = []
    config = SimpleNamespace(setting={'session_autosave_interval_min': 0})
    with (
        patch('picard.tagger.get_config', return_value=config),
        patch('picard.tagger.QtCore.QTimer.singleShot'),
    ):
        Tagger.run(tagger)
    calls = [call[0] for call in tagger.mock_calls]
    assert calls.index('get_plugin_manager().init_plugins') < calls.index('warn_about_unknown_script_functions')
    tagger.warn_about_unknown_script_functions.assert_called_once_with(config)


def test_recheck_only_warns_when_new_errors_appear():
    tagger = Mock()
    tagger._unknown_script_errors = set()
    error = ('scripting', 'Script', '$missing')
    with (
        patch('picard.tagger.iter_unknown_script_functions', side_effect=[[error], [error], [], [error]]),
        patch('picard.tagger.QtWidgets.QMessageBox') as message,
    ):
        for _ in range(4):
            Tagger.warn_about_unknown_script_functions(tagger, None)
    assert message.call_count == 2


def test_profile_toggle_rechecks_effective_scripts_after_menu_closes(qapp, tmp_path):
    config = Config.from_file(None, str(tmp_path / 'picard.ini'))
    config.setting['enable_tagger_scripts'] = True
    config.setting['list_of_scripts'] = [(0, 'Base', True, '$missingbase()')]
    config.profiles['user_profiles'] = [{'id': 'p1', 'enabled': False, 'title': 'Profile'}]
    config.profiles['user_profile_settings'] = {'p1': {'list_of_scripts': [(0, 'Profile', True, '$missingprofile()')]}}
    window = Mock(spec=MainWindow)
    window.tagger = Mock(spec=Tagger)
    # Headless Qt platforms do not reliably show native popup menus.
    # Model their visibility explicitly while retaining the real timer event loop.
    window.profile_quick_selector_menu = Mock(spec=QtWidgets.QMenu)
    window.options_menu = Mock(spec=QtWidgets.QMenu)
    window.profile_quick_selector_menu.isVisible.return_value = True
    window.options_menu.isVisible.return_value = False
    window._profile_script_check_pending = False
    window._schedule_profile_script_check = lambda: MainWindow._schedule_profile_script_check(window)
    window._check_pending_profile_scripts = lambda: MainWindow._check_pending_profile_scripts(window)
    observed = []
    window.tagger.warn_about_unknown_script_functions.side_effect = lambda: observed.append(
        list(iter_unknown_script_functions(config))
    )

    def hide_menu(menu):
        # aboutToHide schedules the check before the menu becomes invisible.
        window._schedule_profile_script_check()
        menu.isVisible.return_value = False
        qapp.processEvents()

    with patch('picard.ui.mainwindow.get_config', return_value=config):
        MainWindow._set_profile_enabled(window, 'p1', True)
        MainWindow._set_profile_enabled(window, 'p1', False)
        MainWindow._set_profile_enabled(window, 'p1', True)
        qapp.processEvents()
        assert not observed

        hide_menu(window.profile_quick_selector_menu)
        assert observed == [[('scripting', 'Profile', '$missingprofile')]]

        window.profile_quick_selector_menu.isVisible.return_value = True
        window.options_menu.isVisible.return_value = True
        MainWindow._set_profile_enabled(window, 'p1', False)
        MainWindow._set_profile_enabled(window, 'p1', False)
        hide_menu(window.profile_quick_selector_menu)
        assert len(observed) == 1
        hide_menu(window.options_menu)
        assert observed == [[('scripting', 'Profile', '$missingprofile')], [('scripting', 'Base', '$missingbase')]]

        # A native menu action may be triggered after its menu has already hidden.
        MainWindow._set_profile_enabled(window, 'p1', True)
        qapp.processEvents()
        assert observed[-1] == [('scripting', 'Profile', '$missingprofile')]
        assert len(observed) == 3
        window._schedule_profile_script_check()
        qapp.processEvents()
        assert len(observed) == 3


def test_options_close_rechecks_scripts():
    window = Mock(spec=MainWindow)
    window.tagger = Mock(spec=Tagger)
    with patch('picard.ui.mainwindow.QtCore.QTimer.singleShot', side_effect=lambda _, callback: callback()):
        MainWindow._options_closed(window)
    window.tagger.warn_about_unknown_script_functions.assert_called_once_with()


def test_session_load_rechecks_restored_settings(tmp_path):
    config = Config.from_file(None, str(tmp_path / 'picard.ini'))
    config.setting['rename_files'] = False
    config.setting['move_files'] = False
    config.setting['active_file_naming_script_id'] = 'active'
    config.setting['file_renaming_scripts'] = {'active': {'script': '$missingnaming()'}}
    assert not list(iter_unknown_script_functions(config))
    tagger = Mock(spec=Tagger)
    observed = []
    tagger.warn_about_unknown_script_functions.side_effect = lambda: observed.append(
        list(iter_unknown_script_functions(config))
    )
    with (
        patch('picard.session.session_loader.get_config', return_value=config),
        patch(
            'picard.tagger.load_session_from_path',
            side_effect=lambda *_: ConfigurationManager().restore_options({'rename_files': True}),
        ),
    ):
        Tagger.load_session_from_path(tagger, tmp_path / 'session.mbps.gz')
    assert observed == [[('filerenaming', 'File naming script', '$missingnaming')]]
