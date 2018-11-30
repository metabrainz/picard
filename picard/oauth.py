# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2014 Lukáš Lalinský
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
import time

from PyQt5.QtCore import (
    QUrl,
    QUrlQuery,
)
from PyQt5.QtNetwork import QNetworkRequest

from picard import (
    config,
    log,
)
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

    def is_authorized(self):
        return bool(config.persist["oauth_refresh_token"] and
                    config.persist["oauth_refresh_token_scopes"])

    def is_logged_in(self):
        return self.is_authorized() and bool(config.persist["oauth_username"])

    def revoke_tokens(self):
        # TODO actually revoke the tokens on MB (I think it's not implementented there)
        self.forget_refresh_token()
        self.forget_access_token()

    def forget_refresh_token(self):
        config.persist.remove("oauth_refresh_token")
        config.persist.remove("oauth_refresh_token_scopes")

    def forget_access_token(self):
        config.persist.remove("oauth_access_token")
        config.persist.remove("oauth_access_token_expires")

    def get_access_token(self, callback):
        if not self.is_authorized():
            callback(None)
        else:
            access_token = config.persist["oauth_access_token"]
            access_token_expires = config.persist["oauth_access_token_expires"]
            if access_token and time.time() < access_token_expires:
                callback(access_token)
            else:
                self.forget_access_token()
                self.refresh_access_token(callback)

    def get_authorization_url(self, scopes):
        host, port = config.setting['server_host'], config.setting['server_port']
        params = {"response_type": "code", "client_id":
                  MUSICBRAINZ_OAUTH_CLIENT_ID, "redirect_uri":
                  "urn:ietf:wg:oauth:2.0:oob", "scope": scopes}
        url = build_qurl(host, port, path="/oauth2/authorize",
                         queryargs=params)
        return bytes(url.toEncoded()).decode()

    def set_refresh_token(self, refresh_token, scopes):
        log.debug("OAuth: got refresh_token %s with scopes %s", refresh_token, scopes)
        config.persist["oauth_refresh_token"] = refresh_token
        config.persist["oauth_refresh_token_scopes"] = scopes

    def set_access_token(self, access_token, expires_in):
        log.debug("OAuth: got access_token %s that expires in %s seconds", access_token, expires_in)
        config.persist["oauth_access_token"] = access_token
        config.persist["oauth_access_token_expires"] = int(time.time() + expires_in - 60)

    def set_username(self, username):
        log.debug("OAuth: got username %s", username)
        config.persist["oauth_username"] = username

    def refresh_access_token(self, callback):
        refresh_token = config.persist["oauth_refresh_token"]
        log.debug("OAuth: refreshing access_token with a refresh_token %s", refresh_token)
        host, port = config.setting['server_host'], config.setting['server_port']
        path = "/oauth2/token"
        url = QUrl()
        url_query = QUrlQuery()
        url_query.addQueryItem("grant_type", "refresh_token")
        url_query.addQueryItem("refresh_token", refresh_token)
        url_query.addQueryItem("client_id", MUSICBRAINZ_OAUTH_CLIENT_ID)
        url_query.addQueryItem("client_secret", MUSICBRAINZ_OAUTH_CLIENT_SECRET)
        url.setQuery(url_query.query(QUrl.FullyEncoded))
        data = url.query()
        self.webservice.post(host, port, path, data,
                             partial(self.on_refresh_access_token_finished, callback),
                             mblogin=True, priority=True, important=True,
                             request_mimetype="application/x-www-form-urlencoded")

    def on_refresh_access_token_finished(self, callback, data, http, error):
        access_token = None
        try:
            if error:
                log.error("OAuth: access_token refresh failed: %s", data)
                if http.attribute(QNetworkRequest.HttpStatusCodeAttribute) == 400:
                    response = load_json(data)
                    if response["error"] == "invalid_grant":
                        self.forget_refresh_token()
            else:
                self.set_access_token(data["access_token"], data["expires_in"])
                access_token = data["access_token"]
        except Exception as e:
            log.error('OAuth: Unexpected error handling access token response: %r', e)
        finally:
            callback(access_token)

    def exchange_authorization_code(self, authorization_code, scopes, callback):
        log.debug("OAuth: exchanging authorization_code %s for an access_token", authorization_code)
        host, port = config.setting['server_host'], config.setting['server_port']
        path = "/oauth2/token"
        url = QUrl()
        url_query = QUrlQuery()
        url_query.addQueryItem("grant_type", "authorization_code")
        url_query.addQueryItem("code", authorization_code)
        url_query.addQueryItem("client_id", MUSICBRAINZ_OAUTH_CLIENT_ID)
        url_query.addQueryItem("client_secret", MUSICBRAINZ_OAUTH_CLIENT_SECRET)
        url_query.addQueryItem("redirect_uri", "urn:ietf:wg:oauth:2.0:oob")
        url.setQuery(url_query.query(QUrl.FullyEncoded))
        data = url.query()
        self.webservice.post(host, port, path, data,
                             partial(self.on_exchange_authorization_code_finished, scopes, callback),
                             mblogin=True, priority=True, important=True,
                             request_mimetype="application/x-www-form-urlencoded")

    def on_exchange_authorization_code_finished(self, scopes, callback, data, http, error):
        successful = False
        try:
            if error:
                log.error("OAuth: authorization_code exchange failed: %s", data)
            else:
                self.set_refresh_token(data["refresh_token"], scopes)
                self.set_access_token(data["access_token"], data["expires_in"])
                successful = True
        except Exception as e:
            log.error('OAuth: Unexpected error handling authorization code response: %r', e)
        finally:
            callback(successful)

    def fetch_username(self, callback):
        log.debug("OAuth: fetching username")
        host, port = config.setting['server_host'], config.setting['server_port']
        path = "/oauth2/userinfo"
        self.webservice.get(host, port, path,
                            partial(self.on_fetch_username_finished, callback),
                            mblogin=True, priority=True, important=True)

    def on_fetch_username_finished(self, callback, data, http, error):
        successful = False
        try:
            if error:
                log.error("OAuth: username fetching failed: %s", data)
            else:
                self.set_username(data["sub"])
                successful = True
        except Exception as e:
            log.error('OAuth: Unexpected error handling username fetch response: %r', e)
        finally:
            callback(successful)
