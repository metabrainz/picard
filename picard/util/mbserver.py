# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Philipp Wolfer
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

from collections import namedtuple

from picard.config import get_config
from picard.const import MUSICBRAINZ_SERVERS
from picard.util import build_qurl


ServerTuple = namedtuple('ServerTuple', ('host', 'port'))


def is_official_server(host):
    """Returns True, if host is an official MusicBrainz server for the primary database.

    Args:
        host: the hostname

    Returns: True, if host is an official MusicBrainz server, False otherwise
    """
    return host in MUSICBRAINZ_SERVERS


def get_submission_server():
    """Returns the host and port used for data submission.

    Data submission usually should be done against the primary database. This function
    will return the hostname configured as `server_host` if it is an official MusicBrainz
    server, otherwise it will return the primary official server.

    Returns: Tuple of hostname and port number, e.g. `('musicbrainz.org', 443)`
    """
    config = get_config()
    host = config.setting['server_host']
    if is_official_server(host):
        return ServerTuple(host, 443)
    elif host and config.setting['use_server_for_submission']:
        port = config.setting['server_port']
        return ServerTuple(host, port)
    else:
        return ServerTuple(MUSICBRAINZ_SERVERS[0], 443)


def build_submission_url(path=None, query_args=None):
    """Builds a submission URL with path and query parameters.

    Args:
        path: The path for the URL
        query_args: A dict of query parameters

    Returns: The submission URL as a string
    """
    server = get_submission_server()
    url = build_qurl(server.host, server.port, path, query_args)
    return url.toString()
