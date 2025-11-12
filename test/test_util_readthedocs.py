# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Bob Swift
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

from picard.const import (
    DOCS_SERVER_URL,
    READTHEDOCS_BASE_LANGUAGE,
    READTHEDOCS_BASE_VERSION,
)
from picard.util import get_url
from picard.util.readthedocs import ReadTheDocs
from picard.version import Version


class MyTestCase:
    def __init__(self, language: str, language_used: str, version: Version, version_used: str):
        self.language = language
        self.language_used = language_used
        self.version = version
        self.version_used = version_used
        self.version_text = version.short_str()


class TestReadTheDocs(PicardTestCase):
    """Test the ReadTheDocs module"""

    def setUp(self):
        """Save current state of ReadTheDocs settings"""
        super().setUp()
        self.save_webservice = ReadTheDocs._webservice
        self.save_languages_api = ReadTheDocs._languages_api
        self.save_versions_api = ReadTheDocs._versions_api
        self.save_matched_language = ReadTheDocs.matched_language
        self.save_matched_version = ReadTheDocs.matched_version
        self.default_language_set = set([READTHEDOCS_BASE_LANGUAGE])
        self.default_version_set = set([READTHEDOCS_BASE_VERSION])
        ReadTheDocs._webservice = None  # Ensure no internet connection is used during testing

    def tearDown(self):
        """Restore original state of ReadTheDocs settings"""
        ReadTheDocs._webservice = self.save_webservice
        ReadTheDocs._languages_api = self.save_languages_api
        ReadTheDocs._versions_api = self.save_versions_api
        ReadTheDocs.matched_language = self.save_matched_language
        ReadTheDocs.matched_version = self.save_matched_version
        super().tearDown()

    def test_languages_1(self):
        """Test default language"""
        ReadTheDocs._languages_api.available_items = set()

        self.assertEqual(ReadTheDocs._get_language('en'), 'en')
        self.assertEqual(ReadTheDocs._get_language('en_CA'), 'en')
        self.assertEqual(ReadTheDocs._get_language('fr'), 'en')
        self.assertEqual(ReadTheDocs._get_language('fr_CA'), 'en')

    def test_languages_2(self):
        """Test languages without additional locale code"""
        ReadTheDocs._languages_api.available_items = {'en', 'fr'}

        self.assertEqual(ReadTheDocs._get_language('en'), 'en')
        self.assertEqual(ReadTheDocs._get_language('en_CA'), 'en')
        self.assertEqual(ReadTheDocs._get_language('fr'), 'fr')
        self.assertEqual(ReadTheDocs._get_language('fr_CA'), 'fr')
        self.assertEqual(ReadTheDocs._get_language('de'), 'en')

    def test_languages_3(self):
        """Test languages with additional locale code"""
        ReadTheDocs._languages_api.available_items = {'en_CA', 'en_GB', 'fr_CA'}

        self.assertEqual(ReadTheDocs._get_language('en'), 'en_CA')
        self.assertEqual(ReadTheDocs._get_language('en_CA'), 'en_CA')
        self.assertEqual(ReadTheDocs._get_language('en_GB'), 'en_GB')
        self.assertEqual(ReadTheDocs._get_language('en_US'), 'en_CA')
        self.assertEqual(ReadTheDocs._get_language('fr'), 'fr_CA')
        self.assertEqual(ReadTheDocs._get_language('fr_CA'), 'fr_CA')

    def test_languages_4(self):
        """Test languages with language from QLocale"""
        ReadTheDocs._languages_api.available_items = {'en_CA', 'en_GB', 'fr_CA'}
        with patch('picard.util.readthedocs.QLocale.system') as mock_system:
            mock_system.return_value.name.return_value = 'en_US'
            self.assertEqual(ReadTheDocs._get_language(), 'en_CA')

    def test_versions_1(self):
        """Test default version"""
        ReadTheDocs._versions_api.available_items = set()
        self.assertEqual(ReadTheDocs._get_version(), READTHEDOCS_BASE_VERSION)
        self.assertEqual(ReadTheDocs._get_version(Version(1, 0, 0)), READTHEDOCS_BASE_VERSION)

    def test_versions_2(self):
        """Test version matching"""
        ReadTheDocs._versions_api.available_items = {'v2.0', 'v2.1'}
        self.assertEqual(ReadTheDocs._get_version(Version(1, 0, 0)), READTHEDOCS_BASE_VERSION)

        self.assertEqual(ReadTheDocs._get_version(Version(2, 0, 0)), 'v2.0')
        self.assertEqual(ReadTheDocs._get_version(Version(2, 0, 1)), 'v2.0')
        self.assertEqual(ReadTheDocs._get_version(Version(2, 0, 2, 'b', 1)), READTHEDOCS_BASE_VERSION)

        self.assertEqual(ReadTheDocs._get_version(Version(2, 1, 0)), 'v2.1')
        self.assertEqual(ReadTheDocs._get_version(Version(2, 1, 1)), 'v2.1')
        self.assertEqual(ReadTheDocs._get_version(Version(2, 1, 2, 'b', 1)), READTHEDOCS_BASE_VERSION)

        self.assertEqual(ReadTheDocs._get_version(Version(2, 2, 0)), READTHEDOCS_BASE_VERSION)
        self.assertEqual(ReadTheDocs._get_version(Version(3, 0, 0)), READTHEDOCS_BASE_VERSION)

    def test_parse_languages_1(self):
        """Test parsing languages response - throttled"""
        ReadTheDocs._languages_api.available_items = set()
        response = {'detail': ReadTheDocs.THROTTLED_MESSAGE}
        ReadTheDocs._languages_json_loaded(response=response, reply=None, error=False)
        self.assertEqual(ReadTheDocs._languages_api.available_items, set())

    def test_parse_languages_2(self):
        """Test parsing languages response - RTD error"""
        ReadTheDocs._languages_api.available_items = set()
        response = {'detail': 'RTD error'}
        ReadTheDocs._languages_json_loaded(response=response, reply=None, error=False)
        self.assertEqual(ReadTheDocs._languages_api.available_items, self.default_language_set)

    def test_parse_languages_3(self):
        """Test parsing languages response - No languages in results"""
        ReadTheDocs._languages_api.available_items = set()
        response = {'results': []}
        ReadTheDocs._languages_json_loaded(response=response, reply=None, error=False)
        self.assertEqual(ReadTheDocs._languages_api.available_items, self.default_language_set)

    def test_parse_languages_4(self):
        """Test parsing languages response - Languages in results"""
        ReadTheDocs._languages_api.available_items = set()
        response = {
            'results': [
                {'language': {'code': 'en_CA'}},
                {'language': {'code': 'en_GB'}},
                {'language': {'code': 'fr'}},
                {'language': {'code': 'fr_CA'}},
            ]
        }
        test_set = set([READTHEDOCS_BASE_LANGUAGE, 'en_CA', 'en_GB', 'fr', 'fr_CA'])
        ReadTheDocs._languages_json_loaded(response=response, reply=None, error=False)
        self.assertEqual(ReadTheDocs._languages_api.available_items, test_set)

    def test_parse_versions_1(self):
        """Test parsing versions response - throttled"""
        ReadTheDocs._versions_api.available_items = set()
        response = {'detail': ReadTheDocs.THROTTLED_MESSAGE}
        ReadTheDocs._versions_json_loaded(response=response, reply=None, error=False)
        self.assertEqual(ReadTheDocs._versions_api.available_items, set())

    def test_parse_versions_2(self):
        """Test parsing versions response - RTD error"""
        ReadTheDocs._versions_api.available_items = set()
        response = {'detail': 'RTD error'}
        ReadTheDocs._versions_json_loaded(response=response, reply=None, error=False)
        self.assertEqual(ReadTheDocs._versions_api.available_items, self.default_version_set)

    def test_parse_versions_3(self):
        """Test parsing versions response - No versions in results"""
        ReadTheDocs._versions_api.available_items = set()
        response = {'results': []}
        ReadTheDocs._versions_json_loaded(response=response, reply=None, error=False)
        self.assertEqual(ReadTheDocs._versions_api.available_items, self.default_version_set)

    def test_parse_versions_4(self):
        """Test parsing versions response - Both active and inactive versions in results"""
        ReadTheDocs._versions_api.available_items = set()
        response = {
            'results': [
                {'active': True, 'slug': 'v1.0'},
                {'active': True, 'slug': 'v1.1'},
                {'active': True, 'slug': 'v2.0'},
                {'active': False, 'slug': 'v3.0'},
                {'active': True, 'slug': 'stable'},
            ]
        }
        test_set = set([READTHEDOCS_BASE_VERSION, 'v1.0', 'v1.1', 'v2.0', 'stable'])
        ReadTheDocs._versions_json_loaded(response=response, reply=None, error=False)
        self.assertEqual(ReadTheDocs._versions_api.available_items, test_set)

    def test_documentation_items(self):
        """Test documentation items are properly updated with version and language changes"""
        ReadTheDocs._versions_api.available_items = {'v1.0', 'v2.0', 'v2.1', 'stable', 'latest'}
        ReadTheDocs._languages_api.available_items = {'en', 'fr'}

        for testcase in [
            MyTestCase('en_CA', 'en', Version(2, 0, 0), 'v2.0'),
            MyTestCase('fr', 'fr', Version(2, 1, 0), 'v2.1'),
            MyTestCase('de', READTHEDOCS_BASE_LANGUAGE, Version(2, 1, 0), 'v2.1'),
            MyTestCase(
                READTHEDOCS_BASE_LANGUAGE, READTHEDOCS_BASE_LANGUAGE, Version(3, 0, 0), READTHEDOCS_BASE_VERSION
            ),
        ]:
            with patch('picard.util.readthedocs.QLocale.system') as mock_system:
                mock_system.return_value.name.return_value = testcase.language
                with patch('picard.util.readthedocs.PICARD_VERSION', testcase.version):
                    test_text = f"Testing language='{testcase.language}' and version='{testcase.version_text}'"

                    ReadTheDocs.matched_language = ReadTheDocs._get_language()
                    ReadTheDocs.matched_version = ReadTheDocs._get_version()

                    base = f"{DOCS_SERVER_URL}{testcase.language_used}/{testcase.version_used}"

                    self.assertEqual(ReadTheDocs.matched_language, testcase.language_used, test_text)
                    self.assertEqual(ReadTheDocs.matched_version, testcase.version_used, test_text)
                    self.assertEqual(
                        get_url('documentation_server'),
                        f"{DOCS_SERVER_URL}{testcase.language_used}/{READTHEDOCS_BASE_VERSION}/",
                        test_text,
                    )
                    self.assertEqual(get_url('documentation'), base, test_text)
                    self.assertEqual(
                        get_url('troubleshooting'),
                        f"{base}/troubleshooting/troubleshooting.html",
                        test_text,
                    )
                    self.assertEqual(get_url('doc_options'), f"{base}/config/configuration.html", test_text)
                    self.assertEqual(get_url('doc_scripting'), f"{base}/extending/scripting.html", test_text)
                    self.assertEqual(
                        get_url('doc_tags_from_filenames'),
                        f"{base}/usage/tags_from_file_names.html",
                        test_text,
                    )
                    self.assertEqual(
                        get_url('doc_naming_script_edit'),
                        f"{base}/config/options_filerenaming_editor.html",
                        test_text,
                    )
                    self.assertEqual(
                        get_url('/test.html'),
                        f"{base}/test.html",
                        test_text,
                    )
