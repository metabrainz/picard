# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020-2021 Philipp Wolfer
# Copyright (C) 2020-2022, 2025 Laurent Monin
# Copyright (C) 2024 Giorgio Fontanive
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


from test.picardtestcase import PicardTestCase

from picard.coverart.providers.caa import (
    caa_image_types_accepted,
    caa_url_fallback_list,
)


class CoverArtImageProviderCaaTest(PicardTestCase):
    def test_caa_url_fallback_list(self):
        def do_tests(sizes, expectations):
            # we create a dummy url named after matching size
            thumbnails = {size: "url %s" % size for size in sizes}
            msgfmt = "for size %s, with sizes %r, got %r, expected %r"
            for size, expect in expectations.items():
                result = [thumbnail.url for thumbnail in caa_url_fallback_list(size, thumbnails)]
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
            50: [],
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
            50: [],
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
            50: [],
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


class CaaImageTypesAcceptedTest(PicardTestCase):
    """Regression tests for the CAA include/exclude type filtering.

    Contract (as described in the CAA types selector dialog):
      - An image with at least one type in the 'Include' list is a candidate,
        UNLESS it ALSO has any type found in the 'Exclude' list.
      - Images with a type in the 'Exclude' list are NEVER used (exclude wins).
      - Types in neither list are ignored when deciding.

    See https://community.metabrainz.org/t/artwork-downloads-from-caa/815842/
    The historical bug accepted images like ['front', 'booklet'] or
    ['back', 'spine'] even when 'booklet'/'spine' were in the exclude list,
    because the exclude set was subtracted from the include intersection rather
    than tested against the image's full type set.
    """

    def test_included_only(self):
        self.assertTrue(caa_image_types_accepted(['front'], {'front', 'back'}, set()))
        self.assertTrue(caa_image_types_accepted(['back'], {'front', 'back'}, set()))

    def test_not_included(self):
        # No matching include type -> rejected
        self.assertFalse(caa_image_types_accepted(['medium'], {'front', 'back'}, set()))
        self.assertFalse(caa_image_types_accepted(['booklet'], {'front', 'back'}, set()))

    def test_exclude_overrides_include(self):
        # These are the exact cases from the bug report: an image that has both
        # an included and an excluded type must be REJECTED.
        included = {'front', 'back'}
        excluded = {'booklet', 'spine', 'sticker', 'obi', 'raw/unedited', 'watermark'}
        self.assertFalse(caa_image_types_accepted(['front', 'booklet'], included, excluded))
        self.assertFalse(caa_image_types_accepted(['back', 'spine'], included, excluded))

    def test_pure_excluded(self):
        # Only an excluded type (and nothing included) -> rejected
        self.assertFalse(caa_image_types_accepted(['sticker'], {'front'}, {'sticker'}))

    def test_included_without_excluded_type(self):
        # Included type, and the image carries no excluded type -> accepted
        self.assertTrue(caa_image_types_accepted(['front'], {'front'}, {'booklet', 'spine'}))

    def test_exclude_not_in_include(self):
        # Exclude must veto even when the excluded type is not part of the
        # include list at all (the default exclude list contains such types).
        self.assertFalse(caa_image_types_accepted(['front', 'watermark'], {'front'}, {'watermark'}))

    def test_unknown_pseudo_type(self):
        # Images with no type get the pseudo type 'unknown'; accepted only if
        # 'unknown' is included and not excluded.
        self.assertTrue(caa_image_types_accepted(['unknown'], {'unknown'}, set()))
        self.assertFalse(caa_image_types_accepted(['unknown'], {'front'}, set()))
