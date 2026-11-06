# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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

"""Find a MusicBrainz entity reference (a type and an MBID) in a text.

The text can be a bare MBID, ``release:<mbid>``, a MusicBrainz URL or anything
else that contains one. This has no dependency on the GUI, so every frontend
can share it.
"""

import re
from typing import NamedTuple


RE_MB_ENTITY = re.compile(
    r"""
    \b(?P<entity>area|artist|instrument|label|place|recording|release|release-group|series|track|url|work)?
    \W*(?P<id>[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12})
""",
    re.VERBOSE | re.IGNORECASE,
)

RE_MB_CDTOC = re.compile(
    r"""
    \b(?P<entity>cdtoc)
    \W*(?P<id>[a-z0-9-_.]{28})
""",
    re.VERBOSE | re.IGNORECASE,
)


class MBEntityRef(NamedTuple):
    """An entity type (``release``, ``recording``, ``cdtoc``, ...) and its id."""

    entity: str
    id: str


def parse_mb_entity(text: str, default_entity: str | None = None) -> MBEntityRef | None:
    """Return the entity reference found in ``text``, or ``None``.

    When ``text`` holds an MBID without saying what it identifies, it is taken
    to be a ``default_entity``; without one, nothing is returned. The entity is
    lower case, and so is the id except for a ``cdtoc`` one, which is case
    sensitive.
    """
    match = RE_MB_ENTITY.search(text) or RE_MB_CDTOC.search(text)
    if match is None:
        return None
    entity = match.group('entity')
    if entity is None:
        if default_entity is None:
            return None
        entity = default_entity
    else:
        entity = entity.lower()
    id_ = match.group('id')
    if entity != 'cdtoc':
        id_ = id_.lower()
    return MBEntityRef(entity, id_)
