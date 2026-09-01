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

"""Extension point for local cover art matching modes.

A "matching mode" is a way of selecting which local files are treated as cover
art for an album (for example: matching file names against a regular
expression). The Local Files cover art provider does not hard-code the
available modes; instead each mode is a :class:`LocalCoverArtMode` registered
against :data:`ext_point_local_cover_art_modes`.

Picard core registers the regular-expression mode. Plugins can register further
modes from their ``enable(api)`` function via
``api.register_local_cover_art_mode(...)`` (or this module's
:func:`register_local_cover_art_mode`), supplying their own value storage
(typically backed by the plugin's own config), queue behavior and, optionally,
a live matcher used by the options-page playground and a documentation button.

The options page renders the registered modes in a selector and drives its
single input field, labels, playground and documentation button entirely from
the active mode's descriptor, so a new mode needs no change to the provider or
the options page.
"""

from collections.abc import Callable
from dataclasses import dataclass

from picard.extension_points import ExtensionPoint


# A matcher takes the current field value and returns a predicate that tells the
# playground whether a given file name would match, or ``None`` when the value
# cannot produce a matcher (e.g. it is empty or invalid). Implementations may
# surface validation errors to the user through the ``on_error`` callback.
LineMatcher = Callable[[str], bool]
MatcherFactory = Callable[[str, Callable[[str], None]], LineMatcher | None]

# Queues cover art images for an album. Called as ``queue_images(provider,
# value)`` where ``provider`` is the CoverArtProviderLocal instance and
# ``value`` is the active mode's stored value.
QueueImages = Callable[[object, str], None]


@dataclass(frozen=True)
class LocalCoverArtMode:
    """Describes one way of selecting local cover art files.

    Attributes:
        id: Stable identifier persisted in the ``local_cover_match_mode``
            setting. Must be unique across modes.
        title: Human-readable name shown in the mode selector (mark with N_()).
        description: Label shown above the input field for this mode (N_()).
        note: Explanatory note shown under the field (N_()).
        queue_images: Callable ``(provider, value)`` that queues the cover art
            images for the active album using this mode's stored value.
        get_value: Returns this mode's currently stored value (a string).
        set_value: Persists this mode's value (a string).
        example: Optional example pattern, shown as the field placeholder.
        playground: Whether the options-page playground is shown for this mode.
        make_matcher: Optional factory building the playground predicate from
            the field value; required for the playground to do anything.
        show_doc: Optional callable ``(parent_widget)`` opening documentation;
            when set, a documentation button is shown next to the field.
        doc_tooltip: Optional tooltip for the documentation button (N_()).
    """

    id: str
    title: str
    description: str
    note: str
    queue_images: QueueImages
    get_value: Callable[[], str]
    set_value: Callable[[str], None]
    example: str = ""
    playground: bool = False
    make_matcher: MatcherFactory | None = None
    show_doc: Callable[[object], None] | None = None
    doc_tooltip: str = ""


ext_point_local_cover_art_modes = ExtensionPoint[LocalCoverArtMode](label='local_cover_art_modes')


def register_local_cover_art_mode(mode: LocalCoverArtMode) -> None:
    """Register a local cover art matching mode.

    Args:
        mode: The :class:`LocalCoverArtMode` to register.
    """
    # The extension point gates registrations by the module that registered
    # them (so a mode is only offered while its plugin is enabled). The mode is
    # a dataclass instance defined in this module, so derive the owning module
    # from the plugin-provided queue_images callable instead.
    module = getattr(mode.queue_images, '__module__', __name__)
    ext_point_local_cover_art_modes.register(module, mode)


def local_cover_art_modes() -> list[LocalCoverArtMode]:
    """Return the registered modes (only those from enabled sources)."""
    return list(ext_point_local_cover_art_modes)


def get_local_cover_art_mode(mode_id: str) -> LocalCoverArtMode | None:
    """Return the registered mode with the given id, or None if not found."""
    for mode in ext_point_local_cover_art_modes:
        if mode.id == mode_id:
            return mode
    return None
