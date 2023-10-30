# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2011 Lukáš Lalinský
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2012-2013, 2018, 2021 Philipp Wolfer
# Copyright (C) 2013, 2018, 2020-2021 Laurent Monin
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
from picard.util import mbid_validate
from picard.util.thread import to_main


try:
    from http.server import ThreadingHTTPServer
except ImportError:
    from socketserver import ThreadingMixIn

    class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True


SERVER_VERSION = '%s-%s/%s' % (PICARD_ORG_NAME, PICARD_APP_NAME, PICARD_VERSION_STR)
RE_VALID_ORIGINS = re.compile(r'^(?:[^\.]+\.)*musicbrainz\.org$')


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
        if config.setting["browser_integration_localhost_only"]:
            host_address = '127.0.0.1'
        else:
            host_address = '0.0.0.0'  # nosec

        try:
            for port in range(config.setting["browser_integration_port"], 65535):
                try:
                    self.server = ThreadingHTTPServer((host_address, port), RequestHandler)
                except OSError:
                    continue
                log.info("Starting the browser integration (%s:%d)", host_address, port)
                self.listen_port_changed.emit(port)
                threading.Thread(target=self.server.serve_forever).start()
                break
            else:
                log.error("Failed finding an available port for the browser integration.")
                self.stop()
        except Exception:
            log.error("Failed starting the browser integration on %s", host_address, exc_info=True)

    def stop(self):
        if self.server:
            try:
                log.info("Stopping the browser integration")
                self.server.shutdown()
                self.server.server_close()
                self.server = None
                self.listen_port_changed.emit(self.port)
            except Exception:
                log.error("Failed stopping the browser integration", exc_info=True)
        else:
            log.debug("Browser integration inactive, no need to stop")


class RequestHandler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        origin = self.headers['origin']
        if _is_valid_origin(origin):
            self.send_response(204)
            self.send_header('Access-Control-Allow-Origin', origin)
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
            log.error('Browser integration failed handling request', exc_info=True)
            self._response(500, 'Unexpected request error')

    def log_error(self, format, *args):
        log.error(format, *args)

    def log_message(self, format, *args):
        log.info(format, *args)

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

    def _response(self, code, content='', content_type='text/plain'):
        self.server_version = SERVER_VERSION
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Cache-Control', 'max-age=0')
        origin = self.headers['origin']
        if _is_valid_origin(origin):
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Vary', 'Origin')
        self.end_headers()
        self.wfile.write(content.encode())
