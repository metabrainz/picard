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

from picard import log
from picard.config import get_config
from picard.const import MUSICBRAINZ_SERVERS
from picard.util import (
    format_time,
    htmlescape,
)
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


def is_enabled():
    tagger = QCoreApplication.instance()
    return tagger.browser_integration.is_running


def submit_cluster(cluster):
    _open_url_with_token({'cluster': hash(cluster)})


def submit_file(file):
    _open_url_with_token({'file': file.filename})


def serve_form(token):
    try:
        payload = jwt.decode(token, __key, algorithms=__algorithm)
        log.debug('received JWT token %r', payload)
        if 'cluster' in payload:
            cluster = _find_cluster(payload['cluster'])
            if not cluster:
                raise NotFoundError('Cluster not found')
            return _get_cluster_form(cluster)
        elif 'file' in payload:
            file = _find_file(payload['file'])
            if not file:
                raise NotFoundError('File not found')
            return _get_file_form(file)
        else:
            raise InvalidTokenError
    except jwt.exceptions.InvalidTokenError:
        raise InvalidTokenError


def extract_discnumber(metadata):
    try:
        discnumber = metadata.get('discnumber', '1').split('/')[0]
        return int(discnumber)
    except ValueError:
        return 1


def _open_url_with_token(payload):
    token = jwt.encode(payload, __key, algorithm=__algorithm)
    if isinstance(token, bytes):  # For compatibility with PyJWT 1.x
        token = token.decode()
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


def _find_file(path):
    tagger = QCoreApplication.instance()
    return tagger.files.get(path, None)


def _mbserver_url(path):
    config = get_config()
    host = config.setting["server_host"]
    if host not in MUSICBRAINZ_SERVERS:
        host = MUSICBRAINZ_SERVERS[0]  # Submission only works to official servers
    return "https://%s%s" % (host, path)


def _get_cluster_form(cluster):
    return _get_form(
        _('Add cluster as release'),
        '/release/add',
        _('Add cluster as release...'),
        _get_cluster_data(cluster)
    )


def _get_file_form(cluster):
    return _get_form(
        _('Add file as recording'),
        '/recording/create',
        _('Add file as recording...'),
        _get_file_data(cluster)
    )


def _get_cluster_data(cluster):
    # See https://musicbrainz.org/doc/Development/Release_Editor_Seeding
    metadata = cluster.metadata
    data = {
        'name': metadata['album'],
        'artist_credit.names.0.artist.name': metadata['albumartist'],
    }

    def mkey(disc, track, name):
        return 'mediums.%i.track.%i.%s' % (disc, track, name)

    disc_counter = 0
    track_counter = 0
    last_discnumber = None
    for f in cluster.files:
        m = f.metadata
        discnumber = extract_discnumber(m)
        if last_discnumber is not None and discnumber != last_discnumber:
            disc_counter += 1
            track_counter = 0
        last_discnumber = discnumber
        data[mkey(disc_counter, track_counter, 'name')] = m['title']
        data[mkey(disc_counter, track_counter, 'number')] = m['tracknumber'] or str(track_counter + 1)
        data[mkey(disc_counter, track_counter, 'length')] = str(m.length)
        track_counter += 1

    return data


def _get_file_data(file):
    metadata = file.metadata
    data = {
        'edit-recording.name': metadata['title'],
        'edit-recording.artist_credit.names.0.artist.name': metadata['artist'],
        'edit-recording.length': format_time(file.metadata.length),
    }
    return data


def _get_form(title, action, label, form_data):
    return _form_template.format(
        title=htmlescape(title),
        submit_label=htmlescape(label),
        action=htmlescape(_mbserver_url(action)),
        form_data=_format_form_data(form_data),
    )


def _format_form_data(data):
    return ''.join((
        _form_input_template.format(name=htmlescape(name), value=htmlescape(value))
        for name, value in data.items()
    ))
