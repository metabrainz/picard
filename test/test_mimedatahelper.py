# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Stevil Knevil
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


from PyQt6 import QtCore

from test.picardtestcase import PicardTestCase

import pytest

from picard.ui.metadatabox.mimedatahelper import MimeDataHelper


class MimeDataHelperTest(PicardTestCase):
    MIMETYPE_TSV = 'text/tab-separated-values'
    MIMETYPE_TEXT = 'text/plain'

    def test_register_none(self):
        helper = MimeDataHelper()
        helper.register(self.MIMETYPE_TEXT)
        self.assertTrue(helper.is_registered(self.MIMETYPE_TEXT))
        self.assertTrue(helper.encode_func(self.MIMETYPE_TEXT) is None)
        self.assertTrue(helper.decode_func(self.MIMETYPE_TEXT) is None)

    def test_register(self):
        helper = MimeDataHelper()
        helper.register(self.MIMETYPE_TEXT,
                        encode_func=lambda x: x,
                        decode_func=lambda x: x)
        self.assertTrue(helper.is_registered(self.MIMETYPE_TEXT))
        self.assertTrue(helper.encode_func(self.MIMETYPE_TEXT) is not None)
        self.assertTrue(helper.decode_func(self.MIMETYPE_TEXT) is not None)

    def test_reregister(self):
        helper = MimeDataHelper()
        helper.register(self.MIMETYPE_TEXT,
                        encode_func=lambda x: x,
                        decode_func=lambda x: x)
        with pytest.raises(ValueError):
            helper.register(self.MIMETYPE_TEXT,
                            encode_func=lambda x: x,
                            decode_func=lambda x: x)

    def test_non_callable(self):
        helper = MimeDataHelper()
        with pytest.raises(ValueError):
            helper.register(self.MIMETYPE_TEXT,
                            encode_func=1)

    def test_encode(self):
        helper = MimeDataHelper()
        result = self.MIMETYPE_TEXT + " encoded"
        helper.register(self.MIMETYPE_TEXT,
                        encode_func=lambda: result)
        fn = helper.encode_func(self.MIMETYPE_TEXT)
        self.assertTrue(fn() == result)

    def test_decode(self):
        helper = MimeDataHelper()
        result = self.MIMETYPE_TEXT + " decoded"
        helper.register(self.MIMETYPE_TEXT,
                        encode_func=lambda: result)
        fn = helper.encode_func(self.MIMETYPE_TEXT)
        self.assertTrue(fn() == result)

    def test_encode_generator(self):
        helper = MimeDataHelper()
        result = self.MIMETYPE_TEXT + " decoded"
        helper.register(self.MIMETYPE_TEXT,
                        encode_func=lambda: result)
        result = self.MIMETYPE_TSV + " decoded"
        helper.register(self.MIMETYPE_TSV,
                        encode_func=lambda: result)

        results = []
        for mimetype, encode_func in helper.encode_funcs():
            results.append((mimetype, encode_func()))
        self.assertTrue(len(results) == 2)
        self.assertTrue(results[0][0] == self.MIMETYPE_TEXT)
        self.assertTrue(results[1][0] == self.MIMETYPE_TSV)

    def test_decode_generator(self):
        mimedata = QtCore.QMimeData()
        helper = MimeDataHelper()

        txtresult = self.MIMETYPE_TEXT + " decoded"
        helper.register(self.MIMETYPE_TEXT,
                        decode_func=lambda: txtresult)
        mimedata.setData(self.MIMETYPE_TEXT, txtresult.encode())

        for fn in helper.decode_funcs(mimedata):
            self.assertTrue(fn() == txtresult)

    def test_decode_generator_sorted(self):
        mimedata = QtCore.QMimeData()
        helper = MimeDataHelper()
        txtresult = self.MIMETYPE_TEXT + " decoded"
        helper.register(self.MIMETYPE_TEXT,
                        decode_func=lambda: txtresult)

        tsvresult = self.MIMETYPE_TSV + " decoded"
        helper.register(self.MIMETYPE_TSV,
                        decode_func=lambda: tsvresult)
        mimedata.setData(self.MIMETYPE_TSV, tsvresult.encode())

        results = []
        for result in helper.decode_funcs(mimedata):
            results.append(result)
        self.assertTrue(len(results) == 1)
        self.assertTrue(results[0]() == tsvresult)
