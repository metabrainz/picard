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

import json
import time
from functools import partial
from PyQt4.QtNetwork import QNetworkRequest
from PyQt4.QtCore import QUrl
from picard import config, log
from picard.const import (
    MUSICBRAINZ_SERVERS,
    MUSICBRAINZ_OAUTH_CLIENT_ID,
    MUSICBRAINZ_OAUTH_CLIENT_SECRET,
)
from picard.util import build_qurl


class OAuthManager(object):

    def __init__(self, xmlws):
        self.xmlws = xmlws

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
                         queryargs=params, mblogin=True)
        return str(url.toEncoded())

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
        url.addQueryItem("grant_type", "refresh_token")
        url.addQueryItem("refresh_token", refresh_token)
        url.addQueryItem("client_id", MUSICBRAINZ_OAUTH_CLIENT_ID)
        url.addQueryItem("client_secret", MUSICBRAINZ_OAUTH_CLIENT_SECRET)
        data = str(url.encodedQuery())
        self.xmlws.post(host, port, path, data,
                        partial(self.on_refresh_access_token_finished, callback),
                        xml=False, mblogin=True, priority=True, important=True)

    def on_refresh_access_token_finished(self, callback, data, http, error):
        access_token = None
        try:
            if error:
                log.error("OAuth: access_token refresh failed: %s", data)
                if http.attribute(QNetworkRequest.HttpStatusCodeAttribute) == 400:
                    response = json.loads(data)
                    if response["error"] == "invalid_grant":
                        self.forget_refresh_token()
            else:
                response = json.loads(data)
                self.set_access_token(response["access_token"], response["expires_in"])
                access_token = response["access_token"]
        finally:
            callback(access_token)

    def exchange_authorization_code(self, authorization_code, scopes, callback):
        log.debug("OAuth: exchanging authorization_code %s for an access_token", authorization_code)
        host, port = config.setting['server_host'], config.setting['server_port']
        path = "/oauth2/token"
        url = QUrl()
        url.addQueryItem("grant_type", "authorization_code")
        url.addQueryItem("code", authorization_code)
        url.addQueryItem("client_id", MUSICBRAINZ_OAUTH_CLIENT_ID)
        url.addQueryItem("client_secret", MUSICBRAINZ_OAUTH_CLIENT_SECRET)
        url.addQueryItem("redirect_uri", "urn:ietf:wg:oauth:2.0:oob")
        data = str(url.encodedQuery())
        self.xmlws.post(host, port, path, data,
                        partial(self.on_exchange_authorization_code_finished, scopes, callback),
                        xml=False, mblogin=True, priority=True, important=True)

    def on_exchange_authorization_code_finished(self, scopes, callback, data, http, error):
        successful = False
        try:
            if error:
                log.error("OAuth: authorization_code exchange failed: %s", data)
            else:
                response = json.loads(data)
                self.set_refresh_token(response["refresh_token"], scopes)
                self.set_access_token(response["access_token"], response["expires_in"])
                successful = True
        finally:
            callback(successful)

    def fetch_username(self, callback):
        log.debug("OAuth: fetching username")
        host, port = config.setting['server_host'], config.setting['server_port']
        path = "/oauth2/userinfo"
        self.xmlws.get(host, port, path,
                        partial(self.on_fetch_username_finished, callback),
                        xml=False, mblogin=True, priority=True, important=True)

    def on_fetch_username_finished(self, callback, data, http, error):
        successful = False
        try:
            if error:
                log.error("OAuth: username fetching failed: %s", data)
            else:
                response = json.loads(data)
                self.set_username(response["sub"])
                successful = True
        finally:
            callback(successful)
