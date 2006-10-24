# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006 Lukáš Lalinský
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

from PyQt4 import QtCore
import BaseHTTPServer
import httplib
import socket
import urllib


class TaggerRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def __init__(self,conn,addr,server):
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, conn, addr, server)

    def do_POST(self):
        self.send_error(405, "POST not supported")

    def do_HEAD(self):
        self.send_error(405, "HEAD not supported")

    def do_GET(self):
        action, args = urllib.splitquery(self.path)
        parsed_args = dict(arg.split("=") for arg in args.split('&'))
        if action.startswith("/"):
            action = action[1:]
        self.server.integration.action(action, parsed_args)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            '<html><head><meta http-equiv="pragma" content="no-cache"></head>'
            '<body>Nothing to see here!</body></html>')

    def do_QUIT(self):
        self.server.integration.exit_thread = True
        self.send_response(200)
        self.end_headers()        
        
    def log_message(self, format, *args):
        pass


class TaggerServer(BaseHTTPServer.HTTPServer):

    allow_reuse_address = False

    def __init__(self, integration, addr, handlerClass):
        BaseHTTPServer.HTTPServer.__init__(self, addr, handlerClass)
        self.integration = integration


class BrowserIntegration(QtCore.QThread):
  
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.exit_thread = False
        
    def start(self):
        self.log.debug(u"Starting the browser integration")
        QtCore.QThread.start(self)
        
    def stop(self):
        self.log.debug(u"Stopping the browser integration")
        if self.isRunning():
            if self.server:
                conn = httplib.HTTPConnection(
                    "%s:%d" % self.server.server_address)
                conn.request("QUIT", "/")
                conn.getresponse()
            self.wait()

    def action(self, action, args):
        self.log.debug(
            "Browser integration event: action=%r, args=%r", action, args)
        if action == "init":
            self.emit(QtCore.SIGNAL("init(int)"), args)
        elif action == "openalbum":
            self.tagger.thread_assist.proxy_to_main(
                self.tagger.load_album, args["id"])
        else:
            self.log.warning("Unknown browser integration event %r", action)

    def run(self):
        self.port = 8056
        self.server = None
        while not self.server:
            try:
                self.server = TaggerServer(
                    self, ("127.0.0.1", self.port), TaggerRequestHandler)
            except socket.error:
                self.port += 1
        self.action("init", self.port)
        while not self.exit_thread:
            self.server.handle_request()
