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


"""
Asynchronous XML web service.
"""

import re
import md5
import sha
from PyQt4 import QtCore, QtNetwork, QtXml
from picard import version_string


def _md5(text):
    m = md5.new()
    m.update(text)
    return m.hexdigest()


def _node_name(name):
    return re.sub('[^a-zA-Z0-9]', '_', unicode(name))


class XmlNode(object):

    def __init__(self):
        self.text = u''
        self.children = {}
        self.attribs = {}

    def __repr__(self):
        return repr(self.__dict__)

    def __getattr__(self, name):
        try:
            return self.children[name]
        except KeyError:
            try:
                return self.attribs[name]
            except KeyError:
                raise AttributeError, name


class XmlHandler(QtXml.QXmlDefaultHandler):

    def init(self):
        self.document = XmlNode()
        self.node = self.document
        self.path = []

    def startElement(self, namespace, name, qname, attrs):
        node = XmlNode()
        for i in xrange(attrs.count()):
            node.attribs[_node_name(attrs.localName(i))] = unicode(attrs.value(i))
        self.node.children.setdefault(_node_name(name), []).append(node)
        self.path.append(self.node)
        self.node = node
        return True

    def endElement(self, namespace, name, qname):
        self.node = self.path.pop()
        return True

    def characters(self, text):
        self.node.text += unicode(text)
        return True


def test(doc, http, err):
    print err

class XmlWebService(QtNetwork.QHttp):

    def __init__(self, cachedir, parent=None):
        QtNetwork.QHttp.__init__(self, parent)
        self.connect(self, QtCore.SIGNAL("requestStarted(int)"), self._start_request)
        self.connect(self, QtCore.SIGNAL("requestFinished(int, bool)"), self._finish_request)
        self.connect(self, QtCore.SIGNAL("readyRead(const QHttpResponseHeader &)"), self._read_data)
        self._cachedir = cachedir
        self._request_handlers = {}
        self._puid_data = {}
        self._xml_handler = XmlHandler()
        self._xml_reader = QtXml.QXmlSimpleReader()
        self._xml_reader.setContentHandler(self._xml_handler)
        self._xml_input = QtXml.QXmlInputSource()
        self._using_proxy = False

    def _make_cache_filename(self, host, port, path):
        url = "%s:%d%s" % (host, port, path)
        filename = sha.new(url).hexdigest()
        m = re.search(r"\.([a-z]{2,3})(?:\?|$)", url)
        if m:
            filename += "." + m.group(1)
        return os.path.join(self._cachedir, filename)

    def _start_request(self, request_id):
        if request_id in self._request_handlers:
            self._xml_handler.init()
            self._new_request = True

    def _finish_request(self, request_id, error):
        try:
            handler = self._request_handlers[request_id]
        except KeyError:
            pass
        else:
            if handler is not None:
                response = self.lastResponse()
                if response.isValid() and response.statusCode() != 200:
                    error = True
                handler(self._xml_handler.document, self, error)
            del self._request_handlers[request_id]

    def _read_data(self, response):
        if response.statusCode() == 200:
            self._xml_input.setData(self.readAll())
            if self._new_request:
                self._xml_reader.parse(self._xml_input, True)
                self._new_request = False
            else:
                self._xml_reader.parseContinue()
        elif response.statusCode() == 401 and self.currentId() in self._puid_data:
            data, handler = self._puid_data[self.currentId()]
            del self._puid_data[self.currentId()]
            digest = unicode(response.value('WWW-Authenticate'))
            if digest.startswith('Digest '):
                username = self.config.setting["username"].encode('utf-8')
                password = self.config.setting["password"].encode('utf-8')
                path = str(self.currentRequest().path())
                digest = dict([[b.strip('"') for b in a.split('=')] for a in digest[7:].split(', ')])
                ha1 = _md5(username + ':' + digest['realm'] + ':' + password)
                ha2 = _md5('POST:' + path)
                digest['response'] = _md5(ha1 + ':' + digest['nonce'] + ':' + ha2)
                digest['uri'] = path
                digest['username'] = username
                header = self.currentRequest()
                header.setValue('Authorization', 'Digest ' + ', '.join(['%s="%s"' % a for a in digest.items()]))
                self.setHost(self.config.setting["server_host"], self.config.setting["server_port"])
                requestid = self.request(header, data)
                self._request_handlers[requestid] = handler

    def _prepare(self, method, host, port, path):
        self.log.debug("%s http://%s:%d%s", method, host, port, path)
        header = QtNetwork.QHttpRequestHeader(method, path)
        if port == 80:
            header.setValue("Host", "%s" % host)
        else:
            header.setValue("Host", "%s:%d" % (host, port))
        header.setValue("User-Agent", "MusicBrainz Picard/%s" % version_string)
        header.setValue("Connection", "Keep-Alive")
        if method == "POST":
            header.setContentType("application/x-www-form-urlencoded")
        if self.config.setting["use_proxy"]:
            self.setProxy(self.config.setting["proxy_server_host"], self.config.setting["proxy_server_port"],
                          self.config.setting["proxy_username"], self.config.setting["proxy_password"])
            self._using_proxy = True
        elif self._using_proxy:
            self.setProxy(QtCore.QString(), QtCore.QString())
            self._using_proxy = False
        self.setHost(host, port)
        return header

    def get(self, host, port, path, handler):
        header = self._prepare("GET", host, port, path)
        requestid = self.request(header)
        self._request_handlers[requestid] = handler

    def post(self, host, port, path, data, handler):
        header = self._prepare("POST", host, port, path)
        requestid = self.request(header, data)
        self._request_handlers[requestid] = handler

    def get_release_by_id(self, releaseid, handler, inc=[]):
        host = self.config.setting["server_host"]
        port = self.config.setting["server_port"]
        path = "/ws/1/release/%s?type=xml&inc=%s" % (releaseid, "+".join(inc))
        self.get(host, port, path, handler)

    def get_track_by_id(self, releaseid, handler, inc=[]):
        host = self.config.setting["server_host"]
        port = self.config.setting["server_port"]
        path = "/ws/1/track/%s?type=xml&inc=%s" % (releaseid, "+".join(inc))
        self.get(host, port, path, handler)

    def find_releases(self, handler, **kwargs):
        host = self.config.setting["server_host"]
        port = self.config.setting["server_port"]
        filters = []
        for name, value in kwargs.items():
            value = str(QtCore.QUrl.toPercentEncoding(value))
            filters.append('%s=%s' % (str(name), value))
        path = "/ws/1/release/?type=xml&" + "&".join(filters)
        self.get(host, port, path, handler)

    def submit_puids(self, puids, handler):
        host = self.config.setting["server_host"]
        port = self.config.setting["server_port"]
        data = ('client=MusicBrainz Picard-%s&' % version_string) + '&'.join(['puid=%s%%20%s' % i for i in puids.items()])
        header = self._prepare("POST", host, port, '/ws/1/track/')
        requestid = self.request(header, None)
        self._puid_data[requestid] = data.encode('ascii', 'ignore'), handler
