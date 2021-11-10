# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020 Laurent Monin
# Copyright (C) 2020 Philipp Wolfer
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
            msgfmt = "for size %s, with sizes %r, got %r, expected %r"
            for size, expect in expectations.items():
                result = caa_url_fallback_list(size, thumbnails)
                self.assertEqual(result, expect, msg=msgfmt % (size, sizes, result, expect))

        # For historical reasons, caa web service returns 2 identical urls,
        # for 2 different keys (250/small, 500/large)
        # Here is an example of the json relevant part:
        # "thumbnails": {
        #   "250": "http://coverartarchive.org/release/d20247ad-940e-486d-948f-be4c17024ab9/24885128253-250.jpg",
        #   "500": "http://coverartarchive.org/release/d20247ad-940e-486d-948f-be4c17024ab9/24885128253-500.jpg",
        #   "1200": "http://coverartarchive.org/release/d20247ad-940e-486d-948f-be4c17024ab9/24885128253-1200.jpg",
        #   "large": "http://coverartarchive.org/release/d20247ad-940e-486d-948f-be4c17024ab9/24885128253-500.jpg",
        #   "small": "http://coverartarchive.org/release/d20247ad-940e-486d-948f-be4c17024ab9/24885128253-250.jpg"
        # },
        sizes = ("250", "500", "1200", "large", "small")
        expectations = {
            50:  [],
            250: ['url 250'],
            400: ['url 250'],
            500: ['url 500', 'url 250'],
            600: ['url 500', 'url 250'],
            1200: ['url 1200', 'url 500', 'url 250'],
            1500: ['url 1200', 'url 500', 'url 250'],
        }
        do_tests(sizes, expectations)

        # Some older releases have no 1200px thumbnail
        sizes = ("250", "500", "large", "small")
        expectations = {
            50:  [],
            250: ['url 250'],
            400: ['url 250'],
            500: ['url 500', 'url 250'],
            600: ['url 500', 'url 250'],
            1200: ['url 500', 'url 250'],
            1500: ['url 500', 'url 250'],
        }
        do_tests(sizes, expectations)

        # In the future, large and small might be removed or new size added
        # test if we can handle that (through size aliases)
        sizes = ("small", "large", "1200", "2000", "unknownsize")
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

        with self.assertRaises(TypeError):
            caa_url_fallback_list("not_an_integer", {"250": "url 250"})

        with self.assertRaises(AttributeError):
            caa_url_fallback_list(250, 666)
