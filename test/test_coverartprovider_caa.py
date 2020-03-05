# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020 Laurent Monin
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

from picard.coverart.providers.caa import caa_url_fallback_list


class CoverArtImageProviderCaaTest(PicardTestCase):
    def test_caa_url_fallback_list(self):
        def do_tests(sizes, expectations):
            # we create a dummy url named after matching size
            thumbnails = dict([(size, "url %s" % size) for size in sizes])
            for size, expect in expectations.items():
                result = caa_url_fallback_list(size, thumbnails)
                self.assertEqual(result, expect)

        sizes = ("250", "500", "1200", "large", "small")
        expectations = {
            50:  [],
            250: ['url small'],
            400: ['url small'],
            500: ['url large', 'url small'],
            600: ['url large', 'url small'],
            1200: ['url 1200', 'url large', 'url small'],
            1500: ['url 1200', 'url large', 'url small'],
        }
        do_tests(sizes, expectations)

        # no 1200px in thumbnails list
        sizes = ("250", "500", "large", "small")
        expectations = {
            50:  [],
            250: ['url small'],
            400: ['url small'],
            500: ['url large', 'url small'],
            600: ['url large', 'url small'],
            1200: ['url large', 'url small'],
            1500: ['url large', 'url small'],
        }
        do_tests(sizes, expectations)

        with self.assertRaises(TypeError):
            caa_url_fallback_list("not_an_integer", {"250": "url 250"})

        with self.assertRaises(TypeError):
            caa_url_fallback_list(250, 666)
