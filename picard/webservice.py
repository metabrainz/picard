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

import os
import sys
import re
import traceback
from PyQt4 import QtCore, QtNetwork, QtXml
from picard import version_string
from picard.util import partial
from picard.const import PUID_SUBMIT_HOST, PUID_SUBMIT_PORT


REQUEST_DELAY = 1000
USER_AGENT_STRING = 'MusicBrainz%%20Picard-%s' % version_string


def _escape_lucene_query(text):
    return re.sub(r'([+\-&|!(){}\[\]\^"~*?:\\])', r'\\\1', text)


def _node_name(name):
    return re.sub('[^a-zA-Z0-9]', '_', unicode(name))


def _wrap_xml_metadata(data):
    return ('<?xml version="1.0" encoding="UTF-8"?>' +
        '<metadata xmlns="http://musicbrainz.org/ns/mmd-2.0#">%s</metadata>' % data)


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


class XmlWebServiceRequest(object):

    def __init__(self, request, reply, handler, xml=True):
        self.request = request
        self.reply = reply
        self.handler = handler
        self.xml = xml
        self.finished = False

    def errorString(self):
        return str(self.reply.errorString())


class XmlWebService(QtCore.QObject):
    """
    Signals:
      - authentication_required
    """

    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.manager = QtNetwork.QNetworkAccessManager()
        self.setup_proxy()
        self.manager.connect(self.manager, QtCore.SIGNAL("finished(QNetworkReply *)"), self._process_reply)
        self.manager.connect(self.manager, QtCore.SIGNAL("authenticationRequired(QNetworkReply *, QAuthenticator *)"), self._site_authenticate)
        self.manager.connect(self.manager, QtCore.SIGNAL("proxyAuthenticationRequired(QNetworkProxy *, QAuthenticator *)"), self._proxy_authenticate)
        self._last_request_times = {}
        self._active_hosts = set()
        self._active_requests = {}
        self._queue = []
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._run_next_task)

    def setup_proxy(self):
        self.proxy = QtNetwork.QNetworkProxy()
        if self.config.setting["use_proxy"]:
            self.proxy.setType(QtNetwork.QNetworkProxy.HttpProxy)
            self.proxy.setHostName(self.config.setting["proxy_server_host"])
            self.proxy.setPort(self.config.setting["proxy_server_port"])
            self.proxy.setUser(self.config.setting["proxy_username"])
            self.proxy.setPassword(self.config.setting["proxy_password"])
        self.manager.setProxy(self.proxy)

    def _prepare_request(self, method, host, port, path, username=None, password=None):
        self.log.debug("%s http://%s:%d%s", method, host, port, path)
        self.url = QtCore.QUrl.fromEncoded("http://%s:%d%s" % (host, port, path))
        if username:
            self.url.setUserName(username)
            self.url.setPassword(password)
        self.genrequest = QtNetwork.QNetworkRequest(self.url)
        self.genrequest.setRawHeader("User-Agent", "MusicBrainz-Picard/%s" % version_string)
        if method == "POST":
            contenttype = "application/x-www-form-urlencoded" if host == "ofa.musicdns.org" else "application/xml; charset=utf-8"
            self.genrequest.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader, contenttype)
        return self.genrequest

    def _start_request(self, host, port, request):
        key = host, port
        self._last_request_times[key] = QtCore.QTime.currentTime()
        #print "starting request", key, request.reply, self._last_request_times[key]
        request.key = key
        self._active_requests[request.reply] = request
        self._active_hosts.add(key)

    def _finish_request(self):
        for reply, request in self._active_requests.items():
            if request.finished:
                self._active_hosts.remove(request.key)
                del self._active_requests[reply]
        self._timer.start(0)

    def _process_reply(self, reply):
        try:
            #print "finishing request", reply
            request = self._active_requests.get(reply)
            if request is None:
                print "**** request not found", reply.request().url(), reply
                return
            request.finished = True
            error = int(reply.error())
            if request.handler is not None:
                if error:
                    #print "ERROR", reply.error(), reply.errorString()
                    #for name in reply.rawHeaderList():
                    #    print name, reply.rawHeader(name)
                    self.log.debug("HTTP Error: %d", error)
                if request.xml:
                    xml_handler = XmlHandler()
                    xml_handler.init()
                    xml_reader = QtXml.QXmlSimpleReader()
                    xml_reader.setContentHandler(xml_handler)
                    xml_input = QtXml.QXmlInputSource(reply)
                    xml_reader.parse(xml_input)
                    request.handler(xml_handler.document, request, error)
                else:
                    request.handler(str(reply.readAll()), request, error)
            reply.close()
        finally:
            QtCore.QTimer.singleShot(0, self._finish_request)

    def _get(self, host, port, path, handler, xml=True, mblogin=False):
        if mblogin:
            self.username = self.config.setting["username"]
            self.password = self.config.setting["password"]
            request = self._prepare_request("GET", host, port, path, self.username, self.password)
        else:
            request = self._prepare_request("GET", host, port, path)
        reply = self.manager.get(request)
        self._start_request(host, port, XmlWebServiceRequest(request, reply, handler, xml))
        return True

    def _post(self, host, port, path, data, handler, mblogin=True):
        self.log.debug("POST-DATA %r", data)
        if mblogin:
            self.username = self.config.setting["username"]
            self.password = self.config.setting["password"]
            request = self._prepare_request("POST", host, port, path, self.username, self.password)
        else:
            request = self._prepare_request("POST", host, port, path)
        reply = self.manager.post(request, data)
        self._start_request(host, port, XmlWebServiceRequest(request, reply, handler))
        return True

    def get(self, host, port, path, handler, xml = True, position = None, mblogin = False):
        func = partial(self._get, host, port, path, handler, xml, mblogin)
        self.add_task(func, host, port, position)

    def post(self, host, port, path, data, handler, position = None, mblogin = True):
        func = partial(self._post, host, port, path, data, handler, mblogin)
        self.add_task(func, host, port, position)

    def _site_authenticate(self, reply, authenticator):
        self.emit(QtCore.SIGNAL("authentication_required"), reply, authenticator)

    def _proxy_authenticate(self, proxy, authenticator):
        self.emit(QtCore.SIGNAL("proxyAuthentication_required"), proxy, authenticator)

    def stop(self):
        for request in self._active_requests.itervalues():
            request.reply.abort()

    def _run_next_task(self):
        delay, index, key = sys.maxint, None, None
        now = QtCore.QTime.currentTime()
        for i, (k, task) in enumerate(self._queue):
            if k == key or k in self._active_hosts:
                continue
            last = self._last_request_times.get(k)
            last_ms = last.msecsTo(now) if last is not None else REQUEST_DELAY
            if last_ms >= REQUEST_DELAY:
                self.log.debug("Last request to %s was %d ms ago, starting another one", k, last_ms)
                del self._queue[i]
                task()
                return
            d = REQUEST_DELAY - last_ms
            if d < delay:
                delay, index, key = d, i, k
        if index is not None and not self._timer.isActive():
            self.log.debug("Waiting %d ms before starting another request to %s",
                           delay, key)
            self._timer.start(delay)

    def add_task(self, func, host, port, position=None):
        key = (host, port)
        if position is None:
            self._queue.append((key, func))
        else:
            self._queue.insert(position, (key, func))
        if key not in self._active_hosts:
            self._timer.start(0)

    def _get_by_id(self, entitytype, entityid, handler, inc=[], mblogin=False):
        host = self.config.setting["server_host"]
        port = self.config.setting["server_port"]
        path = "/ws/2/%s/%s?inc=%s" % (entitytype, entityid, "+".join(inc))
        if entitytype == "discid": path += "&cdstubs=no"
        self.get(host, port, path, handler, mblogin=mblogin)

    def get_release_group_by_id(self, releasegroupid, handler):
        inc = ['releases', 'media']
        self._get_by_id('release-group', releasegroupid, handler, inc)

    def get_release_by_id(self, releaseid, handler, inc=[], mblogin=False):
        self._get_by_id('release', releaseid, handler, inc, mblogin=mblogin)

    def get_track_by_id(self, trackid, handler):
        inc = ['releases', 'release-groups', 'media', 'artist-credits']
        self._get_by_id('recording', trackid, handler, inc)

    def lookup_puid(self, puid, handler):
        inc = ['releases', 'release-groups', 'media', 'artist-credits']
        self._get_by_id('puid', puid, handler, inc)

    def lookup_discid(self, discid, handler):
        self._get_by_id('discid', discid, handler, ['artist-credits'])

    def _find(self, entitytype, handler, kwargs):
        host = self.config.setting["server_host"]
        port = self.config.setting["server_port"]
        filters = []
        query = []
        for name, value in kwargs.items():
            if name == 'limit':
                filters.append((name, value))
            else:
                value = _escape_lucene_query(value).strip().lower()
                if value: query.append('%s:(%s)' % (name, value))
        if query: filters.append(('query', ' '.join(query)))
        params = []
        for name, value in filters:
            value = str(QtCore.QUrl.toPercentEncoding(QtCore.QString(value)))
            params.append('%s=%s' % (str(name), value))
        path = "/ws/2/%s/?%s" % (entitytype, "&".join(params))
        self.get(host, port, path, handler)

    def find_releases(self, handler, **kwargs):
        self._find('release', handler, kwargs)

    def find_tracks(self, handler, **kwargs):
        self._find('recording', handler, kwargs)

    def submit_puids(self, puids, handler):
        path = '/ws/2/recording/?client=' + USER_AGENT_STRING
        recordings = ''.join(['<recording id="%s"><puid-list><puid id="%s"/></puid-list></recording>' % i for i in puids.items()])
        data = _wrap_xml_metadata('<recording-list>%s</recording-list>' % recordings)
        self.post(PUID_SUBMIT_HOST, PUID_SUBMIT_PORT, path, data, handler)

    def submit_ratings(self, ratings, handler):
        host = self.config.setting['server_host']
        port = self.config.setting['server_port']
        path = '/ws/2/rating/?client=' + USER_AGENT_STRING
        recordings = (''.join(['<recording id="%s"><user-rating>%s</user-rating></recording>' %
            (i[1], j*20) for i, j in ratings.items() if i[0] == 'recording']))
        data = _wrap_xml_metadata('<recording-list>%s</recording-list>' % recordings)
        self.post(host, port, path, data, handler)

    def query_musicdns(self, handler, **kwargs):
        host = 'ofa.musicdns.org'
        port = 80
        filters = []
        for name, value in kwargs.items():
            value = str(QtCore.QUrl.toPercentEncoding(value))
            filters.append('%s=%s' % (str(name), value))
        self.post(host, port, '/ofa/1/track/', '&'.join(filters), handler, mblogin = False)

    def download(self, host, port, path, handler, position=None):
        self.get(host, port, path, handler, xml=False, position=position)
