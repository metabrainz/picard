# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019, 2023-2024 Philipp Wolfer
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


import os
import shutil
import tempfile
import unittest
from unittest.mock import (
    call,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard import i18n


localedir = os.path.join(os.path.dirname(__file__), '..', 'locale')


class TestI18n(PicardTestCase):

    def test_missing_locales(self):
        tmplocaledir = tempfile.mkdtemp()

        def cleanup_tmplocale():
            shutil.rmtree(tmplocaledir)

        self.addCleanup(cleanup_tmplocale)
        locale_de = os.path.join(tmplocaledir, 'de', 'LC_MESSAGES', 'picard.mo')
        self.assertFalse(os.path.exists(locale_de), 'unexpected file %s' % locale_de)
        i18n.setup_gettext(tmplocaledir, 'de')
        self.assertEqual('foo', _('foo'))
        self.assertEqual('Country', _('Country'))
        self.assertEqual('Country', N_('Country'))
        self.assertEqual('%i image', ngettext('%i image', '%i images', 1))
        self.assertEqual('%i images', ngettext('%i image', '%i images', 2))
        self.assertEqual('Cassette', pgettext_attributes('medium_format', 'Cassette'))
        self.assertEqual('French', gettext_constants('French'))
        self.assertEqual('France', gettext_countries('France'))

    @unittest.skipUnless(os.path.exists(os.path.join(localedir, 'de')),
        'Test requires locales to be built with "python setup.py build_locales -i"')
    def test_existing_locales(self):
        locale_de = os.path.join(localedir, 'de', 'LC_MESSAGES', 'picard.mo')
        self.assertTrue(os.path.exists(locale_de), 'expected file %s' % locale_de)

        gettext_before_setup = _
        i18n.setup_gettext(localedir, 'de')
        gettext_after_setup = _

        self.assertNotEqual(gettext_before_setup, gettext_after_setup)

        self.assertEqual('foo', _('foo'))
        self.assertEqual('Land', _('Country'))
        self.assertEqual('Country', N_('Country'))
        self.assertEqual('%i Bild', ngettext('%i image', '%i images', 1))
        self.assertEqual('%i Bilder', ngettext('%i image', '%i images', 2))
        self.assertEqual('Kassette', pgettext_attributes('medium_format', 'Cassette'))
        # self.assertEqual('Französisch', gettext_constants('French'))
        self.assertEqual('Frankreich', gettext_countries('France'))

    def test_sort_key(self):
        i18n.setup_gettext(localedir, 'de')
        self.assertLess(i18n.sort_key('äb'), i18n.sort_key('ac'))
        self.assertLess(i18n.sort_key('foo002'), i18n.sort_key('foo1'))
        self.assertLess(i18n.sort_key('002 foo'), i18n.sort_key('1 foo'))
        self.assertLess(i18n.sort_key('1'), i18n.sort_key('C'))
        self.assertLess(i18n.sort_key(''), i18n.sort_key('0'))
        self.assertLess(i18n.sort_key('\0'), i18n.sort_key('0'))
        self.assertLess(i18n.sort_key('0'), i18n.sort_key('00'))
        self.assertLess(i18n.sort_key('foo1', numeric=True), i18n.sort_key('foo002', numeric=True))
        self.assertLess(i18n.sort_key('004', numeric=True), i18n.sort_key('5', numeric=True))
        self.assertLess(i18n.sort_key('0042', numeric=True), i18n.sort_key('50', numeric=True))
        self.assertLess(i18n.sort_key('5', numeric=True), i18n.sort_key('0042', numeric=True))
        self.assertLess(i18n.sort_key('99', numeric=True), i18n.sort_key('100', numeric=True))

    def test_sort_key_numbers_different_scripts(self):
        i18n.setup_gettext(localedir, 'en')
        for four in ('4', '𝟜', '٤', '๔'):
            self.assertLess(
                i18n.sort_key('3', numeric=True), i18n.sort_key(four, numeric=True),
                msg=f'3 < {four}'
            )
            self.assertLess(
                i18n.sort_key(four, numeric=True), i18n.sort_key('5', numeric=True),
                msg=f'{four} < 5'
            )


@patch('locale.getpreferredencoding', autospec=True)
class TestTryEncodingsLocales(PicardTestCase):
    def test_try_encodings_iso(self, locale_getpreferredencoding_mock):
        locale_getpreferredencoding_mock.return_value = 'ISO-8859-1'
        result = tuple(i18n._try_encodings())
        expected = ('ISO-8859-1', 'UTF-8', None)
        self.assertEqual(expected, result)
        locale_getpreferredencoding_mock.assert_called_once()

    def test_try_encodings_utf8(self, locale_getpreferredencoding_mock):
        locale_getpreferredencoding_mock.return_value = 'UTF-8'
        result = tuple(i18n._try_encodings())
        expected = ('UTF-8', None)
        self.assertEqual(expected, result)
        locale_getpreferredencoding_mock.assert_called_once()

    @patch('locale.normalize', autospec=True)
    def test_try_locales_utf8_en(self, locale_nomalize_mock, locale_getpreferredencoding_mock):
        locale_getpreferredencoding_mock.return_value = 'UTF-8'
        locale_nomalize_mock.return_value = 'en_US.UTF-8'
        result = tuple(i18n._try_locales('en'))
        expected = ('en_US.UTF-8', 'en')
        self.assertEqual(expected, result)
        locale_getpreferredencoding_mock.assert_called_once()
        calls = [call('en.UTF-8')]
        locale_nomalize_mock.assert_has_calls(calls)

    @patch('locale.normalize', autospec=True)
    def test_try_locales_iso_en(self, locale_nomalize_mock, locale_getpreferredencoding_mock):
        locale_getpreferredencoding_mock.return_value = 'ISO-8859-1'
        locale_nomalize_mock.side_effect = lambda x: x.lower()
        result = tuple(i18n._try_locales('EN'))
        expected = ('en.iso-8859-1', 'en.utf-8', 'EN')
        self.assertEqual(expected, result)
        locale_getpreferredencoding_mock.assert_called_once()
        calls = [call('EN.ISO-8859-1'), call('EN.UTF-8')]
        locale_nomalize_mock.assert_has_calls(calls)


class TestBcp47ToLocale(PicardTestCase):
    def test_language_with_region(self):
        self.assertEqual('en_US', i18n._bcp47_to_locale('en-US'))
        self.assertEqual('en_GB', i18n._bcp47_to_locale('en-GB'))
        self.assertEqual('pt_BR', i18n._bcp47_to_locale('pt-BR'))

    def test_language_with_script_and_region(self):
        self.assertEqual('zh_CN', i18n._bcp47_to_locale('zh-Hans-CN'))
        self.assertEqual('zh_TW', i18n._bcp47_to_locale('zh-Hant-TW'))

    @patch('locale.normalize', autospec=True)
    def test_bare_language_normalizes(self, locale_normalize_mock):
        locale_normalize_mock.return_value = 'en_US.ISO8859-1'
        self.assertEqual('en_US', i18n._bcp47_to_locale('en'))
        locale_normalize_mock.assert_called_once_with('en')

    @patch('locale.normalize', autospec=True)
    def test_bare_language_no_mapping(self, locale_normalize_mock):
        # locale.normalize returns input unchanged if no mapping exists
        locale_normalize_mock.return_value = 'xx'
        self.assertEqual('xx', i18n._bcp47_to_locale('xx'))
        locale_normalize_mock.assert_called_once_with('xx')

    def test_numeric_region(self):
        # UN M.49 numeric region codes (3 digits)
        self.assertEqual('es_419', i18n._bcp47_to_locale('es-419'))
