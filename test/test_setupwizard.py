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

from test.picardtestcase import PicardTestCase

from picard.config import get_config

from picard.ui.setupwizard import (
    MetadataPage,
    SetupWizard,
)


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
