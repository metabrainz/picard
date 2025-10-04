# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

"""Unit tests for UserScriptScanner.

Tests the UserScriptScanner class that scans all user tagging scripts
for variable definitions to enhance autocompletion.
"""

from unittest.mock import Mock, patch

from picard.script import TaggingScriptSetting

import pytest

from picard.ui.widgets.user_script_scanner import UserScriptScanner
from picard.ui.widgets.variable_extractor import VariableExtractor


@pytest.fixture
def mock_variable_extractor():
    """Create a mock variable extractor."""
    return Mock(spec=VariableExtractor)


@pytest.fixture
def user_script_scanner(mock_variable_extractor):
    """Create a UserScriptScanner instance for testing."""
    return UserScriptScanner(mock_variable_extractor)


@pytest.fixture
def sample_scripts():
    """Sample user scripts for testing."""
    return [
        TaggingScriptSetting(name="Script 1", enabled=True, content="$set(artist_name, %artist%)"),
        TaggingScriptSetting(name="Script 2", enabled=True, content="$set(album_title, %album%)"),
        TaggingScriptSetting(name="Script 3", enabled=False, content="$set(disabled_var, %title%)"),
        TaggingScriptSetting(name="Script 4", enabled=True, content=""),
    ]


class TestUserScriptScannerInitialization:
    """Test UserScriptScanner initialization."""

    def test_initialization_with_extractor(self, mock_variable_extractor):
        """Test initialization with variable extractor."""
        scanner = UserScriptScanner(mock_variable_extractor)
        assert scanner._variable_extractor is mock_variable_extractor
        assert scanner._cached_variables == set()
        assert scanner._last_scan_hash is None

    def test_initialization_creates_empty_cache(self, mock_variable_extractor):
        """Test that initialization creates empty cache."""
        scanner = UserScriptScanner(mock_variable_extractor)
        assert scanner._cached_variables == set()
        assert scanner._last_scan_hash is None


class TestUserScriptScannerScanning:
    """Test user script scanning functionality."""

    def test_scan_all_user_scripts_with_enabled_scripts(self, user_script_scanner, sample_scripts):
        """Test scanning all enabled user scripts."""
        user_script_scanner._variable_extractor.extract_variables.side_effect = [
            {"artist_name"},  # Script 1
            {"album_title"},  # Script 2
            # Script 3 is disabled, so not scanned
            # Script 4 is empty, so not scanned
        ]

        with patch('picard.ui.widgets.user_script_scanner.iter_active_tagging_scripts') as mock_iter:
            mock_iter.return_value = [s for s in sample_scripts if s.enabled and s.content]

            result = user_script_scanner.scan_all_user_scripts()

            assert result == {"artist_name", "album_title"}
            assert user_script_scanner._cached_variables == {"artist_name", "album_title"}

    def test_scan_all_user_scripts_with_empty_scripts(self, user_script_scanner):
        """Test scanning when no scripts are available."""
        with patch('picard.ui.widgets.user_script_scanner.iter_active_tagging_scripts') as mock_iter:
            mock_iter.return_value = []

            result = user_script_scanner.scan_all_user_scripts()

            assert result == set()
            assert user_script_scanner._cached_variables == set()

    def test_scan_all_user_scripts_with_exception(self, user_script_scanner):
        """Test scanning when an exception occurs."""
        with patch('picard.ui.widgets.user_script_scanner.iter_active_tagging_scripts') as mock_iter:
            mock_iter.side_effect = AttributeError("Script access error")

            result = user_script_scanner.scan_all_user_scripts()

            # Should return empty set and not raise exception
            assert result == set()
            assert user_script_scanner._cached_variables == set()

    def test_scan_all_user_scripts_extractor_exception(self, user_script_scanner, sample_scripts):
        """Test scanning when variable extractor raises exception."""
        user_script_scanner._variable_extractor.extract_variables.side_effect = TypeError("Extraction error")

        with patch('picard.ui.widgets.user_script_scanner.iter_active_tagging_scripts') as mock_iter:
            mock_iter.return_value = [s for s in sample_scripts if s.enabled and s.content]

            result = user_script_scanner.scan_all_user_scripts()

            # Should return empty set and not raise exception
            assert result == set()
            assert user_script_scanner._cached_variables == set()


class TestUserScriptScannerCaching:
    """Test user script scanner caching functionality."""

    def test_get_cached_variables_returns_copy(self, user_script_scanner):
        """Test that get_cached_variables returns a copy."""
        user_script_scanner._cached_variables = {"var1", "var2"}

        cached = user_script_scanner.get_cached_variables()

        assert cached == {"var1", "var2"}
        assert cached is not user_script_scanner._cached_variables  # Should be a copy

    def test_get_cached_variables_empty(self, user_script_scanner):
        """Test get_cached_variables when cache is empty."""
        user_script_scanner._cached_variables = set()

        cached = user_script_scanner.get_cached_variables()

        assert cached == set()

    def test_force_rescan_clears_hash(self, user_script_scanner, sample_scripts):
        """Test that force_rescan clears the hash and rescans."""
        user_script_scanner._last_scan_hash = 12345
        user_script_scanner._cached_variables = {"old_var"}

        user_script_scanner._variable_extractor.extract_variables.return_value = {"new_var"}

        with patch('picard.ui.widgets.user_script_scanner.iter_active_tagging_scripts') as mock_iter:
            mock_iter.return_value = [s for s in sample_scripts if s.enabled and s.content]

            result = user_script_scanner.force_rescan()

            assert result == {"new_var"}
            assert user_script_scanner._cached_variables == {"new_var"}


class TestUserScriptScannerChangeDetection:
    """Test user script change detection."""

    def test_should_rescan_when_no_previous_scan(self, user_script_scanner):
        """Test should_rescan when no previous scan has been done."""
        with patch('picard.ui.widgets.user_script_scanner.iter_active_tagging_scripts') as mock_iter:
            mock_iter.return_value = [TaggingScriptSetting(name="test", enabled=True, content="$set(var, value)")]

            result = user_script_scanner.should_rescan()

            assert result is True

    def test_should_rescan_when_scripts_unchanged(self, user_script_scanner):
        """Test should_rescan when scripts haven't changed."""
        script = TaggingScriptSetting(name="test", enabled=True, content="$set(var, value)")
        # Calculate the hash the same way the scanner does
        expected_hash = hash(tuple((s.name, s.content) for s in [script]))
        user_script_scanner._last_scan_hash = expected_hash

        with patch('picard.ui.widgets.user_script_scanner.iter_active_tagging_scripts') as mock_iter:
            mock_iter.return_value = [script]

            result = user_script_scanner.should_rescan()

            assert result is False

    def test_should_rescan_when_scripts_changed(self, user_script_scanner):
        """Test should_rescan when scripts have changed."""
        script = TaggingScriptSetting(name="test", enabled=True, content="$set(var, new_value)")
        # Set hash for old content
        old_script = TaggingScriptSetting(name="test", enabled=True, content="$set(var, old_value)")
        user_script_scanner._last_scan_hash = hash(tuple((s.name, s.content) for s in [old_script]))

        with patch('picard.ui.widgets.user_script_scanner.iter_active_tagging_scripts') as mock_iter:
            mock_iter.return_value = [script]

            result = user_script_scanner.should_rescan()

            assert result is True

    def test_should_rescan_when_script_added(self, user_script_scanner):
        """Test should_rescan when a new script is added."""
        scripts = [
            TaggingScriptSetting(name="test1", enabled=True, content="$set(var1, value1)"),
            TaggingScriptSetting(name="test2", enabled=True, content="$set(var2, value2)"),
        ]
        # Set hash for only the first script
        old_script = TaggingScriptSetting(name="test1", enabled=True, content="$set(var1, value1)")
        user_script_scanner._last_scan_hash = hash(tuple((s.name, s.content) for s in [old_script]))

        with patch('picard.ui.widgets.user_script_scanner.iter_active_tagging_scripts') as mock_iter:
            mock_iter.return_value = scripts

            result = user_script_scanner.should_rescan()

            assert result is True

    def test_should_rescan_when_script_removed(self, user_script_scanner):
        """Test should_rescan when a script is removed."""
        # Set hash for two scripts
        old_scripts = [
            TaggingScriptSetting(name="test1", enabled=True, content="$set(var1, value1)"),
            TaggingScriptSetting(name="test2", enabled=True, content="$set(var2, value2)"),
        ]
        user_script_scanner._last_scan_hash = hash(tuple((s.name, s.content) for s in old_scripts))

        with patch('picard.ui.widgets.user_script_scanner.iter_active_tagging_scripts') as mock_iter:
            mock_iter.return_value = [TaggingScriptSetting(name="test1", enabled=True, content="$set(var1, value1)")]

            result = user_script_scanner.should_rescan()

            assert result is True

    def test_should_rescan_with_exception(self, user_script_scanner):
        """Test should_rescan when an exception occurs."""
        with patch('picard.ui.widgets.user_script_scanner.iter_active_tagging_scripts') as mock_iter:
            mock_iter.side_effect = ValueError("Access error")

            result = user_script_scanner.should_rescan()

            # Should return True when we can't determine if scripts changed
            assert result is True


class TestUserScriptScannerIntegration:
    """Test integration scenarios."""

    def test_full_scan_and_cache_cycle(self, user_script_scanner, sample_scripts):
        """Test complete scan and cache cycle."""
        user_script_scanner._variable_extractor.extract_variables.side_effect = [
            {"artist_name"},  # Script 1
            {"album_title"},  # Script 2
        ]

        with patch('picard.ui.widgets.user_script_scanner.iter_active_tagging_scripts') as mock_iter:
            mock_iter.return_value = [s for s in sample_scripts if s.enabled and s.content]

            # First scan
            result = user_script_scanner.scan_all_user_scripts()
            assert result == {"artist_name", "album_title"}

            # Check cache
            cached = user_script_scanner.get_cached_variables()
            assert cached == {"artist_name", "album_title"}

            # Should not rescan if nothing changed
            assert not user_script_scanner.should_rescan()

    def test_scan_with_mixed_script_states(self, user_script_scanner):
        """Test scanning with mixed script states (enabled/disabled, empty/non-empty)."""
        scripts = [
            TaggingScriptSetting(name="enabled_with_content", enabled=True, content="$set(var1, value1)"),
            TaggingScriptSetting(name="enabled_empty", enabled=True, content=""),
            TaggingScriptSetting(name="disabled_with_content", enabled=False, content="$set(var2, value2)"),
            TaggingScriptSetting(name="disabled_empty", enabled=False, content=""),
        ]

        user_script_scanner._variable_extractor.extract_variables.return_value = {"var1"}

        with patch('picard.ui.widgets.user_script_scanner.iter_active_tagging_scripts') as mock_iter:
            mock_iter.return_value = [s for s in scripts if s.enabled and s.content]

            result = user_script_scanner.scan_all_user_scripts()

            # Should only scan enabled scripts with content
            assert result == {"var1"}
            user_script_scanner._variable_extractor.extract_variables.assert_called_once_with("$set(var1, value1)")

    def test_unicode_variable_names(self, user_script_scanner):
        """Test scanning with unicode variable names."""
        scripts = [
            TaggingScriptSetting(name="unicode", enabled=True, content="$set(var_ñ, value)"),
            TaggingScriptSetting(name="chinese", enabled=True, content="$set(var_中文, value)"),
        ]

        user_script_scanner._variable_extractor.extract_variables.side_effect = [
            {"var_ñ"},
            {"var_中文"},
        ]

        with patch('picard.ui.widgets.user_script_scanner.iter_active_tagging_scripts') as mock_iter:
            mock_iter.return_value = scripts

            result = user_script_scanner.scan_all_user_scripts()

            assert result == {"var_ñ", "var_中文"}

    def test_duplicate_variable_names(self, user_script_scanner):
        """Test scanning with duplicate variable names across scripts."""
        scripts = [
            TaggingScriptSetting(name="script1", enabled=True, content="$set(common_var, value1)"),
            TaggingScriptSetting(name="script2", enabled=True, content="$set(common_var, value2)"),
        ]

        user_script_scanner._variable_extractor.extract_variables.side_effect = [
            {"common_var"},
            {"common_var"},
        ]

        with patch('picard.ui.widgets.user_script_scanner.iter_active_tagging_scripts') as mock_iter:
            mock_iter.return_value = scripts

            result = user_script_scanner.scan_all_user_scripts()

            # Should deduplicate automatically via set union
            assert result == {"common_var"}
