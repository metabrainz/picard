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
Asynchronous web service utilities.
"""

from PySide6.QtCore import QUrl


def port_from_qurl(qurl):
    """Returns QUrl port or default ports (443 for https, 80 for http)"""
    if qurl.scheme() == 'https':
        return qurl.port(443)
    return qurl.port(80)


def hostkey_from_url(url):
    """Returns (host, port) from passed url (as string or QUrl)"""
    if not isinstance(url, QUrl):
        url = QUrl(url)
    return (url.host(), port_from_qurl(url))


def host_port_to_url(host, port, path=None, scheme=None, as_string=False):
    """Convert host & port (with optional path and scheme) to an URL"""
    url = QUrl()
    if scheme is None:
        if port == 443:
            scheme = 'https'
        else:
            scheme = 'http'
    url.setScheme(scheme)

    if ((scheme == 'https' and port != 443)
            or (scheme == 'http' and port != 80)):
        url.setPort(port)

    url.setHost(host)

    if path is not None:
        url.setPath(path)

    return url.toString() if as_string else url
