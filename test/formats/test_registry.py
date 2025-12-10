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

import os
from pathlib import Path
import tempfile
from unittest.mock import (
    Mock,
    patch,
)

from picard.file import File
from picard.formats.registry import FormatRegistry


class MockFormat1(File):
    """Mock format for testing."""

    EXTENSIONS = ['.ogg', '.ogv']
    NAME = "Mock Format 1"

    def __init__(self, filename):
        super().__init__(filename)

    def _load(self, filename):
        return None

    def _save(self, filename, metadata):
        pass


class MockFormat2(File):
    """Mock format for testing with overlapping extensions."""

    EXTENSIONS = ['.mba', '.mbv', '.OGG']
    NAME = "Mock Format 2"

    def __init__(self, filename):
        super().__init__(filename)

    def _load(self, filename):
        return None

    def _save(self, filename, metadata):
        pass


class MockFormat3(File):
    """Mock format for testing without NAME attribute."""

    EXTENSIONS = ['.xyz']

    def __init__(self, filename):
        super().__init__(filename)

    def _load(self, filename):
        return None

    def _save(self, filename, metadata):
        pass


class MockMutagenFile:
    """Mock Mutagen file with score method."""

    @staticmethod
    def score(filename, fileobj, header):
        # Simple scoring: return 50 if header starts with 'MOCK'
        if header.startswith(b'MOCK'):
            return 50
        return 0


class MockFormatWithScore(File):
    """Mock format with Mutagen-style scoring."""

    EXTENSIONS = ['.mock']
    NAME = "Mock Format With Score"
    _File = MockMutagenFile

    def __init__(self, filename):
        super().__init__(filename)

    def _load(self, filename):
        return None

    def _save(self, filename, metadata):
        pass


class TestFormatRegistry:
    """Test suite for FormatRegistry."""

    def test_registry_creation(self):
        """Test that a FormatRegistry can be created."""
        registry = FormatRegistry()
        assert isinstance(registry, FormatRegistry)

    def test_register_single_format(self):
        """Test registering a single format."""
        registry = FormatRegistry()
        registry.register(MockFormat1)

        # Check that extensions are registered
        extensions = registry.supported_extensions()
        assert '.ogg' in extensions
        assert '.ogv' in extensions
        assert len(extensions) == 2

    def test_register_multiple_formats(self):
        """Test registering multiple formats."""
        registry = FormatRegistry()
        registry.register(MockFormat1)
        registry.register(MockFormat2)

        # Check that all unique extensions are registered (case-insensitive)
        extensions = set(registry.supported_extensions())
        assert extensions == {'.ogg', '.ogv', '.mba', '.mbv'}

    def test_register_normalizes_case(self):
        """Test that extension registration is case-insensitive."""
        registry = FormatRegistry()
        registry.register(MockFormat2)  # Has '.OGG' in uppercase

        extensions = registry.supported_extensions()
        assert '.ogg' in extensions
        # Should only appear once despite MockFormat2 having '.OGG'
        assert extensions.count('.ogg') == 1

    def test_supported_extensions_empty(self):
        """Test supported_extensions on empty registry."""
        registry = FormatRegistry()
        assert registry.supported_extensions() == []

    def test_iter_formats(self):
        """Test registry can iterate over all registered formats."""
        registry = FormatRegistry()
        registry.register(MockFormat1)
        registry.register(MockFormat2)
        assert list(registry.__iter__()), [MockFormat1, MockFormat2]

    def test_supported_extensions_returns_sorted_list(self):
        """Test that supported_extensions returns a sorted list."""
        registry = FormatRegistry()
        registry.register(MockFormat1)
        registry.register(MockFormat2)

        extensions = registry.supported_extensions()
        assert extensions == sorted(extensions)

    def test_supported_formats_empty(self):
        """Test supported_formats on empty registry."""
        registry = FormatRegistry()
        assert registry.supported_formats() == []

    def test_supported_formats_returns_extensions_and_names(self):
        """Test that supported_formats returns correct data."""
        registry = FormatRegistry()
        registry.register(MockFormat1)
        registry.register(MockFormat2)

        formats = registry.supported_formats()
        assert len(formats) == 2

        # Check structure
        for extensions, name in formats:
            assert isinstance(extensions, list)
            assert isinstance(name, str)

        # Check specific formats
        format_dict = {name: extensions for extensions, name in formats}
        assert "Mock Format 1" in format_dict
        assert "Mock Format 2" in format_dict
        assert format_dict["Mock Format 1"] == ['.ogg', '.ogv']
        assert format_dict["Mock Format 2"] == ['.mba', '.mbv', '.OGG']

    def test_supported_formats_skips_formats_without_name(self):
        """Test that formats without NAME attribute are skipped."""
        registry = FormatRegistry()
        registry.register(MockFormat1)
        registry.register(MockFormat3)  # No NAME attribute

        formats = registry.supported_formats()
        names = [name for _, name in formats]

        assert "Mock Format 1" in names
        assert len(names) == 1

    def test_extension_to_formats_empty_registry(self):
        """Test extension_to_formats on empty registry."""
        registry = FormatRegistry()
        assert registry.extension_to_formats('.ogg') == tuple()
        assert registry.extension_to_formats('.nothing') == tuple()

    def test_extension_to_formats_single_format(self):
        """Test extension_to_formats with single format per extension."""
        registry = FormatRegistry()
        registry.register(MockFormat1)

        formats = registry.extension_to_formats('.ogg')
        assert formats == (MockFormat1,)

        formats = registry.extension_to_formats('.ogv')
        assert formats == (MockFormat1,)

    def test_extension_to_formats_multiple_formats(self):
        """Test extension_to_formats with multiple formats for same extension."""
        registry = FormatRegistry()
        registry.register(MockFormat1)  # Has .ogg
        registry.register(MockFormat2)  # Also has .OGG

        formats = registry.extension_to_formats('.ogg')
        assert set(formats) == {MockFormat1, MockFormat2}

    def test_extension_to_formats_case_insensitive(self):
        """Test that extension_to_formats is case-insensitive."""
        registry = FormatRegistry()
        registry.register(MockFormat1)

        assert registry.extension_to_formats('.ogg') == (MockFormat1,)
        assert registry.extension_to_formats('.OGG') == (MockFormat1,)
        assert registry.extension_to_formats('.OgG') == (MockFormat1,)

    def test_extension_to_formats_with_and_without_dot(self):
        """Test extension_to_formats handles extensions with or without leading dot."""
        registry = FormatRegistry()
        registry.register(MockFormat1)

        assert registry.extension_to_formats('.ogg') == (MockFormat1,)
        assert registry.extension_to_formats('ogg') == (MockFormat1,)

    def test_extension_to_formats_unknown_extension(self):
        """Test extension_to_formats with unknown extension."""
        registry = FormatRegistry()
        registry.register(MockFormat1)

        assert registry.extension_to_formats('.unknown') == tuple()
        assert registry.extension_to_formats('.xyz') == tuple()

    def test_open_with_string_path(self):
        """Test opening a file with string path."""
        registry = FormatRegistry()
        registry.register(MockFormat1)

        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as f:
            temp_file = f.name

        try:
            with patch.object(MockFormat1, '__init__', return_value=None) as mock_init:
                result = registry.open(temp_file)
                assert isinstance(result, MockFormat1)
                mock_init.assert_called_once_with(temp_file)
        finally:
            os.unlink(temp_file)

    def test_open_with_path_object(self):
        """Test opening a file with Path object."""
        registry = FormatRegistry()
        registry.register(MockFormat1)

        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as f:
            temp_file = Path(f.name)

        try:
            with patch.object(MockFormat1, '__init__', return_value=None) as mock_init:
                result = registry.open(temp_file)
                assert isinstance(result, MockFormat1)
                mock_init.assert_called_once_with(str(temp_file))
        finally:
            temp_file.unlink()

    def test_open_tries_all_formats_for_extension(self):
        """Test that open tries all formats registered for an extension."""
        registry = FormatRegistry()
        registry.register(MockFormat1)
        registry.register(MockFormat2)

        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as f:
            temp_file = f.name

        try:
            # Make MockFormat1 fail, MockFormat2 should be tried
            with patch.object(MockFormat1, '__init__', side_effect=Exception("Failed")):
                with patch.object(MockFormat2, '__init__', return_value=None) as mock_init2:
                    result = registry.open(temp_file)
                    assert isinstance(result, MockFormat2)
                    mock_init2.assert_called_once()
        finally:
            os.unlink(temp_file)

    def test_open_returns_none_on_all_failures(self):
        """Test that open returns None if all formats fail."""
        registry = FormatRegistry()
        registry.register(MockFormat1)

        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as f:
            temp_file = f.name

        try:
            with patch.object(MockFormat1, '__init__', side_effect=Exception("Failed")):
                with patch.object(registry, 'guess_format', return_value=None):
                    result = registry.open(temp_file)
                    assert result is None
        finally:
            os.unlink(temp_file)

    def test_open_falls_back_to_guess_format(self):
        """Test that open falls back to guess_format if extension-based opening fails."""
        registry = FormatRegistry()
        registry.register(MockFormat1)

        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as f:
            temp_file = f.name

        try:
            mock_file = Mock()
            with patch.object(MockFormat1, '__init__', side_effect=Exception("Failed")):
                with patch.object(registry, 'guess_format', return_value=mock_file) as mock_guess:
                    result = registry.open(temp_file)
                    assert result == mock_file
                    mock_guess.assert_called_once()
        finally:
            os.unlink(temp_file)

    def test_open_with_no_extension(self):
        """Test opening a file with no extension falls back to guess_format."""
        registry = FormatRegistry()
        registry.register(MockFormat1)

        with tempfile.NamedTemporaryFile(suffix='', delete=False) as f:
            temp_file = f.name

        try:
            mock_file = Mock()
            with patch.object(registry, 'guess_format', return_value=mock_file) as mock_guess:
                result = registry.open(temp_file)
                assert result == mock_file
                mock_guess.assert_called_once()
        finally:
            os.unlink(temp_file)

    def test_guess_format_with_valid_header(self):
        """Test guess_format with a file that has a recognized header."""
        registry = FormatRegistry()
        registry.register(MockFormatWithScore)

        # Create a temp file with MOCK header
        with tempfile.NamedTemporaryFile(suffix='.mock', delete=False) as f:
            f.write(b'MOCK' + b'\x00' * 124)
            temp_file = f.name

        try:
            with patch.object(MockFormatWithScore, '__init__', return_value=None) as mock_init:
                result = registry.guess_format(temp_file)
                assert isinstance(result, MockFormatWithScore)
                mock_init.assert_called_once_with(temp_file)
        finally:
            os.unlink(temp_file)

    def test_guess_format_with_invalid_header(self):
        """Test guess_format with a file that has no recognized header."""
        registry = FormatRegistry()
        registry.register(MockFormatWithScore)

        # Create a temp file without MOCK header
        with tempfile.NamedTemporaryFile(suffix='.mock', delete=False) as f:
            f.write(b'INVALID' + b'\x00' * 121)
            temp_file = f.name

        try:
            result = registry.guess_format(temp_file)
            assert result is None
        finally:
            os.unlink(temp_file)

    def test_guess_format_with_options(self):
        """Test guess_format with specific format options."""
        registry = FormatRegistry()
        registry.register(MockFormat1)

        # Create a temp file with MOCK header
        with tempfile.NamedTemporaryFile(suffix='.mock', delete=False) as f:
            f.write(b'MOCK' + b'\x00' * 124)
            temp_file = f.name

        try:
            # Only try MockFormatWithScore, even if not in registry
            with patch.object(MockFormatWithScore, '__init__', return_value=None) as mock_init:
                result = registry.guess_format(temp_file, options=[MockFormatWithScore])
                assert isinstance(result, MockFormatWithScore)
                mock_init.assert_called_once()
        finally:
            os.unlink(temp_file)

    def test_guess_format_with_nonexistent_file(self):
        """Test guess_format with a file that doesn't exist."""
        registry = FormatRegistry()
        registry.register(MockFormatWithScore)

        result = registry.guess_format('/nonexistent/file.mock')
        assert result is None

    def test_guess_format_selects_highest_score(self):
        """Test that guess_format selects format with highest score."""

        class MockMutagenLowScore:
            @staticmethod
            def score(filename, fileobj, header):
                return 10

        class MockMutagenHighScore:
            @staticmethod
            def score(filename, fileobj, header):
                return 100

        class FormatLowScore(File):
            EXTENSIONS = ['.test']
            NAME = "Low Score"
            _File = MockMutagenLowScore

            def _load(self, filename):
                return None

            def _save(self, filename, metadata):
                pass

        class FormatHighScore(File):
            EXTENSIONS = ['.test']
            NAME = "High Score"
            _File = MockMutagenHighScore

            def _load(self, filename):
                return None

            def _save(self, filename, metadata):
                pass

        registry = FormatRegistry()
        registry.register(FormatLowScore)
        registry.register(FormatHighScore)

        with tempfile.NamedTemporaryFile(suffix='.test', delete=False) as f:
            f.write(b'TEST' + b'\x00' * 124)
            temp_file = f.name

        try:
            with patch.object(FormatHighScore, '__init__', return_value=None) as mock_high:
                with patch.object(FormatLowScore, '__init__', return_value=None) as mock_low:
                    result = registry.guess_format(temp_file)
                    assert isinstance(result, FormatHighScore)
                    # Should call the high score format
                    mock_high.assert_called_once()
                    mock_low.assert_not_called()
        finally:
            os.unlink(temp_file)

    def test_guess_format_skips_formats_without_score(self):
        """Test that guess_format skips formats without _File.score method."""
        registry = FormatRegistry()
        registry.register(MockFormat1)  # No _File attribute
        registry.register(MockFormatWithScore)

        with tempfile.NamedTemporaryFile(suffix='.mock', delete=False) as f:
            f.write(b'MOCK' + b'\x00' * 124)
            temp_file = f.name

        try:
            with patch.object(MockFormatWithScore, '__init__', return_value=None) as mock_init:
                result = registry.guess_format(temp_file)
                assert isinstance(result, MockFormatWithScore)
                # Should only try MockFormatWithScore
                mock_init.assert_called_once()
        finally:
            os.unlink(temp_file)

    def test_rebuild_extension_map_empty_registry(self):
        """Test rebuild_extension_map on empty registry."""
        registry = FormatRegistry()
        registry.rebuild_extension_map()

        assert registry.supported_extensions() == []
        assert registry.extension_to_formats('.ogg') == tuple()

    def test_rebuild_extension_map_with_formats(self):
        """Test rebuild_extension_map rebuilds the extension map correctly."""
        registry = FormatRegistry()
        registry.register(MockFormat1)
        registry.register(MockFormat2)

        # Verify initial state
        initial_extensions = set(registry.supported_extensions())
        assert initial_extensions == {'.ogg', '.ogv', '.mba', '.mbv'}

        # Rebuild the map
        registry.rebuild_extension_map()

        # Verify extensions are still correct after rebuild
        rebuilt_extensions = set(registry.supported_extensions())
        assert rebuilt_extensions == initial_extensions

        # Verify format mappings are still correct
        assert set(registry.extension_to_formats('.ogg')) == {MockFormat1, MockFormat2}
        assert registry.extension_to_formats('.ogv') == (MockFormat1,)
        assert registry.extension_to_formats('.mba') == (MockFormat2,)

    def test_rebuild_extension_map_after_manual_corruption(self):
        """Test rebuild_extension_map can recover from corrupted state."""
        registry = FormatRegistry()
        registry.register(MockFormat1)
        registry.register(MockFormat2)

        # Manually corrupt the extension map
        registry._extension_map['.fake'] = {MockFormat1}
        registry._extension_map['.ogg'].clear()

        # Verify corrupted state
        assert '.fake' in registry.supported_extensions()
        assert registry.extension_to_formats('.ogg') == tuple()

        # Rebuild should fix the corruption
        registry.rebuild_extension_map()

        # Verify map is restored correctly
        assert '.fake' not in registry.supported_extensions()
        assert set(registry.extension_to_formats('.ogg')) == {MockFormat1, MockFormat2}
        assert registry.extension_to_formats('.ogv') == (MockFormat1,)

    def test_rebuild_extension_map_after_format_removal(self):
        """Test rebuild_extension_map after formats are removed from extension point."""
        registry = FormatRegistry()
        registry.register(MockFormat1)
        registry.register(MockFormat2)

        # Verify initial state
        assert '.ogg' in registry.supported_extensions()
        assert '.mba' in registry.supported_extensions()
        assert set(registry.extension_to_formats('.ogg')) == {MockFormat1, MockFormat2}

        # Extension map still has old data
        assert set(registry.extension_to_formats('.ogg')) == {MockFormat1, MockFormat2}
        assert '.mba' in registry.supported_extensions()

        # Mock the extension point to return only MockFormat1 (simulating plugin disable)
        mock_ext_point = Mock()
        mock_ext_point.__iter__ = Mock(return_value=iter([MockFormat1]))
        registry._ext_point_formats = mock_ext_point

        # Rebuild should remove MockFormat2 from extension map
        registry.rebuild_extension_map()

        # Verify MockFormat2 extensions are cleaned up
        assert registry.extension_to_formats('.ogg') == (MockFormat1,)
        assert '.mba' not in registry.supported_extensions()
        assert '.mbv' not in registry.supported_extensions()
        # MockFormat1 extensions should still be present
        assert '.ogg' in registry.supported_extensions()
        assert '.ogv' in registry.supported_extensions()

    def test_rebuild_extension_map_preserves_case_insensitivity(self):
        """Test rebuild_extension_map preserves case-insensitive behavior."""
        registry = FormatRegistry()
        registry.register(MockFormat2)  # Has '.OGG' in uppercase

        # Initial registration normalizes to lowercase
        assert '.ogg' in registry.supported_extensions()

        # Rebuild should preserve lowercase normalization
        registry.rebuild_extension_map()

        assert '.ogg' in registry.supported_extensions()
        # Case-insensitive lookups should still work
        assert registry.extension_to_formats('.OGG') == (MockFormat2,)
        assert registry.extension_to_formats('.ogg') == (MockFormat2,)
        assert registry.extension_to_formats('.OgG') == (MockFormat2,)

    def test_rebuild_extension_map_handles_multiple_formats_per_extension(self):
        """Test rebuild_extension_map correctly handles multiple formats per extension."""
        registry = FormatRegistry()
        registry.register(MockFormat1)  # Has .ogg
        registry.register(MockFormat2)  # Also has .OGG

        # Both formats should be registered for .ogg
        ogg_formats_before = set(registry.extension_to_formats('.ogg'))
        assert ogg_formats_before == {MockFormat1, MockFormat2}

        # Rebuild
        registry.rebuild_extension_map()

        # Should still have both formats
        ogg_formats_after = set(registry.extension_to_formats('.ogg'))
        assert ogg_formats_after == {MockFormat1, MockFormat2}

    def test_rebuild_extension_map_clears_previous_state(self):
        """Test rebuild_extension_map completely clears previous state."""
        registry = FormatRegistry()
        registry.register(MockFormat1)

        # Add fake data to extension map
        registry._extension_map['.fake1'] = {MockFormat1}
        registry._extension_map['.fake2'] = {MockFormat2}

        # Verify fake extensions exist
        assert '.fake1' in registry.supported_extensions()
        assert '.fake2' in registry.supported_extensions()

        # Rebuild should clear everything and rebuild from scratch
        registry.rebuild_extension_map()

        # Fake extensions should be gone
        assert '.fake1' not in registry.supported_extensions()
        assert '.fake2' not in registry.supported_extensions()
        # Real extensions from MockFormat1 should be present
        assert '.ogg' in registry.supported_extensions()
        assert '.ogv' in registry.supported_extensions()

    def test_rebuild_extension_map_idempotent(self):
        """Test rebuild_extension_map can be called multiple times safely."""
        registry = FormatRegistry()
        registry.register(MockFormat1)
        registry.register(MockFormat2)

        # Get initial state
        extensions_initial = set(registry.supported_extensions())
        formats_ogg_initial = set(registry.extension_to_formats('.ogg'))

        # Rebuild multiple times
        registry.rebuild_extension_map()
        extensions_after_1 = set(registry.supported_extensions())
        formats_ogg_after_1 = set(registry.extension_to_formats('.ogg'))

        registry.rebuild_extension_map()
        extensions_after_2 = set(registry.supported_extensions())
        formats_ogg_after_2 = set(registry.extension_to_formats('.ogg'))

        # State should be identical after each rebuild
        assert extensions_initial == extensions_after_1 == extensions_after_2
        assert formats_ogg_initial == formats_ogg_after_1 == formats_ogg_after_2
