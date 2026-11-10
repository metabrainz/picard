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

"""What the built-in commands have in common: reading arguments, waiting for
background work, and describing entities in a result."""

from collections.abc import Iterable
from typing import Any

from picard.album import Album
from picard.cli.engine.candidates import Candidate
from picard.cli.engine.commands import EngineSession
from picard.cli.engine.result import (
    EngineItemResult,
    EngineResult,
)
from picard.file import File
from picard.track import Track


# How long, in seconds, a command waits for the background work it started: one
# web request (a release, a lookup), files or a disc, work that needs fingerprints
# or several lookups.
TIMEOUT_SHORT = 60
TIMEOUT_DEFAULT = 120
TIMEOUT_LONG = 300


def drain(session: EngineSession, timeout: float, notes: list[str]) -> bool:
    """Wait for the session's background work; note a timeout for the result.

    Returns True when everything finished. On a timeout the work may still be
    running, so the command's outcome can be incomplete: a message is added to
    ``notes`` (deduplicated) for the command to put in its result.
    """
    drained = bool(session.run_until_idle(timeout=timeout))
    if not drained:
        note = f"timed out after {timeout:g}s waiting for background work; results may be incomplete"
        if note not in notes:
            notes.append(note)
    return drained


def join_notes(notes: list[str]) -> str:
    return '; '.join(notes)


def handles_of(session: EngineSession, entities: Iterable[Any]) -> list[str]:
    """The handles of ``entities``, minting those they do not have yet."""
    return [session.handle_for(entity) for entity in entities]


def entity_item(session: EngineSession, entity: Any, status: str) -> EngineItemResult:
    """A result item for ``entity``: its handle, ``status`` and a description."""
    return EngineItemResult(handle=session.handle_for(entity), status=status, data=describe_entity(entity))


def album_result(session: EngineSession, album: Any, status: str, notes: list[str]) -> EngineResult:
    """The result of a command that brought ``album`` into the working set."""
    item = entity_item(session, album, status)
    return EngineResult(items=[item], mints=[item.handle], message=join_notes(notes))


def arg_words(arg: Any) -> list[str]:
    """The words bound to a command argument, which is None, one word or a list of them."""
    if arg is None:
        return []
    return [arg] if isinstance(arg, str) else list(arg)


def arg_first(arg: Any) -> 'str | None':
    """The first word bound to a command argument, if any."""
    words = arg_words(arg)
    return words[0] if words else None


def arg_joined(arg: Any) -> 'str | None':
    """All the words bound to a command argument as one text (the rest of the line), if any."""
    words = arg_words(arg)
    return ' '.join(words) if words else None


def _entity_mb_ref(entity: Any) -> 'tuple[str, str] | tuple[None, None]':
    """Return the ``(entity_type, mbid)`` an entity points at, or ``(None, None)``.

    Uses MusicBrainz entity-type vocabulary (``release`` for albums,
    ``recording`` for tracks/files) so the reference round-trips with the
    MB web service and the ``album load <type>:<mbid>`` style tools. The MBID
    comes from the entity's own identity (Album.id / Track.id) or, for a
    standalone file, its ``musicbrainz_recordingid`` tag.
    """
    if isinstance(entity, Album):
        return ('release', entity.id) if entity.id else (None, None)
    if isinstance(entity, Track):
        return ('recording', entity.id) if entity.id else (None, None)
    if isinstance(entity, File):
        recording_id = entity.metadata['musicbrainz_recordingid']
        return ('recording', recording_id) if recording_id else (None, None)
    return (None, None)


def describe_entity(entity: Any) -> dict[str, Any]:
    """A small, serializable summary of an entity for ``ls`` / item data.

    Uses the entity's own ``column()`` accessors where available (the same
    source the GUI columns use), falling back to a filename for files. A lookup
    :class:`Candidate` is projected via its own ``describe()`` so ``ls m*``
    shows the same release reference/title/score as the lookup listing.
    """
    if isinstance(entity, Candidate):
        return entity.describe()

    data: dict[str, Any] = {}
    entity_type, mbid = _entity_mb_ref(entity)
    if entity_type and mbid:
        data['entity_type'] = entity_type
        data['mbid'] = mbid
    column = getattr(entity, 'column', None)
    if callable(column):
        # Title/artist are the common human labels for albums/clusters/tracks.
        title = column('title')
        if title:
            data['title'] = title
        artist = column('artist') or column('albumartist')
        if artist:
            data['artist'] = artist
    base_filename = getattr(entity, 'base_filename', None)
    if base_filename:
        data['filename'] = base_filename
    # File count for containers (clusters/albums), if cheaply available.
    files = getattr(entity, 'files', None)
    if files is not None:
        data['file_count'] = len(files)
    return data


def reject_candidates(
    session: EngineSession,
    command: str,
    entities: list,
    unresolved: list[str],
    what: str = "holds no files",
) -> 'EngineResult | None':
    """A failure if ``entities`` include a lookup candidate, which ``what`` it lacks.

    For the commands that act on the files of a selection (``save``, ``move``,
    ``trash``) or on its tags: ``save m1`` is a mistake worth saying so, not an
    error from deep inside the command.
    """
    for entity in entities:
        if isinstance(entity, Candidate):
            return EngineResult.failure(
                f"{command}: {session.handle_for(entity)} is a lookup candidate, it {what}",
                unresolved=unresolved,
            )
    return None
