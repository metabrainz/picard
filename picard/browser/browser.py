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

from PyQt4 import QtCore, QtNetwork


class BrowserIntegration(QtNetwork.QTcpServer):
    """Simple HTTP server for web browser integration."""

    def __init__(self, parent=None):
        QtNetwork.QTcpServer.__init__(self, parent)
        self.newConnection.connect(self.accept_connection)

    def start(self):
        self.port = 8000
        while self.port < 65535:
            self.log.debug("Starting the browser integration (port %d)", self.port)
            if self.listen(QtNetwork.QHostAddress(QtNetwork.QHostAddress.Any), self.port):
                self.tagger.listen_port_changed.emit(self.port)
                break
            self.port += 1

    def stop(self):
        self.log.debug("Stopping the browser integration")
        self.close()

    def process_request(self):
        conn = self.sender()
        line = str(conn.readLine())
        conn.write("HTTP/1.1 200 OK\r\nCache-Control: max-age=0\r\n\r\nNothing to see here.")
        conn.disconnectFromHost()
        line = line.split()
        self.log.debug("Browser integration request: %r", line)
        if line[0] == "GET" and "?" in line[1]:
            action, args = line[1].split("?")
            args = [a.split("=", 1) for a in args.split("&")]
            args = dict((a, unicode(QtCore.QUrl.fromPercentEncoding(b))) for (a, b) in args)
            if action == "/openalbum":
                self.tagger.load_album(args["id"])
            elif action == "/opennat":
                self.tagger.load_nat(args["id"])
            else:
                self.log.error("Unknown browser integration request: %r", action)

    def accept_connection(self):
        conn = self.nextPendingConnection()
        conn.readyRead.connect(self.process_request)
