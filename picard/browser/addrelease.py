# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021-2022 Laurent Monin
# Copyright (C) 2021-2023 Philipp Wolfer
# Copyright (C) 2022 Bob Swift
# Copyright (C) 2022 jesus2099
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


from html import escape
from secrets import token_bytes

from PyQt5.QtCore import QCoreApplication

from picard import log
from picard.util import format_time
from picard.util.mbserver import build_submission_url
from picard.util.webbrowser2 import open


try:
    import jwt
    import jwt.exceptions
except ImportError:
    log.debug('PyJWT not available, addrelease functionality disabled')
    jwt = None

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


def is_available():
    return jwt is not None


def is_enabled():
    tagger = QCoreApplication.instance()
    return tagger.browser_integration.is_running


def submit_cluster(cluster):
    _open_url_with_token({'cluster': hash(cluster)})


def submit_file(file, as_release=False):
    _open_url_with_token({'file': file.filename, 'as_release': as_release})


def serve_form(token):
    try:
        payload = jwt.decode(token, __key, algorithms=__algorithm)
        log.debug('received JWT token %r', payload)
        tagger = QCoreApplication.instance()
        tport = tagger.browser_integration.port
        if 'cluster' in payload:
            cluster = _find_cluster(tagger, payload['cluster'])
            if not cluster:
                raise NotFoundError('Cluster not found')
            return _get_cluster_form(cluster, tport)
        elif 'file' in payload:
            file = _find_file(tagger, payload['file'])
            if not file:
                raise NotFoundError('File not found')
            if payload.get('as_release', False):
                return _get_file_as_release_form(file, tport)
            else:
                return _get_file_as_recording_form(file, tport)
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
    url = f'http://127.0.0.1:{browser_integration.port}/add?token={token}'
    open(url)


def _find_cluster(tagger, cluster_hash):
    for cluster in tagger.clusters:
        if hash(cluster) == cluster_hash:
            return cluster
    return None


def _find_file(tagger, path):
    return tagger.files.get(path, None)


def _get_cluster_form(cluster, tport):
    return _get_form(
        _('Add cluster as release'),
        '/release/add',
        _('Add cluster as release...'),
        _get_cluster_data(cluster),
        {'tport': tport}
    )


def _get_file_as_release_form(file, tport):
    return _get_form(
        _('Add file as release'),
        '/release/add',
        _('Add file as release...'),
        _get_file_as_release_data(file),
        {'tport': tport}
    )


def _get_file_as_recording_form(file, tport):
    return _get_form(
        _('Add file as recording'),
        '/recording/create',
        _('Add file as recording...'),
        _get_file_as_recording_data(file),
        {'tport': tport}
    )


def _get_cluster_data(cluster):
    # See https://musicbrainz.org/doc/Development/Release_Editor_Seeding
    metadata = cluster.metadata
    data = {
        'name': metadata['album'],
        'artist_credit.names.0.artist.name': metadata['albumartist'],
    }

    _add_track_data(data, cluster.files)
    return data


def _get_file_as_release_data(file):
    # See https://musicbrainz.org/doc/Development/Release_Editor_Seeding
    metadata = file.metadata
    data = {
        'name': metadata['album'] or metadata['title'],
        'artist_credit.names.0.artist.name': metadata['albumartist'] or metadata['artist'],
    }

    _add_track_data(data, [file])
    return data


def _get_file_as_recording_data(file):
    metadata = file.metadata
    data = {
        'edit-recording.name': metadata['title'],
        'edit-recording.artist_credit.names.0.artist.name': metadata['artist'],
        'edit-recording.length': format_time(file.metadata.length),
    }
    return data


def _add_track_data(data, files):
    def mkey(disc, track, name):
        return 'mediums.%i.track.%i.%s' % (disc, track, name)

    labels = set()
    barcode = None

    disc_counter = 0
    track_counter = 0
    last_discnumber = None
    for f in files:
        m = f.metadata
        discnumber = extract_discnumber(m)
        if last_discnumber is not None and discnumber != last_discnumber:
            disc_counter += 1
            track_counter = 0
        last_discnumber = discnumber
        if m['label'] or m['catalognumber']:
            labels.add((m['label'], m['catalognumber']))
        if m['barcode']:
            barcode = m['barcode']
        data[mkey(disc_counter, track_counter, 'name')] = m['title']
        data[mkey(disc_counter, track_counter, 'artist_credit.names.0.name')] = m['artist']
        data[mkey(disc_counter, track_counter, 'number')] = m['tracknumber'] or str(track_counter + 1)
        data[mkey(disc_counter, track_counter, 'length')] = str(m.length)
        if m['musicbrainz_recordingid']:
            data[mkey(disc_counter, track_counter, 'recording')] = m['musicbrainz_recordingid']
        track_counter += 1

    for i, label in enumerate(labels):
        (label, catalog_number) = label
        data['labels.%i.name' % i] = label
        data['labels.%i.catalog_number' % i] = catalog_number

    if barcode:
        data['barcode'] = barcode


def _get_form(title, action, label, form_data, query_args=None):
    return _form_template.format(
        title=escape(title),
        submit_label=escape(label),
        action=escape(build_submission_url(action, query_args)),
        form_data=_format_form_data(form_data),
    )


def _format_form_data(data):
    return ''.join(
        _form_input_template.format(name=escape(name), value=escape(value))
        for name, value in data.items()
    )
