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
import urllib
import httplib
import BaseHTTPServer

class TaggerRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def __init__(self,conn,addr,server):
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, conn, addr, server)

    def do_POST(self):
        self.send_error(405, "POST not supported")

    def do_HEAD(self):
        self.send_error(405, "HEAD not supported")

    def do_GET(self):
        parsedArgs = {}
        [action, rest] = urllib.splitquery(self.path)
        if rest:
            args = rest.split('&');
            for kv in args:
               [key, value] = kv.split('=')
               parsedArgs[key] = unicode(value)

        if action[0] == '/':
            action = action[1:]
        self.server.getBrowserIntegrationModule().action(action, parsedArgs)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write('<html><head><meta http-equiv="pragma" content="no-cache"></head><body>Nothing to see here!</body></html>\n')

    def do_QUIT(self):
        self.server.getBrowserIntegrationModule().exitThread = True
        self.send_response(200)
        self.end_headers()        
        
    def log_message(self, format, *args):
        pass


class TaggerServer(BaseHTTPServer.HTTPServer, QtCore.QObject):

    def __init__(self, addr, handlerClass):
        BaseHTTPServer.HTTPServer.__init__(self, addr, handlerClass)

    def setBrowserIntegrationModule(self, bim):
        self.bim = bim

    def getBrowserIntegrationModule(self):
        return self.bim 

class BrowserIntegration(QtCore.QThread):
  
    defaultPort = 8056
    
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.exitThread = False
        self.server = None
        
    def start(self):
        self.log.debug(u"Starting the browser integration")
        QtCore.QThread.start(self)
        
    def stop(self):
        self.log.debug(u"Stopping the browser integration")
        if self.isRunning():
            if self.port:
                conn = httplib.HTTPConnection("%s:%d" % self.server.server_address)
                conn.request("QUIT", "/")
                conn.getresponse()
            self.wait()

    def action(self, action, args):
        self.log.debug(u"Browser integration event: action=%r, args=%r", action, args)
        if action == "init":
            self.emit(QtCore.SIGNAL("init(int)"), args)
        elif action == "openalbum":
            self.tagger.thread_assist.proxy_to_main(self.tagger.load_album,
                                                    (args["id"],))
        else:
            self.log.warning(u"Unknown browser integration event '%s'!", action)

    def run(self):
        # Start the HTTP server
        port = self.defaultPort
        self.port = None
        while not self.port:
            try:
                self.server = TaggerServer(("127.0.0.1", port), TaggerRequestHandler)
                self.port = port
            except:
                port = port + 1

        # Report the port number back to the main app
        self.action("init", self.port)

        self.server.setBrowserIntegrationModule(self)
        while not self.exitThread:
            self.server.handle_request()

