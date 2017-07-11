# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2017 Sambhav Kothari
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
Asynchronous web service.
"""

import sys
import time
import os.path
import platform
import math
from collections import deque, defaultdict
from functools import partial
from PyQt5 import QtCore, QtNetwork
from PyQt5.QtCore import QUrl, QStandardPaths, QUrlQuery
from picard import (PICARD_APP_NAME,
                    PICARD_ORG_NAME,
                    PICARD_VERSION_STR,
                    config,
                    log)
from picard.oauth import OAuthManager
from picard.util import build_qurl
from picard.util.xml import parse_xml


COUNT_REQUESTS_DELAY_MS = 250
REQUEST_DELAY = defaultdict(lambda: 1000)
USER_AGENT_STRING = '%s-%s/%s (%s;%s-%s)' % (PICARD_ORG_NAME, PICARD_APP_NAME,
                                             PICARD_VERSION_STR,
                                             platform.platform(),
                                             platform.python_implementation(),
                                             platform.python_version())
CLIENT_STRING = string_(QUrl.toPercentEncoding('%s %s-%s' % (PICARD_ORG_NAME,
                                                         PICARD_APP_NAME,
                                                         PICARD_VERSION_STR)))

DEFAULT_RESPONSE_PARSER = "xml"


class UnknownResponseParserError(Exception):
    pass


class WebService(QtCore.QObject):

    PARSERS = dict()

    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.manager = QtNetwork.QNetworkAccessManager()
        self.manager.setRedirectPolicy(QtNetwork.QNetworkRequest.NoLessSafeRedirectPolicy)
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
        location = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
        cache.setCacheDirectory(os.path.join(location, 'picard'))
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

    def _start_request_continue(self, method, host, port, path, data, handler, parse_response_format,
                                mblogin=False, cacheloadcontrol=None, refresh=None,
                                access_token=None, queryargs=None):
        url = build_qurl(host, port, path=path, queryargs=queryargs)
        request = QtNetwork.QNetworkRequest(url)
        if mblogin and access_token:
            # access_token must not be unicode - PyQt5 doesn't like it.
            request.setRawHeader(b"Authorization", ("Bearer %s" % string_(access_token)).encode('utf-8'))
        if mblogin or (method == "GET" and refresh):
            request.setPriority(QtNetwork.QNetworkRequest.HighPriority)
            request.setAttribute(QtNetwork.QNetworkRequest.CacheLoadControlAttribute,
                                 QtNetwork.QNetworkRequest.AlwaysNetwork)
        elif method == "PUT" or method == "DELETE":
            request.setPriority(QtNetwork.QNetworkRequest.HighPriority)
        elif cacheloadcontrol is not None:
            request.setAttribute(QtNetwork.QNetworkRequest.CacheLoadControlAttribute,
                                 cacheloadcontrol)
        request.setRawHeader(b"User-Agent", USER_AGENT_STRING.encode('utf-8'))
        if parse_response_format:
            request.setRawHeader(b"Accept", self.response_header(parse_response_format).encode('utf-8'))
        if data is not None:
            if method == "POST" and host == config.setting["server_host"] and parse_response_format:
                request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader, "%s; charset=utf-8" % self.response_header(parse_response_format))
            else:
                request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader, "application/x-www-form-urlencoded")
        send = self._request_methods[method]
        reply = send(request, data.encode('utf-8')) if data is not None else send(request)
        self._remember_request_time((host, port))
        self._active_requests[reply] = (request, handler, parse_response_format, refresh)

    def _start_request(self, method, host, port, path, data, handler, parse_response_format,
                       mblogin=False, cacheloadcontrol=None, refresh=None,
                       queryargs=None):
        def start_request_continue(access_token=None):
            self._start_request_continue(
                method, host, port, path, data, handler, parse_response_format,
                mblogin=mblogin, cacheloadcontrol=cacheloadcontrol, refresh=refresh,
                access_token=access_token, queryargs=queryargs)
        if mblogin and path != "/oauth2/token":
            self.oauth_manager.get_access_token(start_request_continue)
        else:
            start_request_continue()

    def _handle_reply(self, reply, request, handler, parse_response_format, refresh):
        error = int(reply.error())
        if error:
            log.error("Network request error for %s: %s (QT code %d, HTTP code %s)",
                      reply.request().url().toString(QUrl.RemoveUserInfo),
                      reply.errorString(),
                      error,
                      repr(reply.attribute(QtNetwork.QNetworkRequest.HttpStatusCodeAttribute))
                      )
            if handler is not None:
                handler(reply.readAll(), reply, error)
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
                if parse_response_format:
                    response_parser = self.response_parser(parse_response_format)
                    try:
                        document = response_parser(reply)
                    except UnknownResponseParserError as e:
                        log.error("Attempting to parse the response body without a proper parser")
                        document = reply.readAll()
                    finally:
                        handler(document, reply, error)
                else:
                    handler(reply.readAll(), reply, error)

    def _process_reply(self, reply):
        try:
            request, handler, parse_response_format, refresh = self._active_requests.pop(reply)
        except KeyError:
            log.error("Request not found for %s" % reply.request().url().toString(QUrl.RemoveUserInfo))
            return
        try:
            self._handle_reply(reply, request, handler, parse_response_format, refresh)
        finally:
            reply.close()
            reply.deleteLater()

    def get(self, host, port, path, handler, parse_response_format=DEFAULT_RESPONSE_PARSER, priority=False,
            important=False, mblogin=False, cacheloadcontrol=None, refresh=False, queryargs=None):
        func = partial(self._start_request, "GET", host, port, path, None,
                       handler, parse_response_format, mblogin, cacheloadcontrol=cacheloadcontrol, refresh=refresh, queryargs=queryargs)
        return self.add_task(func, host, port, priority, important=important)

    def post(self, host, port, path, data, handler, parse_response_format=DEFAULT_RESPONSE_PARSER, priority=False, important=False, mblogin=True, queryargs=None):
        log.debug("POST-DATA %r", data)
        func = partial(self._start_request, "POST", host, port, path, data, handler, parse_response_format, mblogin, queryargs=queryargs)
        return self.add_task(func, host, port, priority, important=important)

    def put(self, host, port, path, data, handler, priority=True, important=False, mblogin=True, queryargs=None):
        func = partial(self._start_request, "PUT", host, port, path, data, handler, False, mblogin, queryargs=queryargs)
        return self.add_task(func, host, port, priority, important=important)

    def delete(self, host, port, path, handler, priority=True, important=False, mblogin=True, queryargs=None):
        func = partial(self._start_request, "DELETE", host, port, path, None, handler, False, mblogin, queryargs=queryargs)
        return self.add_task(func, host, port, priority, important=important)

    def download(self, host, port, path, handler, priority=False,
                 important=False, cacheloadcontrol=None, refresh=False,
                 queryargs=None):
        return self.get(host, port, path, handler, parse_response_format=None,
                        priority=priority, important=important,
                        cacheloadcontrol=cacheloadcontrol, refresh=refresh,
                        queryargs=queryargs)

    def stop(self):
        for reply in list(self._active_requests.keys()):
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
            self._remember_request_time(hostkey)  # set it on first run
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
        prio = int(priority)  # priority is a boolean
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
        except Exception as e:
            log.debug(e)

    @classmethod
    def add_parser(cls, name, header, parser):
        cls.PARSERS[name] = {'header': header, 'parser': parser}

    @classmethod
    def response_header(cls, name):
        if name in cls.PARSERS:
            return cls.PARSERS[name]['header']
        else:
            log.error('Parser of type %s not found', name)

    @classmethod
    def response_parser(cls, name):
        if name in cls.PARSERS:
            return cls.PARSERS[name]['parser']
        else:
            raise UnknownResponseParserError


WebService.add_parser('xml', 'application/xml', parse_xml)
