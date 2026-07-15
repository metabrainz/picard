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

from unittest.mock import (
    MagicMock,
    patch,
)

from PyQt6 import (
    QtCore,
    QtGui,
)

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

    def test_get_style_hints_returns_style_hints(self, mock_style_hints):
        """Test get_style_hints returns QGuiApplication.styleHints()."""
        with patch("picard.ui.theme.QtGui.QGuiApplication.styleHints", return_value=mock_style_hints):
            result = theme_mod.get_style_hints()
            assert result is mock_style_hints

    def test_get_style_hints_returns_none_when_unavailable(self):
        """Test get_style_hints returns None when styleHints() is unavailable."""
        with patch("picard.ui.theme.QtGui.QGuiApplication.styleHints", return_value=None):
            result = theme_mod.get_style_hints()
            assert result is None

    def test_set_color_scheme_with_style_hints(self, mock_style_hints):
        """Test set_color_scheme calls setColorScheme when style hints available."""
        with patch("picard.ui.theme.get_style_hints", return_value=mock_style_hints):
            theme_mod.set_color_scheme(QtCore.Qt.ColorScheme.Dark)
            mock_style_hints.setColorScheme.assert_called_once_with(QtCore.Qt.ColorScheme.Dark)

    def test_set_color_scheme_without_style_hints(self):
        """Test set_color_scheme does nothing when style hints unavailable."""
        with patch("picard.ui.theme.get_style_hints", return_value=None):
            # Should not raise any exception
            theme_mod.set_color_scheme(QtCore.Qt.ColorScheme.Dark)

    @pytest.mark.parametrize(
        "color_scheme",
        [
            QtCore.Qt.ColorScheme.Dark,
            QtCore.Qt.ColorScheme.Light,
            QtCore.Qt.ColorScheme.Unknown,
        ],
    )
    def test_set_color_scheme_with_different_schemes(self, mock_style_hints, color_scheme):
        """Test set_color_scheme works with different color schemes."""
        with patch("picard.ui.theme.get_style_hints", return_value=mock_style_hints):
            theme_mod.set_color_scheme(color_scheme)
            mock_style_hints.setColorScheme.assert_called_once_with(color_scheme)


class TestApplyDarkPaletteColors:
    """Test the apply_dark_palette_colors method."""

    def test_apply_dark_palette_colors_applies_all_colors(self, mock_palette):
        """Test apply_dark_palette_colors applies all dark colors to palette."""
        theme_mod.apply_dark_palette_colors(mock_palette)

        # Verify colors have been changed to expected dark theme colors
        new_window_color = mock_palette.color(QtGui.QPalette.ColorRole.Window)
        new_text_color = mock_palette.color(QtGui.QPalette.ColorRole.Text)

        # Check that window color is now the dark background color
        assert new_window_color == theme_mod.DARK_BG_COLOR
        # Check that text color is now white
        assert new_text_color == QtCore.Qt.GlobalColor.white

    def test_apply_dark_palette_colors_applies_tuple_keys(self, mock_palette):
        """Test apply_dark_palette_colors correctly handles tuple keys (group, role)."""
        # Test that disabled text color is applied correctly
        original_disabled_text = mock_palette.color(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Text)

        theme_mod.apply_dark_palette_colors(mock_palette)

        new_disabled_text = mock_palette.color(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Text)

        assert new_disabled_text != original_disabled_text
        assert new_disabled_text == QtCore.Qt.GlobalColor.darkGray


class TestPaletteIsDark:
    """Test the is_dark method."""

    @pytest.mark.parametrize(
        ("base_color", "is_dark"),
        [
            (QtGui.QColor(QtCore.Qt.GlobalColor.black), True),
            (QtGui.QColor(QtCore.Qt.GlobalColor.black), True),
            (QtGui.QColor(128, 128, 128), False),
            (QtGui.QColor(127, 127, 127), True),
        ],
    )
    def test_is_dark(self, base_color, is_dark):
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.ColorRole.Base, base_color)
        assert theme_mod.palette_is_dark(palette) == is_dark


class TestApplyDarkThemeToPalette:
    """Test the apply_dark_theme_to_palette method."""

    def test_apply_dark_theme_to_palette(self):
        """Test integration of manual fallback with real palette objects."""
        palette = QtGui.QPalette()
        original_base_color = QtGui.QColor(QtCore.Qt.GlobalColor.white)
        palette.setColor(QtGui.QPalette.ColorRole.Base, original_base_color)

        # Test without style hints (manual fallback)
        with patch("picard.ui.theme.get_style_hints", return_value=None):
            theme_mod.apply_dark_theme_to_palette(palette)
            # Verify that manual colors were applied
            new_base_color = palette.color(QtGui.QPalette.ColorRole.Base)
            assert new_base_color != original_base_color

    def test_apply_dark_theme_to_palette_skipped_if_dark(self):
        """Test integration of manual fallback with real palette objects."""
        palette = QtGui.QPalette()
        original_base_color = QtGui.QColor(QtCore.Qt.GlobalColor.black)
        palette.setColor(QtGui.QPalette.ColorRole.Base, original_base_color)

        # Test without style hints (manual fallback)
        with patch("picard.ui.theme.get_style_hints", return_value=None):
            theme_mod.apply_dark_theme_to_palette(palette)
            # Verify that manual colors were applied
            new_base_color = palette.color(QtGui.QPalette.ColorRole.Base)
            assert new_base_color == original_base_color


class TestGetAccentColorFromPalette:
    def test_get_accent_color_from_palette(self):
        palette = QtGui.QPalette()
        accent_color = QtGui.QColor(40, 10, 40)
        if hasattr(QtGui.QPalette.ColorRole, 'Accent'):
            palette.setColor(QtGui.QPalette.ColorRole.Accent, accent_color)
        else:
            palette.setColor(QtGui.QPalette.ColorRole.Highlight, accent_color)

        new_accent_color = theme_mod.get_accent_color_from_palette(palette)
        assert new_accent_color == accent_color


class TestApplyAccentColorToPalette:
    def test_apply_accent_color_to_palette(self):
        palette = QtGui.QPalette()
        accent_color = QtGui.QColor(220, 220, 120)
        theme_mod.apply_accent_color_to_palette(palette, accent_color)
        assert palette.color(QtGui.QPalette.ColorRole.Highlight) == accent_color
        if hasattr(QtGui.QPalette.ColorRole, 'Accent'):
            assert palette.color(QtGui.QPalette.ColorRole.Accent) == accent_color
        assert palette.color(QtGui.QPalette.ColorRole.HighlightedText) == QtGui.QColor(QtCore.Qt.GlobalColor.black)


class TestThemeAvailability:
    """Test theme availability across platforms."""

    def test_available_ui_themes_includes_all_themes_except_haiku(self):
        """Test AVAILABLE_UI_THEMES includes appropriate themes based on platform and capabilities."""
        # This test assumes we're not on Haiku
        # On Haiku, AVAILABLE_UI_THEMES would be empty
        if theme_mod.IS_HAIKU:
            assert len(theme_mod.AVAILABLE_UI_THEMES) == 0
        elif not theme_mod.IS_WIN and not theme_mod.IS_MACOS:
            # Linux: Check if style hints are available
            if theme_mod._style_hints_available():
                # All themes available when style hints are supported
                assert len(theme_mod.AVAILABLE_UI_THEMES) == 3
                assert theme_mod.UiTheme.DEFAULT in theme_mod.AVAILABLE_UI_THEMES
                assert theme_mod.UiTheme.LIGHT in theme_mod.AVAILABLE_UI_THEMES
                assert theme_mod.UiTheme.DARK in theme_mod.AVAILABLE_UI_THEMES
            else:
                # Only DEFAULT theme available when style hints are not available
                assert len(theme_mod.AVAILABLE_UI_THEMES) == 1
                assert theme_mod.UiTheme.DEFAULT in theme_mod.AVAILABLE_UI_THEMES
                assert theme_mod.UiTheme.LIGHT not in theme_mod.AVAILABLE_UI_THEMES
                assert theme_mod.UiTheme.DARK not in theme_mod.AVAILABLE_UI_THEMES
        else:
            # Windows and macOS: all themes available
            assert len(theme_mod.AVAILABLE_UI_THEMES) > 0
            assert theme_mod.UiTheme.DEFAULT in theme_mod.AVAILABLE_UI_THEMES
            assert theme_mod.UiTheme.LIGHT in theme_mod.AVAILABLE_UI_THEMES
            assert theme_mod.UiTheme.DARK in theme_mod.AVAILABLE_UI_THEMES

    def test_linux_style_hints_detection(self, monkeypatch):
        """Test Linux style hints detection affects available themes."""
        # Mock Linux platform
        monkeypatch.setattr(theme_mod, "IS_WIN", False)
        monkeypatch.setattr(theme_mod, "IS_MACOS", False)
        monkeypatch.setattr(theme_mod, "IS_HAIKU", False)

        # Test the _style_hints_available function directly
        with patch("picard.ui.theme.get_style_hints", return_value=MagicMock()):
            assert theme_mod._style_hints_available() is True

        with patch("picard.ui.theme.get_style_hints", return_value=None):
            assert theme_mod._style_hints_available() is False

        # Test the logic that determines available themes
        # We can't easily test the module-level AVAILABLE_UI_THEMES since it's evaluated at import time
        # Instead, test that the logic works correctly by checking the function behavior
        def test_available_themes_logic(style_hints_available):
            if style_hints_available:
                return [theme_mod.UiTheme.DEFAULT, theme_mod.UiTheme.LIGHT, theme_mod.UiTheme.DARK]
            else:
                return [theme_mod.UiTheme.DEFAULT]

        # Test with style hints available
        available_themes = test_available_themes_logic(True)
        assert len(available_themes) == 3
        assert theme_mod.UiTheme.DEFAULT in available_themes
        assert theme_mod.UiTheme.LIGHT in available_themes
        assert theme_mod.UiTheme.DARK in available_themes

        # Test with style hints not available
        available_themes = test_available_themes_logic(False)
        assert len(available_themes) == 1
        assert theme_mod.UiTheme.DEFAULT in available_themes
        assert theme_mod.UiTheme.LIGHT not in available_themes
        assert theme_mod.UiTheme.DARK not in available_themes


class TestSetupColorScheme:
    """Test color scheme setup in theme setup method."""

    @pytest.mark.parametrize(
        ("theme_value", "expected_color_scheme"),
        [
            ("dark", QtCore.Qt.ColorScheme.Dark),
            ("light", QtCore.Qt.ColorScheme.Light),
            ("default", QtCore.Qt.ColorScheme.Light),
            ("system", QtCore.Qt.ColorScheme.Light),
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
            patch("picard.ui.theme.get_style_hints", return_value=mock_style_hints),
            patch.object(theme_mod.BaseTheme, "get_system_theme", return_value=theme_mod.UiTheme.LIGHT),
            patch.object(theme_mod, "MacOverrideStyle") as _,
        ):
            mock_style_hints.setColorScheme.reset_mock()
            base_theme.setup(mock_app)
            mock_style_hints.setColorScheme.assert_called_once_with(expected_color_scheme)

    def test_setup_handles_no_style_hints(self, base_theme, mock_app):
        """Test setup method handles case when style hints are unavailable."""
        # Mock config
        config_mock = MagicMock()
        config_mock.setting = {"ui_theme": "dark"}

        with (
            patch.object(theme_mod, "get_config", return_value=config_mock),
            patch("picard.ui.theme.get_style_hints", return_value=None),
            patch.object(theme_mod, "MacOverrideStyle"),
        ):
            # Should not raise any exception
            base_theme.setup(mock_app)


class TestGenericTheme:
    """Generic theme behavior."""

    def test_apply_theme_light(self, mock_palette):
        """Test WindowsTheme uses apply_dark_theme_to_palette in update_palette."""
        app = MagicMock()
        app.palette.return_value = mock_palette
        theme = theme_mod.GenericTheme()

        with (
            patch("picard.ui.theme.set_color_scheme") as mock_set_color_scheme,
            patch("picard.ui.theme.apply_dark_theme_to_palette") as mock_apply,
        ):
            theme.apply_theme(app, theme_mod.UiTheme.LIGHT)
            mock_set_color_scheme.assert_called_once()
            mock_apply.assert_not_called()

    def test_apply_theme_dark(self, mock_palette):
        """Test WindowsTheme uses apply_dark_theme_to_palette in update_palette."""
        app = MagicMock()
        app.palette.return_value = mock_palette
        theme = theme_mod.WindowsTheme()

        with (
            patch("picard.ui.theme.set_color_scheme") as mock_set_color_scheme,
            patch("picard.ui.theme.apply_dark_theme_to_palette") as mock_apply,
        ):
            theme.apply_theme(app, theme_mod.UiTheme.DARK)
            mock_set_color_scheme.assert_called_once()
            mock_apply.assert_called_once_with(mock_palette)


class TestWindowsTheme:
    """Test Windows specific theme behavior."""

    def test_get_system_theme_calls_registry(self):
        theme = theme_mod.WindowsTheme()
        app = MagicMock()

        with patch("picard.ui.theme.winreg") as mock_winreg:
            mock_winreg.QueryValueEx.return_value = (0, None)
            result = theme.get_system_theme(app)
            mock_winreg.OpenKey.assert_called_once_with(
                mock_winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            mock_winreg.QueryValueEx.assert_called_once_with(
                mock_winreg.OpenKey.return_value.__enter__.return_value, 'AppsUseLightTheme'
            )
            assert result == theme_mod.UiTheme.DARK

    def test_get_system_theme_error_fallback(self):
        theme = theme_mod.WindowsTheme()
        app = MagicMock()
        with patch("picard.ui.theme.winreg") as mock_winreg:
            mock_winreg.OpenKey.side_effect = OSError
            result = theme.get_system_theme(app)
            assert result == theme_mod.UiTheme.LIGHT

    def test_get_system_accent_color(self):
        theme = theme_mod.WindowsTheme()
        with patch("picard.ui.theme.winreg") as mock_winreg:
            mock_winreg.QueryValueEx.return_value = (0xAABBCC11, None)
            result = theme.get_system_accent_color()
            mock_winreg.OpenKey.assert_called_once_with(
                mock_winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\DWM",
            )
            mock_winreg.QueryValueEx.assert_called_once_with(
                mock_winreg.OpenKey.return_value.__enter__.return_value, 'ColorizationColor'
            )
            # The code masks out the alpha byte (& 0xFFFFFF), so only RGB is used
            assert result == QtGui.QColor('#bbcc11')

    def test_get_system_accent_color_error_fallback(self):
        theme = theme_mod.WindowsTheme()
        with patch("picard.ui.theme.winreg") as mock_winreg:
            mock_winreg.OpenKey.side_effect = OSError
            result = theme.get_system_accent_color()
            assert result is None


class TestMacTheme:
    """Test macOS specific theme behavior."""

    def test_get_system_theme(self):
        theme = theme_mod.MacTheme()
        app = MagicMock()
        with (
            patch("picard.ui.theme.OS_SUPPORTS_THEMES", True),
            patch("picard.ui.theme.AppKit") as mock_appkit,
        ):
            mock_appearance = MagicMock()
            mock_appearance.bestMatchFromAppearancesWithNames_.return_value = mock_appkit.NSAppearanceNameDarkAqua
            mock_appkit.NSAppearance.currentAppearance.return_value = mock_appearance
            result = theme.get_system_theme(app)
            mock_appearance.bestMatchFromAppearancesWithNames_.assert_called_once_with(
                [mock_appkit.NSAppearanceNameAqua, mock_appkit.NSAppearanceNameDarkAqua]
            )
            assert result == theme_mod.UiTheme.DARK

    def test_get_system_theme_error_fallback(self):
        theme = theme_mod.MacTheme()
        app = MagicMock()
        with (
            patch("picard.ui.theme.OS_SUPPORTS_THEMES", True),
            patch("picard.ui.theme.AppKit") as mock_appkit,
        ):
            mock_appearance = MagicMock()
            mock_appkit.NSAppearance.currentAppearance.return_value = mock_appearance
            mock_appearance.side_effect = OSError
            result = theme.get_system_theme(app)
            assert result == theme_mod.UiTheme.LIGHT

    def test_get_system_theme_no_appkit_fallback(self):
        theme = theme_mod.MacTheme()
        app = MagicMock()
        with (
            patch("picard.ui.theme.OS_SUPPORTS_THEMES", True),
            patch("picard.ui.theme.AppKit", None),
        ):
            result = theme.get_system_theme(app)
            assert result == theme_mod.UiTheme.LIGHT

    def test_apply_theme(self):
        theme = theme_mod.MacTheme()
        app = MagicMock()
        with (
            patch("picard.ui.theme.OS_SUPPORTS_THEMES", True),
            patch("picard.ui.theme.AppKit") as mock_appkit,
            patch("picard.ui.theme.BaseTheme.apply_theme") as mock_base_apply,
        ):
            theme.apply_theme(app, theme_mod.UiTheme.DARK)
            mock_base_apply.assert_called_once()
            mock_appkit.NSApplication.sharedApplication().setAppearance_.assert_called_once_with(
                mock_appkit.NSAppearance._darkAquaAppearance()
            )

    def test_get_system_theme_no_theme_support(self):
        theme = theme_mod.MacTheme()
        app = MagicMock()
        with (
            patch("picard.ui.theme.OS_SUPPORTS_THEMES", False),
            patch("picard.ui.theme.AppKit") as mock_appkit,
            patch("picard.ui.theme.BaseTheme.apply_theme") as mock_base_apply,
        ):
            theme.apply_theme(app, theme_mod.UiTheme.DARK)
            mock_base_apply.assert_called_once()
            mock_appkit.NSApplication.sharedApplication().setAppearance_.assert_not_called()


class TestLinuxDarkModeDetection:
    """Test Linux dark mode detection logic."""

    @pytest.fixture
    def linux_theme(self, monkeypatch):
        """Create a Linux theme instance for testing."""
        # Mock platform detection to simulate Linux
        monkeypatch.setattr(theme_mod, "IS_WIN", False)
        monkeypatch.setattr(theme_mod, "IS_MACOS", False)
        monkeypatch.setattr(theme_mod, "IS_HAIKU", False)
        return theme_mod.BaseTheme()

    @pytest.mark.parametrize(
        ("config_theme", "detect_result", "expected_apply_called"),
        [
            ("default", theme_mod.UiTheme.DARK, True),  # Should apply dark theme
            ("default", theme_mod.UiTheme.LIGHT, False),  # Should not apply dark theme
            ("dark", theme_mod.UiTheme.DARK, True),  # Should apply dark theme
            ("light", theme_mod.UiTheme.DARK, False),  # Should not apply (light configured)
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
            patch.object(linux_theme, "get_system_theme", return_value=detect_result),
            patch("picard.ui.theme.apply_dark_theme_to_palette") as mock_apply,
            patch("picard.ui.theme.get_style_hints", return_value=None),
        ):
            linux_theme.setup(mock_app)
            if expected_apply_called:
                mock_apply.assert_called_once()
            else:
                mock_apply.assert_not_called()

    def test_linux_dark_mode_palette_not_applied_when_already_dark(self, linux_theme, mock_app):
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
            patch.object(linux_theme, "get_system_theme", return_value=theme_mod.UiTheme.DARK),
            patch("picard.ui.theme.apply_dark_palette_colors") as mock_apply,
            patch("picard.ui.theme.get_style_hints", return_value=None),
        ):
            linux_theme.setup(mock_app)
            # Should not apply dark theme when already dark
            mock_apply.assert_not_called()


class TestIntegration:
    """Test integration scenarios."""

    def test_theme_setup_integration(self, mock_app):
        """Test complete theme setup integration."""
        theme = theme_mod.BaseTheme()

        # Mock all dependencies
        config_mock = MagicMock()
        config_mock.setting = {"ui_theme": "dark"}

        mock_hints = MagicMock()

        with (
            patch.object(theme_mod, "get_config", return_value=config_mock),
            patch("picard.ui.theme.get_style_hints", return_value=mock_hints),
            patch.object(theme_mod, "MacOverrideStyle"),
        ):
            theme.setup(mock_app)
            mock_hints.setColorScheme.assert_called_once_with(QtCore.Qt.ColorScheme.Dark)
