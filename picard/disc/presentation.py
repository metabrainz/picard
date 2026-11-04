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

"""Frontend-agnostic presentation of CD/disc lookup results.

Looking up a disc on MusicBrainz is core work (read the TOC, query the web
service), but *presenting the matching releases for the user to pick* is a
frontend concern. In the GUI this is the modal ``CDLookupDialog``; historically
the core :class:`picard.disc.Disc` reached straight into
``picard.ui.cdlookup`` and ``picard.ui.util`` from its web-service callbacks,
which does not exist in headless/CLI mode (and made :mod:`picard.disc` import
``picard.ui``).

This module provides a small process-wide facade whose methods the disc
callbacks call unconditionally:

    from picard.disc.presentation import disc_presentation

    disc_presentation().lookup_finished()
    disc_presentation().present_releases(disc, releases, files_to_match)

A GUI frontend installs a sink (showing the dialog / stopping the busy cursor).
With no sink (headless), ``lookup_finished`` is a no-op and ``present_releases``
auto-loads the single match (loading nothing when there is no unambiguous
choice), so a CD/log lookup still resolves without a human picker. Mirrors the
injected-sink pattern of :mod:`picard.notification` and
:mod:`picard.view_presentation`.
"""

from typing import (
    Protocol,
    runtime_checkable,
)

from picard import log


@runtime_checkable
class DiscPresentationSink(Protocol):
    """Interface a frontend provides to present disc lookup results.

    A GUI satisfies this structurally: ``disc_lookup_finished`` ends the
    busy-cursor shown during the lookup, and ``present_disc_releases`` shows the
    release picker (``CDLookupDialog``) and loads the chosen release, matching
    ``files_to_match`` to it when given.
    """

    def disc_lookup_finished(self) -> None: ...

    def present_disc_releases(self, disc, releases, files_to_match=None) -> None: ...


class DiscPresentation:
    """Presents disc lookup results via an installed sink, or headless defaults.

    A single instance is shared process-wide (see :func:`disc_presentation`). A
    GUI frontend installs a sink; in headless mode the sink stays ``None`` and
    the facade falls back to a UI-free default.
    """

    def __init__(self):
        self._sink: DiscPresentationSink | None = None
        # The album auto-loaded by the most recent headless present_releases,
        # or None. Lets a non-interactive caller (the disc commands) learn the
        # matched album even when load_album returned an already-loaded one.
        self.last_loaded_album = None

    def set_sink(self, sink: DiscPresentationSink | None):
        """Install (or clear, with ``None``) the sink to forward to."""
        self._sink = sink

    def reset_last_loaded(self) -> None:
        """Clear :attr:`last_loaded_album` before driving a fresh lookup."""
        self.last_loaded_album = None

    @property
    def has_sink(self) -> bool:
        return self._sink is not None

    def lookup_finished(self) -> None:
        """Signal that a disc lookup web request has completed.

        Forwards to the sink (the GUI ends the busy cursor it started for the
        lookup); a no-op in headless mode.
        """
        if self._sink is not None:
            self._sink.disc_lookup_finished()

    def present_releases(self, disc, releases, files_to_match=None, skip_dialog=False) -> None:
        """Present the matching ``releases`` for the user to choose from.

        With a GUI sink, shows the release picker and loads the chosen release
        (matching ``files_to_match`` to it when given) — unless ``skip_dialog``
        is set and there is exactly one match, in which case that single match
        is auto-loaded without a picker (the lookup-from-tags / non-interactive
        behaviour). Headless, there is never a picker: the single unambiguous
        match is auto-loaded (and files matched to it), or nothing is loaded and
        the outcome is logged when there is no match or the choice is ambiguous.

        Either way, the auto-load carries the disc id and the ISRCs read from
        the disc, so they tag the album and get registered for submission.

        Returns the loaded :class:`~picard.album.Album` when a match was
        auto-loaded headless (so a non-interactive caller knows the outcome even
        if the release was already in the session), or ``None`` when a GUI
        picker was shown or nothing was loaded.
        """
        if self._sink is None or (skip_dialog and len(releases) == 1):
            album = self._auto_load(disc, releases, files_to_match)
            self.last_loaded_album = album
            return album
        self._sink.present_disc_releases(disc, releases, files_to_match=files_to_match)
        return None

    @staticmethod
    def _auto_load(disc, releases, files_to_match):
        """Headless default: load the single match, or log and do nothing.

        Returns the loaded album, or ``None`` when there is no match or the
        choice is ambiguous.
        """
        # Imported here to avoid an import cycle (picard.workspace reaches disc
        # presentation indirectly, and picard.disc imports this module).
        from picard.workspace import workspace

        if not releases:
            log.info("Disc lookup for %s returned no matching releases", disc.id)
            return None
        if len(releases) > 1:
            log.info(
                "Disc lookup for %s returned %d releases; headless mode cannot pick, skipping",
                disc.id,
                len(releases),
            )
            return None
        release_id = releases[0].get('id')
        if not release_id:
            log.warning("Disc lookup match for %s has no release id", disc.id)
            return None
        album = workspace().load_album(release_id, discid=disc.id, disc_isrcs=disc.isrcs)
        if files_to_match:
            workspace().move_files_to_album(files_to_match, album=album)
        return album


_disc_presentation = DiscPresentation()


def disc_presentation() -> DiscPresentation:
    """Return the process-wide :class:`DiscPresentation` facade."""
    return _disc_presentation


def set_disc_presentation_sink(sink: DiscPresentationSink | None) -> None:
    """Install the sink (e.g. the application) disc results are presented through.

    Passing ``None`` clears the sink and reverts to headless (default) behaviour.
    """
    _disc_presentation.set_sink(sink)
