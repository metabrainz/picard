# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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

"""Tests for PICARD-3399: styled browser integration auth response pages."""

from unittest.mock import patch

from test.picardtestcase import PicardTestCase

from picard.browser import auth_responses


class AuthResponsePagesTest(PicardTestCase):
    def test_success_page_is_html(self):
        page = auth_responses.success_page()
        self.assertIn('<!doctype html>', page)
        self.assertIn('<title>', page)
        self.assertIn('Authentication successful', page)

    def test_success_page_applies_status_colors(self):
        page = auth_responses.success_page()
        # The page applies role-based status colors in its own CSS.
        self.assertIn(auth_responses.COLORS.ok, page)
        self.assertIn(auth_responses.COLORS.failed, page)

    def test_success_page_shows_close_hint(self):
        page = auth_responses.success_page()
        self.assertIn('close this window', page.lower())

    def test_cancelled_page_is_html(self):
        page = auth_responses.cancelled_page()
        self.assertIn('<!doctype html>', page)
        self.assertIn('Authentication cancelled', page)

    def test_cancelled_page_distinct_from_success(self):
        success = auth_responses.success_page()
        cancelled = auth_responses.cancelled_page()
        self.assertNotEqual(success, cancelled)
        # Different status icons visually distinguish the two states.
        self.assertIn('\u2713', success)  # check mark
        self.assertIn('\u2717', cancelled)  # cross mark

    def test_pages_embed_logo(self):
        # Inject a controlled logo so the test does not depend on the shipped
        # asset, which may change over time.
        fake_logo = '<svg data-test="logo"></svg>'
        with patch.object(auth_responses, '_PICARD_LOGO_SVG', fake_logo):
            for page in (auth_responses.success_page(), auth_responses.cancelled_page()):
                self.assertIn('aria-label="MusicBrainz Picard"', page)
                self.assertIn(fake_logo, page)

    def test_logo_svg_accessor(self):
        svg = auth_responses.logo_svg()
        self.assertTrue(svg.startswith('<svg'))
        self.assertIn('</svg>', svg)

    def test_success_status_line_separate_from_detail(self):
        page = auth_responses.success_page()
        # The short status (with its icon) must stand alone on its own line,
        # separate from the detail paragraph.
        self.assertIn(
            '<p class="status ok"><span class="icon" aria-hidden="true">\u2713</span>Authentication successful.</p>',
            page,
        )
        self.assertIn('<p class="detail">Picard has been authorized.</p>', page)

    def test_cancelled_page_known_error_code_is_translated(self):
        # A known OAuth error code is mapped to a friendly message, not the raw
        # code echoed back.
        page = auth_responses.cancelled_page('access_denied')
        self.assertIn('Authorization was declined.', page)
        self.assertNotIn('access_denied', page)

    def test_cancelled_page_unknown_code_falls_back_to_description(self):
        page = auth_responses.cancelled_page('some_new_code', 'A detailed reason')
        self.assertIn('A detailed reason', page)

    def test_cancelled_page_unknown_code_without_description(self):
        page = auth_responses.cancelled_page('some_new_code')
        self.assertIn('some_new_code', page)

    def test_cancelled_page_no_error_info(self):
        page = auth_responses.cancelled_page()
        self.assertIn('Picard has not been authorized.', page)

    def test_cancelled_page_escapes_description(self):
        page = auth_responses.cancelled_page('unknown_code', '<script>alert(1)</script>')
        self.assertNotIn('<script>alert(1)</script>', page)
        self.assertIn('&lt;script&gt;', page)

    def test_cancelled_page_escapes_unknown_code(self):
        page = auth_responses.cancelled_page('<script>alert(1)</script>')
        self.assertNotIn('<script>alert(1)</script>', page)
        self.assertIn('&lt;script&gt;', page)

    def test_error_page_is_html(self):
        page = auth_responses.error_page()
        self.assertIn('<!doctype html>', page)
        self.assertIn('Authentication error', page)
        self.assertIn('\u2717', page)  # cross mark

    def test_error_page_custom_detail(self):
        page = auth_responses.error_page('Something specific went wrong')
        self.assertIn('Something specific went wrong', page)

    def test_error_page_escapes_detail(self):
        page = auth_responses.error_page('<script>alert(1)</script>')
        self.assertNotIn('<script>alert(1)</script>', page)
        self.assertIn('&lt;script&gt;', page)

    def test_pages_have_no_unfilled_placeholders(self):
        # The template uses str.format(); ensure no named field is left
        # unsubstituted in the rendered output.
        pages = (auth_responses.success_page(), auth_responses.cancelled_page(), auth_responses.error_page())
        for page in pages:
            for field in ('{title}', '{status}', '{detail}', '{icon}', '{status_class}', '{logo}', '{hint}'):
                self.assertNotIn(field, page)
