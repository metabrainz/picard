# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2017-2018 Wieland Hoffmann
# Copyright (C) 2018, 2020-2026 Laurent Monin
# Copyright (C) 2019-2026 Philipp Wolfer
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from PyQt6.QtCore import QUrl

from test.picardtestcase import PicardTestCase

from picard.webservice.utils import (
    host_port_to_url,
    hostkey_from_url,
    port_from_qurl,
)


class WebServiceUtilsTest(PicardTestCase):
    def test_port_from_qurl_http(self):
        self.assertEqual(port_from_qurl(QUrl('http://example.org')), 80)

    def test_port_from_qurl_http_other(self):
        self.assertEqual(port_from_qurl(QUrl('http://example.org:666')), 666)

    def test_port_from_qurl_https(self):
        self.assertEqual(port_from_qurl(QUrl('https://example.org')), 443)

    def test_port_from_qurl_https_other(self):
        self.assertEqual(port_from_qurl(QUrl('https://example.org:666')), 666)

    def test_port_from_qurl_exception(self):
        with self.assertRaises(AttributeError):
            port_from_qurl('xxx')

    def test_hostkey_from_qurl_http(self):
        self.assertEqual(hostkey_from_url(QUrl('http://example.org')), ('example.org', 80))

    def test_hostkey_from_url_https_other(self):
        self.assertEqual(hostkey_from_url('https://example.org:666'), ('example.org', 666))

    def test_host_port_to_url_http_80(self):
        self.assertEqual(
            host_port_to_url('example.org', 80).toString(),
            'http://example.org',
        )

    def test_host_port_to_url_https_443(self):
        self.assertEqual(
            host_port_to_url('example.org', 443).toString(),
            'https://example.org',
        )

    def test_host_port_to_url_https_scheme_80(self):
        self.assertEqual(
            host_port_to_url('example.org', 80, scheme='https').toString(),
            'https://example.org:80',
        )

    def test_host_port_to_url_http_666_with_path(self):
        self.assertEqual(
            host_port_to_url('example.org', 666, path='/abc').toString(),
            'http://example.org:666/abc',
        )
