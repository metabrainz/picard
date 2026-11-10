# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2012-2013 Michael Wiencek
# Copyright (C) 2013, 2018-2020, 2023-2026 Laurent Monin
# Copyright (C) 2014, 2017 Sophist-UK
# Copyright (C) 2017 Wieland Hoffmann
# Copyright (C) 2017-2018 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2019, 2021-2022, 2024 Philipp Wolfer
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from collections import defaultdict
from collections.abc import Callable
from functools import partial
from itertools import combinations
import traceback
from typing import (
    TYPE_CHECKING,
    Any,
)

from PyQt6.QtNetwork import QNetworkReply

from picard import log
from picard.config import get_config
from picard.i18n import (
    N_,
    gettext as _,
    pgettext_attributes,
)
from picard.item import MetadataItem
from picard.mbjson import (
    countries_from_node,
    label_info_from_node,
    media_formats_from_node,
)
from picard.services import services
from picard.util import (
    countries_shortlist,
    uniqify,
)
from picard.webservice import PendingRequest
from picard.workspace import workspace


if TYPE_CHECKING:
    # Only for the annotations: picard.album imports this module.
    from picard.album import Album


VERSIONS_MAX_TRACKS = 10
VERSIONS_NAME_KEYS = ('tracks', 'year', 'country', 'format', 'label', 'catnum')
VERSIONS_HEADINGS = {
    'tracks': N_("Tracks"),
    'year': N_("Year"),
    'country': N_("Country"),
    'format': N_("Format"),
    'label': N_("Label"),
    'catnum': N_("Cat No"),
}
# additional keys displayed only for disambiguation
VERSIONS_EXTRA_HEADINGS = {
    'packaging': N_("Packaging"),
    'barcode': N_("Barcode"),
    'disambiguation': N_("Disambiguation"),
}
VERSIONS_EXTRA_KEYS = ('packaging', 'barcode', 'disambiguation')


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
            'id': node['id'],
            'year': node['date'][:4] if 'date' in node else '????',
            'country': country_label,
            'format': media_formats_from_node(node['media']),
            'label': ', '.join(' '.join(x.split(' ')[:2]) for x in set(labels)),
            'catnum': ', '.join(set(catnums)),
            'tracks': tracks,
            'barcode': node.get('barcode', '') or _('[no barcode]'),
            'packaging': pgettext_attributes('release_packaging', node.get('packaging', '') or '??'),
            'disambiguation': node.get('disambiguation', ''),
            '_disambiguate_name': list(),
            'totaltracks': sum(m['track-count'] for m in node['media']),
            'countries': countries,
            'formats': formats,
        }


class ReleaseGroup(MetadataItem):
    def __init__(self, rg_id: str) -> None:
        super().__init__(rg_id)
        self.loaded = False
        self.versions: list[dict] = []
        self.version_headings = " / ".join(_(VERSIONS_HEADINGS[k]) for k in VERSIONS_NAME_KEYS)
        self.loaded_albums: set[str] = set()
        self.refcount = 0
        self.versions_count: int | None = None
        # Why the last request for the versions failed, or None.
        self.load_error: str | None = None

    def load_versions(self, callback: Callable) -> PendingRequest:
        kwargs = {'release-group': self.id, 'limit': 100}
        return services().mb_api.browse_releases(partial(self._request_finished, callback), **kwargs)

    def _parse_versions(self, document: dict) -> None:
        """Parse document and return a list of releases"""
        del self.versions[:]

        try:
            releases = document['releases']
        except (TypeError, KeyError):
            return

        self.versions_count = document.get('release-count', None)

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
                extra = "\n".join(
                    "%s: %s" % (_(VERSIONS_EXTRA_HEADINGS[k]), release[k]) for k in VERSIONS_EXTRA_KEYS if release[k]
                )
                version = {
                    'id': release['id'],
                    'name': disname,
                    'totaltracks': release['totaltracks'],
                    'countries': release['countries'],
                    'formats': release['formats'],
                    'extra': extra,
                }
                # The parts of the name, and of the disambiguation, each on its own.
                for key in VERSIONS_NAME_KEYS + VERSIONS_EXTRA_KEYS:
                    version[key] = release[key]
                self.versions.append(version)

    def _request_finished(
        self,
        callback: Callable,
        document: dict,
        http: QNetworkReply,
        error: QNetworkReply.NetworkError | Exception | None,
    ) -> None:
        self.load_error = None
        try:
            if error:
                self.load_error = http.errorString()
                log.error("%r", self.load_error)
            else:
                try:
                    self._parse_versions(document)
                except BaseException:
                    log.error(traceback.format_exc())
        finally:
            self.loaded = True
            callback()

    def remove_album(self, album_id: str) -> None:
        self.loaded_albums.discard(album_id)
        self.refcount -= 1
        if self.refcount == 0:
            del workspace().release_groups[self.id]


# The group of a version in alternative_versions(): 0 when it is like the album
# (or what is preferred), 1 when it is not, for the track count, the countries
# and the formats, in this order.
VersionGroup = tuple[int, int, int]


def alternative_versions(album: 'Album') -> list[tuple[VersionGroup, dict[str, Any]]]:
    """The versions of the release group of ``album``, in the order to offer them.

    The versions with as many tracks as the album come first, then those of the
    preferred release countries, then those of the preferred release formats
    (``preferred_release_countries`` and ``preferred_release_formats``). The
    versions of a group are ordered by name, then by release ID.

    Returns ``(group, version)`` pairs, ``version`` being an item of
    ``album.release_group.versions``, so that a list can be divided by group,
    and nothing for an album whose release group is not known yet.
    """
    release_group = album.release_group
    if release_group is None:
        return []
    config = get_config()
    album_tracks_count = album.get_num_total_files() or len(album.tracks)
    preferred_countries = set(config.setting['preferred_release_countries'])
    preferred_formats = set(config.setting['preferred_release_formats'])
    ORDER_BEFORE, ORDER_AFTER = 0, 1

    alternatives = []
    for version in release_group.versions:
        trackmatch = countrymatch = formatmatch = ORDER_BEFORE
        if version['totaltracks'] != album_tracks_count:
            trackmatch = ORDER_AFTER
        if preferred_countries:
            countries = set(version['countries'])
            if not countries or not countries.intersection(preferred_countries):
                countrymatch = ORDER_AFTER
        if preferred_formats:
            formats = set(version['formats'])
            if not formats or not formats.intersection(preferred_formats):
                formatmatch = ORDER_AFTER
        alternatives.append(((trackmatch, countrymatch, formatmatch), version))
    alternatives.sort(key=lambda item: (item[0], item[1]['name'], item[1]['id'], item[1]['extra']))
    return alternatives
