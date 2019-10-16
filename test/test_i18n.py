# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019, 2023 Philipp Wolfer
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

from test.picardtestcase import PicardTestCase

from picard import i18n


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
        self.assertEqual('France', gettext_countries('France'))
        self.assertEqual('Cassette', pgettext_attributes('medium_format', 'Cassette'))

    def test_existing_locales(self):
        localedir = os.path.join(os.path.dirname(__file__), '..', 'locale')
        locale_de = os.path.join(localedir, 'de', 'LC_MESSAGES', 'picard.mo')
        self.assertTrue(os.path.exists(locale_de), 'expected file %s' % locale_de)
        i18n.setup_gettext(localedir, 'de')
        self.assertEqual('foo', _('foo'))
        self.assertEqual('Land', _('Country'))
        self.assertEqual('Country', N_('Country'))
        self.assertEqual('%i Bild', ngettext('%i image', '%i images', 1))
        self.assertEqual('%i Bilder', ngettext('%i image', '%i images', 2))
        self.assertEqual('Frankreich', gettext_countries('France'))
        self.assertEqual('Kassette', pgettext_attributes('medium_format', 'Cassette'))
