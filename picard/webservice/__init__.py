# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018-2022, 2024, 2026 Philipp Wolfer
# Copyright (C) 2018-2024 Laurent Monin
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
)
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
import os.path
import platform
import sys
from typing import (
    Any,
    ClassVar,
    Protocol,
    TypeAlias,
    runtime_checkable,
)
import weakref

from PyQt6 import (
    QtCore,
    QtNetwork,
)
from PyQt6.QtCore import (
    QObject,
    QUrl,
)
from PyQt6.QtNetwork import (
    QNetworkReply,
    QNetworkRequest,
    QSslError,
)

from picard import (
    PICARD_APP_NAME,
    PICARD_ORG_NAME,
    PICARD_VERSION_STR,
    log,
)
from picard.config import get_config
from picard.const import appdirs
from picard.const.defaults import DEFAULT_CACHE_SIZE_IN_BYTES
from picard.debug_opts import DebugOpt
from picard.oauth import OAuthManager
from picard.util import (
    bytes2human,
    encoded_queryargs,
    parse_json,
)
from picard.util.xml import parse_xml
from picard.webservice import ratecontrol
from picard.webservice.utils import port_from_qurl


COUNT_REQUESTS_DELAY_MS = 250

TEMP_ERRORS_RETRIES = 5
MAX_PENDING_AUTHORIZATION_REQUESTS = 1000
USER_AGENT_STRING = '%s-%s/%s (%s;%s-%s)' % (
    PICARD_ORG_NAME,
    PICARD_APP_NAME,
    PICARD_VERSION_STR,
    platform.platform(),
    platform.python_implementation(),
    platform.python_version(),
)
CLIENT_STRING = '%s %s-%s' % (PICARD_ORG_NAME, PICARD_APP_NAME, PICARD_VERSION_STR)


DEFAULT_RESPONSE_PARSER_TYPE = "json"

# MusicBrainz Web Service inc params that require authentication.
# Requests with these params will get a 401 if not logged in.
_AUTH_REQUIRED_INC_PARAMS = frozenset(
    (
        'user-collections',
        'user-genres',
        'user-ratings',
        'user-tags',
    )
)


@dataclass
class Parser:
    mimetype: str
    parser: Callable[[QNetworkReply], Any]


@runtime_checkable
class ReplyLike(Protocol):
    """Protocol defining the interface handlers expect from a reply object.

    Both QNetworkReply and _AuthorizationErrorReply satisfy this protocol.
    """

    def errorString(self) -> str: ...
    def url(self) -> QUrl: ...
    def attribute(self, code: QNetworkRequest.Attribute) -> Any: ...


ReplyHandler: TypeAlias = Callable[[Any, ReplyLike, QNetworkReply.NetworkError | Exception | None], None]


class UnknownResponseParserError(Exception):
    def __init__(self, response_type):
        message = (
            "Unknown parser for response type '%s'. Parser for given response type does not exist." % response_type
        )
        super().__init__(message)


class WSRequest(QNetworkRequest):
    """Represents a single HTTP request."""

    _access_token = None
    _high_prio_no_cache = True
    _mblogin = False
    _retries = 0

    response_mimetype = None
    response_parser = None

    def __init__(
        self,
        *,
        method: str | None = None,
        handler: ReplyHandler | None = None,
        parse_response_type: str | None = None,
        data: str | None = None,
        mblogin: bool = False,
        cacheloadcontrol: QNetworkRequest.CacheLoadControl | None = None,
        refresh: bool = False,
        priority: bool = False,
        important: bool = False,
        request_mimetype: str | None = None,
        url: QUrl | str | None = None,
        queryargs: dict | None = None,
        unencoded_queryargs: dict | None = None,
        headers: dict[str, str] | None = None,
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
            queryargs: Encoded query arguments, a dictionary mapping field names to values
            unencoded_queryargs: Unencoded query arguments, a dictionary mapping field names to values
            headers: Additional headers to include with the request, a dictionary mapping header names to values
        """
        # mandatory parameters
        if method not in {'GET', 'PUT', 'DELETE', 'POST'}:
            raise AssertionError('invalid method')
        self.method = method

        if handler is None:
            raise AssertionError('handler undefined')
        self.handler: ReplyHandler = handler

        if url is None:
            raise AssertionError('URL undefined')

        if not isinstance(url, QUrl):
            url = QUrl(url)

        if queryargs is not None or unencoded_queryargs is not None:
            if queryargs is None:
                queryargs = {}
            if unencoded_queryargs:
                queryargs.update(encoded_queryargs(unencoded_queryargs))
            query = QtCore.QUrlQuery(url)
            for k, v in queryargs.items():
                query.addQueryItem(k, str(v))
            url.setQuery(query)

        super().__init__(url)

        # To simulate an ssl error, uncomment following lines
        # ssl = self.sslConfiguration()
        # ssl.setCaCertificates(list())
        # self.setSslConfiguration(ssl)

        # optional parameters
        self.parse_response_type = parse_response_type
        self.request_mimetype = request_mimetype
        self.data = data
        self.mblogin = mblogin
        self.cacheloadcontrol = cacheloadcontrol
        self.refresh = refresh
        self.has_priority = priority
        self.important = important
        self.extra_headers = headers

        # set headers and attributes
        self.access_token = None  # call _update_authorization_header

        if self.method == 'GET':
            self._high_prio_no_cache = self.refresh
            self.setAttribute(QNetworkRequest.Attribute.HttpPipeliningAllowedAttribute, True)

        # use HTTP/2 if possible
        self.setAttribute(QNetworkRequest.Attribute.Http2AllowedAttribute, True)

        self.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, USER_AGENT_STRING)

        if self.mblogin or self._high_prio_no_cache:
            self.setPriority(QNetworkRequest.Priority.HighPriority)
            self.setAttribute(
                QNetworkRequest.Attribute.CacheLoadControlAttribute, QNetworkRequest.CacheLoadControl.AlwaysNetwork
            )
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
                self.request_mimetype = self.response_mimetype or 'application/x-www-form-urlencoded'
            self.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, self.request_mimetype)

        if self.extra_headers:
            for name, value in self.extra_headers.items():
                self.setRawHeader(name.encode('utf-8'), value.encode('utf-8'))

    @property
    def has_auth(self):
        return self.mblogin and self.access_token

    def _update_authorization_header(self):
        if self.mblogin and self.access_token:
            auth = 'Bearer ' + self.access_token
            self.setRawHeader(b'Authorization', auth.encode('utf-8'))

    @property
    def host(self) -> str:
        return self.url().host()

    @property
    def port(self) -> int:
        return port_from_qurl(self.url())

    @property
    def path(self) -> str:
        return self.url().path()

    @property
    def access_token(self) -> str | None:
        return self._access_token

    @access_token.setter
    def access_token(self, access_token: str | None):
        self._access_token = access_token
        self._update_authorization_header()

    @property
    def mblogin(self) -> bool:
        return self._mblogin

    @mblogin.setter
    def mblogin(self, mblogin: bool):
        self._mblogin = mblogin
        self._update_authorization_header()

    def get_host_key(self) -> ratecontrol.HostKey:
        return (self.host, self.port)

    def max_retries_reached(self):
        return self._retries >= TEMP_ERRORS_RETRIES

    def mark_for_retry(self, important=True, priority=True):
        # Put retries at the head of the list in order to not penalize
        # the load an album unlucky enough to hit a temporary service
        # snag.
        self.important = important
        self.has_priority = priority
        self._retries += 1
        return self._retries


class PendingRequest:
    """Represents a queued webservice request."""

    def __init__(self, hostkey: ratecontrol.HostKey, func: Callable | None, priority: int):
        self.hostkey = hostkey
        self.func = func
        self.priority = priority
        self.aborted = False

    @staticmethod
    def from_request(request: WSRequest, func: Callable | None):
        # priority is a boolean
        return PendingRequest(request.get_host_key(), func, int(request.has_priority))


class RequestPriorityQueue:
    def __init__(self):
        self._queues = defaultdict(lambda: defaultdict(deque))
        self._count = 0

    def count(self):
        return self._count

    def add_task(self, task: PendingRequest, important: bool = False) -> PendingRequest:
        queue = self._queues[task.priority][task.hostkey]
        if important:
            queue.appendleft(task.func)
        else:
            queue.append(task.func)
        self._count += 1
        return task

    def remove_task(self, task: PendingRequest):
        try:
            self._queues[task.priority][task.hostkey].remove(task.func)
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
            for hostkey in sorted(prio_queue.keys(), key=ratecontrol.current_delay):
                queue = self._queues[prio][hostkey]
                if not queue:
                    del self._queues[prio][hostkey]
                    continue
                wait, d = ratecontrol.get_delay_to_next_request(hostkey)
                if not wait:
                    queue.popleft()()
                    self._count -= 1
                if d < delay:
                    delay = d
        return delay


class WebService(QtCore.QObject):
    PARSERS: ClassVar[dict[str, Parser]] = dict()

    authorization_required = QtCore.pyqtSignal()
    authorization_state_changed = QtCore.pyqtSignal()
    pending_requests_changed = QtCore.pyqtSignal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.manager = QtNetwork.QNetworkAccessManager()
        self.manager.sslErrors.connect(self.ssl_errors)
        self.oauth_manager = OAuthManager(self)
        self.oauth_manager.authorization_state_changed.connect(self.authorization_state_changed)
        config = get_config()
        self._init_cache()
        self.set_cache_size()
        self.setup_proxy()
        self.set_transfer_timeout(config.setting['network_transfer_timeout_seconds'])
        self.manager.finished.connect(self._process_reply)
        self._request_methods: dict[str, Callable] = {
            'GET': self.manager.get,
            'POST': self.manager.post,
            'PUT': self.manager.put,
            'DELETE': self.manager.deleteResource,
        }
        self._init_queues()
        self._init_timers()

    def ssl_errors(self, reply: QNetworkReply, errors: list[QSslError]):
        # According to forums, sometimes sslErrors is triggered with errors set to NoError
        # This can also be used to ignore others if needed
        ignored_errors = {
            QSslError.SslError.NoError,
        }
        has_errors = False
        for error in errors:
            if error.error() not in ignored_errors:
                has_errors = True
                log.error("SSL error: %s" % error.errorString())
        if not has_errors:
            reply.ignoreSslErrors()

    @staticmethod
    def http_response_code(reply: QNetworkReply) -> int:
        response_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        return int(response_code) if response_code else 0

    @staticmethod
    def http_response_phrase(reply: QNetworkReply) -> Any:
        return reply.attribute(QNetworkRequest.Attribute.HttpReasonPhraseAttribute)

    @staticmethod
    def display_url(url: QUrl) -> str:
        return url.toDisplayString(
            QUrl.UrlFormattingOption.RemoveUserInfo | QUrl.ComponentFormattingOption.EncodeSpaces
        )

    def _init_queues(self):
        self._active_requests = {}
        self._task_to_reply: dict[PendingRequest, QNetworkReply] = {}
        self._queue = RequestPriorityQueue()
        self.num_pending_web_requests = 0
        self._notify_on_cancel = False
        self._awaiting_authorization: list[WSRequest] = []
        self._authorization_pending = False

    def _init_timers(self):
        self._timer_run_next_task = QtCore.QTimer(self)
        self._timer_run_next_task.setSingleShot(True)
        self._timer_run_next_task.timeout.connect(self._run_next_task)
        self._timer_count_pending_requests = QtCore.QTimer(self)
        self._timer_count_pending_requests.setSingleShot(True)
        self._timer_count_pending_requests.timeout.connect(self._count_pending_requests)

    def _init_cache(self):
        cache = QtNetwork.QNetworkDiskCache()
        cache.setCacheDirectory(os.path.join(appdirs.cache_folder(), 'network'))
        self.manager.setCache(cache)
        log.debug("NetworkDiskCache dir: %r", cache.cacheDirectory())

    def get_valid_cache_size(self):
        try:
            config = get_config()
            cache_size = int(config.setting['network_cache_size_bytes'])
            if cache_size >= 0:
                return cache_size
        except ValueError:
            pass
        return DEFAULT_CACHE_SIZE_IN_BYTES

    def set_cache_size(self):
        cache_size_in_bytes = self.get_valid_cache_size()
        cache = self.manager.cache()
        if isinstance(cache, QtNetwork.QNetworkDiskCache) and cache.maximumCacheSize() != cache_size_in_bytes:
            cache.setMaximumCacheSize(cache_size_in_bytes)
            log.debug(
                "NetworkDiskCache size: %s maxsize: %s",
                bytes2human.decimal(cache.cacheSize(), l10n=False),
                bytes2human.decimal(cache.maximumCacheSize(), l10n=False),
            )

    def clear_cache(self):
        cache = self.manager.cache()
        if isinstance(cache, QtNetwork.QNetworkDiskCache):
            cache.clear()
            log.info("Network cache cleared")

    def get_cache_size(self):
        cache = self.manager.cache()
        if isinstance(cache, QtNetwork.QNetworkDiskCache):
            return cache.cacheSize()
        return 0

    def setup_proxy(self):
        proxy = QtNetwork.QNetworkProxy()
        config = get_config()
        if config.setting['use_proxy']:
            if config.setting['proxy_type'] == 'socks':
                proxy.setType(QtNetwork.QNetworkProxy.ProxyType.Socks5Proxy)
            else:
                proxy.setType(QtNetwork.QNetworkProxy.ProxyType.HttpProxy)
            proxy.setHostName(config.setting['proxy_server_host'])
            proxy.setPort(config.setting['proxy_server_port'])
            if config.setting['proxy_username']:
                proxy.setUser(config.setting['proxy_username'])
            if config.setting['proxy_password']:
                proxy.setPassword(config.setting['proxy_password'])
        self.manager.setProxy(proxy)

    def set_transfer_timeout(self, timeout: int):
        timeout_ms = timeout * 1000
        self.manager.setTransferTimeout(timeout_ms)

    def _send_request(self, request: WSRequest, task: PendingRequest | None = None, access_token=None):
        hostkey = request.get_host_key()
        ratecontrol.increment_requests(hostkey)

        request.access_token = access_token
        send = self._request_methods[request.method]
        data = request.data
        if data is not None:
            reply = send(request, data.encode('utf-8'))
        else:
            reply = send(request)
        self._active_requests[reply] = request
        if task and reply:
            self._task_to_reply[task] = reply

    def _start_request(self, request: WSRequest, task_ref: weakref.ReferenceType[PendingRequest] | None = None):
        # Check if task was aborted before starting
        task = task_ref() if task_ref else None
        if task and task.aborted:
            log.debug("Skipping aborted task for %s", request.url().toString())
            return

        if request.mblogin:
            self.oauth_manager.get_access_token(partial(self._send_request, request, task))
        else:
            self._send_request(request, task)

    @staticmethod
    def urls_equivalent(leftUrl: QUrl, rightUrl: QUrl) -> bool:
        """
        Lazy method to determine whether two QUrls are equivalent. At the moment it assumes that if ports are unset
        that they are port 80 - in absence of a URL normalization function in QUrl or ability to use qHash
        from QT 4.7
        """
        return leftUrl.port(80) == rightUrl.port(80) and leftUrl.toString(
            QUrl.UrlFormattingOption.RemovePort
        ) == rightUrl.toString(QUrl.UrlFormattingOption.RemovePort)

    def _handle_redirect(self, reply: QNetworkReply, request: WSRequest, redirect: QUrl):
        # merge with base url (to cover the possibility of the URL being relative)
        redirect_url = request.url().resolved(redirect)
        reply_url = reply.request().url()
        display_redirect_url = self.display_url(redirect_url)
        display_reply_url = self.display_url(reply_url)
        if not WebService.urls_equivalent(redirect_url, reply_url):
            log.debug("Redirect to %s requested", display_redirect_url)

            redirect_request = WSRequest(
                method='GET',
                url=redirect_url,
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
            log.error("Redirect loop: %s", display_reply_url)
            request.handler(reply.readAll().data(), reply, QNetworkReply.NetworkError.TooManyRedirectsError)

    def _handle_reply(self, reply: QNetworkReply, request: WSRequest):
        hostkey = request.get_host_key()
        ratecontrol.decrement_requests(hostkey)

        for task, stored_reply in list(self._task_to_reply.items()):
            if stored_reply == reply:
                del self._task_to_reply[task]
                break

        self._timer_run_next_task.start(0)

        slow_down = False

        error = reply.error()

        # Silently ignore canceled operations (user-initiated abort)
        if error == QNetworkReply.NetworkError.OperationCanceledError:
            if self._notify_on_cancel:
                handler = request.handler
                if handler is not None:
                    handler(b'', reply, error)
            else:
                log.debug("Request canceled for %s", self.display_url(reply.request().url()))
            return

        handler = request.handler
        response_code = self.http_response_code(reply)
        display_reply_url = self.display_url(reply.request().url())
        if reply.attribute(QNetworkRequest.Attribute.Http2WasUsedAttribute):
            proto = 'HTTP2'
        else:
            proto = 'HTTP'
        if error != QNetworkReply.NetworkError.NoError:
            errstr = reply.errorString()
            log.error(
                "Network request error for %s -> %s (QT code %r, %s code %d)",
                display_reply_url,
                errstr,
                error,
                proto,
                response_code,
            )
            if request.mblogin and response_code == 401:
                if not request.has_auth and self.oauth_manager.is_authorized():
                    # User has since logged in (e.g. this is a stale request
                    # that was in-flight before authorization completed).
                    # Retry immediately with the new token.
                    log.debug("Retrying %s with updated authorization", display_reply_url)
                    self.add_request(request)
                else:
                    # Queue the request for retry after authorization and
                    # signal that user authorization is needed, but only once.
                    log.debug("Authorization required for %s", display_reply_url)
                    if len(self._awaiting_authorization) >= MAX_PENDING_AUTHORIZATION_REQUESTS:
                        # Drop the oldest request to prevent unbounded growth
                        dropped = self._awaiting_authorization.pop(0)
                        log.debug("Authorization queue full, dropping %s", dropped.url().toString())
                        if dropped.handler is not None:
                            dropped.handler(b'', _AuthorizationErrorReply(dropped), error)
                    self._awaiting_authorization.append(request)
                    if not self._authorization_pending:
                        self._authorization_pending = True
                        self.authorization_required.emit()

            elif not request.max_retries_reached() and (
                response_code == 503
                or response_code == 429
                # Sometimes QT returns a http status code of 200 even when there
                # is a service unavailable error.
                or error == QNetworkReply.NetworkError.ServiceUnavailableError
            ):
                slow_down = True
                retries = request.mark_for_retry()
                log.debug("Retrying %s (#%d)", display_reply_url, retries)
                self.add_request(request)

            elif handler is not None:
                handler(reply.readAll().data(), reply, error)

            slow_down = slow_down or response_code >= 500

        else:
            error = None
            redirect = reply.attribute(QNetworkRequest.Attribute.RedirectionTargetAttribute)
            from_cache = reply.attribute(QNetworkRequest.Attribute.SourceIsFromCacheAttribute)
            cached = ' (CACHED)' if from_cache else ''
            log.debug(
                "Received reply for %s -> %s %d (%s) %s",
                display_reply_url,
                proto,
                response_code,
                self.http_response_phrase(reply),
                cached,
            )
            if handler is not None:
                # Redirect if found and not infinite
                if redirect:
                    self._handle_redirect(reply, request, redirect)
                elif request.response_parser:
                    try:
                        document = request.response_parser(reply)
                        if DebugOpt.WS_REPLIES.enabled:
                            log.debug("Response received: %s", document)
                    except Exception as e:
                        log.error("Unable to parse the response for %s -> %s", display_reply_url, e)
                        document = reply.readAll().data()
                        error = e
                    finally:
                        handler(document, reply, error)
                else:
                    # readAll() returns QtCore.QByteArray, so convert to bytes
                    handler(reply.readAll().data(), reply, error)

        ratecontrol.adjust(hostkey, slow_down)

    def _process_reply(self, reply: QNetworkReply):
        try:
            request = self._active_requests.pop(reply)
        except KeyError:
            display_reply_url = self.display_url(reply.request().url())
            log.error("Request not found for %s", display_reply_url)
            return
        try:
            self._handle_reply(reply, request)
        finally:
            try:
                reply.close()
                reply.deleteLater()
            except RuntimeError:
                # Qt object may already be deleted
                pass

    def get_url(self, **kwargs) -> PendingRequest:
        kwargs['method'] = 'GET'
        kwargs['parse_response_type'] = kwargs.get('parse_response_type', DEFAULT_RESPONSE_PARSER_TYPE)
        return self.add_request(WSRequest(**kwargs))

    def post_url(self, **kwargs) -> PendingRequest:
        kwargs['method'] = 'POST'
        kwargs['parse_response_type'] = kwargs.get('parse_response_type', DEFAULT_RESPONSE_PARSER_TYPE)
        if DebugOpt.WS_POST.enabled:
            log.debug("POST-DATA %r", kwargs['data'])
        return self.add_request(WSRequest(**kwargs))

    def put_url(self, **kwargs) -> PendingRequest:
        kwargs['method'] = 'PUT'
        kwargs['priority'] = kwargs.get('priority', True)
        return self.add_request(WSRequest(**kwargs))

    def delete_url(self, **kwargs) -> PendingRequest:
        kwargs['method'] = 'DELETE'
        kwargs['priority'] = kwargs.get('priority', True)
        return self.add_request(WSRequest(**kwargs))

    def download_url(self, **kwargs) -> PendingRequest:
        kwargs['method'] = 'GET'
        return self.add_request(WSRequest(**kwargs))

    def stop(self):
        for reply in list(self._active_requests):
            reply.abort()
        self._init_queues()

    def stop_and_notify(self):
        """Stop all requests, calling handlers with the cancellation error.

        Unlike stop(), this passes the error to handlers so they can
        transition to a proper error state (e.g. albums mark as ERROR).
        """
        self._notify_on_cancel = True
        for reply in list(self._active_requests):
            reply.abort()
        self._notify_on_cancel = False
        self._init_queues()

    def _count_pending_requests(self):
        count = len(self._active_requests) + self._queue.count()
        if count != self.num_pending_web_requests:
            self.num_pending_web_requests = count
            self.pending_requests_changed.emit()
        if count:
            self._timer_count_pending_requests.start(COUNT_REQUESTS_DELAY_MS)

    def _run_next_task(self):
        delay = self._queue.run_ready_tasks()
        if delay < sys.maxsize:
            self._timer_run_next_task.start(delay)

    def add_task(self, func: Callable, request: WSRequest):
        task = PendingRequest.from_request(request, func)
        self._queue.add_task(task, request.important)

        if not self._timer_run_next_task.isActive():
            self._timer_run_next_task.start(0)

        if not self._timer_count_pending_requests.isActive():
            self._timer_count_pending_requests.start(0)

        return task

    def add_request(self, request: WSRequest) -> PendingRequest:
        task = PendingRequest.from_request(request, None)
        task.func = partial(self._start_request, request, weakref.ref(task))
        self._queue.add_task(task, request.important)

        if not self._timer_run_next_task.isActive():
            self._timer_run_next_task.start(0)

        if not self._timer_count_pending_requests.isActive():
            self._timer_count_pending_requests.start(0)

        return task

    def abort_task(self, task: PendingRequest):
        """Abort a request task, whether queued or active.

        Args:
            task: PendingRequest to abort
        """
        # Mark task as aborted so it won't execute if still queued
        task.aborted = True

        # If task has an active reply, abort it
        reply = self._task_to_reply.get(task, None)
        if reply:
            try:
                reply.abort()
                del self._task_to_reply[task]
            except (RuntimeError, KeyError):
                # Reply may already be deleted
                pass

        # Try to remove from queue (may already be executing)
        self._remove_task(task)

    def _remove_task(self, task: PendingRequest):
        """Internal method to remove a task from the queue."""
        self._queue.remove_task(task)
        if not self._timer_count_pending_requests.isActive():
            self._timer_count_pending_requests.start(0)

    def retry_authorized_requests(self):
        """Retry all requests that were waiting for authorization.

        Call this after the user has successfully logged in.
        """
        self._authorization_pending = False
        requests = self._awaiting_authorization
        self._awaiting_authorization = []
        for request in requests:
            log.debug("Retrying authorized request for %s", request.url().toString())
            self.add_request(request)

    def discard_authorized_requests(self):
        """Discard authorization requirement and retry requests without user data.

        Call this when the user declines to log in or login fails.
        GET requests are retried without user-specific inc params (user-ratings,
        user-collections, etc.) so that public data still loads.
        Non-GET requests (submissions) are dropped and their handlers called
        with the authentication error.
        """
        self._authorization_pending = False
        requests = self._awaiting_authorization
        self._awaiting_authorization = []
        error = QNetworkReply.NetworkError.AuthenticationRequiredError
        for request in requests:
            if request.method == 'GET':
                self._retry_without_auth(request)
            else:
                handler = request.handler
                if handler is not None:
                    handler(b'', _AuthorizationErrorReply(request), error)

    def _retry_without_auth(self, request: WSRequest):
        """Retry a request without authentication and user-specific inc params.

        Only retries if user-specific params were actually removed from the URL.
        If nothing changed, the request is dropped and the handler is called with
        the authentication error.
        """
        url = QUrl(request.url())
        query = QtCore.QUrlQuery(url)
        modified = False
        if query.hasQueryItem('inc'):
            inc_value = query.queryItemValue('inc', QUrl.ComponentFormattingOption.FullyDecoded)
            inc_params = set(inc_value.split('+'))
            filtered_params = inc_params - _AUTH_REQUIRED_INC_PARAMS
            if filtered_params != inc_params:
                modified = True
                query.removeQueryItem('inc')
                if filtered_params:
                    query.addQueryItem('inc', '+'.join(sorted(filtered_params)))
                url.setQuery(query)
        if modified:
            request.setUrl(url)
            request.mblogin = False
            log.debug("Retrying without authentication: %s", url.toString())
            self.add_request(request)
        else:
            log.debug("Cannot retry without authentication: %s", url.toString())
            handler = request.handler
            if handler is not None:
                handler(b'', _AuthorizationErrorReply(request), QNetworkReply.NetworkError.AuthenticationRequiredError)

    @classmethod
    def add_parser(cls, response_type: str, mimetype: str, parser: Callable[[QNetworkReply], Any]):
        cls.PARSERS[response_type] = Parser(mimetype=mimetype, parser=parser)

    @classmethod
    def get_response_mimetype(cls, response_type: str) -> str:
        if response_type in cls.PARSERS:
            return cls.PARSERS[response_type].mimetype
        else:
            raise UnknownResponseParserError(response_type)

    @classmethod
    def get_response_parser(cls, response_type: str) -> Callable[[QNetworkReply], Any]:
        if response_type in cls.PARSERS:
            return cls.PARSERS[response_type].parser
        else:
            raise UnknownResponseParserError(response_type)


class _AuthorizationErrorReply:
    """Minimal reply-like object passed to handlers when authorization is declined.

    Provides the subset of the QNetworkReply interface that handlers commonly use
    when handling errors (errorString, url, attribute).
    Satisfies the ReplyLike protocol.
    """

    def __init__(self, request: WSRequest):
        self._request = request

    def errorString(self) -> str:
        return 'Authorization required'

    def url(self) -> QUrl:
        return self._request.url()

    def attribute(self, code: QNetworkRequest.Attribute) -> Any:
        if code == QNetworkRequest.Attribute.HttpStatusCodeAttribute:
            return 401
        return None


WebService.add_parser('xml', 'application/xml', parse_xml)
WebService.add_parser('json', 'application/json', parse_json)
