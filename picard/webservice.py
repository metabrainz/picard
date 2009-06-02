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

import hashlib
import os.path
import re
from PyQt4 import QtCore, QtNetwork, QtXml
from picard import version_string
from picard.util import partial
from picard.const import PUID_SUBMIT_HOST, PUID_SUBMIT_PORT, MAX_RATINGS_PER_REQUEST


def _escape_lucene_query(text):
    return re.sub(r'([+\-&|!(){}\[\]\^"~*?:\\])', r'\\\1', text)


def _md5(text):
    m = hashlib.md5()
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


class XmlWebService(QtNetwork.QHttp):
    """
    Signals:
      - authentication_required
    """

    def __init__(self, cachedir, parent=None):
        QtNetwork.QHttp.__init__(self, parent)
        self.connect(self, QtCore.SIGNAL("requestStarted(int)"), self._start_request)
        self.connect(self, QtCore.SIGNAL("requestFinished(int, bool)"), self._finish_request)
        self.connect(self, QtCore.SIGNAL("readyRead(const QHttpResponseHeader &)"), self._read_data)
        self.connect(self, QtCore.SIGNAL("authenticationRequired(const QString &, quint16, QAuthenticator *)"), self._authenticate)
        self._cachedir = cachedir
        self._request_handlers = {}
        self._last_request_time = None
        self._used_http_auth = False
        self._xml_handler = XmlHandler()
        self._xml_reader = QtXml.QXmlSimpleReader()
        self._xml_reader.setContentHandler(self._xml_handler)
        self._xml_input = QtXml.QXmlInputSource()
        self._using_proxy = False
        self._queue = []

    def _make_cache_filename(self, host, port, path):
        url = "%s:%d%s" % (host, port, path)
        filename = hashlib.sha1(url).hexdigest()
        m = re.search(r"\.([a-z]{2,3})(?:\?|$)", url)
        if m:
            filename += "." + m.group(1)
        return os.path.join(self._cachedir, filename)

    def _start_request(self, request_id):
        try:
            handler, xml = self._request_handlers[request_id]
        except KeyError:
            return

        self._last_request_time = QtCore.QTime.currentTime()
        if xml:
            self._xml_handler.init()
            self._new_request = True

    def _finish_request(self, request_id, error):
        try:
            handler, xml = self._request_handlers[request_id]
        except KeyError:
            return

        try:
            response = self.lastResponse()
            statuscode = response.statusCode()

            # handle 302 redirects
            if not error and response.isValid() and (statuscode == 302 or statuscode == 307):
                location = response.value("Location")
                if location:
                    self.log.debug("Redirect => %s", location)
                    location = QtCore.QUrl(location)
                    self.get(location.host(), location.port(80), location.path(), handler, xml=xml, position=1)
                    # don't call the handle for this request, only for the redirected one
                    handler = None

            # cleanup the dict of request handlers
            del self._request_handlers[request_id]

            # call the handler
            if handler is not None:
                if response.isValid() and statuscode != 200:
                    error = True
                if error:
                    self.log.debug("HTTP Error: %s %s (status: %s)", self.errorString(), self.error(), statuscode)
                if xml:
                    handler(self._xml_handler.document, self, error)
                else:
                    handler(str(self.readAll()), self, error)

        finally:
            delay = min(1000, 1000 - self._last_request_time.msecsTo(QtCore.QTime.currentTime()))
            if delay > 0:
                self.log.debug("Waiting %d ms before starting another HTTP request", delay)
                QtCore.QTimer.singleShot(delay, self._run_next_task)
            else:
                self._run_next_task()

    def _authenticate(self, host, port, authenticator):
        self.emit(QtCore.SIGNAL("authentication_required"), host, port, authenticator)

    def _run_next_task(self):
        while len(self._queue) >= 1:
            try:
                if self._next_task():
                    return
            except:
                import traceback
                self.log.error(traceback.format_exc())

    def _next_task(self):
        self._queue.pop(0)
        if self._queue:
            return self._queue[0]()
        return True

    def _read_data(self, response):
        request_id = self.currentId()
        if not request_id:
            return
        handler, xml = self._request_handlers[request_id]
        if xml:
            self._xml_input.setData(self.readAll())
            if self._new_request:
                self._xml_reader.parse(self._xml_input, True)
                self._new_request = False
            else:
                self._xml_reader.parseContinue()

    def _prepare(self, method, host, port, path):
        self.log.debug("%s http://%s:%d%s", method, host, port, path)
        header = QtNetwork.QHttpRequestHeader(method, path)
        if port == 80:
            header.setValue("Host", "%s" % host)
        else:
            header.setValue("Host", "%s:%d" % (host, port))
        header.setValue("User-Agent", "MusicBrainz-Picard/%s" % version_string)
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

    def _get(self, host, port, path, handler, xml=True):
        header = self._prepare("GET", host, port, path)
        requestid = self.request(header)
        self._request_handlers[requestid] = (handler, xml)
        return True

    def _post(self, host, port, path, data, handler):
        header = self._prepare("POST", host, port, path)
        self.log.debug("POST-DATA %r", data)
        requestid = self.request(header, data)
        self._request_handlers[requestid] = (handler, True)
        return True

    def add_task(self, func, position=None):
        if position is None:
            self._queue.append(func)
        else:
            self._queue.insert(position, func)
        if len(self._queue) == 1:
            func()

    def get(self, host, port, path, handler, xml=True, position=None):
        func = partial(self._get, host, port, path, handler, xml)
        self.add_task(func, position)

    def post(self, host, port, path, data, handler, position=None):
        func = partial(self._post, host, port, path, data, handler)
        self.add_task(func, position)

    def _get_by_id(self, entitytype, entityid, handler, inc=[]):
        host = self.config.setting["server_host"]
        port = self.config.setting["server_port"]
        path = "/ws/1/%s/%s?type=xml&inc=%s" % (entitytype, entityid, "+".join(inc))
        self.get(host, port, path, handler)

    def get_release_by_id(self, releaseid, handler, inc=[]):
        self._get_by_id('release', releaseid, handler, inc)

    def get_track_by_id(self, releaseid, handler, inc=[]):
        self._get_by_id('track', releaseid, handler, inc)

    def _find(self, entitytype, handler, kwargs):
        host = self.config.setting["server_host"]
        port = self.config.setting["server_port"]
        filters = []
        query = []
        for name, value in kwargs.items():
            if name in ('limit', 'puid', 'discid'):
                filters.append((name, value))
            elif name == 'cdstubs':
                filters.append((name, 'yes' if value else 'no'))
            else:
                value = _escape_lucene_query(value).strip().lower()
                if value:
                    query.append('%s:(%s)' % (name, value))
        if query:
            filters.append(('query', ' '.join(query)))
        params = []
        for name, value in filters:
            value = str(QtCore.QUrl.toPercentEncoding(QtCore.QString(value)))
            params.append('%s=%s' % (str(name), value))
        path = "/ws/1/%s/?type=xml&%s" % (entitytype, "&".join(params))
        self.get(host, port, path, handler)

    def find_releases(self, handler, **kwargs):
        self._find('release', handler, kwargs)

    def find_tracks(self, handler, **kwargs):
        self._find('track', handler, kwargs)

    def _submit_puids(self, puids, handler):
        data = ('client=MusicBrainz Picard-%s&' % version_string) + '&'.join(['puid=%s%%20%s' % i for i in puids.items()])
        data = data.encode('ascii', 'ignore')
        header = self._prepare("POST", PUID_SUBMIT_HOST, PUID_SUBMIT_PORT, '/ws/1/track/')
        self.setUser(self.config.setting["username"],
                     self.config.setting["password"])
        if not self._used_http_auth:
            # dummy request to workaround bugs in  Qt 4.3
            requestid = self.request(header, '')
            self._request_handlers[requestid] = (None, True)
            self._used_http_auth = True
        requestid = self.request(header, data)
        self._request_handlers[requestid] = (handler, True)

    def submit_puids(self, puids, handler):
        func = partial(self._submit_puids, puids, handler)
        self.add_task(func)

    def submit_ratings(self, ratings, handler):
        """
        Submit entity ratings to the MB server.
        Ratings is a hash containing the numerical ratings for each
        entity. The key of the hash is a tuple consisting of the entity type
        and an entity ID.
        """
        data_list = []
        number = 0
        for (entitytype, entityid), rating in ratings.items():
            data_list.append('&entity.%i=%s&id.%i=%s&rating.%i=%i' % (number, entitytype, 
                                                                      number, entityid,
                                                                      number, rating))
            number = (number + 1) % MAX_RATINGS_PER_REQUEST
        
        self.setUser(self.config.setting["username"],
                     self.config.setting["password"])
        
        i = 0
        while i < len(data_list):
            data = "".join(data_list[i : i + MAX_RATINGS_PER_REQUEST])
            data = data.encode('ascii', 'ignore')
            self.post(self.config.setting['server_host'], self.config.setting['server_port'], '/ws/1/rating/', data, handler)
            i += MAX_RATINGS_PER_REQUEST

    def query_musicdns(self, handler, **kwargs):
        host = 'ofa.musicdns.org'
        port = 80
        filters = []
        for name, value in kwargs.items():
            value = str(QtCore.QUrl.toPercentEncoding(value))
            filters.append('%s=%s' % (str(name), value))
        self.post(host, port, '/ofa/1/track/', '&'.join(filters), handler)

    def download(self, host, port, path, handler, position=None):
        self.get(host, port, path, handler, xml=False, position=position)

    def cleanup(self):
        # FIXME remove old cache entries
        pass
