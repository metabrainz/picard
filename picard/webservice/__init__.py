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

from PyQt6 import (
    QtCore,
    QtNetwork,
)
from PyQt6.QtCore import QUrl
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
from picard.const import (
    CACHE_SIZE_IN_BYTES,
    appdirs,
)
from picard.debug_opts import DebugOpt
from picard.oauth import OAuthManager
from picard.util import (
    build_qurl,
    bytes2human,
    encoded_queryargs,
    parse_json,
)
from picard.util.xml import parse_xml
from picard.webservice import ratecontrol
from picard.webservice.utils import port_from_qurl


COUNT_REQUESTS_DELAY_MS = 250

TEMP_ERRORS_RETRIES = 5
USER_AGENT_STRING = '%s-%s/%s (%s;%s-%s)' % (PICARD_ORG_NAME, PICARD_APP_NAME,
                                             PICARD_VERSION_STR,
                                             platform.platform(),
                                             platform.python_implementation(),
                                             platform.python_version())
CLIENT_STRING = '%s %s-%s' % (PICARD_ORG_NAME, PICARD_APP_NAME, PICARD_VERSION_STR)


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
        unencoded_queryargs=None,
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
        self.priority = priority
        self.important = important

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
                self.request_mimetype = self.response_mimetype or 'application/x-www-form-urlencoded'
            self.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, self.request_mimetype)

    @property
    def has_auth(self):
        return self.mblogin and self.access_token

    def _update_authorization_header(self):
        auth = 'Bearer ' + self.access_token if self.has_auth else ''
        self.setRawHeader(b'Authorization', auth.encode('utf-8'))

    @property
    def host(self):
        return self.url().host()

    @property
    def port(self):
        return port_from_qurl(self.url())

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
        self.manager.sslErrors.connect(self.ssl_errors)
        self.oauth_manager = OAuthManager(self)
        config = get_config()
        self._init_cache()
        self.set_cache_size()
        self.setup_proxy()
        self.set_transfer_timeout(config.setting['network_transfer_timeout_seconds'])
        self.manager.finished.connect(self._process_reply)
        self._request_methods = {
            'GET': self.manager.get,
            'POST': self.manager.post,
            'PUT': self.manager.put,
            'DELETE': self.manager.deleteResource
        }
        self._init_queues()
        self._init_timers()

    def ssl_errors(self, reply, errors):
        # According to forums, sometimes sslErrors is triggered with errors set to NoError
        # This can also be used to ignore others if needed
        ignored_errors = {
            QSslError.NoError,
        }
        has_errors = False
        for error in errors:
            if error not in ignored_errors:
                has_errors = True
                log.error("SSL error: %s" % error.errorString())
        if not has_errors:
            reply.ignoreSslErrors()

    @staticmethod
    def http_response_code(reply):
        response_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        return int(response_code) if response_code else 0

    @staticmethod
    def http_response_phrase(reply):
        return reply.attribute(QNetworkRequest.Attribute.HttpReasonPhraseAttribute)

    @staticmethod
    def display_url(url):
        return url.toDisplayString(QUrl.UrlFormattingOption.RemoveUserInfo | QUrl.ComponentFormattingOption.EncodeSpaces)

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

    def _init_cache(self, cache_size_in_bytes=None):
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
        return CACHE_SIZE_IN_BYTES

    def set_cache_size(self):
        cache_size_in_bytes = self.get_valid_cache_size()
        cache = self.manager.cache()
        if cache.maximumCacheSize() != cache_size_in_bytes:
            cache.setMaximumCacheSize(cache_size_in_bytes)
            log.debug(
                "NetworkDiskCache size: %s maxsize: %s",
                bytes2human.decimal(cache.cacheSize(), l10n=False),
                bytes2human.decimal(cache.maximumCacheSize(), l10n=False)
            )

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

    def set_transfer_timeout(self, timeout):
        timeout_ms = timeout * 1000
        self.manager.setTransferTimeout(timeout_ms)

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
            leftUrl.toString(QUrl.UrlFormattingOption.RemovePort) == rightUrl.toString(QUrl.UrlFormattingOption.RemovePort)

    def _handle_redirect(self, reply, request, redirect):
        error = int(reply.error())
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
            request.handler(reply.readAll(), reply, error)

    def _handle_reply(self, reply, request):
        hostkey = request.get_host_key()
        ratecontrol.decrement_requests(hostkey)

        self._timer_run_next_task.start(0)

        slow_down = False

        error = reply.error()
        handler = request.handler
        response_code = self.http_response_code(reply)
        display_reply_url = self.display_url(reply.request().url())
        if reply.attribute(QNetworkRequest.Attribute.Http2WasUsedAttribute):
            proto = 'HTTP2'
        else:
            proto = 'HTTP'
        if error != QNetworkReply.NetworkError.NoError:
            errstr = reply.errorString()
            log.error("Network request error for %s -> %s (QT code %r, %s code %d)",
                      display_reply_url, errstr, error, proto, response_code)
            if (not request.max_retries_reached()
                and (response_code == 503
                     or response_code == 429
                     # Sometimes QT returns a http status code of 200 even when there
                     # is a service unavailable error.
                     or error == QNetworkReply.NetworkError.ServiceUnavailableError
                     )):
                slow_down = True
                retries = request.mark_for_retry()
                log.debug("Retrying %s (#%d)", display_reply_url, retries)
                self.add_request(request)

            elif handler is not None:
                handler(reply.readAll(), reply, error)

            slow_down = (slow_down or response_code >= 500)

        else:
            error = None
            redirect = reply.attribute(QNetworkRequest.Attribute.RedirectionTargetAttribute)
            from_cache = reply.attribute(QNetworkRequest.Attribute.SourceIsFromCacheAttribute)
            cached = ' (CACHED)' if from_cache else ''
            log.debug("Received reply for %s -> %s %d (%s) %s",
                      display_reply_url,
                      proto,
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
                        if DebugOpt.WS_REPLIES.enabled:
                            log.debug("Response received: %s", document)
                    except Exception as e:
                        log.error("Unable to parse the response for %s -> %s", display_reply_url, e)
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
            display_reply_url = self.display_url(reply.request().url())
            log.error("Request not found for %s", display_reply_url)
            return
        try:
            self._handle_reply(reply, request)
        finally:
            reply.close()
            reply.deleteLater()

    def get(self, host, port, path, handler, parse_response_type=DEFAULT_RESPONSE_PARSER_TYPE,
            priority=False, important=False, mblogin=False, cacheloadcontrol=None, refresh=False,
            queryargs=None):
        log.warning("This method is deprecated, use WebService.get_url() instead")
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
        log.warning("This method is deprecated, use WebService.post_url() instead")
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
        log.warning("This method is deprecated, use WebService.put_url() instead")
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
        log.warning("This method is deprecated, use WebService.delete_url() instead")
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
        log.warning("This method is deprecated, use WebService.download_url() instead")
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
