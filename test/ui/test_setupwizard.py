# Picard, the next-generation MusicBrainz tagger
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

from unittest.mock import (
    Mock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.config import get_config

from picard.ui.setupwizard import (
    MetadataPage,
    SetupWizard,
    UpdatesPage,
)


class TestSetupWizardUpdatesPage(PicardTestCase):
    """Tests for UpdatesPage.save_settings update-trigger guards.

    On builds without autoupdate, ``Tagger.updatecheckmanager`` does not exist,
    so ``save_settings`` must not trigger the program update check even if the
    stored config value is enabled.
    """

    def test_updates_page_registered(self):
        self.assertIn(UpdatesPage, SetupWizard.PAGES)

    def _make_page(self, autoupdate_enabled, plugin_manager):
        tagger = Mock()
        tagger.autoupdate_enabled = autoupdate_enabled
        tagger.get_plugin_manager.return_value = plugin_manager
        tagger.window = Mock()
        patcher = patch('picard.ui.setupwizard.tagger_instance', return_value=tagger)
        patcher.start()
        self.addCleanup(patcher.stop)
        return UpdatesPage(), tagger

    def test_autoupdate_disabled_does_not_trigger_update_check(self):
        # Config enabled (the default), but the build has autoupdate disabled.
        self.set_config_values(
            setting={
                'check_for_updates': True,
                'check_for_plugin_updates': False,
                'check_rtd_updates': False,
            }
        )
        config = get_config()
        page, tagger = self._make_page(autoupdate_enabled=False, plugin_manager=None)
        try:
            # The wizard calls initializePage() on every page as it is shown,
            # even for the hidden checkbox, so is_checked() reflects the stored
            # config value (True by default) at save time.
            page.initializePage()
            page.save_settings(config)
            # The crashing call must not happen when autoupdate is disabled.
            tagger.window._auto_update_check.assert_not_called()
        finally:
            page.deleteLater()

    def test_autoupdate_enabled_triggers_update_check(self):
        self.set_config_values(
            setting={
                'check_for_updates': True,
                'check_for_plugin_updates': False,
                'check_rtd_updates': False,
            }
        )
        config = get_config()
        page, tagger = self._make_page(autoupdate_enabled=True, plugin_manager=None)
        try:
            page.update_check_app.set_checked(True)
            page.save_settings(config)
            tagger.window._auto_update_check.assert_called_once()
        finally:
            page.deleteLater()

    def test_autoupdate_enabled_but_unchecked_does_not_trigger(self):
        self.set_config_values(
            setting={
                'check_for_updates': True,
                'check_for_plugin_updates': False,
                'check_rtd_updates': False,
            }
        )
        config = get_config()
        page, tagger = self._make_page(autoupdate_enabled=True, plugin_manager=None)
        try:
            page.update_check_app.set_checked(False)
            page.save_settings(config)
            tagger.window._auto_update_check.assert_not_called()
            self.assertFalse(config.setting['check_for_updates'])
        finally:
            page.deleteLater()


class TestSetupWizardMetadataPage(PicardTestCase):
    def test_metadata_page_registered(self):
        self.assertIn(MetadataPage, SetupWizard.PAGES)

    def test_initialize_reflects_config_disabled(self, *args):
        self._check_roundtrip(initial=False)

    def test_initialize_reflects_config_enabled(self, *args):
        self._check_roundtrip(initial=True)

    def _check_roundtrip(self, initial):
        self.set_config_values(setting={'track_ars': initial})
        config = get_config()
        page = MetadataPage()
        try:
            page.initializePage()
            self.assertEqual(page.track_ars_checkbox.is_checked(), initial)

            # Toggle and save; config should reflect the new value.
            page.track_ars_checkbox.set_checked(not initial)
            page.save_settings(config)
            self.assertEqual(config.setting['track_ars'], not initial)
        finally:
            page.deleteLater()

    def test_convert_punctuation_reflects_config_disabled(self, *args):
        self._check_convert_punctuation_roundtrip(initial=False)

    def test_convert_punctuation_reflects_config_enabled(self, *args):
        self._check_convert_punctuation_roundtrip(initial=True)

    def _check_convert_punctuation_roundtrip(self, initial):
        self.set_config_values(setting={'convert_punctuation': initial})
        config = get_config()
        page = MetadataPage()
        try:
            page.initializePage()
            self.assertEqual(page.convert_punctuation_checkbox.is_checked(), initial)

            page.convert_punctuation_checkbox.set_checked(not initial)
            page.save_settings(config)
            self.assertEqual(config.setting['convert_punctuation'], not initial)
        finally:
            page.deleteLater()
