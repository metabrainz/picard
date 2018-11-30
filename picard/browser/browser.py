# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
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

from urllib.parse import (
    parse_qs,
    urlparse,
)

from PyQt5 import QtNetwork

from picard import (
    config,
    log,
)
from picard.util import mbid_validate


def response(code):
    if code == 200:
        resp = '200 OK'
    elif code == 400:
        resp = '400 Bad Request'
    else:
        resp = '500 Internal Server Error'
    return bytearray(
        'HTTP/1.1 {}\r\n'
        'Cache-Control: max-age=0\r\n'
        '\r\n'
        'Nothing to see here.\r\n'.format(resp), 'ascii')


class BrowserIntegration(QtNetwork.QTcpServer):

    """Simple HTTP server for web browser integration."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.newConnection.connect(self._accept_connection)
        self.port = 0
        self.host_address = None

    def start(self):
        if self.port:
            self.stop()

        if config.setting["browser_integration_localhost_only"]:
            self.host_address = QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHost)
        else:
            self.host_address = QtNetwork.QHostAddress(QtNetwork.QHostAddress.Any)

        for port in range(config.setting["browser_integration_port"], 65535):
            if self.listen(self.host_address, port):
                log.debug("Starting the browser integration (%s:%d)", self.host_address.toString(), port)
                self.port = port
                self.tagger.listen_port_changed.emit(self.port)
                break

    def stop(self):
        if self.port > 0:
            log.debug("Stopping the browser integration")
            self.port = 0
            self.tagger.listen_port_changed.emit(self.port)
            self.close()
        else:
            log.debug("Browser integration inactive, no need to stop")

    def _process_request(self):
        conn = self.sender()
        rawline = conn.readLine().data()
        log.debug("Browser integration request: %r", rawline)

        def parse_line(line):
            orig_line = line
            try:
                line = line.split()
                if line[0] == "GET" and "?" in line[1]:
                    parsed = urlparse(line[1])
                    args = parse_qs(parsed.query)
                    if 'id' in args and args['id']:
                        mbid = args['id'][0]
                        if not mbid_validate(mbid):
                            log.error("Browser integration failed: bad mbid %r", mbid)
                            return False

                        def load_it(loader):
                            self.tagger.bring_tagger_front()
                            loader(mbid)
                            return True
                        action = parsed.path
                        if action == '/openalbum':
                            return load_it(self.tagger.load_album)
                        elif action == '/opennat':
                            return load_it(self.tagger.load_nat)
            except Exception as e:
                log.error("Browser integration failed with %r on line %r", e, orig_line)
                return False
            log.error("Browser integration failed: cannot parse %r", orig_line)
            return False

        try:
            line = rawline.decode()
            if parse_line(line):
                conn.write(response(200))
            else:
                conn.write(response(400))
        except UnicodeDecodeError as e:
            conn.write(response(500))
            log.error(e)
            return
        finally:
            conn.disconnectFromHost()

    def _accept_connection(self):
        conn = self.nextPendingConnection()
        conn.readyRead.connect(self._process_request)
