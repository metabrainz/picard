# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2022, 2024-2025 Philipp Wolfer
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2021-2024 Laurent Monin
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the GNU General Public License version 2
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

from unittest.mock import MagicMock, patch

from PyQt6 import QtCore, QtGui

import pytest

import picard.ui.theme as theme_mod


@pytest.fixture
def base_theme():
    """Create a BaseTheme instance for testing."""
    return theme_mod.BaseTheme()


@pytest.fixture
def mock_style_hints():
    """Create a mock QStyleHints object."""
    mock_hints = MagicMock()
    mock_hints.setColorScheme = MagicMock()
    return mock_hints


@pytest.fixture
def mock_palette():
    """Create a mock QPalette object."""
    palette = QtGui.QPalette()
    # Set some initial colors to verify changes
    palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(255, 255, 255))
    palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(0, 0, 0))
    return palette


@pytest.fixture
def mock_app():
    """Create a mock app for testing."""
    app = MagicMock()
    app.palette.return_value = QtGui.QPalette()
    return app


class TestStyleHintsMethods:
    """Test the new style hints related methods."""

    def test_get_style_hints_returns_style_hints(self, base_theme, mock_style_hints):
        """Test _get_style_hints returns QGuiApplication.styleHints()."""
        with patch("picard.ui.theme.QtGui.QGuiApplication.styleHints", return_value=mock_style_hints):
            result = base_theme._get_style_hints()
            assert result is mock_style_hints

    def test_get_style_hints_returns_none_when_unavailable(self, base_theme):
        """Test _get_style_hints returns None when styleHints() is unavailable."""
        with patch("picard.ui.theme.QtGui.QGuiApplication.styleHints", return_value=None):
            result = base_theme._get_style_hints()
            assert result is None

    def test_set_color_scheme_with_style_hints(self, base_theme, mock_style_hints):
        """Test _set_color_scheme calls setColorScheme when style hints available."""
        with patch.object(base_theme, "_get_style_hints", return_value=mock_style_hints):
            base_theme._set_color_scheme(QtCore.Qt.ColorScheme.Dark)
            mock_style_hints.setColorScheme.assert_called_once_with(QtCore.Qt.ColorScheme.Dark)

    def test_set_color_scheme_without_style_hints(self, base_theme):
        """Test _set_color_scheme does nothing when style hints unavailable."""
        with patch.object(base_theme, "_get_style_hints", return_value=None):
            # Should not raise any exception
            base_theme._set_color_scheme(QtCore.Qt.ColorScheme.Dark)

    @pytest.mark.parametrize(
        "color_scheme",
        [
            QtCore.Qt.ColorScheme.Dark,
            QtCore.Qt.ColorScheme.Light,
            QtCore.Qt.ColorScheme.Unknown,
        ],
    )
    def test_set_color_scheme_with_different_schemes(self, base_theme, mock_style_hints, color_scheme):
        """Test _set_color_scheme works with different color schemes."""
        with patch.object(base_theme, "_get_style_hints", return_value=mock_style_hints):
            base_theme._set_color_scheme(color_scheme)
            mock_style_hints.setColorScheme.assert_called_once_with(color_scheme)


class TestApplyDarkPaletteColors:
    """Test the _apply_dark_palette_colors method."""

    def test_apply_dark_palette_colors_applies_all_colors(self, base_theme, mock_palette):
        """Test _apply_dark_palette_colors applies all expected colors."""
        base_theme._apply_dark_palette_colors(mock_palette)

        # Check that the palette colors were changed to dark theme colors
        window_color = mock_palette.color(QtGui.QPalette.ColorRole.Window)
        assert window_color.getRgb() == (51, 51, 51, 255)

        window_text_color = mock_palette.color(QtGui.QPalette.ColorRole.WindowText)
        assert window_text_color == QtCore.Qt.GlobalColor.white

        base_color = mock_palette.color(QtGui.QPalette.ColorRole.Base)
        assert base_color.getRgb() == (31, 31, 31, 255)

    def test_apply_dark_palette_colors_applies_tuple_keys(self, base_theme, mock_palette):
        """Test _apply_dark_palette_colors correctly handles tuple keys (group, role)."""
        base_theme._apply_dark_palette_colors(mock_palette)

        # Check disabled text color (tuple key)
        disabled_text_color = mock_palette.color(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Text)
        assert disabled_text_color == QtCore.Qt.GlobalColor.darkGray

        # Check disabled base color (tuple key)
        disabled_base_color = mock_palette.color(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Base)
        assert disabled_base_color.getRgb() == (60, 60, 60, 255)


class TestApplyDarkThemeToPalette:
    """Test the _apply_dark_theme_to_palette method."""

    def test_apply_dark_theme_to_palette_with_style_hints(self, base_theme, mock_palette, mock_style_hints):
        """Test _apply_dark_theme_to_palette uses style hints when available."""
        with patch.object(base_theme, "_get_style_hints", return_value=mock_style_hints):
            base_theme._apply_dark_theme_to_palette(mock_palette)
            mock_style_hints.setColorScheme.assert_called_once_with(QtCore.Qt.ColorScheme.Dark)

    def test_apply_dark_theme_to_palette_without_style_hints(self, base_theme, mock_palette):
        """Test _apply_dark_theme_to_palette falls back to manual colors when style hints unavailable."""
        with patch.object(base_theme, "_get_style_hints", return_value=None):
            base_theme._apply_dark_theme_to_palette(mock_palette)

            # Should have applied manual dark colors
            window_color = mock_palette.color(QtGui.QPalette.ColorRole.Window)
            assert window_color.getRgb() == (51, 51, 51, 255)

    def test_apply_dark_theme_to_palette_calls_manual_fallback(self, base_theme, mock_palette):
        """Test _apply_dark_theme_to_palette calls _apply_dark_palette_colors when style hints unavailable."""
        with (
            patch.object(base_theme, "_get_style_hints", return_value=None),
            patch.object(base_theme, "_apply_dark_palette_colors") as mock_apply,
        ):
            base_theme._apply_dark_theme_to_palette(mock_palette)
            mock_apply.assert_called_once_with(mock_palette)


class TestThemeAvailability:
    """Test the updated theme availability logic."""

    def test_available_ui_themes_includes_all_themes_except_haiku(self):
        """Test AVAILABLE_UI_THEMES includes DEFAULT, LIGHT, and DARK themes."""
        # The current implementation includes all themes for all platforms except Haiku
        expected_themes = [theme_mod.UiTheme.DEFAULT, theme_mod.UiTheme.LIGHT, theme_mod.UiTheme.DARK]

        # Check that all expected themes are present
        for theme in expected_themes:
            assert theme in theme_mod.AVAILABLE_UI_THEMES

        # Check that we have exactly the expected themes (for non-Haiku platforms)
        if not theme_mod.IS_HAIKU:
            assert len(theme_mod.AVAILABLE_UI_THEMES) == len(expected_themes)
            for theme in theme_mod.AVAILABLE_UI_THEMES:
                assert theme in expected_themes


class TestSetupColorScheme:
    """Test the color scheme setting logic in setup method."""

    @pytest.mark.parametrize(
        ("theme_value", "expected_color_scheme"),
        [
            ("dark", QtCore.Qt.ColorScheme.Dark),
            ("light", QtCore.Qt.ColorScheme.Light),
            ("default", QtCore.Qt.ColorScheme.Unknown),
            ("system", QtCore.Qt.ColorScheme.Unknown),
        ],
    )
    def test_setup_sets_color_scheme_based_on_theme(
        self, base_theme, mock_app, mock_style_hints, theme_value, expected_color_scheme
    ):
        """Test setup method sets color scheme based on theme configuration."""
        # Mock config
        config_mock = MagicMock()
        config_mock.setting = {"ui_theme": theme_value}

        with (
            patch.object(theme_mod, "get_config", return_value=config_mock),
            patch.object(base_theme, "_get_style_hints", return_value=mock_style_hints),
            patch.object(theme_mod, "MacOverrideStyle") as _,
        ):
            base_theme.setup(mock_app)
            mock_style_hints.setColorScheme.assert_called_once_with(expected_color_scheme)

    def test_setup_handles_no_style_hints(self, base_theme, mock_app):
        """Test setup method handles case when style hints are unavailable."""
        # Mock config
        config_mock = MagicMock()
        config_mock.setting = {"ui_theme": "dark"}

        with (
            patch.object(theme_mod, "get_config", return_value=config_mock),
            patch.object(base_theme, "_get_style_hints", return_value=None),
            patch.object(theme_mod, "MacOverrideStyle"),
        ):
            # Should not raise any exception
            base_theme.setup(mock_app)


class TestWindowsTheme:
    """Test the WindowsTheme class updates."""

    def test_windows_theme_apply_dark_theme_to_palette(self, mock_palette):
        """Test WindowsTheme uses _apply_dark_theme_to_palette in update_palette."""
        theme = theme_mod.WindowsTheme()

        with patch.object(theme, "_apply_dark_theme_to_palette") as mock_apply:
            theme.update_palette(mock_palette, True, None)
            mock_apply.assert_called_once_with(mock_palette)

    def test_windows_theme_does_not_apply_dark_theme_when_not_dark(self, mock_palette):
        """Test WindowsTheme does not apply dark theme when dark_theme is False."""
        theme = theme_mod.WindowsTheme()

        with patch.object(theme, "_apply_dark_theme_to_palette") as mock_apply:
            theme.update_palette(mock_palette, False, None)
            mock_apply.assert_not_called()


class TestLinuxDarkModeDetection:
    """Test the Linux dark mode detection logic."""

    @pytest.fixture
    def linux_theme(self, monkeypatch):
        """Create a BaseTheme instance with Linux platform settings."""
        monkeypatch.setattr(theme_mod, "IS_WIN", False)
        monkeypatch.setattr(theme_mod, "IS_MACOS", False)
        monkeypatch.setattr(theme_mod, "IS_HAIKU", False)
        return theme_mod.BaseTheme()

    @pytest.mark.parametrize(
        ("config_theme", "detect_result", "expected_apply_called"),
        [
            ("default", True, True),  # Should apply dark theme
            ("default", False, False),  # Should not apply dark theme
            ("dark", True, False),  # Should not apply (already dark)
            ("light", True, False),  # Should not apply (explicit light)
            ("system", True, False),  # Should not apply (system theme)
        ],
    )
    def test_linux_dark_mode_detection_logic(
        self, linux_theme, mock_app, config_theme, detect_result, expected_apply_called
    ):
        """Test Linux dark mode detection logic in setup method."""
        # Mock config
        config_mock = MagicMock()
        config_mock.setting = {"ui_theme": config_theme}

        # Mock palette with light base color (not already dark)
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(255, 255, 255))
        mock_app.palette.return_value = palette

        with (
            patch.object(theme_mod, "get_config", return_value=config_mock),
            patch.object(linux_theme, "_detect_linux_dark_mode", return_value=detect_result),
            patch.object(linux_theme, "_apply_dark_theme_to_palette") as mock_apply,
            patch.object(linux_theme, "_get_style_hints", return_value=None),
        ):
            linux_theme.setup(mock_app)

            if expected_apply_called:
                mock_apply.assert_called_once()
            else:
                mock_apply.assert_not_called()

    def test_linux_dark_mode_not_applied_when_already_dark(self, linux_theme, mock_app):
        """Test Linux dark mode is not applied when palette is already dark."""
        # Mock config
        config_mock = MagicMock()
        config_mock.setting = {"ui_theme": "default"}

        # Mock palette with dark base color (already dark)
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(0, 0, 0))
        mock_app.palette.return_value = palette

        with (
            patch.object(theme_mod, "get_config", return_value=config_mock),
            patch.object(linux_theme, "_detect_linux_dark_mode", return_value=True),
            patch.object(linux_theme, "_apply_dark_theme_to_palette") as mock_apply,
            patch.object(linux_theme, "_get_style_hints", return_value=None),
        ):
            linux_theme.setup(mock_app)
            mock_apply.assert_not_called()


class TestIntegration:
    """Integration tests for the new functionality."""

    def test_style_hints_integration_with_real_palette(self, base_theme):
        """Test integration of style hints with real palette objects."""
        palette = QtGui.QPalette()
        original_window_color = palette.color(QtGui.QPalette.ColorRole.Window)

        # Test with style hints available
        mock_hints = MagicMock()
        with patch.object(base_theme, "_get_style_hints", return_value=mock_hints):
            base_theme._apply_dark_theme_to_palette(palette)
            mock_hints.setColorScheme.assert_called_once_with(QtCore.Qt.ColorScheme.Dark)
            # Palette should not be modified when using style hints
            assert palette.color(QtGui.QPalette.ColorRole.Window) == original_window_color

    def test_manual_fallback_integration(self, base_theme):
        """Test integration of manual fallback with real palette objects."""
        palette = QtGui.QPalette()
        original_window_color = palette.color(QtGui.QPalette.ColorRole.Window)

        # Test without style hints (manual fallback)
        with patch.object(base_theme, "_get_style_hints", return_value=None):
            base_theme._apply_dark_theme_to_palette(palette)
            # Palette should be modified with dark colors
            new_window_color = palette.color(QtGui.QPalette.ColorRole.Window)
            assert new_window_color.getRgb() == (51, 51, 51, 255)
            assert new_window_color != original_window_color

    def test_theme_setup_integration(self, mock_app):
        """Test complete theme setup integration."""
        theme = theme_mod.BaseTheme()

        # Mock all dependencies
        config_mock = MagicMock()
        config_mock.setting = {"ui_theme": "dark"}

        mock_hints = MagicMock()

        with (
            patch.object(theme_mod, "get_config", return_value=config_mock),
            patch.object(theme, "_get_style_hints", return_value=mock_hints),
            patch.object(theme_mod, "MacOverrideStyle"),
        ):
            theme.setup(mock_app)

            # Verify style hints were used
            mock_hints.setColorScheme.assert_called_once_with(QtCore.Qt.ColorScheme.Dark)
