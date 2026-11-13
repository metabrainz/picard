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

"""Lookup match candidates.

A :class:`Candidate` wraps one scored release returned by a lookup
(:class:`~picard.matching.SimMatchRelease`). It is a session-side object — NOT
a Workspace entity — minted an ``m`` handle by the HandleRegistry (the session
classifier maps ``Candidate`` -> ``'m'``), so a user/agent can refer to a
non-winning alternative and apply it with ``match``.

Candidates are TRANSIENT: a new lookup of a target replaces its candidates, and
once the session drops the old ones their weak handles expire. The session
holds the current candidates (keyed by target) with strong refs; see
``LocalEngineSession``.

``describe()`` projects a candidate to a small, JSON-serializable dict read
directly from the MB release search node (the fields the GUI search dialog
shows), for an EngineResult item. It deliberately avoids the full
``release_to_metadata`` mapping, which drags in config-dependent artist
standardization/translation unneeded for a display projection.
"""

from typing import Any


def _artist_name(release: dict) -> 'str | None':
    """Best-effort artist label from a release search node (no standardization)."""
    credits = release.get('artist-credit')
    if not credits:
        return None
    parts = []
    for credit in credits:
        name = credit.get('name') or credit.get('artist', {}).get('name')
        if name:
            parts.append(name)
        join = credit.get('joinphrase')
        if join:
            parts.append(join)
    return ''.join(parts) or None


class Candidate:
    """One scored release candidate from a lookup.

    ``match`` holds the :class:`~picard.matching.SimMatchRelease` (its
    ``release`` is the raw MB release search node; ``similarity`` the final
    score). ``applied`` is True for the candidate auto-applied by the lookup.

    A candidate is always a release (cluster lookup searches releases), which
    is the entity type of the reference ``release:<mbid>`` it is shown with.
    """

    ENTITY_TYPE = 'release'

    __slots__ = ('match', 'applied', '__weakref__')

    def __init__(self, match: Any, applied: bool = False):
        self.match = match
        self.applied = applied

    @property
    def release_id(self) -> 'str | None':
        release = self.match.release
        return release.get('id') if release else None

    @property
    def similarity(self) -> float:
        return self.match.similarity

    def describe(self) -> dict[str, Any]:
        """A small, serializable projection of the candidate release.

        Reads display fields straight from the MB release search node (as the
        GUI search dialog does), so it needs no config and tolerates the
        no-match sentinel (release None).
        """
        release = self.match.release or {}
        rg = release.get('release-group') or {}
        data: dict[str, Any] = {
            'entity_type': self.ENTITY_TYPE,
            'mbid': release.get('id'),
            'title': release.get('title'),
            'artist': _artist_name(release),
            'date': release.get('date'),
            'country': release.get('country'),
            'type': rg.get('primary-type'),
            'tracks': release.get('track-count'),
            'score': release.get('score'),
            'similarity': round(self.similarity, 4),
            'applied': self.applied,
        }
        # Drop empty values for a tidy result.
        return {k: v for k, v in data.items() if v not in ('', None)}
