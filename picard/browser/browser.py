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

from PyQt5 import QtCore, QtNetwork
from picard import log, config


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
        line = string_(conn.readLine())
        conn.write(b"HTTP/1.1 200 OK\r\nCache-Control: max-age=0\r\n\r\nNothing to see here.")
        conn.disconnectFromHost()
        line = line.split()
        log.debug("Browser integration request: %r", line)
        if line[0] == "GET" and "?" in line[1]:
            action, args = line[1].split("?")
            args = [a.split("=", 1) for a in args.split("&")]
            args = dict((a, string_(QtCore.QUrl.fromPercentEncoding(b.encode('ascii')))) for (a, b) in args)
            self.tagger.bring_tagger_front()
            if action == "/openalbum":
                self.tagger.load_album(args["id"])
            elif action == "/opennat":
                self.tagger.load_nat(args["id"])
            else:
                log.error("Unknown browser integration request: %r", action)

    def _accept_connection(self):
        conn = self.nextPendingConnection()
        conn.readyRead.connect(self._process_request)
