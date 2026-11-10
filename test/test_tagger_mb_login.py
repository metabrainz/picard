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

"""The GUI part of the MusicBrainz login (Tagger.mb_login): the browser and the dialog."""

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

    def test_without_redirect_the_code_is_asked_for(self):
        self.app.webservice.oauth_manager.is_oob = True
        self.app._mb_login_dialog.return_value = 'the-code'
        Tagger.mb_login(self.app, self.callback, parent='parent')
        self.app._mb_login_dialog.assert_called_once_with('parent')
        self.mblogin.finish_login.assert_called_once_with('the-code', self.callback)

    def test_a_cancelled_dialog_fails_the_login(self):
        self.app.webservice.oauth_manager.is_oob = True
        self.app._mb_login_dialog.return_value = None
        Tagger.mb_login(self.app, self.callback)
        self.mblogin.finish_login.assert_not_called()
        self.callback.assert_called_once_with(False, None)

    def test_with_the_browser_integration_the_redirect_completes_the_login(self):
        self.app.webservice.oauth_manager.is_oob = False
        Tagger.mb_login(self.app, self.callback)
        self.app._mb_login_dialog.assert_not_called()
        self.mblogin.finish_login.assert_not_called()

    def test_logout(self):
        Tagger.mb_logout(self.app, self.callback)
        self.mblogin.logout.assert_called_once_with(self.callback)
