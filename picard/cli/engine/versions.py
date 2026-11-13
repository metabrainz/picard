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

"""Release versions.

A :class:`Version` wraps one release of the release group of an album, as
:func:`picard.releasegroup.alternative_versions` offers it (the "Other versions"
of the GUI). Like a :class:`~picard.cli.engine.candidates.Candidate` it is a
session-side object, not a Workspace entity, minted a ``v`` handle by the
HandleRegistry, so that ``album switch`` can name it.

Versions are TRANSIENT: ``album versions`` replaces the versions held for an
album, and the old ``v`` handles expire. The session holds the current ones
(keyed by album) with strong refs; see ``LocalEngineSession``.
"""

from typing import Any

from picard.releasegroup import ReleaseVersion


# The fields of a version that are shown as they are, if they are not empty.
_DESCRIBED_FIELDS = (
    'tracks',
    'year',
    'country',
    'format',
    'label',
    'catnum',
    'packaging',
    'barcode',
    'disambiguation',
)


class Version:
    """One release of the release group of an album.

    ``version`` is the item of ``ReleaseGroup.versions``, ``group`` how it ranks
    (see ``alternative_versions``: 0 for each of the track count, the countries
    and the formats that are like the album's or preferred, 1 otherwise) and
    ``current`` whether it is the release the album is now.
    """

    ENTITY_TYPE = 'release'

    __slots__ = ('version', 'group', 'current', '__weakref__')

    def __init__(self, version: ReleaseVersion, group: tuple[int, int, int], current: bool = False):
        self.version = version
        self.group = group
        self.current = current

    @property
    def release_id(self) -> str:
        return self.version['id']

    @property
    def preferred(self) -> bool:
        """True if it has as many tracks as the album and is of a preferred country and format."""
        return not any(self.group)

    def describe(self) -> dict[str, Any]:
        """A small, serializable projection of the version."""
        data: dict[str, Any] = {
            'entity_type': self.ENTITY_TYPE,
            'mbid': self.release_id,
            'title': self.version['name'],
        }
        for field in _DESCRIBED_FIELDS:
            data[field] = self.version.get(field)
        data['preferred'] = self.preferred
        data['current'] = self.current
        # Drop empty values for a tidy result.
        return {k: v for k, v in data.items() if v not in ('', None)}
