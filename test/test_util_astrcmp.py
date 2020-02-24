# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Lukáš Lalinský
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2017-2018 Wieland Hoffmann
# Copyright (C) 2018 Laurent Monin
# Copyright (C) 2018-2019 Philipp Wolfer
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


import unittest

from test.picardtestcase import PicardTestCase

from picard.util.astrcmp import astrcmp_py


try:
    from picard.util.astrcmp import astrcmp_c
except ImportError:
    astrcmp_c = None


class AstrcmpBase(object):
    func = None

    def test_astrcmp(self):
        astrcmp = self.__class__.func
        self.assertAlmostEqual(0.0, astrcmp(u"", u""))
        self.assertAlmostEqual(0.0, astrcmp(u"a", u""))
        self.assertAlmostEqual(0.0, astrcmp(u"", u"a"))
        self.assertAlmostEqual(1.0, astrcmp(u"a", u"a"))
        self.assertAlmostEqual(0.0, astrcmp(u"a", u"b"))
        self.assertAlmostEqual(0.0, astrcmp(u"ab", u"ba"))
        self.assertAlmostEqual(0.7083333333333333, astrcmp(u"The Great Gig in the Sky", u"Great Gig In The sky"))


class AstrcmpCTest(AstrcmpBase, PicardTestCase):
    func = astrcmp_c

    @unittest.skipIf(astrcmp_c is None, "The _astrcmp C extension module has not been compiled")
    def test_astrcmp(self):
        super().test_astrcmp()


class AstrcmpPyTest(AstrcmpBase, PicardTestCase):
    func = astrcmp_py
