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

import sys
import re
import time
import os.path
from collections import deque, defaultdict
from PyQt4 import QtCore, QtNetwork, QtXml
from PyQt4.QtGui import QDesktopServices
from PyQt4.QtCore import QUrl
from picard import version_string
from picard.util import partial
from picard.const import ACOUSTID_KEY, ACOUSTID_HOST


REQUEST_DELAY = defaultdict(lambda: 1000)
REQUEST_DELAY[(ACOUSTID_HOST, 80)] = 333
REQUEST_DELAY[("coverartarchive.org", 80)] = 0
USER_AGENT_STRING = 'MusicBrainz%%20Picard-%s' % version_string


def _escape_lucene_query(text):
    return re.sub(r'([+\-&|!(){}\[\]\^"~*?:\\])', r'\\\1', text)


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

    def append_child(self, name, node=None):
        if node is None:
            node = XmlNode()
        self.children.setdefault(name, []).append(node)
        return node

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
        _node_name_re = re.compile('[^a-zA-Z0-9]')
        self._node_name = lambda n: _node_name_re.sub('_', unicode(n))
        self.path = []

    def startElement(self, namespace, name, qname, attrs):
        node = XmlNode()
        for i in xrange(attrs.count()):
            node.attribs[self._node_name(attrs.localName(i))] = unicode(attrs.value(i))
        self.node.append_child(self._node_name(name), node)
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

    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.manager = QtNetwork.QNetworkAccessManager()
        self.set_cache()
        self.setup_proxy()
        self.manager.finished.connect(self._process_reply)
        self._last_request_times = {}
        self._active_requests = {}
        self._high_priority_queues = {}
        self._low_priority_queues = {}
        self._hosts = []
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._run_next_task)
        self._request_methods = {
            "GET": self.manager.get,
            "POST": self.manager.post,
            "PUT": self.manager.put,
            "DELETE": self.manager.deleteResource
        }

    def set_cache(self, cache_size_in_mb=100):
        cache = QtNetwork.QNetworkDiskCache()
        location = QDesktopServices.storageLocation(QDesktopServices.CacheLocation)
        cache.setCacheDirectory(os.path.join(unicode(location), u'picard'))
        cache.setMaximumCacheSize(cache_size_in_mb * 1024 * 1024)
        self.manager.setCache(cache)
        self.log.debug("NetworkDiskCache dir: %s", cache.cacheDirectory())
        self.log.debug("NetworkDiskCache size: %s / %s", cache.cacheSize(),
                       cache.maximumCacheSize())

    def setup_proxy(self):
        self.proxy = QtNetwork.QNetworkProxy()
        if self.config.setting["use_proxy"]:
            self.proxy.setType(QtNetwork.QNetworkProxy.HttpProxy)
            self.proxy.setHostName(self.config.setting["proxy_server_host"])
            self.proxy.setPort(self.config.setting["proxy_server_port"])
            self.proxy.setUser(self.config.setting["proxy_username"])
            self.proxy.setPassword(self.config.setting["proxy_password"])
        self.manager.setProxy(self.proxy)

    def _start_request(self, method, host, port, path, data, handler, xml,
                       mblogin=False, cacheloadcontrol=None):
        self.log.debug("%s http://%s:%d%s", method, host, port, path)
        url = QUrl.fromEncoded("http://%s:%d%s" % (host, port, path))
        if mblogin:
            url.setUserName(self.config.setting["username"])
            url.setPassword(self.config.setting["password"])
        request = QtNetwork.QNetworkRequest(url)
        if cacheloadcontrol is not None:
            request.setAttribute(QtNetwork.QNetworkRequest.CacheLoadControlAttribute,
                                 cacheloadcontrol)
        request.setRawHeader("User-Agent", "MusicBrainz-Picard/%s" % version_string)
        if data is not None:
            if method == "POST" and host == self.config.setting["server_host"]:
                request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader, "application/xml; charset=utf-8")
            else:
                request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader, "application/x-www-form-urlencoded")
        send = self._request_methods[method]
        reply = send(request, data) if data is not None else send(request)
        key = (host, port)
        self._last_request_times[key] = time.time()
        self._active_requests[reply] = (request, handler, xml)
        return True

    @staticmethod
    def urls_equivalent(leftUrl, rightUrl):
        """
            Lazy method to determine whether two QUrls are equivalent. At the moment it assumes that if ports are unset
            that they are port 80 - in absence of a URL normalization function in QUrl or ability to use qHash
            from QT 4.7
        """
        return leftUrl.port(80) == rightUrl.port(80) and \
            leftUrl.toString(QUrl.FormattingOption(QUrl.RemovePort)) == rightUrl.toString(QUrl.FormattingOption(QUrl.RemovePort))

    def _process_reply(self, reply):
        try:
            request, handler, xml = self._active_requests.pop(reply)
        except KeyError:
            self.log.error("Error: Request not found for %s" % str(reply.request().url().toString()))
            return
        error = int(reply.error())
        redirect = reply.attribute(QtNetwork.QNetworkRequest.RedirectionTargetAttribute).toUrl()
        fromCache = reply.attribute(QtNetwork.QNetworkRequest.SourceIsFromCacheAttribute).toBool()
        cached = ' (CACHED)' if fromCache else ''
        self.log.debug("Received reply for %s: HTTP %d (%s) %s",
                       reply.request().url().toString(),
                       reply.attribute(QtNetwork.QNetworkRequest.HttpStatusCodeAttribute).toInt()[0],
                       reply.attribute(QtNetwork.QNetworkRequest.HttpReasonPhraseAttribute).toString(),
                       cached
                      )
        if handler is not None:
            if error:
                self.log.error("Network request error for %s: %s (QT code %d, HTTP code %d)",
                              reply.request().url().toString(),
                              reply.errorString(),
                              error,
                              reply.attribute(QtNetwork.QNetworkRequest.HttpStatusCodeAttribute).toInt()[0])

            # Redirect if found and not infinite
            if not redirect.isEmpty() and not XmlWebService.urls_equivalent(redirect, reply.request().url()):
                self.log.debug("Redirect to %s requested", redirect.toString())
                redirect_host = str(redirect.host())
                redirect_port = redirect.port(80)

                url = request.url()
                original_host = str(url.host())
                original_port = url.port(80)

                if ((original_host, original_port) in REQUEST_DELAY
                    and (redirect_host, redirect_port) not in REQUEST_DELAY):
                    self.log.debug("Setting rate limit for %s:%i to %i" %
                            (redirect_host, redirect_port,
                            REQUEST_DELAY[(original_host, original_port)]))
                    REQUEST_DELAY[(redirect_host, redirect_port)] =\
                        REQUEST_DELAY[(original_host, original_port)]

                self.get(redirect_host,
                         redirect_port,
                         # retain path, query string and anchors from redirect URL
                         redirect.toString(QUrl.FormattingOption(QUrl.RemoveAuthority | QUrl.RemoveScheme)),
                         handler, xml, priority=True, important=True,
                         cacheloadcontrol=request.attribute(QtNetwork.QNetworkRequest.CacheLoadControlAttribute))
            elif xml:
                xml_handler = XmlHandler()
                xml_handler.init()
                xml_reader = QtXml.QXmlSimpleReader()
                xml_reader.setContentHandler(xml_handler)
                xml_input = QtXml.QXmlInputSource(reply)
                xml_reader.parse(xml_input)
                handler(xml_handler.document, reply, error)
            else:
                handler(str(reply.readAll()), reply, error)
        reply.close()

    def get(self, host, port, path, handler, xml=True, priority=False,
            important=False, mblogin=False, cacheloadcontrol=None):
        func = partial(self._start_request, "GET", host, port, path, None,
                       handler, xml, mblogin, cacheloadcontrol=cacheloadcontrol)
        return self.add_task(func, host, port, priority, important=important)

    def post(self, host, port, path, data, handler, xml=True, priority=True, important=True, mblogin=True):
        self.log.debug("POST-DATA %r", data)
        func = partial(self._start_request, "POST", host, port, path, data, handler, xml, mblogin)
        return self.add_task(func, host, port, priority, important=important)

    def put(self, host, port, path, data, handler, priority=True, important=True, mblogin=True):
        func = partial(self._start_request, "PUT", host, port, path, data, handler, False, mblogin)
        return self.add_task(func, host, port, priority, important=important)

    def delete(self, host, port, path, handler, priority=True, important=True, mblogin=True):
        func = partial(self._start_request, "DELETE", host, port, path, None, handler, False, mblogin)
        return self.add_task(func, host, port, priority, important=important)

    def stop(self):
        self._high_priority_queues = {}
        self._low_priority_queues = {}
        for reply in self._active_requests.keys():
            reply.abort()

    def _run_next_task(self):
        delay = sys.maxint
        for key in self._hosts:
            queue = self._high_priority_queues.get(key) or self._low_priority_queues.get(key)
            if not queue:
                continue
            now = time.time()
            last = self._last_request_times.get(key)
            request_delay = REQUEST_DELAY[key]
            last_ms = (now - last) * 1000 if last is not None else request_delay
            if last_ms >= request_delay:
                self.log.debug("Last request to %s was %d ms ago, starting another one", key, last_ms)
                d = request_delay
                queue.popleft()()
            else:
                d = request_delay - last_ms
                self.log.debug("Waiting %d ms before starting another request to %s", d, key)
            if d < delay:
                delay = d
        if delay < sys.maxint:
            self._timer.start(delay)

    def add_task(self, func, host, port, priority, important=False):
        key = (host, port)
        if key not in self._hosts:
            self._hosts.append(key)
        if priority:
            queues = self._high_priority_queues
        else:
            queues = self._low_priority_queues
        queues.setdefault(key, deque())
        if important:
            queues[key].appendleft(func)
        else:
            queues[key].append(func)
        if not self._timer.isActive():
            self._timer.start(0)
        return (key, func, priority)

    def remove_task(self, task):
        key, func, priority = task
        if priority:
            queue = self._high_priority_queues[key]
        else:
            queue = self._low_priority_queues[key]
        try:
            queue.remove(func)
        except:
            pass

    def _get_by_id(self, entitytype, entityid, handler, inc=[], params=[], priority=False, important=False, mblogin=False):
        host = self.config.setting["server_host"]
        port = self.config.setting["server_port"]
        path = "/ws/2/%s/%s?inc=%s" % (entitytype, entityid, "+".join(inc))
        if params: path += "&" + "&".join(params)
        return self.get(host, port, path, handler, priority=priority, important=important, mblogin=mblogin)

    def get_release_by_id(self, releaseid, handler, inc=[], priority=True, important=False, mblogin=False):
        return self._get_by_id('release', releaseid, handler, inc, priority=priority, important=important, mblogin=mblogin)

    def get_track_by_id(self, trackid, handler, inc=[], priority=True, important=False, mblogin=False):
        return self._get_by_id('recording', trackid, handler, inc, priority=priority, important=important, mblogin=mblogin)

    def lookup_discid(self, discid, handler, priority=True, important=True):
        inc = ['artist-credits', 'labels']
        return self._get_by_id('discid', discid, handler, inc, params=["cdstubs=no"], priority=priority, important=important)

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
            value = str(QUrl.toPercentEncoding(QtCore.QString(value)))
            params.append('%s=%s' % (str(name), value))
        path = "/ws/2/%s/?%s" % (entitytype, "&".join(params))
        return self.get(host, port, path, handler)

    def find_releases(self, handler, **kwargs):
        return self._find('release', handler, kwargs)

    def find_tracks(self, handler, **kwargs):
        return self._find('recording', handler, kwargs)

    def _browse(self, entitytype, handler, kwargs, inc=[], priority=False, important=False):
        host = self.config.setting["server_host"]
        port = self.config.setting["server_port"]
        params = "&".join(["%s=%s" % (k, v) for k, v in kwargs.items()])
        path = "/ws/2/%s?%s&inc=%s" % (entitytype, params, "+".join(inc))
        return self.get(host, port, path, handler, priority=priority, important=important)

    def browse_releases(self, handler, priority=True, important=True, **kwargs):
        inc = ["media", "labels"]
        return self._browse("release", handler, kwargs, inc, priority=priority, important=important)

    def submit_ratings(self, ratings, handler):
        host = self.config.setting['server_host']
        port = self.config.setting['server_port']
        path = '/ws/2/rating/?client=' + USER_AGENT_STRING
        recordings = (''.join(['<recording id="%s"><user-rating>%s</user-rating></recording>' %
            (i[1], j*20) for i, j in ratings.items() if i[0] == 'recording']))
        data = _wrap_xml_metadata('<recording-list>%s</recording-list>' % recordings)
        return self.post(host, port, path, data, handler)

    def _encode_acoustid_args(self, args):
        filters = []
        args['client'] = ACOUSTID_KEY
        args['clientversion'] = version_string
        args['format'] = 'xml'
        for name, value in args.items():
            value = str(QUrl.toPercentEncoding(value))
            filters.append('%s=%s' % (str(name), value))
        return '&'.join(filters)

    def query_acoustid(self, handler, **args):
        host, port = ACOUSTID_HOST, 80
        body = self._encode_acoustid_args(args)
        return self.post(host, port, '/v2/lookup', body, handler, mblogin=False)

    def submit_acoustid_fingerprints(self, submissions, handler):
        args = {'user': self.config.setting["acoustid_apikey"]}
        for i, submission in enumerate(submissions):
            args['fingerprint.%d' % i] = str(submission.fingerprint)
            args['duration.%d' % i] = str(submission.duration)
            args['mbid.%d' % i] = str(submission.trackid)
            if submission.puid:
                args['puid.%d' % i] = str(submission.puid)
        host, port = ACOUSTID_HOST, 80
        body = self._encode_acoustid_args(args)
        return self.post(host, port, '/v2/submit', body, handler, mblogin=False)

    def download(self, host, port, path, handler, priority=False,
                 important=False, cacheloadcontrol=None):
        return self.get(host, port, path, handler, xml=False, priority=priority,
                        important=important, cacheloadcontrol=cacheloadcontrol)

    def get_collection(self, id, handler, limit=100, offset=0):
        host, port = self.config.setting['server_host'], self.config.setting['server_port']
        path = "/ws/2/collection"
        if id is not None:
            inc = ["releases", "artist-credits", "media"]
            path += "/%s/releases?inc=%s&limit=%d&offset=%d" % (id, "+".join(inc), limit, offset)
        return self.get(host, port, path, handler, priority=True, important=True, mblogin=True)

    def get_collection_list(self, handler):
        return self.get_collection(None, handler)

    def _collection_request(self, id, releases):
        while releases:
            ids = ";".join(releases if len(releases) <= 400 else releases[:400])
            releases = releases[400:]
            yield "/ws/2/collection/%s/releases/%s?client=%s" % (id, ids, USER_AGENT_STRING)

    def put_to_collection(self, id, releases, handler):
        host, port = self.config.setting['server_host'], self.config.setting['server_port']
        for path in self._collection_request(id, releases):
            self.put(host, port, path, "", handler)

    def delete_from_collection(self, id, releases, handler):
        host, port = self.config.setting['server_host'], self.config.setting['server_port']
        for path in self._collection_request(id, releases):
            self.delete(host, port, path, handler)
