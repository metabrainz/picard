# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Khoa Nguyen
# Copyright (C) 2025 The MusicBrainz Team
# Copyright (C) 2025-2026 Philipp Wolfer
# Copyright (C) 2026 Bryan Roessler
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


"""Lightweight Qt-free fakes shared by the CoverArtBox info tests.

These avoid instantiating real Qt widgets (and QPixmap) so the cover-art
display logic can be exercised deterministically and thread-safely. The thumb
and CoverArtBoxLite fakes differ between the two test modules that use them, so
only the pieces that are genuinely identical live here.
"""

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass
class DummyImage:
    types_text: str
    datalength: int
    width: int | None = None
    height: int | None = None
    mimetype: str | None = None

    def types_as_string(self) -> str:
        return self.types_text


class DummyLabel:
    def __init__(self) -> None:
        self._text: str = ""
        self._visible: bool = True

    def setText(self, text: str) -> None:  # noqa: N802
        self._text = text

    def text(self) -> str:
        return self._text

    def setVisible(self, visible: bool) -> None:  # noqa: N802
        self._visible = visible

    def isVisible(self) -> bool:  # noqa: N802
        return self._visible


class DummyButton:
    def __init__(self) -> None:
        self._visible: bool = False

    def setVisible(self, visible: bool) -> None:  # noqa: N802
        self._visible = visible

    def isVisible(self) -> bool:  # noqa: N802
        return self._visible


def lines_to_text(lines: Iterable[str]) -> str:
    return "\n".join(lines)
