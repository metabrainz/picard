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
from picard.ui.options.dialog import OptionsDialog
from picard.ui.options.scripting import ScriptCheckError, ScriptingOptionsPage
from picard.ui.setupwizard import CoverArtPage, FileOrganizationPage, SetupWizard


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
                (
                    dialog.informativeText(),
                    dialog.textFormat(),
                    [button.text() for button in dialog.buttons()],
                    dialog.text(),
                )
            )
            button = dialog.button(QtWidgets.QMessageBox.StandardButton.Close)
            if page:
                button = next((button for button in dialog.buttons() if button.text() == button_text), button)
            button.click()

    with patch('picard.tagger.iter_unknown_script_functions', return_value=errors):
        QtCore.QTimer.singleShot(0, dismiss_dialog)
        Tagger.warn_about_unknown_script_functions(tagger, None)

    assert len(dialogs) == 1
    text, format_, buttons, description = dialogs[0]
    assert 'have been applied' not in description
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


def _profile_test_window():
    window = Mock(spec=MainWindow)
    window.tagger = Mock(spec=Tagger)
    window.profile_quick_selector_menu = Mock(spec=QtWidgets.QMenu)
    window.options_menu = Mock(spec=QtWidgets.QMenu)
    window._pending_profile_change = None
    window._profile_script_check_pending = False
    window._confirm_pending_profile_change = lambda: MainWindow._confirm_pending_profile_change(window)
    return window


def _profile_config(tmp_path, base_script='%title%', profile_script='$missingprofile()'):
    config = Config.from_file(None, str(tmp_path / 'picard.ini'))
    config.setting['enable_tagger_scripts'] = True
    config.setting['list_of_scripts'] = [(0, 'Base', True, base_script)]
    config.profiles['user_profiles'] = [{'id': 'p1', 'enabled': False, 'title': 'My Profile'}]
    config.profiles['user_profile_settings'] = {'p1': {'list_of_scripts': [(0, 'Profile', True, profile_script)]}}
    return config


@pytest.mark.parametrize('accept', [False, True])
def test_profile_change_requires_confirmation_before_applying(tmp_path, accept):
    config = _profile_config(tmp_path)
    window = _profile_test_window()
    config.setting['rename_files'] = True
    config.setting['file_renaming_scripts'] = {'broken': {'script': '$missingnaming()'}}
    with patch('picard.ui.mainwindow.get_config', return_value=config):
        MainWindow._select_new_naming_script(window, 'broken')
    window._schedule_profile_script_check.reset_mock()
    callbacks = []
    dialog = Mock(spec=QtWidgets.QMessageBox)
    proceed_button = object()
    dialog.addButton.return_value = proceed_button
    dialog.clickedButton.return_value = proceed_button if accept else None
    with (
        patch('picard.ui.mainwindow.get_config', return_value=config),
        patch('picard.ui.mainwindow.QtCore.QTimer.singleShot', side_effect=lambda _, cb: callbacks.append(cb)),
        patch('picard.ui.mainwindow.QtWidgets.QMessageBox', return_value=dialog),
    ):
        MainWindow._set_profile_enabled(window, 'p1', True)
        # Profile settings cannot be committed before the user accepts.
        assert config.profiles['user_profiles'][0]['enabled'] is False
        assert config.setting.profiles_override is None
        window.profile_quick_selector_menu.close.assert_called_once()
        window.options_menu.close.assert_called_once()
        assert len(callbacks) == 1
        MainWindow._check_pending_profile_scripts(window)
        window.tagger.warn_about_unknown_script_functions.assert_not_called()
        callbacks.pop()()

    assert window._profile_script_check_pending
    window._schedule_profile_script_check.assert_called_once()
    assert config.profiles['user_profiles'][0]['enabled'] is accept
    assert '$missingprofile' in dialog.setInformativeText.call_args.args[0]
    assert '$missingnaming' not in dialog.setInformativeText.call_args.args[0]
    window.profile_quick_selector_menu.isVisible.return_value = False
    window.file_naming_scripts_menu = Mock(spec=QtWidgets.QMenu)
    window.file_naming_scripts_menu.isVisible.return_value = False
    window.quick_settings_menu = Mock(spec=QtWidgets.QMenu)
    window.quick_settings_menu.isVisible.return_value = False
    window.options_menu.isVisible.return_value = False
    MainWindow._check_pending_profile_scripts(window)
    window.tagger.warn_about_unknown_script_functions.assert_called_once()
    if accept:
        window.tagger.acknowledge_unknown_script_functions.assert_called_once_with(
            {('scripting', 'Profile', '$missingprofile')}
        )
        window._reset_option_menu_state.assert_called_once()
    else:
        window._make_profile_selector_menu.assert_called_once()
        window._reset_option_menu_state.assert_not_called()


def test_profile_without_new_unknown_functions_applies_immediately(tmp_path):
    config = _profile_config(tmp_path, profile_script='%title%')
    window = _profile_test_window()
    with patch('picard.ui.mainwindow.get_config', return_value=config):
        MainWindow._set_profile_enabled(window, 'p1', True)
    assert config.profiles['user_profiles'][0]['enabled'] is True
    assert window._pending_profile_change is None
    window.profile_quick_selector_menu.close.assert_not_called()
    window._reset_option_menu_state.assert_called_once()


def test_pending_script_check_waits_for_profile_menu_to_close(qapp):
    window = _profile_test_window()
    window._profile_script_check_pending = True
    window._check_pending_profile_scripts = lambda: MainWindow._check_pending_profile_scripts(window)
    window.quick_settings_menu = Mock(spec=QtWidgets.QMenu)
    window.file_naming_scripts_menu = Mock(spec=QtWidgets.QMenu)
    for menu in (window.quick_settings_menu, window.file_naming_scripts_menu, window.options_menu):
        menu.isVisible.return_value = False

    window.profile_quick_selector_menu.isVisible.return_value = True
    MainWindow._schedule_profile_script_check(window)
    qapp.processEvents()
    window.tagger.warn_about_unknown_script_functions.assert_not_called()

    # aboutToHide schedules the callback before Qt marks the menu hidden.
    MainWindow._schedule_profile_script_check(window)
    window.profile_quick_selector_menu.isVisible.return_value = False
    qapp.processEvents()
    window.tagger.warn_about_unknown_script_functions.assert_called_once_with()


def test_disabling_profile_can_require_confirmation(tmp_path):
    config = _profile_config(tmp_path, base_script='$missingbase()', profile_script='%title%')
    config.profiles['user_profiles'] = [{'id': 'p1', 'enabled': True, 'title': 'My Profile'}]
    window = _profile_test_window()
    callbacks = []
    dialog = Mock(spec=QtWidgets.QMessageBox)
    dialog.clickedButton.return_value = None
    with (
        patch('picard.ui.mainwindow.get_config', return_value=config),
        patch('picard.ui.mainwindow.QtCore.QTimer.singleShot', side_effect=lambda _, cb: callbacks.append(cb)),
        patch('picard.ui.mainwindow.QtWidgets.QMessageBox', return_value=dialog),
    ):
        MainWindow._set_profile_enabled(window, 'p1', False)
        assert config.profiles['user_profiles'][0]['enabled'] is True
        callbacks.pop()()
    assert config.profiles['user_profiles'][0]['enabled'] is True
    assert '$missingbase' in dialog.setInformativeText.call_args.args[0]


def test_profile_preview_restores_existing_overrides(tmp_path):
    config = _profile_config(tmp_path)
    config.setting.set_profiles_override([])
    window = _profile_test_window()
    with (
        patch('picard.ui.mainwindow.get_config', return_value=config),
        patch('picard.ui.mainwindow.QtCore.QTimer.singleShot'),
    ):
        MainWindow._set_profile_enabled(window, 'p1', True)
    assert config.setting.profiles_override == []


def test_acknowledge_unknown_script_functions():
    tagger = Mock(spec=Tagger)
    tagger._unknown_script_errors = set()
    Tagger.acknowledge_unknown_script_functions(tagger, {('scripting', 'Profile', '$missing')})
    assert tagger._unknown_script_errors == {('scripting', 'Profile', '$missing')}


@pytest.mark.parametrize('result', [QtWidgets.QDialog.DialogCode.Accepted, QtWidgets.QDialog.DialogCode.Rejected])
def test_options_close_rechecks_scripts(result):
    window = Mock(spec=MainWindow)
    window.tagger = Mock(spec=Tagger)
    with patch('picard.ui.mainwindow.QtCore.QTimer.singleShot', side_effect=lambda _, callback: callback()):
        MainWindow._options_closed(window, result)
    window.tagger.warn_about_unknown_script_functions.assert_called_once_with(
        settings_applied=result == QtWidgets.QDialog.DialogCode.Accepted
    )


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


def test_file_naming_selection_rechecks_after_options_menu_closes(qapp, tmp_path):
    config = Config.from_file(None, str(tmp_path / 'picard.ini'))
    config.setting['rename_files'] = True
    config.setting['move_files'] = False
    config.setting['file_renaming_scripts'] = {
        'valid': {'script': '%title%'},
        'broken': {'script': '$missingnaming()'},
    }
    config.setting['active_file_naming_script_id'] = 'valid'

    window = Mock(spec=MainWindow)
    window.tagger = Mock(spec=Tagger)
    window._profile_script_check_pending = False
    window.profile_quick_selector_menu = Mock(spec=QtWidgets.QMenu)
    window.file_naming_scripts_menu = Mock(spec=QtWidgets.QMenu)
    window.options_menu = Mock(spec=QtWidgets.QMenu)
    window.profile_quick_selector_menu.isVisible.return_value = False
    window._pending_profile_change = None
    window.quick_settings_menu = Mock(spec=QtWidgets.QMenu)
    window.quick_settings_menu.isVisible.return_value = False
    window.file_naming_scripts_menu.isVisible.return_value = True
    window.options_menu.isVisible.return_value = True
    window._schedule_profile_script_check = lambda: MainWindow._schedule_profile_script_check(window)
    window._check_pending_profile_scripts = lambda: MainWindow._check_pending_profile_scripts(window)
    observed = []
    window.tagger.warn_about_unknown_script_functions.side_effect = lambda: observed.append(
        list(iter_unknown_script_functions(config))
    )

    with patch('picard.ui.mainwindow.get_config', return_value=config):
        MainWindow._select_new_naming_script(window, 'broken')
        qapp.processEvents()
        assert not observed

        window.file_naming_scripts_menu.isVisible.return_value = False
        window._schedule_profile_script_check()
        qapp.processEvents()
        assert not observed

        window.options_menu.isVisible.return_value = False
        window._schedule_profile_script_check()
        qapp.processEvents()
        assert observed == [[('filerenaming', 'File naming script', '$missingnaming')]]

        config.setting['rename_files'] = False
        MainWindow._select_new_naming_script(window, 'valid')
        qapp.processEvents()
        MainWindow._select_new_naming_script(window, 'broken')
        qapp.processEvents()
        assert observed[-1] == []


@pytest.mark.parametrize(
    ('setting', 'expected'),
    [
        ('rename_files', ('filerenaming', 'File naming script', '$missingnaming')),
        ('move_files', ('filerenaming', 'File naming script', '$missingnaming')),
        ('save_images_to_files', ('cover', 'Cover art naming script', '$missingcover')),
        ('enable_tagger_scripts', ('scripting', 'Tagging', '$missingtagging')),
    ],
)
def test_quick_setting_rechecks_active_scripts_after_menu_closes(qapp, tmp_path, setting, expected):
    config = Config.from_file(None, str(tmp_path / 'picard.ini'))
    for key in ('rename_files', 'move_files', 'save_images_to_files', 'enable_tagger_scripts'):
        config.setting[key] = False
    config.setting['file_renaming_scripts'] = {'broken': {'script': '$missingnaming()'}}
    config.setting['active_file_naming_script_id'] = 'broken'
    config.setting['cover_image_filename'] = '$missingcover()'
    config.setting['list_of_scripts'] = [(0, 'Tagging', True, '$missingtagging()')]

    window = _profile_test_window()
    window.file_naming_scripts_menu = Mock(spec=QtWidgets.QMenu)
    window.quick_settings_menu = Mock(spec=QtWidgets.QMenu)
    for menu in (window.profile_quick_selector_menu, window.file_naming_scripts_menu, window.options_menu):
        menu.isVisible.return_value = False
    window.quick_settings_menu.isVisible.return_value = True
    window._schedule_profile_script_check = lambda: MainWindow._schedule_profile_script_check(window)
    window._check_pending_profile_scripts = lambda: MainWindow._check_pending_profile_scripts(window)
    observed = []
    window.tagger.warn_about_unknown_script_functions.side_effect = lambda: observed.append(
        list(iter_unknown_script_functions(config))
    )
    with patch('picard.ui.mainwindow.get_config', return_value=config):
        MainWindow._toggle_quick_setting(window, setting)
        qapp.processEvents()
        assert observed == []
        window._schedule_profile_script_check()
        window.quick_settings_menu.isVisible.return_value = False
        qapp.processEvents()
        assert observed == [[expected]]

        # Also refresh the warning history when the script becomes inactive.
        MainWindow._toggle_quick_setting(window, setting)
        qapp.processEvents()
        assert observed == [[expected], []]

        # Turning the setting on and off within one menu visit only checks the final state.
        window.quick_settings_menu.isVisible.return_value = True
        MainWindow._toggle_quick_setting(window, setting)
        qapp.processEvents()
        MainWindow._toggle_quick_setting(window, setting)
        qapp.processEvents()
        window._schedule_profile_script_check()
        window.quick_settings_menu.isVisible.return_value = False
        qapp.processEvents()
        assert observed == [[expected], [], []]


@pytest.mark.parametrize('finish', [False, True])
def test_setup_wizard_warns_about_scripts_activated_on_finish(qapp, tmp_path, finish):
    config = Config.from_file(None, str(tmp_path / 'wizard.ini'))
    config.setting['rename_files'] = False
    config.setting['move_files'] = False
    config.setting['save_images_to_files'] = False
    config.setting['file_renaming_scripts'] = {'broken': {'script': '$missingnaming()'}}
    config.setting['active_file_naming_script_id'] = 'broken'
    config.setting['cover_image_filename'] = '$missingcover()'
    window = Mock(spec=MainWindow)
    window.tagger = Mock(spec=Tagger)
    window.tagger.window = None
    window.tagger._unknown_script_errors = set()
    window.tagger.warn_about_unknown_script_functions.side_effect = lambda: Tagger.warn_about_unknown_script_functions(
        window.tagger, config
    )
    with (
        patch('picard.ui.setupwizard.get_config', return_value=config),
        patch.object(SetupWizard, 'PAGES', (FileOrganizationPage, CoverArtPage)),
    ):
        wizard = SetupWizard()

        organization, cover_art = (wizard.page(page_id) for page_id in wizard.pageIds())
        assert isinstance(organization, FileOrganizationPage)
        assert isinstance(cover_art, CoverArtPage)
        button_type = (
            QtWidgets.QWizard.WizardButton.FinishButton if finish else QtWidgets.QWizard.WizardButton.CancelButton
        )
        button = wizard.button(button_type)
        assert button is not None

        def choose_settings():
            organization.rename_checkbox.set_checked(True)
            wizard.next()
            cover_art.save_to_files_checkbox.set_checked(True)
            button.click()

        with (
            patch('picard.ui.mainwindow.SetupWizard', return_value=wizard),
            patch('picard.tagger.QtWidgets.QMessageBox') as warning,
        ):
            QtCore.QTimer.singleShot(0, choose_settings)
            MainWindow.show_setup_wizard(window, force=True)
            qapp.processEvents()
            assert config.setting['rename_files'] is finish
            assert config.setting['save_images_to_files'] is finish
            if finish:
                warning.return_value.exec.assert_called_once()
                message = warning.return_value.setInformativeText.call_args.args[0]
                assert 'File naming script: $missingnaming' in message
                assert 'Cover art naming script: $missingcover' in message
            else:
                window.tagger.warn_about_unknown_script_functions.assert_not_called()
        wizard.deleteLater()


def test_scripting_options_can_save_unavailable_plugin_functions():
    page = Mock()
    script_item = Mock()
    page.ui.script_list.selectedItems.return_value = [script_item]
    page.ui.tagger_script.toPlainText.return_value = '$missing_test_plugin_function_3467()'
    page.check.side_effect = lambda **kwargs: ScriptingOptionsPage.check(page, **kwargs)

    # The editor still shows the missing-function error, but does not mark
    # the script as invalid in a way that blocks Make It So!.
    ScriptingOptionsPage.live_update_and_check(page)
    assert script_item.has_error is False
    page.ui.script_error.show.assert_called_once()
    assert 'Unknown function' in page.ui.script_error.setText.call_args.args[0]

    # Saving the options must succeed so the post-save warning can appear.
    ScriptingOptionsPage.check(page)

    # Unrelated syntax errors must still prevent saving invalid scripts.
    for invalid in ('%', '$()', '$missing(', '$missing()%unfinished', '$missing($missingnested()'):
        page.ui.tagger_script.toPlainText.return_value = invalid
        with pytest.raises(ScriptCheckError):
            ScriptingOptionsPage.check(page)


def test_missing_outer_function_does_not_hide_invalid_inner_argument_count():
    page = Mock()
    page.ui.tagger_script.toPlainText.return_value = '$missing($lower(a,b))'
    with pytest.raises(ScriptCheckError) as error:
        ScriptingOptionsPage.check(page)
    assert 'Wrong number of arguments for $lower' in error.value.info


def test_options_accept_saves_profile_script_with_disabled_function(qapp, tmp_path):
    config = _profile_config(tmp_path)
    config.profiles['user_profiles'] = [{'id': 'p1', 'enabled': True, 'title': 'Profile'}]
    script = SimpleNamespace(pos=0, enabled=True, name='Decade', content='$decade(%date%)')
    page = Mock(NAME='scripting', SORT_ORDER=1, loaded=True)
    page.ui.tagger_script.toPlainText.return_value = script.content
    page.ui.enable_tagger_scripts.isChecked.return_value = True
    page.ui.script_list.currentRow.return_value = 0
    page._all_scripts.return_value = [script]
    page.check.side_effect = lambda: ScriptingOptionsPage.check(page)
    page.save.side_effect = lambda: ScriptingOptionsPage.save(page)

    # Exercise OptionsDialog.accept and its finished signal with only the relevant pages loaded.
    dialog = OptionsDialog.__new__(OptionsDialog)
    QtWidgets.QDialog.__init__(dialog)
    dialog._page_instances = {'profiles': Mock(NAME='profiles', SORT_ORDER=0, loaded=True), 'scripting': page}
    window = Mock(spec=MainWindow)
    window.tagger = Mock(spec=Tagger)
    window.tagger._unknown_script_errors = set()
    window.tagger.window = window
    window.tagger.warn_about_unknown_script_functions.side_effect = lambda **kwargs: (
        Tagger.warn_about_unknown_script_functions(window.tagger, config, **kwargs)
    )
    dialog.finished.connect(lambda result: MainWindow._options_closed(window, result))
    with (
        patch('picard.ui.options.dialog.get_config', return_value=config),
        patch('picard.ui.options.scripting.get_config', return_value=config),
        patch('picard.script.get_config', return_value=config),
        patch('picard.tagger.QtWidgets.QMessageBox') as warning,
    ):
        dialog.accept()
        assert dialog.result() == QtWidgets.QDialog.DialogCode.Accepted
        assert config.setting['list_of_scripts'] == [(0, 'Decade', True, script.content)]
        warning.assert_not_called()
        qapp.processEvents()
        warning.return_value.exec.assert_called_once()
        assert 'have been applied' in warning.return_value.setText.call_args.args[0]
        assert 'Decade: $decade' in warning.return_value.setInformativeText.call_args.args[0]
