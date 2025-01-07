# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019, 2023-2024 Philipp Wolfer
# Copyright (C) 2023-2024 Laurent Monin
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

from picard.i18n import (
    N_,
    _try_encodings,
    _try_locales,
    gettext as _,
    gettext_constants,
    gettext_countries,
    ngettext,
    pgettext_attributes,
    setup_gettext,
    sort_key,
)


localedir = os.path.join(os.path.dirname(__file__), '..', 'locale')


class TestI18n(PicardTestCase):

    def test_missing_locales(self):
        tmplocaledir = tempfile.mkdtemp()

        def cleanup_tmplocale():
            shutil.rmtree(tmplocaledir)

        self.addCleanup(cleanup_tmplocale)
        locale_de = os.path.join(tmplocaledir, 'de', 'LC_MESSAGES', 'picard.mo')
        self.assertFalse(os.path.exists(locale_de), 'unexpected file %s' % locale_de)
        setup_gettext(tmplocaledir, 'de')
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

        setup_gettext(localedir, 'de')

        self.assertEqual('foo', _('foo'))
        self.assertEqual('Land', _('Country'))
        self.assertEqual('Country', N_('Country'))
        self.assertEqual('%i Bild', ngettext('%i image', '%i images', 1))
        self.assertEqual('%i Bilder', ngettext('%i image', '%i images', 2))
        self.assertEqual('Kassette', pgettext_attributes('medium_format', 'Cassette'))
        # self.assertEqual('Französisch', gettext_constants('French'))
        self.assertEqual('Frankreich', gettext_countries('France'))

    def test_gettext_handles_empty_string(self):
        setup_gettext(localedir, 'fr')
        self.assertEqual('', _(''))

    def test_sort_key(self):
        setup_gettext(localedir, 'de')
        self.assertLess(sort_key('äb'), sort_key('ac'))
        self.assertLess(sort_key('foo002'), sort_key('foo1'))
        self.assertLess(sort_key('002 foo'), sort_key('1 foo'))
        self.assertLess(sort_key('1'), sort_key('C'))
        self.assertLess(sort_key(''), sort_key('0'))
        self.assertLess(sort_key('\0'), sort_key('0'))
        self.assertLess(sort_key('0'), sort_key('00'))
        self.assertLess(sort_key('foo1', numeric=True), sort_key('foo002', numeric=True))
        self.assertLess(sort_key('004', numeric=True), sort_key('5', numeric=True))
        self.assertLess(sort_key('0042', numeric=True), sort_key('50', numeric=True))
        self.assertLess(sort_key('5', numeric=True), sort_key('0042', numeric=True))
        self.assertLess(sort_key('99', numeric=True), sort_key('100', numeric=True))

    def test_sort_key_numbers_different_scripts(self):
        setup_gettext(localedir, 'en')
        for four in ('4', '𝟜', '٤', '๔'):
            self.assertLess(
                sort_key('3', numeric=True), sort_key(four, numeric=True),
                msg=f'3 < {four}'
            )
            self.assertLess(
                sort_key(four, numeric=True), sort_key('5', numeric=True),
                msg=f'{four} < 5'
            )


@patch('locale.getpreferredencoding', autospec=True)
class TestTryEncodingsLocales(PicardTestCase):
    def test_try_encodings_iso(self, locale_getpreferredencoding_mock):
        locale_getpreferredencoding_mock.return_value = 'ISO-8859-1'
        result = tuple(_try_encodings())
        expected = ('ISO-8859-1', 'UTF-8', None)
        self.assertEqual(expected, result)
        locale_getpreferredencoding_mock.assert_called_once()

    def test_try_encodings_utf8(self, locale_getpreferredencoding_mock):
        locale_getpreferredencoding_mock.return_value = 'UTF-8'
        result = tuple(_try_encodings())
        expected = ('UTF-8', None)
        self.assertEqual(expected, result)
        locale_getpreferredencoding_mock.assert_called_once()

    @patch('locale.normalize', autospec=True)
    def test_try_locales_utf8_en(self, locale_nomalize_mock, locale_getpreferredencoding_mock):
        locale_getpreferredencoding_mock.return_value = 'UTF-8'
        locale_nomalize_mock.return_value = 'en_US.UTF-8'
        result = tuple(_try_locales('en'))
        expected = ('en_US.UTF-8', 'en')
        self.assertEqual(expected, result)
        locale_getpreferredencoding_mock.assert_called_once()
        calls = [call('en.UTF-8')]
        locale_nomalize_mock.assert_has_calls(calls)

    @patch('locale.normalize', autospec=True)
    def test_try_locales_iso_en(self, locale_nomalize_mock, locale_getpreferredencoding_mock):
        locale_getpreferredencoding_mock.return_value = 'ISO-8859-1'
        locale_nomalize_mock.side_effect = lambda x: x.lower()
        result = tuple(_try_locales('EN'))
        expected = ('en.iso-8859-1', 'en.utf-8', 'EN')
        self.assertEqual(expected, result)
        locale_getpreferredencoding_mock.assert_called_once()
        calls = [call('EN.ISO-8859-1'), call('EN.UTF-8')]
        locale_nomalize_mock.assert_has_calls(calls)
