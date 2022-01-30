# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Laurent Monin
# Copyright (C) 2021 Philipp Wolfer
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


from test.picardtestcase import PicardTestCase

from picard.const import MUSICBRAINZ_SERVERS
from picard.util.mbserver import (
    build_submission_url,
    get_submission_server,
    is_official_server,
)


class IsOfficialServerTest(PicardTestCase):

    def test_official(self):
        for host in MUSICBRAINZ_SERVERS:
            self.assertTrue(is_official_server(host))

    def test_not_official(self):
        self.assertFalse(is_official_server('test.musicbrainz.org'))
        self.assertFalse(is_official_server('example.com'))
        self.assertFalse(is_official_server('127.0.0.1'))
        self.assertFalse(is_official_server('localhost'))


class GetSubmissionServerTest(PicardTestCase):

    def test_official(self):
        for host in MUSICBRAINZ_SERVERS:
            self.set_config_values(setting={
                'server_host': host,
                'server_port': 80,
                'use_server_for_submission': False,
            })
            self.assertEqual((host, 443), get_submission_server())

    def test_use_unofficial(self):
        self.set_config_values(setting={
            'server_host': 'example.com',
            'server_port': 8042,
            'use_server_for_submission': True,
        })
        self.assertEqual(('example.com', 8042), get_submission_server())

    def test_unofficial_fallback(self):
        self.set_config_values(setting={
            'server_host': 'test.musicbrainz.org',
            'server_port': 80,
            'use_server_for_submission': False,
        })
        self.assertEqual((MUSICBRAINZ_SERVERS[0], 443), get_submission_server())

    def test_named_tuple(self):
        self.set_config_values(setting={
            'server_host': 'example.com',
            'server_port': 8042,
            'use_server_for_submission': True,
        })
        server = get_submission_server()
        self.assertEqual('example.com', server.host)
        self.assertEqual(8042, server.port)


class BuildSubmissionUrlTest(PicardTestCase):

    def test_official(self):
        for host in MUSICBRAINZ_SERVERS:
            self.set_config_values(setting={
                'server_host': host,
                'server_port': 80,
                'use_server_for_submission': False,
            })
            self.assertEqual('https://%s' % host, build_submission_url())
            self.assertEqual('https://%s/' % host, build_submission_url('/'))
            self.assertEqual('https://%s/some/path?foo=1&bar=baz' % host,
                build_submission_url('/some/path', {'foo': 1, 'bar': 'baz'}))

    def test_use_unofficial(self):
        self.set_config_values(setting={
            'server_host': 'example.com',
            'server_port': 8042,
            'use_server_for_submission': True,
        })
        self.assertEqual('http://example.com:8042', build_submission_url())
        self.assertEqual('http://example.com:8042/', build_submission_url('/'))
        self.assertEqual('http://example.com:8042/some/path?foo=1&bar=baz',
                build_submission_url('/some/path', {'foo': 1, 'bar': 'baz'}))

    def test_unofficial_fallback(self):
        self.set_config_values(setting={
            'server_host': 'test.musicbrainz.org',
            'server_port': 80,
            'use_server_for_submission': False,
        })
        self.assertEqual('https://musicbrainz.org', build_submission_url())
        self.assertEqual('https://musicbrainz.org/', build_submission_url('/'))
        self.assertEqual('https://musicbrainz.org/some/path?foo=1&bar=baz',
                build_submission_url('/some/path', {'foo': 1, 'bar': 'baz'}))
