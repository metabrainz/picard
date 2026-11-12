# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2008, 2011-2012 Lukáš Lalinský
# Copyright (C) 2011 Pavan Chander
# Copyright (C) 2013 Calvin Walton
# Copyright (C) 2013, 2018, 2020-2021, 2023-2026 Laurent Monin
# Copyright (C) 2014-2015 Sophist-UK
# Copyright (C) 2015 Ohm Patel
# Copyright (C) 2015-2016 Wieland Hoffmann
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2020, 2022-2023, 2026 Philipp Wolfer
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


from collections.abc import Callable

from picard import (
    log,
    tagger_instance,
)
from picard.browser.mburls import MusicBrainzUrls
from picard.config import get_config
from picard.const import PICARD_URLS
from picard.disc import Disc
from picard.util import (
    webbrowser2,
)
from picard.util.mbentity import (
    RE_MB_CDTOC,
    RE_MB_ENTITY,
    parse_mb_entity,
)

from picard.ui.searchdialog.album import AlbumSearchDialog


class FileLookup:
    # Kept as class attributes for the code that already uses them.
    RE_MB_ENTITY = RE_MB_ENTITY
    RE_MB_CDTOC = RE_MB_CDTOC

    def __init__(self, parent: object, server: str, port: int, local_port: int) -> None:
        self.urls = MusicBrainzUrls(server, port, local_port)
        self.tagger = tagger_instance()

    def _url(self, path: str, params: dict[str, str | int] | None = None) -> str:
        return self.urls.build(path, params)

    def _build_launch(self, path: str, params: dict[str, str | int] | None = None) -> bool:
        if params is None:
            params = {}
        return self.launch(self._url(path, params))

    def launch(self, url: str) -> bool:
        log.debug("webbrowser2: %s", url)
        webbrowser2.open(url)
        return True

    def _lookup(self, type_: str, id_: str) -> bool:
        return self.launch(self.urls.entity(type_, id_))

    def recording_lookup(self, recording_id: str) -> bool:
        return self._lookup('recording', recording_id)

    def album_lookup(self, album_id: str) -> bool:
        return self._lookup('release', album_id)

    def artist_lookup(self, artist_id: str) -> bool:
        return self._lookup('artist', artist_id)

    def track_lookup(self, track_id: str) -> bool:
        return self._lookup('track', track_id)

    def work_lookup(self, work_id: str) -> bool:
        return self._lookup('work', work_id)

    def release_group_lookup(self, release_group_id: str) -> bool:
        return self._lookup('release-group', release_group_id)

    def discid_lookup(self, discid: str) -> bool:
        return self._lookup('cdtoc', discid)

    def discid_submission(self, url: str) -> bool:
        if self.urls.local_port:
            url = "%s&tport=%d" % (url, self.urls.local_port)
        return self.launch(url)

    def acoust_lookup(self, acoust_id: str) -> bool:
        return self.launch(PICARD_URLS['acoustid_track'] + acoust_id)

    def mbid_lookup(
        self,
        string: str,
        type_: str | None = None,
        mbid_matched_callback: Callable[[str, str], object] | None = None,
        browser_fallback: bool = True,
    ) -> bool:
        """Parses string for known entity type and mbid, open browser for it
        If entity type is 'release', it will load corresponding release if
        possible.
        """
        ref = parse_mb_entity(string, default_entity=type_)
        if ref is None:
            return False
        entity, id = ref
        log.debug("Lookup for %s:%s", entity, id)
        if mbid_matched_callback:
            mbid_matched_callback(entity, id)
        if entity == 'release':
            self.tagger.load_album(id)
            return True
        elif entity == 'recording':
            self.tagger.load_nat(id)
            return True
        elif entity == 'release-group':
            AlbumSearchDialog.show_releasegroup_search(id)
            return True
        elif entity == 'cdtoc':
            disc = Disc(id=id)
            disc.lookup()
            return True
        if browser_fallback:
            return self._lookup(entity, id)
        return False

    def tag_lookup(
        self,
        artist: str,
        release: str,
        track: str,
        tracknum: str,
        duration: str,
        filename: str,
    ) -> bool:
        return self.launch(self.urls.tag_lookup(artist, release, track, tracknum, duration, filename))

    def tag_lookup_item(self, item) -> bool:
        """Look for the release or recording the tags of ``item`` (a file, a cluster, ...) describe."""
        return self.launch(self.urls.tag_lookup_item(item))

    def collection_lookup(self, userid: str) -> bool:
        return self.launch(self.urls.collections(userid))

    def search_entity(
        self,
        type_: str,
        query: str,
        adv: bool = False,
        mbid_matched_callback: Callable[[str, str], object] | None = None,
        force_browser: bool = False,
    ) -> bool:
        if not force_browser and self.mbid_lookup(query, type_, mbid_matched_callback=mbid_matched_callback):
            return True
        config = get_config()
        params = {
            'limit': config.setting['query_limit'],
            'type': type_,
            'query': query,
        }
        if adv:
            params['adv'] = 'on'
        return self._build_launch("/search/textsearch", params)
