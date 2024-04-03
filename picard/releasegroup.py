# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2012-2013 Michael Wiencek
# Copyright (C) 2013, 2018-2020, 2023-2024 Laurent Monin
# Copyright (C) 2014, 2017 Sophist-UK
# Copyright (C) 2017 Wieland Hoffmann
# Copyright (C) 2017-2018 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2019, 2021-2022 Philipp Wolfer
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


from collections import defaultdict
from functools import partial
from itertools import combinations
import traceback

from picard import log
from picard.dataobj import DataObject
from picard.mbjson import (
    countries_from_node,
    label_info_from_node,
    media_formats_from_node,
)
from picard.metadata import Metadata
from picard.util import (
    countries_shortlist,
    uniqify,
)


VERSIONS_MAX_TRACKS = 10


def prepare_releases_for_versions(releases):
    for node in releases:
        labels, catnums = label_info_from_node(node['label-info'])

        countries = countries_from_node(node)
        if countries:
            country_label = countries_shortlist(countries)
        else:
            country_label = node.get('country', '') or '??'

        if len(node['media']) > VERSIONS_MAX_TRACKS:
            tracks = "+".join(str(m['track-count']) for m in node['media'][:VERSIONS_MAX_TRACKS]) + '+…'
        else:
            tracks = "+".join(str(m['track-count']) for m in node['media'])
        formats = []
        for medium in node['media']:
            if 'format' in medium:
                formats.append(medium['format'])
        yield {
            'id':      node['id'],
            'year':    node['date'][:4] if 'date' in node else '????',
            'country': country_label,
            'format':  media_formats_from_node(node['media']),
            'label':  ', '.join(' '.join(x.split(' ')[:2]) for x in set(labels)),
            'catnum': ', '.join(set(catnums)),
            'tracks': tracks,
            'barcode': node.get('barcode', '') or _('[no barcode]'),
            'packaging': node.get('packaging', '') or '??',
            'disambiguation': node.get('disambiguation', ''),
            '_disambiguate_name': list(),
            'totaltracks': sum(m['track-count'] for m in node['media']),
            'countries': countries,
            'formats': formats,
        }


VERSIONS_NAME_KEYS = ('tracks', 'year', 'country', 'format', 'label', 'catnum')
VERSIONS_HEADINGS = {
    'tracks':   N_("Tracks"),
    'year':     N_("Year"),
    'country':  N_("Country"),
    'format':   N_("Format"),
    'label':    N_("Label"),
    'catnum':   N_("Cat No"),
}
# additional keys displayed only for disambiguation
VERSIONS_EXTRA_KEYS = ('packaging', 'barcode', 'disambiguation')


class ReleaseGroup(DataObject):

    def __init__(self, rg_id):
        super().__init__(rg_id)
        self.metadata = Metadata()
        self.loaded = False
        self.versions = []
        self.version_headings = " / ".join(_(VERSIONS_HEADINGS[k]) for k in VERSIONS_NAME_KEYS)
        self.loaded_albums = set()
        self.refcount = 0

    def load_versions(self, callback):
        kwargs = {'release-group': self.id, 'limit': 100}
        self.tagger.mb_api.browse_releases(partial(self._request_finished, callback), **kwargs)

    def _parse_versions(self, document):
        """Parse document and return a list of releases"""
        del self.versions[:]

        try:
            releases = document['releases']
        except (TypeError, KeyError):
            return

        versions = defaultdict(list)

        # Group versions by same display name
        for release in prepare_releases_for_versions(releases):
            name = " / ".join(release[k] for k in VERSIONS_NAME_KEYS)
            if name == release['tracks']:
                name = "%s / %s" % (_('[no release info]'), name)
            versions[name].append(release)

        # de-duplicate names if possible
        for name in versions:
            for a, b in combinations(versions[name], 2):
                for key in VERSIONS_EXTRA_KEYS:
                    (value1, value2) = (a[key], b[key])
                    if value1 != value2:
                        a['_disambiguate_name'].append(value1)
                        b['_disambiguate_name'].append(value2)

        # build the final list of versions, using the disambiguation if needed
        for name in versions:
            for release in versions[name]:
                dis = " / ".join(filter(None, uniqify(release['_disambiguate_name'])))
                disname = name if not dis else name + ' / ' + dis
                version = {
                    'id': release['id'],
                    'name': disname.replace("&", "&&"),
                    'totaltracks': release['totaltracks'],
                    'countries': release['countries'],
                    'formats': release['formats'],
                }
                self.versions.append(version)

    def _request_finished(self, callback, document, http, error):
        try:
            if error:
                log.error("%r", http.errorString())
            else:
                try:
                    self._parse_versions(document)
                except BaseException:
                    error = True
                    log.error(traceback.format_exc())
        finally:
            self.loaded = True
            callback()

    def remove_album(self, album_id):
        self.loaded_albums.discard(album_id)
        self.refcount -= 1
        if self.refcount == 0:
            del self.tagger.release_groups[self.id]
