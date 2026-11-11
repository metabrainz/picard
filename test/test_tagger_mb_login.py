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

"""The GUI part of the MusicBrainz login (Tagger.mb_login): the browser and what receives its redirect."""

from unittest.mock import (
    MagicMock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.tagger import Tagger


class TaggerMBLoginTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.app = MagicMock()
        self.app.browser_integration.is_running = True
        self.app._mb_login_receiver.start.return_value = True
        self.app._mb_login_receiver.redirect_uri = 'http://127.0.0.1:8001/auth'
        self.callback = MagicMock()
        for target in ('picard.tagger.mblogin', 'picard.tagger.webbrowser2'):
            patcher = patch(target)
            setattr(self, target.rsplit('.', 1)[1], patcher.start())
            self.addCleanup(patcher.stop)
        self.mblogin.start_login.return_value = 'https://musicbrainz.org/oauth2/authorize?x'

    def test_the_browser_is_opened_on_the_url(self):
        Tagger.mb_login(self.app, self.callback)
        self.mblogin.start_login.assert_called_once_with(self.callback)
        self.webbrowser2.open.assert_called_once_with('https://musicbrainz.org/oauth2/authorize?x')

    def test_with_the_browser_integration_it_receives_the_redirect(self):
        Tagger.mb_login(self.app, self.callback)
        self.app._mb_login_receiver.start.assert_not_called()

    def test_without_the_browser_integration_a_receiver_listens(self):
        # MusicBrainz no longer accepts the out-of-band flow (a code to copy).
        for integration in (None, MagicMock(is_running=False)):
            with self.subTest(integration=integration):
                self.app.browser_integration = integration
                self.app._mb_login_receiver.start.reset_mock()
                Tagger.mb_login(self.app, self.callback)
                self.app._mb_login_receiver.start.assert_called_once_with()
                self.assertEqual('http://127.0.0.1:8001/auth', self.app.webservice.oauth_manager.redirect_uri)

    def test_no_free_port_fails_the_login(self):
        self.app.browser_integration.is_running = False
        self.app._mb_login_receiver.start.return_value = False
        Tagger.mb_login(self.app, self.callback)
        self.mblogin.start_login.assert_not_called()
        self.webbrowser2.open.assert_not_called()
        successful, error_msg = self.callback.call_args.args
        self.assertFalse(successful)
        self.assertTrue(error_msg)

    def test_logout(self):
        Tagger.mb_logout(self.app, self.callback)
        self.mblogin.logout.assert_called_once_with(self.callback)
