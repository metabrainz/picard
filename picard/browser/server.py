# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2011 Lukáš Lalinský
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2012-2013, 2018, 2021-2022, 2024-2025 Philipp Wolfer
# Copyright (C) 2013, 2018, 2020-2021, 2024 Laurent Monin
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
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


from http.server import (
    BaseHTTPRequestHandler,
    HTTPServer,
)
from itertools import chain
import re
import threading
from urllib.parse import (
    parse_qs,
    urlparse,
)

from PyQt6 import QtCore

from picard import (
    PICARD_APP_NAME,
    PICARD_ORG_NAME,
    PICARD_VERSION_STR,
    log,
)
from picard.browser import addrelease
from picard.config import get_config
from picard.const import BROWSER_INTEGRATION_LOCALIP
from picard.oauth import OAuthInvalidStateError
from picard.util import mbid_validate
from picard.util.thread import to_main


try:
    from http.server import ThreadingHTTPServer as OurHTTPServer
except ImportError:
    from socketserver import ThreadingMixIn

    class OurHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True


SERVER_VERSION = '%s-%s/%s' % (PICARD_ORG_NAME, PICARD_APP_NAME, PICARD_VERSION_STR)
RE_VALID_ORIGINS = re.compile(r'^(?:[^\.]+\.)*musicbrainz\.org$')
LOG_PREFIX = "Browser Integration"


def _is_valid_origin(origin):
    try:
        url = urlparse(origin)
    except ValueError:
        return False
    hostname = url.hostname
    if not hostname:
        return False
    if RE_VALID_ORIGINS.match(hostname):
        return True
    config = get_config()
    return config.setting['server_host'] == hostname


class BrowserIntegration(QtCore.QObject):
    listen_port_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.server = None

    @property
    def host_address(self):
        if not self.server:
            return ''
        return self.server.server_address[0]

    @property
    def port(self):
        if not self.server:
            return 0
        return self.server.server_address[1]

    @property
    def is_running(self):
        return self.server is not None

    def start(self):
        if self.server:
            self.stop()

        config = get_config()

        LISTEN_ALL = '0.0.0.0'
        MIN_PORT = config.setting["browser_integration_port"]
        MAX_PORT = 65535

        if config.setting["browser_integration_localhost_only"]:
            host_address = BROWSER_INTEGRATION_LOCALIP
        else:
            host_address = LISTEN_ALL

        try:
            for port in range(MIN_PORT, MAX_PORT):
                try:
                    self.server = OurHTTPServer((host_address, port), RequestHandler)
                except OSError:
                    continue
                log.info("%s: Starting, listening on address %s and port %d", LOG_PREFIX, host_address, port)
                self.listen_port_changed.emit(port)
                threading.Thread(target=self.server.serve_forever).start()
                break
            else:
                log.error(
                    "%s: Failed to find an available port in range %s-%s on address %s",
                    LOG_PREFIX,
                    MIN_PORT,
                    MAX_PORT,
                    host_address,
                )
                self.stop()
        except Exception:
            log.error("%s: Failed to start listening on %s", LOG_PREFIX, host_address, exc_info=True)

    def stop(self):
        if self.server:
            try:
                log.info("%s: Stopping", LOG_PREFIX)
                self.server.shutdown()
                self.server.server_close()
                self.server = None
                self.listen_port_changed.emit(self.port)
            except Exception:
                log.error("%s: Failed to stop", LOG_PREFIX, exc_info=True)
        else:
            log.debug("%s: inactive, no need to stop", LOG_PREFIX)


# From https://github.com/python/cpython/blob/f474264b1e3cd225b45cf2c0a91226d2a9d3ee9b/Lib/http/server.py#L570C1-L573C43
# https://en.wikipedia.org/wiki/List_of_Unicode_characters#Control_codes
CONTROL_CHAR_TABLE = str.maketrans({c: rf'\x{c:02x}' for c in chain(range(0x20), range(0x7F, 0xA0))})
CONTROL_CHAR_TABLE[ord('\\')] = r'\\'


def safe_message(message):
    return message.translate(CONTROL_CHAR_TABLE)


class RequestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        origin = self.headers['origin']
        if _is_valid_origin(origin):
            self.send_response(204)
            self.send_header('Access-Control-Allow-Origin', clean_header(origin))
            self.send_header('Access-Control-Allow-Methods', 'GET')
            self.send_header('Access-Control-Allow-Credentials', 'false')
            self.send_header('Access-Control-Allow-Private-Network', 'true')
            self.send_header('Access-Control-Max-Age', 3600)
            self.send_header('Vary', 'Origin')
        else:
            self.send_response(401)
        self.end_headers()

    def do_GET(self):
        try:
            self._handle_get()
        except Exception:
            log.error('%s: failed handling request', LOG_PREFIX, exc_info=True)
            self._response(500, 'Unexpected request error')

    def _log(self, log_func, fmt, args):
        log_func(
            "%s: %s %s",
            LOG_PREFIX,
            self.address_string(),
            safe_message(fmt % args),
        )

    def log_error(self, format, *args):
        self._log(log.error, format, args)

    def log_message(self, format, *args):
        self._log(log.info, format, args)

    def _handle_get(self):
        parsed = urlparse(self.path)
        args = parse_qs(parsed.query)
        action = parsed.path

        if action == '/':
            self._response(200, SERVER_VERSION)
        elif action == '/openalbum':
            self._load_mbid('album', args)
        elif action == '/opennat':
            self._load_mbid('nat', args)
        elif action == '/add' and addrelease.is_available():
            self._add_release(args)
        elif action == '/auth':
            self._auth(args)
        else:
            self._response(404, 'Unknown action.')

    def _load_mbid(self, type, args):
        if 'id' in args and args['id']:
            mbid = args['id'][0]
            if not mbid_validate(mbid):
                self._response(400, '"id" is not a valid MBID.')
            else:
                tagger = QtCore.QCoreApplication.instance()
                to_main(tagger.load_mbid, type, mbid)
                self._response(200, 'MBID "%s" loaded' % mbid)
        else:
            self._response(400, 'Missing parameter "id".')

    def _add_release(self, args):
        if 'token' in args and args['token']:
            try:
                content = addrelease.serve_form(args['token'][0])
                self._response(200, content, 'text/html')
            except addrelease.NotFoundError as err:
                self._response(404, str(err))
            except addrelease.InvalidTokenError:
                self._response(400, 'Invalid token')
        else:
            self._response(400, 'Missing parameter "token".')

    def _auth(self, args):
        if 'code' in args and args['code']:
            tagger = QtCore.QCoreApplication.instance()
            oauth_manager = tagger.webservice.oauth_manager
            try:
                state = args.get('state', [''])[0]
                callback = oauth_manager.verify_state(state)
            except OAuthInvalidStateError:
                self._response(400, 'Invalid "state" parameter.')
                return
            to_main(
                oauth_manager.exchange_authorization_code,
                authorization_code=args['code'][0],
                scopes='profile tag rating collection submit_isrc submit_barcode',
                callback=callback,
            )
            self._response(200, "Authentication successful, you can close this window now.", 'text/html')
        else:
            self._response(400, 'Missing parameter "code".')

    def _response(self, code, content='', content_type='text/plain'):
        self.server_version = SERVER_VERSION
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Cache-Control', 'max-age=0')
        origin = self.headers['origin']
        if _is_valid_origin(origin):
            self.send_header('Access-Control-Allow-Origin', clean_header(origin))
            self.send_header('Vary', 'Origin')
        self.end_headers()
        self.wfile.write(content.encode())


def clean_header(header):
    return re.sub("[\r\n:]", "", header)
