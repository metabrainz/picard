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

"""The commands that identify a disc: ``disc read``, ``disc read-log`` and ``disc read-tags``."""

from collections.abc import (
    Callable,
)
from functools import partial
from typing import Any

from picard.cli.engine.builtins.helpers import (
    TIMEOUT_DEFAULT,
    album_result,
    arg_first,
    drain,
    handles_of,
    join_notes,
    reject_candidates,
)
from picard.cli.engine.builtins.registry import command
from picard.cli.engine.commands import (
    EngineSession,
    UsageError,
)
from picard.cli.engine.result import (
    EngineItemResult,
    EngineResult,
)
import picard.disc
from picard.disc.presentation import disc_presentation
from picard.util import (
    iter_files_from_objects,
)
from picard.util.cdrom import get_configured_lookup_device


def _disc_lookup_and_report(
    session: EngineSession, disc, read: Callable[[], object], read_failure: str
) -> EngineResult:
    """Read a disc, look it up and report the album it matched.

    Shared tail of the disc commands: ``read`` (``disc.read`` or
    ``disc.read_log`` with its arguments bound) runs on a worker thread, as for
    the GUI, then the disc-id lookup is issued; both are drained, with any album
    load the headless auto-load scheduled. A failure to read is reported with
    ``read_failure`` as its message. Otherwise the matched album is reported, or
    ``no_match`` when nothing unambiguous was found. The matched album is read
    from the disc-presentation facade (not by diffing the album registry), so a
    release already loaded in the session is still reported as a match rather
    than a spurious ``no_match``.
    """
    dp = disc_presentation()
    dp.reset_last_loaded()
    errors: list[Exception] = []
    disc.read_and_lookup(read, on_error=errors.append)
    notes: list[str] = []
    drained = drain(session, TIMEOUT_DEFAULT, notes, doing="reading the disc and looking it up")

    if errors:
        return EngineResult.failure(f"{read_failure}: {errors[0]}")
    return _disc_match_result(session, disc, drained, notes)


def _disc_match_result(session: EngineSession, disc, drained: bool, notes: list[str]) -> EngineResult:
    """Report the album a disc lookup matched, or ``no_match`` / ``timeout``."""
    album = disc_presentation().last_loaded_album
    if album is None:
        status = 'no_match' if drained else 'timeout'
        return EngineResult(
            items=[EngineItemResult(handle='', status=status, data={'disc_id': disc.id})],
            message=join_notes(notes),
        )
    return album_result(session, album, 'loaded', notes)


@command(
    'disc read',
    usage='disc read [device]',
    help="Read the CD in a drive and load its release.",
    args=('device',),
    arg_kinds=('device',),
)
def _cmd_disc_read(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Read the CD in a drive, and load the matching release.

    It reads the table of contents of the disc, computes its disc ID and looks it up
    on MusicBrainz. Without a device, the first drive of the cd_lookup_device option
    is used, as in the GUI, else the default drive. When there is a single match it
    is loaded; with several, nothing is, as there is no dialog to choose. It needs
    the python-discid library and a readable drive.

    Example:
      disc read /dev/sr0
    """
    if picard.disc.discid is None:
        return EngineResult.failure("disc read: the python-discid library is not available")

    device = arg_first(args.get('device')) or get_configured_lookup_device()

    disc = picard.disc.Disc()
    where = device or 'the default drive'
    return _disc_lookup_and_report(session, disc, partial(disc.read, device), f"disc read: could not read {where}")


@command(
    'disc read-log',
    usage='disc read-log <path>',
    help="Identify a disc from a CD ripper log.",
    args=('path',),
    arg_kinds=('path',),
)
def _cmd_disc_read_log(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Identify a disc from a CD ripper log, and load the matching release.

    It reads the table of contents from the log of EAC, XLD, Whipper, dBpoweramp or
    cyanrip (or a SCSI TOC), computes the disc ID and looks it up on MusicBrainz.
    When there is a single match it is loaded; with several, nothing is. It needs
    the python-discid library.

    Example:
      disc read-log ~/rips/album.log
    """
    if picard.disc.discid is None:
        return EngineResult.failure("disc read-log: the python-discid library is not available")

    path = arg_first(args.get('path'))
    if not path:
        raise UsageError

    disc = picard.disc.Disc()
    return _disc_lookup_and_report(
        session, disc, partial(disc.read_log, path), f"disc read-log: could not parse {path!r}"
    )


@command(
    'disc read-tags',
    usage='disc read-tags <selector>',
    help="Identify a disc from the tags of its files.",
    args=('selector',),
    arg_kinds=('selector',),
)
def _cmd_disc_read_tags(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Identify a disc from the disc information in the tags of its files.

    It uses the itunes_cddb_1 tag of the selected files (an album, a cluster, ...),
    which must be exactly the files of the disc, one per track. It looks the disc up
    on MusicBrainz as 'Lookup CD from tags' does in the GUI, and when there is a
    single match it loads the release and matches the files to it. No drive and no
    python-discid are needed.

    Example:
      disc read-tags c1
    """
    selector = args.get('selector')
    if not selector:
        raise UsageError
    entities, unresolved = session.resolve(selector)
    rejected = reject_candidates(session, 'disc read-tags', entities, unresolved)
    if rejected is not None:
        return rejected
    files = list(iter_files_from_objects(entities))
    if not files:
        return EngineResult.failure(f"disc read-tags: no file in {selector!r}", unresolved=unresolved)
    try:
        toc_string = picard.disc.toc_string_from_tags(files)
    except picard.disc.DiscTagsError as e:
        return EngineResult.failure(f"disc read-tags: {e}", unresolved=unresolved)

    disc_presentation().reset_last_loaded()
    disc = picard.disc.Disc()
    disc.lookup_by_toc(toc_string, skip_dialog=True, files_to_match=files)
    notes: list[str] = []
    drained = drain(session, TIMEOUT_DEFAULT, notes, doing="looking up the disc id")
    result = _disc_match_result(session, disc, drained, notes)
    result.resolved = handles_of(session, entities)
    result.unresolved = unresolved
    return result
