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


from types import SimpleNamespace
from unittest.mock import patch

from test.picardtestcase import PicardTestCase

from picard.services import (
    TaggingServices,
    services,
    set_services_provider,
)


class TaggingServicesTest(PicardTestCase):
    def test_delegates_to_explicit_provider(self):
        provider = SimpleNamespace(
            webservice='WS',
            mb_api='MB',
            format_registry='FR',
            acoustidmanager='AM',
            isrc_submit_manager='ISM',
        )
        svc = TaggingServices(provider)
        self.assertEqual(svc.webservice, 'WS')
        self.assertEqual(svc.mb_api, 'MB')
        self.assertEqual(svc.format_registry, 'FR')
        self.assertEqual(svc.acoustidmanager, 'AM')
        self.assertEqual(svc.isrc_submit_manager, 'ISM')
        self.assertTrue(svc.available)

    def test_resolves_from_app_instance_when_no_provider(self):
        provider = SimpleNamespace(webservice='WS-from-app')
        with patch('picard.services.app_instance', return_value=provider):
            svc = TaggingServices()
            self.assertTrue(svc.available)
            self.assertEqual(svc.webservice, 'WS-from-app')

    def test_unavailable_without_provider_or_app(self):
        with patch('picard.services.app_instance', return_value=None):
            svc = TaggingServices()
            self.assertFalse(svc.available)
            with self.assertRaises(RuntimeError):
                _ = svc.webservice

    def test_unknown_attribute_raises_attribute_error(self):
        svc = TaggingServices(SimpleNamespace())
        with self.assertRaises(AttributeError):
            _ = svc.not_a_service

    def test_process_wide_accessor_is_stable(self):
        self.assertIs(services(), services())
        self.assertIsInstance(services(), TaggingServices)

    def test_set_services_provider_installs_and_clears(self):
        provider = SimpleNamespace(mb_api='installed-mb')
        self.addCleanup(set_services_provider, None)
        set_services_provider(provider)
        self.assertEqual(services().mb_api, 'installed-mb')
        # Clearing reverts to resolving from app_instance()
        set_services_provider(None)
        with patch('picard.services.app_instance', return_value=None):
            self.assertFalse(services().available)
