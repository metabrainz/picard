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

from secrets import token_bytes

import jwt
import jwt.exceptions

from PyQt5.QtCore import QCoreApplication

from picard.config import get_config
from picard.const import MUSICBRAINZ_SERVERS
from picard.util import htmlescape
from picard.util.webbrowser2 import open


__key = token_bytes()  # Generating a new secret on each startup
__algorithm = 'HS256'

_form_template = '''<!doctype html>
<meta charset="UTF-8">
<html>
<head>
    <title>{title}</title>
</head>
<body>
    <form action="{action}" method="post">
        {form_data}
        <input type="submit" value="{submit_label}">
    </form>
    <script>document.forms[0].submit()</script>
</body>
'''

_form_input_template = '<input type="hidden" name="{name}" value="{value}" >'


class InvalidTokenError(Exception):
    pass


class NotFoundError(Exception):
    pass


def submit_cluster(cluster):
    token = jwt.encode({'cluster': hash(cluster)}, __key, algorithm=__algorithm)
    _open_token_url(token)


def serve_form(token):
    try:
        payload = jwt.decode(token, __key, algorithms=__algorithm)
        cluster = _find_cluster(payload['cluster'])
        if not cluster:
            raise NotFoundError('Cluster not found')

        data = _get_form(cluster)
        return _form_template.format(**data)
    except jwt.exceptions.InvalidTokenError:
        raise InvalidTokenError


def _open_token_url(token):
    browser_integration = QCoreApplication.instance().browser_integration
    url = 'http://%s:%s/add?token=%s' % (
        browser_integration.host_address, browser_integration.port, token)
    open(url)


def _find_cluster(cluster_hash):
    tagger = QCoreApplication.instance()
    for cluster in tagger.clusters:
        if hash(cluster) == cluster_hash:
            return cluster
    return None


def _mbserver_url(path):
    config = get_config()
    host = config.setting["server_host"]
    if host not in MUSICBRAINZ_SERVERS:
        host = MUSICBRAINZ_SERVERS[0]  # Submission only works to official servers
    return "https://%s%s" % (host, path)


def _get_form(cluster):
    form_data = _get_form_data(cluster)
    return {
        'title': htmlescape(_('Add cluster as release...')),
        'action': htmlescape(_mbserver_url('/release/add')),
        'form_data': form_data,
        'submit_label': htmlescape(_('Add cluster as release...')),
    }


def _get_form_data(cluster):
    return ''.join((
        _form_input_template.format(name=htmlescape(name), value=htmlescape(value))
        for name, value in _get_cluster_metadata(cluster).items()
    ))


def _get_cluster_metadata(cluster):
    # See https://musicbrainz.org/doc/Development/Release_Editor_Seeding
    metadata = cluster.metadata
    data = {
        'name': metadata['album'],
        'artist_credit.names.0.artist.name': metadata['albumartist'],
    }

    def mkey(disc, track, name):
        return 'mediums.%i.track.%i.%s' % (disc, track, name)

    for i, file in enumerate(cluster.files):
        data[mkey(0, i, 'name')] = file.metadata['title']
        data[mkey(0, i, 'number')] = file.metadata['tracknumber'] or str(i + 1)
        data[mkey(0, i, 'length')] = str(file.metadata.length)

    return data
