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

from collections import (
    defaultdict,
    deque,
    namedtuple,
)
from functools import partial
import math
import os.path
import platform
import sys
import time

from PyQt5 import (
    QtCore,
    QtNetwork,
)
from PyQt5.QtCore import (
    QStandardPaths,
    QUrl,
    QUrlQuery,
)
from PyQt5.QtNetwork import QNetworkRequest

from picard import (
    PICARD_APP_NAME,
    PICARD_ORG_NAME,
    PICARD_VERSION_STR,
    config,
    log,
)
from picard.oauth import OAuthManager
from picard.util import (
    build_qurl,
    parse_json,
)
from picard.util.xml import parse_xml
from picard.webservice import ratecontrol

COUNT_REQUESTS_DELAY_MS = 250

TEMP_ERRORS_RETRIES = 5
USER_AGENT_STRING = '%s-%s/%s (%s;%s-%s)' % (PICARD_ORG_NAME, PICARD_APP_NAME,
                                             PICARD_VERSION_STR,
                                             platform.platform(),
                                             platform.python_implementation(),
                                             platform.python_version())
CLIENT_STRING = bytes(QUrl.toPercentEncoding('%s %s-%s' % (PICARD_ORG_NAME,
                                                           PICARD_APP_NAME,
                                                           PICARD_VERSION_STR))).decode()


DEFAULT_RESPONSE_PARSER_TYPE = "json"

Parser = namedtuple('Parser', 'mimetype parser')


class UnknownResponseParserError(Exception):

    def __init__(self, response_type):
        message = "Unknown parser for response type '%s'. Parser for given response type does not exist." % response_type
        super().__init__(message)


class WSRequest(QNetworkRequest):
    """Represents a single HTTP request."""

    def __init__(self, method, host, port, path, handler, parse_response_type=None, data=None,
                 mblogin=False, cacheloadcontrol=None, refresh=False,
                 queryargs=None, priority=False, important=False,
                 request_mimetype=None):
        """
        Args:
            method: HTTP method.  One of ``GET``, ``POST``, ``PUT``, or ``DELETE``.
            host: Hostname.
            port: TCP port number (80 or 443).
            path: Path component.
            handler: Callback which takes a 3-tuple of `(str:document,
            QNetworkReply:reply, QNetworkReply.Error:error)`.
            parse_response_type: Specifies that request either sends or accepts
            data as ``application/{{response_mimetype}}``.
            data: Data to include with ``PUT`` or ``POST`` requests.
            mblogin: Hints that this request should be tied to a MusicBrainz
            account, requiring that we obtain an OAuth token first.
            cacheloadcontrol: See `QNetworkRequest.CacheLoadControlAttribute`.
            refresh: Indicates a user-specified resource refresh, such as when
            the user wishes to reload a release.  Marks the request as high priority
            and disables caching.
            queryargs: `dict` of query arguments.
            retries: Current retry attempt number.
            priority: Indicates that this is a high priority request.
            important: Indicates that this is an important request.
            request_mimetype: Set the Content-Type header.
        """
        url = build_qurl(host, port, path=path, queryargs=queryargs)
        super().__init__(url)

        # These two are codependent (see _update_authorization_header) and must
        # be initialized explicitly.
        self._access_token = None
        self._mblogin = None

        self._retries = 0

        self.method = method
        self.host = host
        self.port = port
        self.path = path
        self.handler = handler
        self.parse_response_type = parse_response_type
        self.response_parser = None
        self.response_mimetype = None
        self.request_mimetype = request_mimetype
        self.data = data
        self.mblogin = mblogin
        self.cacheloadcontrol = cacheloadcontrol
        self.refresh = refresh
        self.queryargs = queryargs
        self.priority = priority
        self.important = important

        self.access_token = None
        self._init_headers()

    def _init_headers(self, high_prio_no_cache=False):
        self.setHeader(QNetworkRequest.UserAgentHeader, USER_AGENT_STRING)

        if self.mblogin or high_prio_no_cache:
            self.setPriority(QNetworkRequest.HighPriority)
            self.setAttribute(QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.AlwaysNetwork)
        elif self.cacheloadcontrol is not None:
            self.setAttribute(QNetworkRequest.CacheLoadControlAttribute, self.cacheloadcontrol)

        if self.parse_response_type:
            try:
                self.response_mimetype = WebService.get_response_mimetype(self.parse_response_type)
                self.response_parser = WebService.get_response_parser(self.parse_response_type)
            except UnknownResponseParserError as e:
                log.error(e.args[0])
            else:
                self.setRawHeader(b"Accept", self.response_mimetype.encode('utf-8'))

        if self.data:
            if not self.request_mimetype:
                self.request_mimetype = self.response_mimetype or "application/x-www-form-urlencoded"
            self.setHeader(QNetworkRequest.ContentTypeHeader, self.request_mimetype)

    def _update_authorization_header(self):
        authorization = b""
        if self.mblogin and self.access_token:
            authorization = ("Bearer %s" % self.access_token).encode('utf-8')
        self.setRawHeader(b"Authorization", authorization)

    @property
    def access_token(self):
        return self._access_token

    @access_token.setter
    def access_token(self, access_token):
        self._access_token = access_token
        self._update_authorization_header()

    @property
    def mblogin(self):
        return self._mblogin

    @mblogin.setter
    def mblogin(self, mblogin):
        self._mblogin = mblogin
        self._update_authorization_header()

    def get_host_key(self):
        return (self.host, self.port)

    def max_retries_reached(self):
        return self._retries >= TEMP_ERRORS_RETRIES

    def mark_for_retry(self, important=True, priority=True):
        # Put retries at the head of the list in order to not penalize
        # the load an album unlucky enough to hit a temporary service
        # snag.
        self.important = important
        self.priority = priority
        self._retries += 1
        return self._retries


class WSGetRequest(WSRequest):

    def __init__(self, *args, **kwargs):
        super().__init__("GET", *args, **kwargs)

    def _init_headers(self):
        super()._init_headers(high_prio_no_cache=self.refresh)
        self.setAttribute(QNetworkRequest.HttpPipeliningAllowedAttribute,
                          True)


class WSPutRequest(WSRequest):

    def __init__(self, *args, **kwargs):
        super().__init__("PUT", *args, **kwargs)

    def _init_headers(self):
        super()._init_headers(high_prio_no_cache=True)


class WSDeleteRequest(WSRequest):

    def __init__(self, *args, **kwargs):
        super().__init__("DELETE", *args, **kwargs)

    def _init_headers(self):
        super()._init_headers(high_prio_no_cache=True)


class WSPostRequest(WSRequest):

    def __init__(self, *args, **kwargs):
        super().__init__("POST", *args, **kwargs)

    def _init_headers(self):
        super()._init_headers(high_prio_no_cache=True)


class WebService(QtCore.QObject):

    PARSERS = dict()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = QtNetwork.QNetworkAccessManager()
        self.oauth_manager = OAuthManager(self)
        self.set_cache()
        self.setup_proxy()
        self.manager.finished.connect(self._process_reply)
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
        log.debug("NetworkDiskCache dir: %r size: %s / %s",
                  cache.cacheDirectory(), cache.cacheSize(),
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

    def _send_request(self, request, access_token=None):
        hostkey = request.get_host_key()
        ratecontrol.increment_requests(hostkey)

        request.access_token = access_token
        send = self._request_methods[request.method]
        data = request.data
        reply = send(request, data.encode('utf-8')) if data is not None else send(request)
        self._active_requests[reply] = request

    def _start_request(self, request):
        if request.mblogin and request.path != "/oauth2/token":
            self.oauth_manager.get_access_token(partial(self._send_request, request))
        else:
            self._send_request(request)

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

    def _handle_redirect(self, reply, request, redirect):
        url = request.url()
        error = int(reply.error())
        # merge with base url (to cover the possibility of the URL being relative)
        redirect = url.resolved(redirect)
        if not WebService.urls_equivalent(redirect, reply.request().url()):
            log.debug("Redirect to %s requested", redirect.toString(QUrl.RemoveUserInfo))
            redirect_host = redirect.host()
            redirect_port = self.url_port(redirect)
            redirect_query = dict(QUrlQuery(redirect).queryItems(QUrl.FullyEncoded))
            redirect_path = redirect.path()

            original_host = url.host()
            original_port = self.url_port(url)
            original_host_key = (original_host, original_port)
            redirect_host_key = (redirect_host, redirect_port)
            ratecontrol.copy_minimal_delay(original_host_key, redirect_host_key)

            self.get(redirect_host,
                     redirect_port,
                     redirect_path,
                     request.handler, request.parse_response_type, priority=True, important=True,
                     refresh=request.refresh, queryargs=redirect_query, mblogin=request.mblogin,
                     cacheloadcontrol=request.attribute(QNetworkRequest.CacheLoadControlAttribute))
        else:
            log.error("Redirect loop: %s",
                      reply.request().url().toString(QUrl.RemoveUserInfo)
                      )
            request.handler(reply.readAll(), reply, error)

    def _handle_reply(self, reply, request):
        hostkey = request.get_host_key()
        ratecontrol.decrement_requests(hostkey)

        self._timer_run_next_task.start(0)

        slow_down = False

        error = int(reply.error())
        handler = request.handler
        if error:
            code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            code = int(code) if code else 0
            errstr = reply.errorString()
            url = reply.request().url().toString(QUrl.RemoveUserInfo)
            log.error("Network request error for %s: %s (QT code %d, HTTP code %d)",
                      url, errstr, error, code)
            if (not request.max_retries_reached()
                        and (code == 503
                             or code == 429
                             # Sometimes QT returns a http status code of 200 even when there
                             # is a service unavailable error. But it returns a QT error code
                             # of 403 when this happens
                             or error == 403
                             )
                    ):
                slow_down = True
                retries = request.mark_for_retry()
                log.debug("Retrying %s (#%d)", url, retries)
                self.add_request(request)

            elif handler is not None:
                handler(reply.readAll(), reply, error)

            slow_down = (slow_down or code >= 500)

        else:
            redirect = reply.attribute(QNetworkRequest.RedirectionTargetAttribute)
            fromCache = reply.attribute(QNetworkRequest.SourceIsFromCacheAttribute)
            cached = ' (CACHED)' if fromCache else ''
            log.debug("Received reply for %s: HTTP %d (%s) %s",
                      reply.request().url().toString(QUrl.RemoveUserInfo),
                      reply.attribute(QNetworkRequest.HttpStatusCodeAttribute),
                      reply.attribute(QNetworkRequest.HttpReasonPhraseAttribute),
                      cached
                      )
            if handler is not None:
                # Redirect if found and not infinite
                if redirect:
                    self._handle_redirect(reply, request, redirect)
                elif request.response_parser:
                    try:
                        document = request.response_parser(reply)
                    except Exception as e:
                        url = reply.request().url().toString(QUrl.RemoveUserInfo)
                        log.error("Unable to parse the response for %s: %s", url, e)
                        document = reply.readAll()
                        error = e
                    finally:
                        handler(document, reply, error)
                else:
                    handler(reply.readAll(), reply, error)

        ratecontrol.adjust(hostkey, slow_down)

    def _process_reply(self, reply):
        try:
            request = self._active_requests.pop(reply)
        except KeyError:
            log.error("Request not found for %s", reply.request().url().toString(QUrl.RemoveUserInfo))
            return
        try:
            self._handle_reply(reply, request)
        finally:
            reply.close()
            reply.deleteLater()

    def get(self, host, port, path, handler, parse_response_type=DEFAULT_RESPONSE_PARSER_TYPE,
            priority=False, important=False, mblogin=False, cacheloadcontrol=None, refresh=False,
            queryargs=None):
        request = WSGetRequest(host, port, path, handler, parse_response_type=parse_response_type,
                               mblogin=mblogin, cacheloadcontrol=cacheloadcontrol, refresh=refresh,
                               queryargs=queryargs, priority=priority, important=important)
        return self.add_request(request)

    def post(self, host, port, path, data, handler, parse_response_type=DEFAULT_RESPONSE_PARSER_TYPE,
             priority=False, important=False, mblogin=True, queryargs=None, request_mimetype=None):
        request = WSPostRequest(host, port, path, handler, parse_response_type=parse_response_type,
                                data=data, mblogin=mblogin, queryargs=queryargs,
                                priority=priority, important=important,
                                request_mimetype=request_mimetype)
        log.debug("POST-DATA %r", data)
        return self.add_request(request)

    def put(self, host, port, path, data, handler, priority=True, important=False, mblogin=True,
            queryargs=None, request_mimetype=None):
        request = WSPutRequest(host, port, path, handler, data=data, mblogin=mblogin,
                               queryargs=queryargs, priority=priority,
                               important=important, request_mimetype=request_mimetype)
        return self.add_request(request)

    def delete(self, host, port, path, handler, priority=True, important=False, mblogin=True,
               queryargs=None):
        request = WSDeleteRequest(host, port, path, handler, mblogin=mblogin,
                                  queryargs=queryargs, priority=priority, important=important)
        return self.add_request(request)

    def download(self, host, port, path, handler, priority=False,
                 important=False, cacheloadcontrol=None, refresh=False,
                 queryargs=None):
        return self.get(host, port, path, handler, parse_response_type=None,
                        priority=priority, important=important,
                        cacheloadcontrol=cacheloadcontrol, refresh=refresh,
                        queryargs=queryargs)

    def stop(self):
        for reply in list(self._active_requests):
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

    def _run_next_task(self):
        delay = sys.maxsize
        for prio in sorted(self._queues.keys(), reverse=True):
            prio_queue = self._queues[prio]
            if not prio_queue:
                del(self._queues[prio])
                continue
            for hostkey in sorted(prio_queue.keys(),
                                  key=ratecontrol.current_delay):
                queue = self._queues[prio][hostkey]
                if not queue:
                    del(self._queues[prio][hostkey])
                    continue
                wait, d = ratecontrol.get_delay_to_next_request(hostkey)
                if not wait:
                    queue.popleft()()
                if d < delay:
                    delay = d
        if delay < sys.maxsize:
            self._timer_run_next_task.start(delay)

    def add_task(self, func, request):
        hostkey = request.get_host_key()
        prio = int(request.priority)  # priority is a boolean
        if request.important:
            self._queues[prio][hostkey].appendleft(func)
        else:
            self._queues[prio][hostkey].append(func)

        if not self._timer_run_next_task.isActive():
            self._timer_run_next_task.start(0)

        if not self._timer_count_pending_requests.isActive():
            self._timer_count_pending_requests.start(0)

        return (hostkey, func, prio)

    def add_request(self, request):
        return self.add_task(partial(self._start_request, request), request)

    def remove_task(self, task):
        hostkey, func, prio = task
        try:
            self._queues[prio][hostkey].remove(func)
            if not self._timer_count_pending_requests.isActive():
                self._timer_count_pending_requests.start(0)
        except Exception as e:
            log.debug(e)

    @classmethod
    def add_parser(cls, response_type, mimetype, parser):
        cls.PARSERS[response_type] = Parser(mimetype=mimetype, parser=parser)

    @classmethod
    def get_response_mimetype(cls, response_type):
        if response_type in cls.PARSERS:
            return cls.PARSERS[response_type].mimetype
        else:
            raise UnknownResponseParserError(response_type)

    @classmethod
    def get_response_parser(cls, response_type):
        if response_type in cls.PARSERS:
            return cls.PARSERS[response_type].parser
        else:
            raise UnknownResponseParserError(response_type)


WebService.add_parser('xml', 'application/xml', parse_xml)
WebService.add_parser('json', 'application/json', parse_json)
