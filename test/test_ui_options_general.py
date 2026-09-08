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


from picard.config import get_config

import pytest

from picard.ui.options.general import GeneralOptionsPage


@pytest.fixture()
def general_options_page(qapp, patch_tagger_instance):
    tagger = patch_tagger_instance('picard.ui.options')
    oauth_manager = tagger.webservice.oauth_manager
    oauth_manager.is_authorized.return_value = True

    config = get_config()
    config.setting['server_host'] = 'musicbrainz.org'
    config.setting['server_port'] = 443
    config.setting['use_server_for_submission'] = False
    config.setting['enable_user_collections'] = False
    config.setting['remove_complete_albums_after_save'] = False

    page = GeneralOptionsPage()
    page.load()
    # Reset any calls made during construction/load.
    oauth_manager.reset_mock()
    oauth_manager.is_authorized.return_value = True
    return page


def _save_with_host(page, host):
    page.ui.server_host.setEditText(host)
    page.save()


def test_no_logout_when_host_unchanged(general_options_page):
    page = general_options_page
    oauth_manager = page.tagger.webservice.oauth_manager
    _save_with_host(page, 'musicbrainz.org')
    oauth_manager.forget_refresh_token.assert_not_called()
    oauth_manager.forget_access_token.assert_not_called()


def test_no_logout_between_official_servers(general_options_page):
    page = general_options_page
    oauth_manager = page.tagger.webservice.oauth_manager
    _save_with_host(page, 'beta.musicbrainz.org')
    oauth_manager.forget_refresh_token.assert_not_called()
    oauth_manager.forget_access_token.assert_not_called()


def test_logout_when_switching_to_unauthenticated_server(general_options_page):
    page = general_options_page
    oauth_manager = page.tagger.webservice.oauth_manager
    _save_with_host(page, 'test.musicbrainz.org')
    oauth_manager.forget_refresh_token.assert_called_once()
    oauth_manager.forget_access_token.assert_called_once()


def test_no_logout_when_switching_from_unauthenticated_server(general_options_page):
    # No login was tied to the test server, so switching away requires no logout.
    page = general_options_page
    config = get_config()
    config.setting['server_host'] = 'test.musicbrainz.org'
    oauth_manager = page.tagger.webservice.oauth_manager
    _save_with_host(page, 'musicbrainz.org')
    oauth_manager.forget_refresh_token.assert_not_called()
    oauth_manager.forget_access_token.assert_not_called()


def test_no_logout_when_not_authorized(general_options_page):
    page = general_options_page
    oauth_manager = page.tagger.webservice.oauth_manager
    oauth_manager.is_authorized.return_value = False
    _save_with_host(page, 'test.musicbrainz.org')
    oauth_manager.forget_refresh_token.assert_not_called()
    oauth_manager.forget_access_token.assert_not_called()
