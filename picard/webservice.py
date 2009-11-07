# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2009 Carlin Mangar
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
import traceback
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


class XmlWebService(QtCore.QObject):
    """
    Signals:
      - authentication_required
    """

    def __init__(self, cachedir, cachesize = 6000.0, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.manager = QtNetwork.QNetworkAccessManager()
        self.setup_cache(cachedir, cachesize)
        self.setup_proxy()
        self.setup_xml()
        self.manager.connect(self.manager, QtCore.SIGNAL("finished(QNetworkReply *)"), self._process_reply)
        self.manager.connect(self.manager, QtCore.SIGNAL("authenticationRequired(QNetworkReply *, QAuthenticator *)"), self._site_authenticate)
        self.manager.connect(self.manager, QtCore.SIGNAL("proxyAuthenticationRequired(QNetworkProxy *, QAuthenticator *)"), self._proxy_authenticate)
        self._activeRequests = {}
        self._requestHandlers = {}
        self._queue = []

    def setup_xml(self):
        self.xml_handler = XmlHandler()
        self.xml_reader = QtXml.QXmlSimpleReader()
        self.xml_reader.setContentHandler(self.xml_handler)
        self.xml_input = QtXml.QXmlInputSource()

    def setup_cache(self, cachedir, cachesize):
        self._cache = QtNetwork.QNetworkDiskCache()
        self._cache.setCacheDirectory(cachedir)
        self._cache.setMaximumCacheSize(cachesize)
        self.manager.setCache(self._cache)

    def setup_proxy(self):
        self.proxy = QtNetwork.QNetworkProxy()
        if self.config.setting["use_proxy"]:
            self.proxy.setType(QtNetwork.QNetworkProxy.HttpProxy)
            self.proxy.setHostName(self.config.setting["proxy_server_host"])
            self.proxy.setPort(self.config.setting["proxy_server_port"])
            self.proxy.setUser(self.config.setting["proxy_username"])
            self.proxy.setPassword(self.config.setting["proxy_password"])
        self.manager.setProxy(self.proxy)

    def _prepare_request(self, method, host, port, path, username = None, password = None):
        self.log.debug("%s http://%s:%d%s", method, host, port, path)
        if not username or username == '':
            self.url = QtCore.QUrl.fromEncoded("http://%s:%d%s" % (host, port, path))
        else:
            self.url = QtCore.QUrl.fromEncoded("http://%s:%s@%s:%d%s" % (username, password, host, port, path))
        self.genrequest = QtNetwork.QNetworkRequest(self.url)
        self.genrequest.setRawHeader("User-Agent", "MusicBrainz-Picard/%s" % version_string)
        #self.genrequest.setRawHeader("Connection", "close")
        if method == "POST": self.genrequest.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader, "application/x-www-form-urlencoded")
        return self.genrequest

    def _get(self, host, port, path, handler, xml = True, mblogin = False):
        if mblogin:
            self.username = self.config.setting["username"]
            self.password = self.config.setting["password"]
            self.request = self._prepare_request("GET", host, port, path, self.username, self.password)
        else:
            self.request = self._prepare_request("GET", host, port, path)
        self._activeRequests[str(self.request.url())] = self.manager.get(self.request)
        self._requestHandlers[str(self.request.url())] = (handler, xml)
        return True

    def _post(self, host, port, path, data, handler, mblogin = True):
        self.log.debug("POST-DATA %r", data)
        if mblogin:
            self.username = self.config.setting["username"]
            self.password = self.config.setting["password"]
            self.request = self._prepare_request("POST", host, port, path, self.username, self.password)
        else:
            self.request = self._prepare_request("POST", host, port, path)        
        self._activeRequests[str(self.request.url())] = self.manager.post(self.request, data)
        self._requestHandlers[str(self.request.url())] = (handler, True)
        return True

    def get(self, host, port, path, handler, xml = True, position = None, mblogin = False):
        func = partial(self._get, host, port, path, handler, xml, mblogin)
        self.add_task(func, position)

    def post(self, host, port, path, data, handler, position = None, mblogin = True):
        func = partial(self._post, host, port, path, data, handler, mblogin)
        self.add_task(func, position)
        
    def query_musicdns(self, handler, **kwargs):
        host = 'ofa.musicdns.org'
        port = 80
        filters = []
        for name, value in kwargs.items():
            value = str(QtCore.QUrl.toPercentEncoding(value))
            filters.append('%s=%s' % (str(name), value))
        self.post(host, port, '/ofa/1/track/', '&'.join(filters), handler, mblogin = False)
        
    def _process_reply(self, reply):
        try: handler, xml = self._requestHandlers[str(reply.request().url())]
        except KeyError: return
        del self._requestHandlers[str(reply.request().url())]
        del self._activeRequests[str(reply.request().url())]
        error = int(reply.error())
        if handler is not None:
            if error:
                self.log.debug("HTTP Error: %d", error)
            if xml:
                self.xml_handler.init()
                self.xml_input = QtXml.QXmlInputSource(reply)
                self.xml_reader.parse(self.xml_input)
                handler(self.xml_handler.document, self, error)
            else:
                handler(str(reply.readAll()), self, error)
        reply.close()
        self._run_next_task()

    def _site_authenticate(self, reply, authenticator):
        self.emit(QtCore.SIGNAL("authentication_required"), reply, authenticator)

    def _proxy_authenticate(self, proxy, authenticator):
        self.emit(QtCore.SIGNAL("proxyAuthentication_required"), proxy, authenticator)
    
    def abortall(self):
        for reply in self._activeRequests.values():
            reply.abort()

    def stop(self):
        self.manager.cache().clear()
        self.abortall()
        
    def _make_cache_filename(self, host, port, path):
        url = "%s:%d%s" % (host, port, path)
        filename = hashlib.sha1(url).hexdigest()
        m = re.search(r"\.([a-z]{2,3})(?:\?|$)", url)
        if m: filename += "." + m.group(1)
        return os.path.join(self._cachedir, filename)

    def _run_next_task(self):
        while len(self._queue) >= 1:
            try:
                if self._next_task(): return
            except: self.log.error(traceback.format_exc())

    def _next_task(self):
        self._queue.pop(0)
        if self._queue: return self._queue[0]()
        return True

    def add_task(self, func, position=None):
        if position is None: self._queue.append(func)
        else: self._queue.insert(position, func)
        if len(self._queue) == 1: func()

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
            if name in ('limit', 'puid', 'discid'): filters.append((name, value))
            elif name == 'cdstubs': filters.append((name, 'yes' if value else 'no'))
            else:
                value = _escape_lucene_query(value).strip().lower()
                if value: query.append('%s:(%s)' % (name, value))
        if query: filters.append(('query', ' '.join(query)))
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

    def submit_puids(self, puids, handler):
        data = ('client=MusicBrainz Picard-%s&' % version_string) + '&'.join(['puid=%s%%20%s' % i for i in puids.items()])
        data = data.encode('ascii', 'ignore')
        self.post(PUID_SUBMIT_HOST, PUID_SUBMIT_PORT, '/ws/1/track/', data, handler)

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
        for i in range(0, len(data_list), MAX_RATINGS_PER_REQUEST):
            data = "".join(data_list[i : i + MAX_RATINGS_PER_REQUEST])
            data = data.encode('ascii', 'ignore')
            self.post(self.config.setting['server_host'], self.config.setting['server_port'], '/ws/1/rating/', data, handler)

    def download(self, host, port, path, handler, position=None):
        self.get(host, port, path, handler, xml=False, position=position)


