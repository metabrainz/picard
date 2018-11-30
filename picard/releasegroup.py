# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2012 Michael Wiencek
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
    country_list_from_node,
    label_info_from_node,
    media_formats_from_node,
)
from picard.metadata import Metadata
from picard.util import uniqify


class ReleaseGroup(DataObject):

    def __init__(self, rg_id):
        super().__init__(rg_id)
        self.metadata = Metadata()
        self.loaded = False
        self.versions = []
        self.version_headings = ''
        self.loaded_albums = set()
        self.refcount = 0

    def load_versions(self, callback):
        kwargs = {"release-group": self.id, "limit": 100}
        self.tagger.mb_api.browse_releases(partial(self._request_finished, callback), **kwargs)

    def _parse_versions(self, document):
        """Parse document and return a list of releases"""
        del self.versions[:]
        data = []

        namekeys = ("tracks", "year", "country", "format", "label", "catnum")
        headings = {
            "tracks":   N_('Tracks'),
            "year":     N_('Year'),
            "country":  N_('Country'),
            "format":   N_('Format'),
            "label":    N_('Label'),
            "catnum":   N_('Cat No'),
        }
        extrakeys = ("packaging", "barcode", "disambiguation")

        try:
            releases = document['releases']
        except (TypeError, KeyError):
            releases = []

        for node in releases:
            labels, catnums = label_info_from_node(node['label-info'])

            countries = country_list_from_node(node)

            formats = []
            for medium in node['media']:
                if "format" in medium:
                    formats.append(medium['format'])
            release = {
                "id":      node['id'],
                "year":    node['date'][:4] if "date" in node else "????",
                "country": "+".join(countries) if countries
                    else node.get('country', '') or "??",
                "format":  media_formats_from_node(node['media']),
                "label":  ", ".join([' '.join(x.split(' ')[:2]) for x in set(labels)]),
                "catnum": ", ".join(set(catnums)),
                "tracks":  "+".join([str(m['track-count']) for m in node['media']]),
                "barcode": node.get('barcode', '') or _('[no barcode]'),
                "packaging": node.get('packaging', '') or '??',
                "disambiguation": node.get('disambiguation', ''),
                "_disambiguate_name": list(),
                "totaltracks": sum([m['track-count'] for m in node['media']]),
                "countries": countries,
                "formats": formats,
            }
            data.append(release)

        versions = defaultdict(list)
        for release in data:
            name = " / ".join([release[k] for k in namekeys]).replace("&", "&&")
            if name == release["tracks"]:
                name = "%s / %s" % (_('[no release info]'), name)
            versions[name].append(release)

        # de-duplicate names if possible
        for name, releases in versions.items():
            for a, b in combinations(releases, 2):
                for key in extrakeys:
                    (value1, value2) = (a[key], b[key])
                    if value1 != value2:
                        a['_disambiguate_name'].append(value1)
                        b['_disambiguate_name'].append(value2)
        for name, releases in versions.items():
            for release in releases:
                dis = " / ".join(filter(None, uniqify(release['_disambiguate_name']))).replace("&", "&&")
                disname = name if not dis else name + ' / ' + dis
                version = {
                    'id': release['id'],
                    'name': disname,
                    'totaltracks': release['totaltracks'],
                    'countries': release['countries'],
                    'formats': release['formats'],
                }
                self.versions.append(version)
        self.version_headings = " / ".join(_(headings[k]) for k in namekeys)

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
