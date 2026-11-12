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

"""The addresses of the pages of the MusicBrainz website, of the configured server.

This is only about the addresses, with no dependency on the GUI, so that they
can be built without it: :class:`picard.browser.filelookup.FileLookup` opens
them in a web browser, and a frontend without a GUI can print them.
"""

import os.path
from typing import Any

from picard.config import get_config
from picard.util.qt import build_qurl


class MusicBrainzUrls:
    """Builds the addresses of pages of the MusicBrainz website."""

    def __init__(self, server: str, port: int, local_port: int = 0) -> None:
        self.server = server
        self.port = port
        # The port of the browser integration of Picard, if there is one: the
        # website uses it to send what the user chooses back to Picard.
        self.local_port = int(local_port)

    @classmethod
    def from_config(cls, local_port: int = 0) -> 'MusicBrainzUrls':
        """The addresses of the server of the configuration."""
        config = get_config()
        return cls(config.setting['server_host'], config.setting['server_port'], local_port)

    def build(self, path: str, params: dict[str, Any] | None = None) -> str:
        """The address of ``path`` on the server, with the query ``params``."""
        params = dict(params or {})
        if self.local_port:
            params['tport'] = self.local_port
        url = build_qurl(self.server, self.port, path=path, queryargs=params)
        return url.toEncoded().data().decode()

    def entity(self, type_: str, id_: str) -> str:
        """The page of an entity: ``release``, ``recording``, ``collection``, ..."""
        return self.build("/%s/%s" % (type_, id_))

    def collections(self, userid: str) -> str:
        """The page of the collections of a user."""
        return self.build("/user/%s/collections" % userid)

    def tag_lookup(
        self,
        artist: str,
        release: str,
        track: str,
        tracknum: str,
        duration: str,
        filename: str,
    ) -> str:
        """The page that looks for the release or recording these tags describe."""
        params = {
            'artist': artist,
            'release': release,
            'track': track,
            'tracknum': tracknum,
            'duration': duration,
            'filename': os.path.basename(filename),
        }
        return self.build("/taglookup", params)

    def tag_lookup_item(self, item: Any) -> str:
        """The tag lookup page for the tags of ``item``: a file, a cluster, ..."""
        metadata = item.metadata
        return self.tag_lookup(
            metadata['albumartist'] if item.is_album_like else metadata['artist'],
            metadata['album'],
            metadata['title'],
            metadata['tracknumber'],
            '' if item.is_album_like else str(metadata.length),
            getattr(item, 'filename', ''),
        )
