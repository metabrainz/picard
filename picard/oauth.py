# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2014 Lukáš Lalinský
# Copyright (C) 2015 Sophist-UK
# Copyright (C) 2015 Wieland Hoffmann
# Copyright (C) 2015, 2018, 2021 Philipp Wolfer
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Frederik “Freso” S. Olesen
# Copyright (C) 2018-2022 Laurent Monin
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


from functools import partial
from json.decoder import JSONDecodeError
import time
import urllib.parse

from picard import log
from picard.config import get_config
from picard.const import (
    MUSICBRAINZ_OAUTH_CLIENT_ID,
    MUSICBRAINZ_OAUTH_CLIENT_SECRET,
)
from picard.util import (
    build_qurl,
    load_json,
)


class OAuthManager(object):

    def __init__(self, webservice):
        self.webservice = webservice

    @property
    def setting(self):
        config = get_config()
        return config.setting

    @property
    def persist(self):
        config = get_config()
        return config.persist

    @property
    def host(self):
        return self.setting['server_host']

    @property
    def port(self):
        return self.setting['server_port']

    @property
    def refresh_token(self):
        return self.persist['oauth_refresh_token']

    @refresh_token.setter
    def refresh_token(self, value):
        self.persist['oauth_refresh_token'] = value

    @refresh_token.deleter
    def refresh_token(self):
        self.persist.remove('oauth_refresh_token')

    @property
    def refresh_token_scopes(self):
        return self.persist['oauth_refresh_token_scopes']

    @refresh_token_scopes.setter
    def refresh_token_scopes(self, value):
        self.persist['oauth_refresh_token_scopes'] = value

    @refresh_token_scopes.deleter
    def refresh_token_scopes(self):
        self.persist.remove('oauth_refresh_token_scopes')

    @property
    def access_token(self):
        return self.persist['oauth_access_token']

    @access_token.setter
    def access_token(self, value):
        self.persist['oauth_access_token'] = value

    @access_token.deleter
    def access_token(self):
        self.persist.remove('oauth_access_token')

    @property
    def access_token_expires(self):
        return self.persist['oauth_access_token_expires']

    @access_token_expires.setter
    def access_token_expires(self, value):
        self.persist['oauth_access_token_expires'] = value

    @access_token_expires.deleter
    def access_token_expires(self):
        self.persist.remove('oauth_access_token_expires')

    @property
    def username(self):
        return self.persist['oauth_username']

    @username.setter
    def username(self, value):
        self.persist['oauth_username'] = value

    def is_authorized(self):
        return bool(self.refresh_token and self.refresh_token_scopes)

    def is_logged_in(self):
        return self.is_authorized() and bool(self.username)

    def revoke_tokens(self):
        # TODO actually revoke the tokens on MB (I think it's not implementented there)
        self.forget_refresh_token()
        self.forget_access_token()

    def forget_refresh_token(self):
        del self.refresh_token
        del self.refresh_token_scopes

    def forget_access_token(self):
        del self.access_token
        del self.access_token_expires

    def get_access_token(self, callback):
        if not self.is_authorized():
            callback(access_token=None)
        else:
            if self.access_token and time.time() < self.access_token_expires:
                callback(access_token=self.access_token)
            else:
                self.forget_access_token()
                self.refresh_access_token(callback)

    def url(self, path=None, params=None):
        return build_qurl(
            self.host, self.port, path=path,
            queryargs=params
        )

    def get_authorization_url(self, scopes):
        params = {
            'response_type': 'code',
            'client_id': MUSICBRAINZ_OAUTH_CLIENT_ID,
            'redirect_uri': "urn:ietf:wg:oauth:2.0:oob",
            'scope': scopes,
        }
        return bytes(self.url(path="/oauth2/authorize", params=params).toEncoded()).decode()

    def set_refresh_token(self, refresh_token, scopes):
        log.debug("OAuth: got refresh_token %s with scopes %s", refresh_token, scopes)
        self.refresh_token = refresh_token
        self.refresh_token_scopes = scopes

    def set_access_token(self, access_token, expires_in):
        log.debug("OAuth: got access_token %s that expires in %s seconds", access_token, expires_in)
        self.access_token = access_token
        self.access_token_expires = int(time.time() + expires_in - 60)

    @staticmethod
    def _query_data(params):
        return urllib.parse.urlencode({key: value for key, value in params.items() if key})

    def refresh_access_token(self, callback):
        log.debug("OAuth: refreshing access_token with a refresh_token %s", self.refresh_token)
        params = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': MUSICBRAINZ_OAUTH_CLIENT_ID,
            'client_secret': MUSICBRAINZ_OAUTH_CLIENT_SECRET,
        }
        self.webservice.post_url(
            url=self.url(path="/oauth2/token"),
            data=self._query_data(params),
            handler=partial(self.on_refresh_access_token_finished, callback),
            mblogin=True,
            priority=True,
            important=True,
            request_mimetype='application/x-www-form-urlencoded',
        )

    def on_refresh_access_token_finished(self, callback, data, http, error):
        access_token = None
        try:
            if error:
                log.error("OAuth: access_token refresh failed: %s", data)
                if self._http_code(http) == 400:
                    response = load_json(data)
                    if response['error'] == 'invalid_grant':
                        self.forget_refresh_token()
            else:
                access_token = data['access_token']
                self.set_access_token(access_token, data['expires_in'])
        except Exception as e:
            log.error("OAuth: Unexpected error handling access token response: %r", e)
        finally:
            callback(access_token=access_token)

    def exchange_authorization_code(self, authorization_code, scopes, callback):
        log.debug("OAuth: exchanging authorization_code %s for an access_token", authorization_code)
        params = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'client_id': MUSICBRAINZ_OAUTH_CLIENT_ID,
            'client_secret': MUSICBRAINZ_OAUTH_CLIENT_SECRET,
            'redirect_uri': "urn:ietf:wg:oauth:2.0:oob",
        }
        self.webservice.post_url(
            url=self.url(path="/oauth2/token"),
            data=self._query_data(params),
            handler=partial(self.on_exchange_authorization_code_finished, scopes, callback),
            mblogin=True,
            priority=True,
            important=True,
            request_mimetype='application/x-www-form-urlencoded',
        )

    def on_exchange_authorization_code_finished(self, scopes, callback, data, http, error):
        successful = False
        error_msg = None
        try:
            if error:
                log.error("OAuth: authorization_code exchange failed: %s", data)
                error_msg = self._extract_error_description(http, data)
            else:
                self.set_refresh_token(data['refresh_token'], scopes)
                self.set_access_token(data['access_token'], data['expires_in'])
                successful = True
        except Exception as e:
            log.error("OAuth: Unexpected error handling authorization code response: %r", e)
            error_msg = _("Unexpected authentication error")
        finally:
            callback(successful=successful, error_msg=error_msg)

    def fetch_username(self, callback):
        log.debug("OAuth: fetching username")
        self.webservice.get_url(
            url=self.url(path="/oauth2/userinfo"),
            handler=partial(self.on_fetch_username_finished, callback),
            mblogin=True,
            priority=True,
            important=True,
        )

    def on_fetch_username_finished(self, callback, data, http, error):
        successful = False
        error_msg = None
        try:
            if error:
                log.error("OAuth: username fetching failed: %s", data)
                error_msg = self._extract_error_description(http, data)
            else:
                self.username = data['sub']
                log.debug("OAuth: got username %s", self.username)
                successful = True
        except Exception as e:
            log.error("OAuth: Unexpected error handling username fetch response: %r", e)
            error_msg = _("Unexpected authentication error")
        finally:
            callback(successful=successful, error_msg=error_msg)

    def _http_code(self, http):
        return self.webservice.http_response_code(http)

    def _extract_error_description(self, http, data):
        try:
            response = load_json(data)
            return response['error_description']
        except (JSONDecodeError, KeyError, TypeError):
            return _("Unexpected request error (HTTP code %s)") % self._http_code(http)
