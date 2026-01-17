# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
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

from collections import defaultdict
from collections.abc import Generator
from pathlib import Path

from PyQt6.QtCore import (
    QObject,
    pyqtSignal,
)

from picard import log
from picard.extension_points import ExtensionPoint
from picard.file import File


class FormatRegistry(QObject):
    """Registry for file formats."""

    formats_changed = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._ext_point_formats = ExtensionPoint(label='formats')
        self._extension_map: dict[str, set[type[File]]] = defaultdict(set)

    def register(self, format: type[File]) -> None:
        """Registers a file format.

        Args:
            format: The File subclass to register
        """
        # Register with the extension point
        self._ext_point_formats.register(format.__module__, format)

        # Track extensions for quick lookup
        for ext in format.EXTENSIONS:
            self._extension_map[ext.lower()].add(format)

        self.formats_changed.emit()

    def __iter__(self) -> Generator[File, None, None]:
        yield from self._ext_point_formats

    def supported_formats(self) -> list[tuple[list[str], str]]:
        """Returns list of supported formats.

        Returns:
            List of (extensions, name) tuples for each registered format
        """
        formats = []
        for file_format in self._ext_point_formats:
            if hasattr(file_format, 'EXTENSIONS') and hasattr(file_format, 'NAME'):
                name = getattr(file_format, 'NAME', None)
                if name is not None:
                    formats.append((file_format.EXTENSIONS, name))
        return formats

    def supported_extensions(self) -> list[str]:
        """Returns list of supported extensions.

        Returns:
            Sorted list of all registered file extensions (lowercase)
        """
        return sorted(self._extension_map.keys())

    def extension_to_formats(self, ext: str) -> tuple[type[File], ...]:
        """Returns set of formats for given extension.

        Multiple formats might be registered for the same extension. In this case
        the order of formats returned is not defined and is no indicator for how
        well the format matches. Use guess_format() with the "options" parameter
        to get an instance of File for the best matching format.

        Args:
            ext: File extension (with or without leading dot)

        Returns:
            Set of File subclasses that support this extension
        """
        # Normalize extension to lowercase with no leading dot
        normalized_ext = ext.lower()
        if not normalized_ext.startswith('.'):
            normalized_ext = '.' + normalized_ext
        return tuple(self._extension_map[normalized_ext])

    def open(self, filename: str | Path) -> File | None:
        """Opens a file using the appropriate format.

        Attempts to open the file using formats registered for its extension.
        If multiple formats support the extension, tries each until one succeeds.

        Args:
            filename: Path to the file to open

        Returns:
            File instance if successful, None otherwise
        """
        path = Path(filename) if isinstance(filename, str) else filename

        # Try extension-based opening first
        if path.suffix:
            formats = self.extension_to_formats(path.suffix)
            for file_format in formats:
                try:
                    return file_format(str(path))
                except Exception as e:
                    log.debug("Failed to open %r as %s: %s", str(path), file_format.__name__, e)

        # If extension-based opening failed, try format guessing
        return self.guess_format(path)

    def guess_format(self, filename: str | Path, options: list[type[File]] | None = None) -> File | None:
        """Guesses the format of a file by reading its header.

        This method reads the first 128 bytes of the file and uses each format's
        score() method to determine the best match.

        Args:
            filename: Path to the file to identify
            options: Optional list of format classes to try. If None, all registered formats are tried.

        Returns:
            File instance if a format with positive score is found, None otherwise
        """
        path = Path(filename) if isinstance(filename, str) else filename

        if options is None:
            options = list(self._ext_point_formats)

        try:
            # Read file header for format detection
            # Use unbuffered mode since we only read 128 bytes
            with open(path, 'rb', 0) as fileobj:
                header = fileobj.read(128)

                # Score each format
                results = []
                for file_format in options:
                    try:
                        score = file_format.score(str(path), fileobj, header)
                        results.append((score, file_format.__name__, file_format))
                    except Exception as e:
                        log.debug("Failed to score %r with %s: %s", str(path), file_format.__name__, e)

                if results:
                    # Sort by score and return format with highest positive score
                    results.sort()
                    best_score, best_name, best_format = results[-1]
                    if best_score > 0:
                        log.debug("Guessed format for %r: %s (score: %d)", str(path), best_name, best_score)
                        return best_format(str(path))
                    else:
                        log.debug("No format scored positively for %r", str(path))
        except OSError as e:
            log.error("Error reading file %r for format detection: %s", str(path), e)

        return None

    def rebuild_extension_map(self):
        """Rebuild the extension map.

        This is especially needed after a plugin got disabled, which can result in
        formats being no longer available.
        """
        self._extension_map = defaultdict(set)
        for format in self._ext_point_formats:
            for ext in format.EXTENSIONS:
                self._extension_map[ext.lower()].add(format)

        self.formats_changed.emit()
