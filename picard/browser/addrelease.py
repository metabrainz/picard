# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021-2023, 2025 Philipp Wolfer
# Copyright (C) 2021-2024 Laurent Monin
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

from dataclasses import dataclass
from html import escape
from operator import attrgetter
import re
from secrets import token_bytes

from PyQt6.QtCore import QCoreApplication

from picard import log
from picard.const import BROWSER_INTEGRATION_LOCALHOST
from picard.i18n import gettext as _
from picard.util import format_time
from picard.util.mbserver import build_submission_url
from picard.util.webbrowser2 import open


try:
    import jwt  # type: ignore[unresolved-import]
    import jwt.exceptions  # type: ignore[unresolved-import]
except ImportError:
    log.debug("PyJWT not available, addrelease functionality disabled")
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
        log.debug("received JWT token %r", payload)
        tagger = QCoreApplication.instance()
        tport = tagger.browser_integration.port
        if 'cluster' in payload:
            cluster = _find_cluster(tagger, payload['cluster'])
            if not cluster:
                raise NotFoundError("Cluster not found")
            return _get_cluster_form(cluster, tport)
        elif 'file' in payload:
            file = _find_file(tagger, payload['file'])
            if not file:
                raise NotFoundError("File not found")
            if payload.get('as_release', False):
                return _get_file_as_release_form(file, tport)
            else:
                return _get_file_as_recording_form(file, tport)
        else:
            raise InvalidTokenError
    except jwt.exceptions.InvalidTokenError as e:
        raise InvalidTokenError from e


def _generate_token(payload):
    token = jwt.encode(payload, __key, algorithm=__algorithm)
    if isinstance(token, bytes):  # For compatibility with PyJWT 1.x
        token = token.decode()
    return token


def _open_url_with_token(payload):
    token = _generate_token(payload)
    browser_integration = QCoreApplication.instance().browser_integration
    url = f'http://{BROWSER_INTEGRATION_LOCALHOST}:{browser_integration.port}/add?token={token}'
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
        _("Add cluster as release"),
        '/release/add',
        _("Add cluster as release…"),
        _get_cluster_data(cluster),
        {'tport': tport},
    )


def _get_file_as_release_form(file, tport):
    return _get_form(
        _("Add file as release"),
        '/release/add',
        _("Add file as release…"),
        _get_file_as_release_data(file),
        {'tport': tport},
    )


def _get_file_as_recording_form(file, tport):
    return _get_form(
        _("Add file as recording"),
        '/recording/create',
        _("Add file as recording…"),
        _get_file_as_recording_data(file),
        {'tport': tport},
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
    release_dates = set()
    barcode = None

    disc_counter = 0
    track_counter = 0
    last_discnumber = None
    for f in sorted(files, key=attrgetter('discnumber', 'tracknumber')):
        m = f.metadata
        discnumber = f.discnumber
        if last_discnumber is not None and discnumber != last_discnumber:
            disc_counter += 1
            track_counter = 0
        last_discnumber = discnumber
        if m['label'] or m['catalognumber']:
            labels.add((m['label'], m['catalognumber']))
        if m['barcode']:
            barcode = m['barcode']
        if m['discsubtitle'] and not data.get(f'mediums.{disc_counter}.name'):
            data[f'mediums.{disc_counter}.name'] = m['discsubtitle']
        if m['media'] and not data.get(f'mediums.{disc_counter}.format'):
            data[f'mediums.{disc_counter}.format'] = m['media']
        if date := PartialDate.parse(m['releasedate']):
            release_dates.add((date, m['releasecountry']))
        elif date := PartialDate.parse(m['date']):
            release_dates.add((date, m['releasecountry']))
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

    # Only use the date if it is not ambiguous
    if len(release_dates) == 1:
        date, country = release_dates.pop()
        if date.year:
            data['events.0.date.year'] = str(date.year)
            if date.month:
                data['events.0.date.month'] = str(date.month)
                if date.day:
                    data['events.0.date.day'] = str(date.day)
        if country:
            data['events.0.country'] = country


def _get_form(title, action, label, form_data, query_args=None):
    return _form_template.format(
        title=escape(title),
        submit_label=escape(label),
        action=escape(build_submission_url(action, query_args)),
        form_data=_format_form_data(form_data),
    )


def _format_form_data(data):
    return ''.join(_form_input_template.format(name=escape(name), value=escape(value)) for name, value in data.items())


@dataclass(frozen=True)
class PartialDate:
    year: int | None
    month: int | None
    day: int | None

    _re_partial_date = re.compile(r'(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?')

    @classmethod
    def parse(cls, date) -> 'PartialDate | None':
        """Parses a partial date in the form YYYY-mm-dd, where both mm and dd are optional.

        E.g. 2026-01-05, 2026-01 and 2026 are all valid partial dates.

        Returns a PartialDate or None, if the input has an invalid format.
        """
        if match := cls._re_partial_date.match(date):
            parts = map(lambda n: int(n) if n else None, match.groups())
            return cls(*parts)
        else:
            return None
