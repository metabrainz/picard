# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018-2022 Philipp Wolfer
# Copyright (C) 2018-2023 Laurent Monin
# Copyright (C) 2021 Tche333
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
import os.path
import platform
import sys

from PyQt5 import (
    QtCore,
    QtNetwork,
)
from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QNetworkRequest

from picard import (
    PICARD_APP_NAME,
    PICARD_ORG_NAME,
    PICARD_VERSION_STR,
    log,
)
from picard.config import get_config
from picard.const import (
    CACHE_SIZE_IN_BYTES,
    appdirs,
)
from picard.oauth import OAuthManager
from picard.util import (
    build_qurl,
    bytes2human,
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
    _access_token = None
    _high_prio_no_cache = True
    _mblogin = None
    _retries = 0

    response_mimetype = None
    response_parser = None

    def __init__(
        self,
        *,
        method=None,
        handler=None,
        parse_response_type=None,
        data=None,
        mblogin=False,
        cacheloadcontrol=None,
        refresh=False,
        priority=False,
        important=False,
        request_mimetype=None,
        url=None,
        queryargs=None,
    ):
        """
        Args:
            method: HTTP method.  One of ``GET``, ``POST``, ``PUT``, or ``DELETE``.
            handler: Callback which takes a 3-tuple of `(str:document,
                QNetworkReply:reply, QNetworkReply.Error:error)`.
            parse_response_type: Specifies that request either sends or accepts
                data as ``application/{{response_mimetype}}``.
            data: Data to include with ``PUT`` or ``POST`` requests.
            mblogin: Hints that this request should be tied to a MusicBrainz
            account, requiring that we obtain an OAuth token first.
            cacheloadcontrol: See `QNetworkRequest.Attribute.CacheLoadControlAttribute`.
            refresh: Indicates a user-specified resource refresh, such as when
                the user wishes to reload a release.  Marks the request as high priority
                and disables caching.
            priority: Indicates that this is a high priority request.
            important: Indicates that this is an important request.
            request_mimetype: Set the Content-Type header.
            url: URL passed as a string or as a QUrl to use for this request
            queryargs: dictionary of keys and values to add to the url
        """
        # mandatory parameters
        self.method = method
        if self.method not in {'GET', 'PUT', 'DELETE', 'POST'}:
            raise AssertionError('invalid method')

        self.handler = handler
        if self.handler is None:
            raise AssertionError('handler undefined')

        if url is None:
            raise AssertionError('URL undefined')

        if not isinstance(url, QUrl):
            url = QUrl(url)

        if queryargs is not None:
            query = QtCore.QUrlQuery(url)
            for k, v in queryargs.items():
                # FIXME: check if encoding is correct
                query.addQueryItem(k, str(v))
            url.setQuery(query)

        super().__init__(url)

        # optional parameters
        self.parse_response_type = parse_response_type
        self.request_mimetype = request_mimetype
        self.data = data
        self.mblogin = mblogin
        self.cacheloadcontrol = cacheloadcontrol
        self.refresh = refresh
        self.priority = priority
        self.important = important

        # set headers and attributes
        self.access_token = None  # call _update_authorization_header

        if self.method == 'GET':
            self._high_prio_no_cache = self.refresh
            self.setAttribute(QNetworkRequest.Attribute.HttpPipeliningAllowedAttribute, True)

        self.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, USER_AGENT_STRING)

        if self.mblogin or self._high_prio_no_cache:
            self.setPriority(QNetworkRequest.Priority.HighPriority)
            self.setAttribute(QNetworkRequest.Attribute.CacheLoadControlAttribute, QNetworkRequest.CacheLoadControl.AlwaysNetwork)
        elif self.cacheloadcontrol is not None:
            self.setAttribute(QNetworkRequest.Attribute.CacheLoadControlAttribute, self.cacheloadcontrol)

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
            self.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, self.request_mimetype)

    @property
    def has_auth(self):
        return self.mblogin and self.access_token

    def _update_authorization_header(self):
        auth = "Bearer " + self.access_token if self.has_auth else ""
        self.setRawHeader(b"Authorization", auth.encode('utf-8'))

    @property
    def host(self):
        return self.url().host()

    @property
    def port(self):
        """Returns QUrl port or default ports (443 for https, 80 for http)"""
        url = self.url()
        if url.scheme() == 'https':
            return url.port(443)
        return url.port(80)

    @property
    def path(self):
        return self.url().path()

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


class RequestTask(namedtuple('RequestTask', 'hostkey func priority')):

    @staticmethod
    def from_request(request, func):
        # priority is a boolean
        return RequestTask(request.get_host_key(), func, int(request.priority))


class RequestPriorityQueue:

    def __init__(self, ratecontrol):
        self._queues = defaultdict(lambda: defaultdict(deque))
        self._ratecontrol = ratecontrol
        self._count = 0

    def count(self):
        return self._count

    def add_task(self, task, important=False):
        (hostkey, func, prio) = task
        queue = self._queues[prio][hostkey]
        if important:
            queue.appendleft(func)
        else:
            queue.append(func)
        self._count += 1
        return RequestTask(hostkey, func, prio)

    def remove_task(self, task):
        hostkey, func, prio = task
        try:
            self._queues[prio][hostkey].remove(func)
            self._count -= 1
        except Exception as e:
            log.debug(e)

    def run_ready_tasks(self):
        delay = sys.maxsize
        for prio in sorted(self._queues.keys(), reverse=True):
            prio_queue = self._queues[prio]
            if not prio_queue:
                del self._queues[prio]
                continue
            for hostkey in sorted(prio_queue.keys(),
                                  key=self._ratecontrol.current_delay):
                queue = self._queues[prio][hostkey]
                if not queue:
                    del self._queues[prio][hostkey]
                    continue
                wait, d = self._ratecontrol.get_delay_to_next_request(hostkey)
                if not wait:
                    queue.popleft()()
                    self._count -= 1
                if d < delay:
                    delay = d
        return delay


class WebService(QtCore.QObject):

    PARSERS = dict()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = QtNetwork.QNetworkAccessManager()
        self._network_accessible_changed(self.manager.networkAccessible())
        self.manager.networkAccessibleChanged.connect(self._network_accessible_changed)
        self.oauth_manager = OAuthManager(self)
        self.set_cache()
        self.setup_proxy()
        config = get_config()
        self.set_transfer_timeout(config.setting['network_transfer_timeout_seconds'])
        self.manager.finished.connect(self._process_reply)
        self._request_methods = {
            "GET": self.manager.get,
            "POST": self.manager.post,
            "PUT": self.manager.put,
            "DELETE": self.manager.deleteResource
        }
        self._init_queues()
        self._init_timers()

    @staticmethod
    def http_response_code(reply):
        response_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        return int(response_code) if response_code else 0

    @staticmethod
    def http_response_phrase(reply):
        return reply.attribute(QNetworkRequest.Attribute.HttpReasonPhraseAttribute)

    @staticmethod
    def http_response_safe_url(reply):
        return reply.request().url().toString(QUrl.UrlFormattingOption.RemoveUserInfo)

    def _network_accessible_changed(self, accessible):
        # Qt's network accessibility check sometimes fails, e.g. with VPNs on Windows.
        # If the accessibility is reported to be not accessible, set it to
        # unknown instead. Let's just try any request and handle the error.
        # See https://tickets.metabrainz.org/browse/PICARD-1791
        if accessible == QtNetwork.QNetworkAccessManager.NetworkAccessibility.NotAccessible:
            self.manager.setNetworkAccessible(QtNetwork.QNetworkAccessManager.NetworkAccessibility.UnknownAccessibility)
        log.debug("Network accessible requested: %s, actual: %s", accessible, self.manager.networkAccessible())

    def _init_queues(self):
        self._active_requests = {}
        self._queue = RequestPriorityQueue(ratecontrol)
        self.num_pending_web_requests = 0

    def _init_timers(self):
        self._timer_run_next_task = QtCore.QTimer(self)
        self._timer_run_next_task.setSingleShot(True)
        self._timer_run_next_task.timeout.connect(self._run_next_task)
        self._timer_count_pending_requests = QtCore.QTimer(self)
        self._timer_count_pending_requests.setSingleShot(True)
        self._timer_count_pending_requests.timeout.connect(self._count_pending_requests)

    def set_cache(self, cache_size_in_bytes=None):
        if cache_size_in_bytes is None:
            cache_size_in_bytes = CACHE_SIZE_IN_BYTES
        cache = QtNetwork.QNetworkDiskCache()
        cache.setCacheDirectory(os.path.join(appdirs.cache_folder(), 'network'))
        cache.setMaximumCacheSize(cache_size_in_bytes)
        self.manager.setCache(cache)
        log.debug("NetworkDiskCache dir: %r current size: %s max size: %s",
                  cache.cacheDirectory(),
                  bytes2human.decimal(cache.cacheSize(), l10n=False),
                  bytes2human.decimal(cache.maximumCacheSize(), l10n=False))

    def setup_proxy(self):
        proxy = QtNetwork.QNetworkProxy()
        config = get_config()
        if config.setting["use_proxy"]:
            if config.setting["proxy_type"] == 'socks':
                proxy.setType(QtNetwork.QNetworkProxy.ProxyType.Socks5Proxy)
            else:
                proxy.setType(QtNetwork.QNetworkProxy.ProxyType.HttpProxy)
            proxy.setHostName(config.setting["proxy_server_host"])
            proxy.setPort(config.setting["proxy_server_port"])
            if config.setting["proxy_username"]:
                proxy.setUser(config.setting["proxy_username"])
            if config.setting["proxy_password"]:
                proxy.setPassword(config.setting["proxy_password"])
        self.manager.setProxy(proxy)

    def set_transfer_timeout(self, timeout):
        timeout_ms = timeout * 1000
        if hasattr(self.manager, 'setTransferTimeout'):  # Available since Qt 5.15
            self.manager.setTransferTimeout(timeout_ms)
            self._transfer_timeout = 0
        else:  # Use fallback implementation
            self._transfer_timeout = timeout_ms

    def _send_request(self, request, access_token=None):
        hostkey = request.get_host_key()
        ratecontrol.increment_requests(hostkey)

        request.access_token = access_token
        send = self._request_methods[request.method]
        data = request.data
        reply = send(request, data.encode('utf-8')) if data is not None else send(request)
        self._start_transfer_timeout(reply)
        self._active_requests[reply] = request

    def _start_transfer_timeout(self, reply):
        if not self._transfer_timeout:
            return
        # Fallback implementation of a transfer timeout for Qt < 5.15.
        # Aborts a request if no data gets transferred for TRANSFER_TIMEOUT milliseconds.
        timer = QtCore.QTimer(self)
        timer.setSingleShot(True)
        timer.setTimerType(QtCore.Qt.TimerType.PreciseTimer)
        timer.timeout.connect(partial(self._timeout_request, reply))
        reply.finished.connect(timer.stop)
        reset_callback = partial(self._reset_transfer_timeout, timer)
        reply.uploadProgress.connect(reset_callback)
        reply.downloadProgress.connect(reset_callback)
        timer.start(self._transfer_timeout)

    def _reset_transfer_timeout(self, timer, bytesTransferred, bytesTotal):
        timer.start(self._transfer_timeout)

    @staticmethod
    def _timeout_request(reply):
        if reply.isRunning():
            reply.abort()

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
            leftUrl.toString(QUrl.UrlFormattingOption.RemovePort) == rightUrl.toString(QUrl.UrlFormattingOption.RemovePort)

    def _handle_redirect(self, reply, request, redirect):
        error = int(reply.error())
        # merge with base url (to cover the possibility of the URL being relative)
        redirect_qurl = request.url().resolved(redirect)
        if not WebService.urls_equivalent(redirect_qurl, reply.request().url()):
            log.debug("Redirect to %s requested", redirect_qurl.toString(QUrl.UrlFormattingOption.RemoveUserInfo))

            redirect_request = WSRequest(
                method='GET',
                url=redirect_qurl,
                handler=request.handler,
                parse_response_type=request.parse_response_type,
                priority=True,
                important=True,
                mblogin=request.mblogin,
                cacheloadcontrol=request.attribute(QNetworkRequest.Attribute.CacheLoadControlAttribute),
                refresh=request.refresh,
            )

            ratecontrol.copy_minimal_delay(
                request.get_host_key(),
                redirect_request.get_host_key(),
            )

            self.add_request(redirect_request)
        else:
            log.error("Redirect loop: %s",
                      self.http_response_safe_url(reply)
                      )
            request.handler(reply.readAll(), reply, error)

    def _handle_reply(self, reply, request):
        hostkey = request.get_host_key()
        ratecontrol.decrement_requests(hostkey)

        self._timer_run_next_task.start(0)

        slow_down = False

        error = int(reply.error())
        handler = request.handler
        response_code = self.http_response_code(reply)
        url = self.http_response_safe_url(reply)
        if error:
            errstr = reply.errorString()
            log.error("Network request error for %s: %s (QT code %d, HTTP code %d)",
                      url, errstr, error, response_code)
            if (not request.max_retries_reached()
                and (response_code == 503
                     or response_code == 429
                     # Sometimes QT returns a http status code of 200 even when there
                     # is a service unavailable error. But it returns a QT error code
                     # of 403 when this happens
                     or error == 403
                     )):
                slow_down = True
                retries = request.mark_for_retry()
                log.debug("Retrying %s (#%d)", url, retries)
                self.add_request(request)

            elif handler is not None:
                handler(reply.readAll(), reply, error)

            slow_down = (slow_down or response_code >= 500)

        else:
            redirect = reply.attribute(QNetworkRequest.Attribute.RedirectionTargetAttribute)
            from_cache = reply.attribute(QNetworkRequest.Attribute.SourceIsFromCacheAttribute)
            cached = ' (CACHED)' if from_cache else ''
            log.debug("Received reply for %s: HTTP %d (%s) %s",
                      url,
                      response_code,
                      self.http_response_phrase(reply),
                      cached
                      )
            if handler is not None:
                # Redirect if found and not infinite
                if redirect:
                    self._handle_redirect(reply, request, redirect)
                elif request.response_parser:
                    try:
                        document = request.response_parser(reply)
                        log.debug("Response received: %s", document)
                    except Exception as e:
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
            log.error("Request not found for %s", self.http_response_safe_url(reply))
            return
        try:
            self._handle_reply(reply, request)
        finally:
            reply.close()
            reply.deleteLater()

    def get(self, host, port, path, handler, parse_response_type=DEFAULT_RESPONSE_PARSER_TYPE,
            priority=False, important=False, mblogin=False, cacheloadcontrol=None, refresh=False,
            queryargs=None):
        request = WSRequest(
            method='GET',
            url=build_qurl(host, port, path=path, queryargs=queryargs),
            handler=handler,
            parse_response_type=parse_response_type,
            priority=priority,
            important=important,
            mblogin=mblogin,
            cacheloadcontrol=cacheloadcontrol,
            refresh=refresh,
        )
        return self.add_request(request)

    def post(self, host, port, path, data, handler, parse_response_type=DEFAULT_RESPONSE_PARSER_TYPE,
             priority=False, important=False, mblogin=True, queryargs=None, request_mimetype=None):
        request = WSRequest(
            method='POST',
            url=build_qurl(host, port, path=path, queryargs=queryargs),
            handler=handler,
            parse_response_type=parse_response_type,
            priority=priority,
            important=important,
            mblogin=mblogin,
            data=data,
            request_mimetype=request_mimetype,
        )
        log.debug("POST-DATA %r", data)
        return self.add_request(request)

    def put(self, host, port, path, data, handler, priority=True, important=False, mblogin=True,
            queryargs=None, request_mimetype=None):
        request = WSRequest(
            method='PUT',
            url=build_qurl(host, port, path=path, queryargs=queryargs),
            handler=handler,
            priority=priority,
            important=important,
            mblogin=mblogin,
            data=data,
            request_mimetype=request_mimetype,
        )
        return self.add_request(request)

    def delete(self, host, port, path, handler, priority=True, important=False, mblogin=True,
               queryargs=None):
        request = WSRequest(
            method='DELETE',
            url=build_qurl(host, port, path=path, queryargs=queryargs),
            handler=handler,
            priority=priority,
            important=important,
            mblogin=mblogin,
        )
        return self.add_request(request)

    def download(self, host, port, path, handler, priority=False,
                 important=False, cacheloadcontrol=None, refresh=False,
                 queryargs=None):
        request = WSRequest(
            method='GET',
            url=build_qurl(host, port, path=path, queryargs=queryargs),
            handler=handler,
            priority=priority,
            important=important,
            cacheloadcontrol=cacheloadcontrol,
            refresh=refresh,
        )
        return self.add_request(request)

    def get_url(self, **kwargs):
        kwargs['method'] = 'GET'
        kwargs['parse_response_type'] = kwargs.get('parse_response_type', DEFAULT_RESPONSE_PARSER_TYPE)
        return self.add_request(WSRequest(**kwargs))

    def post_url(self, **kwargs):
        kwargs['method'] = 'POST'
        kwargs['parse_response_type'] = kwargs.get('parse_response_type', DEFAULT_RESPONSE_PARSER_TYPE)
        kwargs['mblogin'] = kwargs.get('mblogin', True)
        log.debug("POST-DATA %r", kwargs['data'])
        return self.add_request(WSRequest(**kwargs))

    def put_url(self, **kwargs):
        kwargs['method'] = 'PUT'
        kwargs['priority'] = kwargs.get('priority', True)
        kwargs['mblogin'] = kwargs.get('mblogin', True)
        return self.add_request(WSRequest(**kwargs))

    def delete_url(self, **kwargs):
        kwargs['method'] = 'DELETE'
        kwargs['priority'] = kwargs.get('priority', True)
        kwargs['mblogin'] = kwargs.get('mblogin', True)
        return self.add_request(WSRequest(**kwargs))

    def download_url(self, **kwargs):
        kwargs['method'] = 'GET'
        return self.add_request(WSRequest(**kwargs))

    def stop(self):
        for reply in list(self._active_requests):
            reply.abort()
        self._init_queues()

    def _count_pending_requests(self):
        count = len(self._active_requests) + self._queue.count()
        if count != self.num_pending_web_requests:
            self.num_pending_web_requests = count
            self.tagger.tagger_stats_changed.emit()
        if count:
            self._timer_count_pending_requests.start(COUNT_REQUESTS_DELAY_MS)

    def _run_next_task(self):
        delay = self._queue.run_ready_tasks()
        if delay < sys.maxsize:
            self._timer_run_next_task.start(delay)

    def add_task(self, func, request):
        task = RequestTask.from_request(request, func)
        self._queue.add_task(task, request.important)

        if not self._timer_run_next_task.isActive():
            self._timer_run_next_task.start(0)

        if not self._timer_count_pending_requests.isActive():
            self._timer_count_pending_requests.start(0)

        return task

    def add_request(self, request):
        return self.add_task(partial(self._start_request, request), request)

    def remove_task(self, task):
        self._queue.remove_task(task)
        if not self._timer_count_pending_requests.isActive():
            self._timer_count_pending_requests.start(0)

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
