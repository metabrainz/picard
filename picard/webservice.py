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
import platform
import math
from collections import deque, defaultdict
from functools import partial
from PyQt4 import QtCore, QtNetwork
from PyQt4.QtGui import QDesktopServices
from PyQt4.QtCore import QUrl, QXmlStreamReader
from picard import (PICARD_APP_NAME,
                    PICARD_ORG_NAME,
                    PICARD_VERSION_STR,
                    config,
                    log)
from picard.const import (ACOUSTID_KEY,
                          ACOUSTID_HOST,
                          ACOUSTID_PORT,
                          CAA_HOST,
                          CAA_PORT)
from picard.oauth import OAuthManager
from picard.util import build_qurl


COUNT_REQUESTS_DELAY_MS = 250
REQUEST_DELAY = defaultdict(lambda: 1000)
REQUEST_DELAY[(ACOUSTID_HOST, ACOUSTID_PORT)] = 333
REQUEST_DELAY[(CAA_HOST, CAA_PORT)] = 0
USER_AGENT_STRING = '%s-%s/%s (%s;%s-%s)' % (PICARD_ORG_NAME, PICARD_APP_NAME,
                                             PICARD_VERSION_STR,
                                             platform.platform(),
                                             platform.python_implementation(),
                                             platform.python_version())
CLIENT_STRING = str(QUrl.toPercentEncoding('%s %s-%s' % (PICARD_ORG_NAME,
                                                         PICARD_APP_NAME,
                                                         PICARD_VERSION_STR)))


def escape_lucene_query(text):
    return re.sub(r'([+\-&|!(){}\[\]\^"~*?:\\/])', r'\\\1', text)


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
                raise AttributeError(name)


_node_name_re = re.compile('[^a-zA-Z0-9]')


def _node_name(n):
    return _node_name_re.sub('_', unicode(n))


def _read_xml(stream):
    document = XmlNode()
    current_node = document
    path = []

    while not stream.atEnd():
        stream.readNext()

        if stream.isStartElement():
            node = XmlNode()
            attrs = stream.attributes()

            for i in xrange(attrs.count()):
                attr = attrs.at(i)
                node.attribs[_node_name(attr.name())] = unicode(attr.value())

            current_node.append_child(_node_name(stream.name()), node)
            path.append(current_node)
            current_node = node

        elif stream.isEndElement():
            current_node = path.pop()

        elif stream.isCharacters():
            current_node.text += unicode(stream.text())

    return document


class XmlWebService(QtCore.QObject):

    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.manager = QtNetwork.QNetworkAccessManager()
        self.oauth_manager = OAuthManager(self)
        self.set_cache()
        self.setup_proxy()
        self.manager.finished.connect(self._process_reply)
        self._last_request_times = defaultdict(lambda: 0)
        self._request_methods = {
            "GET": self.manager.get,
            "POST": self.manager.post,
            "PUT": self.manager.put,
            "DELETE": self.manager.deleteResource
        }
        self._init_queues()
        self._init_timers()

    def _init_queues(self):
        self._active_requests = {}
        self._queues = defaultdict(lambda: defaultdict(deque))
        self.num_pending_web_requests = 0
        self._last_num_pending_web_requests = -1

    def _init_timers(self):
        self._timer_run_next_task = QtCore.QTimer(self)
        self._timer_run_next_task.setSingleShot(True)
        self._timer_run_next_task.timeout.connect(self._run_next_task)
        self._timer_count_pending_requests = QtCore.QTimer(self)
        self._timer_count_pending_requests.setSingleShot(True)
        self._timer_count_pending_requests.timeout.connect(self._count_pending_requests)

    def set_cache(self, cache_size_in_mb=100):
        cache = QtNetwork.QNetworkDiskCache()
        location = QDesktopServices.storageLocation(QDesktopServices.CacheLocation)
        cache.setCacheDirectory(os.path.join(unicode(location), u'picard'))
        cache.setMaximumCacheSize(cache_size_in_mb * 1024 * 1024)
        self.manager.setCache(cache)
        log.debug("NetworkDiskCache dir: %s", cache.cacheDirectory())
        log.debug("NetworkDiskCache size: %s / %s", cache.cacheSize(),
                  cache.maximumCacheSize())

    def setup_proxy(self):
        proxy = QtNetwork.QNetworkProxy()
        if config.setting["use_proxy"]:
            proxy.setType(QtNetwork.QNetworkProxy.HttpProxy)
            proxy.setHostName(config.setting["proxy_server_host"])
            proxy.setPort(config.setting["proxy_server_port"])
            proxy.setUser(config.setting["proxy_username"])
            proxy.setPassword(config.setting["proxy_password"])
        self.manager.setProxy(proxy)

    def _start_request_continue(self, method, host, port, path, data, handler, xml,
                                mblogin=False, cacheloadcontrol=None, refresh=None,
                                access_token=None, queryargs=None):
        url = build_qurl(host, port, path=path, mblogin=mblogin,
                         queryargs=queryargs)
        request = QtNetwork.QNetworkRequest(url)
        if mblogin and access_token:
            request.setRawHeader("Authorization", "Bearer %s" % access_token)
        if mblogin or (method == "GET" and refresh):
            request.setPriority(QtNetwork.QNetworkRequest.HighPriority)
            request.setAttribute(QtNetwork.QNetworkRequest.CacheLoadControlAttribute,
                                 QtNetwork.QNetworkRequest.AlwaysNetwork)
        elif method == "PUT" or method == "DELETE":
            request.setPriority(QtNetwork.QNetworkRequest.HighPriority)
        elif cacheloadcontrol is not None:
            request.setAttribute(QtNetwork.QNetworkRequest.CacheLoadControlAttribute,
                                 cacheloadcontrol)
        request.setRawHeader("User-Agent", USER_AGENT_STRING)
        if xml:
            request.setRawHeader("Accept", "application/xml")
        if data is not None:
            if method == "POST" and host == config.setting["server_host"] and xml:
                request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader, "application/xml; charset=utf-8")
            else:
                request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader, "application/x-www-form-urlencoded")
        send = self._request_methods[method]
        reply = send(request, data) if data is not None else send(request)
        self._remember_request_time((host, port))
        self._active_requests[reply] = (request, handler, xml, refresh)

    def _start_request(self, method, host, port, path, data, handler, xml,
                       mblogin=False, cacheloadcontrol=None, refresh=None,
                       queryargs=None):
        def start_request_continue(access_token=None):
            self._start_request_continue(
                method, host, port, path, data, handler, xml,
                mblogin=mblogin, cacheloadcontrol=cacheloadcontrol, refresh=refresh,
                access_token=access_token, queryargs=queryargs)
        if mblogin and path != "/oauth2/token":
            self.oauth_manager.get_access_token(start_request_continue)
        else:
            start_request_continue()

    @staticmethod
    def urls_equivalent(leftUrl, rightUrl):
        """
            Lazy method to determine whether two QUrls are equivalent. At the moment it assumes that if ports are unset
            that they are port 80 - in absence of a URL normalization function in QUrl or ability to use qHash
            from QT 4.7
        """
        return leftUrl.port(80) == rightUrl.port(80) and \
            leftUrl.toString(QUrl.RemovePort) == rightUrl.toString(QUrl.RemovePort)

    @staticmethod
    def url_port(url):
        if url.scheme() == 'https':
            return url.port(443)
        return url.port(80)

    def _handle_reply(self, reply, request, handler, xml, refresh):
        error = int(reply.error())
        if error:
            log.error("Network request error for %s: %s (QT code %d, HTTP code %s)",
                      reply.request().url().toString(QUrl.RemoveUserInfo),
                      reply.errorString(),
                      error,
                      repr(reply.attribute(QtNetwork.QNetworkRequest.HttpStatusCodeAttribute))
                      )
            if handler is not None:
                handler(str(reply.readAll()), reply, error)
        else:
            redirect = reply.attribute(QtNetwork.QNetworkRequest.RedirectionTargetAttribute)
            fromCache = reply.attribute(QtNetwork.QNetworkRequest.SourceIsFromCacheAttribute)
            cached = ' (CACHED)' if fromCache else ''
            log.debug("Received reply for %s: HTTP %d (%s) %s",
                      reply.request().url().toString(QUrl.RemoveUserInfo),
                      reply.attribute(QtNetwork.QNetworkRequest.HttpStatusCodeAttribute),
                      reply.attribute(QtNetwork.QNetworkRequest.HttpReasonPhraseAttribute),
                      cached
                      )
            if handler is not None:
                # Redirect if found and not infinite
                if redirect:
                    url = request.url()
                    # merge with base url (to cover the possibility of the URL being relative)
                    redirect = url.resolved(redirect)
                    if not XmlWebService.urls_equivalent(redirect, reply.request().url()):
                        log.debug("Redirect to %s requested", redirect.toString(QUrl.RemoveUserInfo))
                        redirect_host = str(redirect.host())
                        redirect_port = self.url_port(redirect)
                        redirect_query = dict(redirect.encodedQueryItems())
                        redirect_path = redirect.path()

                        original_host = str(url.host())
                        original_port = self.url_port(url)

                        if ((original_host, original_port) in REQUEST_DELAY
                                and (redirect_host, redirect_port) not in REQUEST_DELAY):
                            log.debug("Setting rate limit for %s:%i to %i" %
                                      (redirect_host, redirect_port,
                                       REQUEST_DELAY[(original_host, original_port)]))
                            REQUEST_DELAY[(redirect_host, redirect_port)] =\
                                REQUEST_DELAY[(original_host, original_port)]

                        self.get(redirect_host,
                                 redirect_port,
                                 redirect_path,
                                 handler, xml, priority=True, important=True, refresh=refresh, queryargs=redirect_query,
                                 cacheloadcontrol=request.attribute(QtNetwork.QNetworkRequest.CacheLoadControlAttribute))
                    else:
                        log.error("Redirect loop: %s",
                                  reply.request().url().toString(QUrl.RemoveUserInfo)
                                  )
                        handler(str(reply.readAll()), reply, error)
                elif xml:
                    document = _read_xml(QXmlStreamReader(reply))
                    handler(document, reply, error)
                else:
                    handler(str(reply.readAll()), reply, error)

    def _process_reply(self, reply):
        try:
            request, handler, xml, refresh = self._active_requests.pop(reply)
        except KeyError:
            log.error("Request not found for %s" % reply.request().url().toString(QUrl.RemoveUserInfo))
            return
        try:
            self._handle_reply(reply, request, handler, xml, refresh)
        finally:
            reply.close()
            reply.deleteLater()

    def get(self, host, port, path, handler, xml=True, priority=False,
            important=False, mblogin=False, cacheloadcontrol=None, refresh=False, queryargs=None):
        func = partial(self._start_request, "GET", host, port, path, None,
                       handler, xml, mblogin, cacheloadcontrol=cacheloadcontrol, refresh=refresh, queryargs=queryargs)
        return self.add_task(func, host, port, priority, important=important)

    def post(self, host, port, path, data, handler, xml=True, priority=False, important=False, mblogin=True, queryargs=None):
        log.debug("POST-DATA %r", data)
        func = partial(self._start_request, "POST", host, port, path, data, handler, xml, mblogin, queryargs=queryargs)
        return self.add_task(func, host, port, priority, important=important)

    def put(self, host, port, path, data, handler, priority=True, important=False, mblogin=True, queryargs=None):
        func = partial(self._start_request, "PUT", host, port, path, data, handler, False, mblogin, queryargs=queryargs)
        return self.add_task(func, host, port, priority, important=important)

    def delete(self, host, port, path, handler, priority=True, important=False, mblogin=True, queryargs=None):
        func = partial(self._start_request, "DELETE", host, port, path, None, handler, False, mblogin, queryargs=queryargs)
        return self.add_task(func, host, port, priority, important=important)

    def stop(self):
        for reply in self._active_requests.keys():
            reply.abort()
        self._init_queues()

    def _count_pending_requests(self):
        count = len(self._active_requests)
        for prio_queue in self._queues.values():
            for queue in prio_queue.values():
                count += len(queue)
        self.num_pending_web_requests = count
        if count != self._last_num_pending_web_requests:
            self._last_num_pending_web_requests = count
            self.tagger.tagger_stats_changed.emit()
        if count:
            self._timer_count_pending_requests.start(COUNT_REQUESTS_DELAY_MS)

    def _get_delay_to_next_request(self, hostkey):
        """Calculate delay to next request to hostkey (host, port)
           returns a tuple (wait, delay) where:
               wait is True if a delay is needed
               delay is the delay in milliseconds to next request
        """
        interval = REQUEST_DELAY[hostkey]
        if not interval:
            log.debug("WSREQ: Starting another request to %s without delay", hostkey)
            return (False, 0)
        last_request = self._last_request_times[hostkey]
        if not last_request:
            log.debug("WSREQ: First request to %s", hostkey)
            self._remember_request_time(hostkey) # set it on first run
            return (False, interval)
        elapsed = (time.time() - last_request) * 1000
        if elapsed >= interval:
            log.debug("WSREQ: Last request to %s was %d ms ago, starting another one", hostkey, elapsed)
            return (False, interval)
        delay = int(math.ceil(interval - elapsed))
        log.debug("WSREQ: Last request to %s was %d ms ago, waiting %d ms before starting another one",
                  hostkey, elapsed, delay)
        return (True, delay)

    def _remember_request_time(self, hostkey):
        if REQUEST_DELAY[hostkey]:
            self._last_request_times[hostkey] = time.time()

    def _run_next_task(self):
        delay = sys.maxsize
        for prio in sorted(self._queues.keys(), reverse=True):
            prio_queue = self._queues[prio]
            if not prio_queue:
                del(self._queues[prio])
                continue
            for hostkey in sorted(prio_queue.keys(),
                                  key=lambda hostkey: REQUEST_DELAY[hostkey]):
                queue = self._queues[prio][hostkey]
                if not queue:
                    del(self._queues[prio][hostkey])
                    continue
                wait, d = self._get_delay_to_next_request(hostkey)
                if not wait:
                    queue.popleft()()
                if d < delay:
                    delay = d
        if delay < sys.maxsize:
            self._timer_run_next_task.start(delay)

    def add_task(self, func, host, port, priority, important=False):
        hostkey = (host, port)
        prio = int(priority)  # priority is a boolean
        if important:
            self._queues[prio][hostkey].appendleft(func)
        else:
            self._queues[prio][hostkey].append(func)
        if not self._timer_run_next_task.isActive():
            self._timer_run_next_task.start(0)
        if not self._timer_count_pending_requests.isActive():
            self._timer_count_pending_requests.start(0)
        return (hostkey, func, prio)

    def remove_task(self, task):
        hostkey, func, prio = task
        try:
            self._queues[prio][hostkey].remove(func)
            if not self._timer_count_pending_requests.isActive():
                self._timer_count_pending_requests.start(0)
        except:
            pass

    def _get_by_id(self, entitytype, entityid, handler, inc=[], queryargs=None,
                   priority=False, important=False, mblogin=False, refresh=False):
        host = config.setting["server_host"]
        port = config.setting["server_port"]
        path = "/ws/2/%s/%s" % (entitytype, entityid)
        if queryargs is None:
            queryargs = {}
        if inc:
            queryargs["inc"] = "+".join(inc)
        return self.get(host, port, path, handler,
                        priority=priority, important=important, mblogin=mblogin,
                        refresh=refresh, queryargs=queryargs)

    def get_release_by_id(self, releaseid, handler, inc=[],
                          priority=False, important=False, mblogin=False, refresh=False):
        return self._get_by_id('release', releaseid, handler, inc,
                               priority=priority, important=important, mblogin=mblogin, refresh=refresh)

    def get_track_by_id(self, trackid, handler, inc=[],
                        priority=False, important=False, mblogin=False, refresh=False):
        return self._get_by_id('recording', trackid, handler, inc,
                               priority=priority, important=important, mblogin=mblogin, refresh=refresh)

    def lookup_discid(self, discid, handler, priority=True, important=True, refresh=False):
        inc = ['artist-credits', 'labels']
        return self._get_by_id('discid', discid, handler, inc, queryargs={"cdstubs": "no"},
                               priority=priority, important=important, refresh=refresh)

    def _find(self, entitytype, handler, kwargs):
        host = config.setting["server_host"]
        port = config.setting["server_port"]
        filters = []

        limit = kwargs.pop("limit")
        if limit:
            filters.append(("limit", limit))

        is_search = kwargs.pop("search", False)
        if is_search:
            if config.setting["use_adv_search_syntax"]:
                query = kwargs["query"]
            else:
                query = escape_lucene_query(kwargs["query"]).strip().lower()
                filters.append(("dismax", 'true'))
        else:
            query = []
            for name, value in kwargs.items():
                value = escape_lucene_query(value).strip().lower()
                if value:
                    query.append('%s:(%s)' % (name, value))
            query = ' '.join(query)

        if query:
            filters.append(("query", query))
        queryargs = {}
        for name, value in filters:
            value = QUrl.toPercentEncoding(unicode(value))
            queryargs[str(name)] = value
        path = "/ws/2/%s" % (entitytype)
        return self.get(host, port, path, handler, queryargs=queryargs)

    def find_releases(self, handler, **kwargs):
        return self._find('release', handler, kwargs)

    def find_tracks(self, handler, **kwargs):
        return self._find('recording', handler, kwargs)

    def find_artists(self, handler, **kwargs):
        return self._find('artist', handler, kwargs)

    def _browse(self, entitytype, handler, kwargs, inc=[], priority=False, important=False):
        host = config.setting["server_host"]
        port = config.setting["server_port"]
        path = "/ws/2/%s" % (entitytype)
        queryargs = kwargs
        if inc:
            queryargs["inc"] = "+".join(inc)
        return self.get(host, port, path, handler, priority=priority,
                        important=important, queryargs=queryargs)

    def browse_releases(self, handler, priority=True, important=True, **kwargs):
        inc = ["media", "labels"]
        return self._browse("release", handler, kwargs, inc, priority=priority, important=important)

    def submit_ratings(self, ratings, handler):
        host = config.setting['server_host']
        port = config.setting['server_port']
        path = '/ws/2/rating/?client=' + CLIENT_STRING
        recordings = (''.join(['<recording id="%s"><user-rating>%s</user-rating></recording>' %
            (i[1], j*20) for i, j in ratings.items() if i[0] == 'recording']))
        data = _wrap_xml_metadata('<recording-list>%s</recording-list>' % recordings)
        return self.post(host, port, path, data, handler, priority=True)

    def _encode_acoustid_args(self, args, format='xml'):
        filters = []
        args['client'] = ACOUSTID_KEY
        args['clientversion'] = PICARD_VERSION_STR
        args['format'] = format
        for name, value in args.items():
            value = str(QUrl.toPercentEncoding(value))
            filters.append('%s=%s' % (str(name), value))
        return '&'.join(filters)

    def query_acoustid(self, handler, **args):
        host, port = ACOUSTID_HOST, ACOUSTID_PORT
        body = self._encode_acoustid_args(args)
        return self.post(host, port, '/v2/lookup', body, handler, priority=False, important=False, mblogin=False)

    def submit_acoustid_fingerprints(self, submissions, handler):
        args = {'user': config.setting["acoustid_apikey"]}
        for i, submission in enumerate(submissions):
            args['fingerprint.%d' % i] = str(submission.fingerprint)
            args['duration.%d' % i] = str(submission.duration)
            args['mbid.%d' % i] = str(submission.recordingid)
            if submission.puid:
                args['puid.%d' % i] = str(submission.puid)
        host, port = ACOUSTID_HOST, ACOUSTID_PORT
        body = self._encode_acoustid_args(args, format='json')
        return self.post(host, port, '/v2/submit', body, handler, priority=True, important=False, mblogin=False)

    def download(self, host, port, path, handler, priority=False,
                 important=False, cacheloadcontrol=None, refresh=False,
                 queryargs=None):
        return self.get(host, port, path, handler, xml=False,
                        priority=priority, important=important,
                        cacheloadcontrol=cacheloadcontrol, refresh=refresh,
                        queryargs=queryargs)

    def get_collection(self, id, handler, limit=100, offset=0):
        host, port = config.setting['server_host'], config.setting['server_port']
        path = "/ws/2/collection"
        queryargs = None
        if id is not None:
            inc = ["releases", "artist-credits", "media"]
            path += "/%s/releases" % (id)
            queryargs = {}
            queryargs["inc"] = "+".join(inc)
            queryargs["limit"] = limit
            queryargs["offset"] = offset
        return self.get(host, port, path, handler, priority=True, important=True,
                        mblogin=True, queryargs=queryargs)

    def get_collection_list(self, handler):
        return self.get_collection(None, handler)

    def _collection_request(self, id, releases):
        while releases:
            ids = ";".join(releases if len(releases) <= 400 else releases[:400])
            releases = releases[400:]
            yield "/ws/2/collection/%s/releases/%s" % (id, ids)

    def _get_client_queryarg(self):
        return {"client": CLIENT_STRING}


    def put_to_collection(self, id, releases, handler):
        host, port = config.setting['server_host'], config.setting['server_port']
        for path in self._collection_request(id, releases):
            self.put(host, port, path, "", handler,
                     queryargs=self._get_client_queryarg())

    def delete_from_collection(self, id, releases, handler):
        host, port = config.setting['server_host'], config.setting['server_port']
        for path in self._collection_request(id, releases):
            self.delete(host, port, path, handler,
                        queryargs=self._get_client_queryarg())
