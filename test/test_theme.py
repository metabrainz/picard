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

import os
from pathlib import Path
import subprocess
import types
from unittest.mock import (
    MagicMock,
    Mock,
    patch,
)

from PyQt6 import (
    QtCore,
    QtGui,
)

import pytest

from picard.ui import theme_detect
import picard.ui.theme as theme_mod


class DummyPalette(QtGui.QPalette):
    """A dummy palette for testing theme functionality."""

    def __init__(self, already_dark_theme=False):
        super().__init__()
        # Set a unique color to detect override
        self.setColor(
            QtGui.QPalette.ColorGroup.Active,
            QtGui.QPalette.ColorRole.Window,
            QtGui.QColor(123, 123, 123),
        )
        # Set base color to dark or light to control self._dark_theme
        if already_dark_theme:
            self.setColor(
                QtGui.QPalette.ColorGroup.Active,
                QtGui.QPalette.ColorRole.Base,
                QtGui.QColor(0, 0, 0),
            )
        else:
            self.setColor(
                QtGui.QPalette.ColorGroup.Active,
                QtGui.QPalette.ColorRole.Base,
                QtGui.QColor(255, 255, 255),
            )


class DummyApp:
    """A dummy application for testing theme functionality."""

    def __init__(self, already_dark_theme=False):
        self._palette = DummyPalette(already_dark_theme)

    def setStyle(self, style):
        pass

    def setStyleSheet(self, stylesheet):
        pass

    def palette(self):
        return self._palette

    def setPalette(self, palette):
        self._palette = palette

    def style(self):
        return None


@pytest.fixture
def kde_config_dir(tmp_path: Path) -> Path:
    config_dir = tmp_path / ".config"
    config_dir.mkdir()
    return config_dir


@pytest.mark.parametrize(
    ("key", "stdout", "expected"),
    [
        ("color-scheme", "prefer-dark", True),
        ("color-scheme", "default", False),
        ("gtk-theme", "Adwaita-dark", True),
        ("gtk-theme", "Adwaita", False),
    ],
)
def test_gsettings_detection(key: str, stdout: str, expected: bool) -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = stdout
        mock_run.return_value.returncode = 0
        if key == "color-scheme":
            assert theme_detect.detect_gnome_color_scheme_dark() is expected
        else:
            assert theme_detect.detect_gnome_gtk_theme_dark() is expected


@pytest.mark.parametrize(
    "side_effect",
    [
        FileNotFoundError(),
        subprocess.CalledProcessError(1, "gsettings"),
    ],
)
def test_gsettings_get_failure(side_effect) -> None:
    with patch("subprocess.run", side_effect=side_effect):
        assert theme_detect.gsettings_get("color-scheme") is None


@pytest.mark.parametrize(
    ("file_content", "expected"),
    [
        ("[General]\nColorScheme=BreezeDark\n", True),
        ("[General]\nColorScheme=Breeze\n", False),
        ("", False),
    ],
)
def test_kde_colorscheme_detection(file_content: str, expected: bool, kde_config_dir: Path) -> None:
    kdeglobals = kde_config_dir / "kdeglobals"
    kdeglobals.write_text(file_content)
    with patch("pathlib.Path.home", return_value=kde_config_dir.parent):
        assert theme_detect.detect_kde_colorscheme_dark() is expected


@pytest.mark.parametrize(
    ("color_scheme", "gtk_theme", "kde_content", "expected", "de"),
    [
        ("prefer-dark", "Adwaita", "ColorScheme=Breeze\n", True, "gnome"),
        ("default", "Adwaita-dark", "ColorScheme=Breeze\n", True, "gnome"),
        ("default", "Adwaita", "ColorScheme=BreezeDark\n", True, "kde"),
        ("default", "Adwaita", "ColorScheme=Breeze\n", False, "kde"),
    ],
)
def test_detect_linux_dark_mode_integration(
    color_scheme: str,
    gtk_theme: str,
    kde_content: str,
    expected: bool,
    de: str,
    kde_config_dir: Path,
) -> None:
    kdeglobals = kde_config_dir / "kdeglobals"
    kdeglobals.write_text(f"[General]\n{kde_content}")
    with (
        patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": de}, clear=True),
        patch("pathlib.Path.home", return_value=kde_config_dir.parent),
        patch("picard.ui.theme_detect.gsettings_get") as mock_gsettings,
        patch("picard.ui.theme_detect.get_dbus_detector") as mock_get_detector,
        patch("picard.ui.theme_detect.detect_freedesktop_color_scheme_dbus", return_value=False),
        patch("picard.ui.theme_detect.detect_gnome_color_scheme_dbus", return_value=False),
    ):
        # Mock D-Bus detector to return None (force fallback to subprocess)
        mock_detector = Mock()
        mock_detector.freedesktop_portal_color_scheme_is_dark.return_value = None
        mock_detector.gnome_color_scheme_is_dark.return_value = None
        mock_get_detector.return_value = mock_detector

        def gsettings_get_side_effect(key):
            if key == "color-scheme":
                return color_scheme
            if key == "gtk-theme":
                return gtk_theme
            return ""

        mock_gsettings.side_effect = gsettings_get_side_effect
        strategies = theme_detect.get_linux_dark_mode_strategies()
        result = False
        for strategy in strategies:
            if strategy():
                result = True
                break
        assert result is expected


# Integration: freedesktop takes priority
def test_detect_linux_dark_mode_priority(tmp_path: Path) -> None:
    # If freedesktop returns dark, it should take priority over others
    with (
        patch("picard.ui.theme_detect.get_dbus_detector") as mock_get_detector,
        patch("subprocess.run") as mock_run,
    ):
        # Mock D-Bus to fail so we test subprocess fallback
        with patch("picard.ui.theme_detect.get_dbus_detector") as mock_get_detector:
            # Mock D-Bus detector to raise exception (simulating D-Bus unavailable)
            mock_get_detector.side_effect = RuntimeError("D-Bus unavailable")

            with patch("subprocess.run") as mock_run:
                # First call: freedesktop (returns '1' for dark)
                # Other calls: return '' (should not be called, but if so, not dark)
                mock_run.return_value.stdout = "1"
                mock_run.return_value.returncode = 0

                # Test the specific function that should work with subprocess fallback
                result = theme_detect.detect_freedesktop_color_scheme_dark()
                assert result is True


# Integration: D-Bus takes priority over subprocess
def test_detect_linux_dark_mode_dbus_priority(tmp_path: Path) -> None:
    # If D-Bus returns dark, it should take priority over subprocess
    with patch("picard.ui.theme_detect_qtdbus.get_dbus_detector") as mock_get_detector:
        # Mock successful D-Bus detection
        mock_detector = Mock()
        mock_detector.freedesktop_portal_color_scheme_is_dark.return_value = True
        mock_get_detector.return_value = mock_detector

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "0"  # subprocess would return light
            mock_run.return_value.returncode = 0

            strategies = theme_detect.get_linux_dark_mode_strategies()
            result = False
            for strategy in strategies:
                if strategy():
                    result = True
                    break

            # D-Bus method should be called and return dark
            mock_get_detector.assert_called()
            assert result is True


# --- XFCE dark mode detection ---
@pytest.mark.parametrize(
    ("stdout", "expected"),
    [
        ("Greybird-dark", True),
        ("Greybird", False),
        ("", False),
    ],
)
def test_xfce_dark_theme_detection(stdout: str, expected: bool) -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = stdout
        mock_run.return_value.returncode = 0
        assert theme_detect.detect_xfce_dark_theme() is expected


@pytest.mark.parametrize(
    "side_effect",
    [
        FileNotFoundError(),
        subprocess.CalledProcessError(1, "xfconf-query"),
    ],
)
def test_xfce_dark_theme_detection_failure(side_effect) -> None:
    with patch("subprocess.run", side_effect=side_effect):
        assert theme_detect.detect_xfce_dark_theme() is False


# --- LXQt dark mode detection ---
@pytest.mark.parametrize(
    ("file_content", "expected"),
    [
        ("theme=DarkTheme\n", True),
        ("theme=LightTheme\n", False),
        ("", False),
    ],
)
def test_lxqt_dark_theme_detection(file_content: str, expected: bool, tmp_path: Path) -> None:
    lxqt_dir = tmp_path / ".config" / "lxqt"
    lxqt_dir.mkdir(parents=True)
    session_conf = lxqt_dir / "session.conf"
    session_conf.write_text(file_content)
    with patch("pathlib.Path.home", return_value=tmp_path):
        assert theme_detect.detect_lxqt_dark_theme() is expected


@pytest.mark.parametrize(
    ("file_exists", "raises"),
    [
        (True, OSError("fail")),
        (False, None),
    ],
)
def test_lxqt_dark_theme_detection_failure(file_exists: bool, raises, tmp_path: Path) -> None:
    lxqt_dir = tmp_path / ".config" / "lxqt"
    lxqt_dir.mkdir(parents=True)
    session_conf = lxqt_dir / "session.conf"
    if file_exists:
        session_conf.write_text("theme=DarkTheme\n")
    with patch("pathlib.Path.home", return_value=tmp_path):
        if file_exists and raises:
            with patch("pathlib.Path.open", side_effect=raises):
                assert theme_detect.detect_lxqt_dark_theme() is False
        elif not file_exists:
            assert theme_detect.detect_lxqt_dark_theme() is False

@pytest.mark.parametrize(
    ("gsettings_value", "expected"),
    [
        ("1", True),
        ("0", False),
        ("", False),
    ],
)
def test_freedesktop_color_scheme_detection(gsettings_value: str, expected: bool) -> None:
    with (
        patch("picard.ui.theme_detect.get_dbus_detector") as mock_get_detector,
        patch("subprocess.run") as mock_run,
    ):
        # Mock D-Bus detector to return None (force fallback to subprocess)
        mock_detector = Mock()
        mock_detector.freedesktop_portal_color_scheme_is_dark.return_value = None
        mock_get_detector.return_value = mock_detector

        mock_run.return_value.stdout = gsettings_value
        mock_run.return_value.returncode = 0
        assert theme_detect.detect_freedesktop_color_scheme_dark() is expected


@pytest.mark.parametrize(
    "side_effect",
    [
        FileNotFoundError(),
        subprocess.CalledProcessError(1, "gsettings"),
    ],
)
def test_freedesktop_color_scheme_detection_failure(side_effect) -> None:
    with (
        patch("picard.ui.theme_detect.get_dbus_detector") as mock_get_detector,
        patch("subprocess.run", side_effect=side_effect),
    ):
        # Mock D-Bus detector to return None (force fallback to subprocess)
        mock_detector = Mock()
        mock_detector.freedesktop_portal_color_scheme_is_dark.return_value = None
        mock_get_detector.return_value = mock_detector

        assert theme_detect.detect_freedesktop_color_scheme_dark() is False


# Shared expected dark palette colors (should match DARK_PALETTE_COLORS in theme.py)
EXPECTED_DARK_PALETTE_COLORS = {
    QtGui.QPalette.ColorRole.Window: QtGui.QColor(51, 51, 51),
    QtGui.QPalette.ColorRole.WindowText: QtCore.Qt.GlobalColor.white,
    QtGui.QPalette.ColorRole.Base: QtGui.QColor(31, 31, 31),
    QtGui.QPalette.ColorRole.AlternateBase: QtGui.QColor(51, 51, 51),
    QtGui.QPalette.ColorRole.ToolTipBase: QtGui.QColor(51, 51, 51),
    QtGui.QPalette.ColorRole.ToolTipText: QtCore.Qt.GlobalColor.white,
    QtGui.QPalette.ColorRole.Text: QtCore.Qt.GlobalColor.white,
    QtGui.QPalette.ColorRole.Button: QtGui.QColor(51, 51, 51),
    QtGui.QPalette.ColorRole.ButtonText: QtCore.Qt.GlobalColor.white,
    QtGui.QPalette.ColorRole.BrightText: QtCore.Qt.GlobalColor.red,
    (
        QtGui.QPalette.ColorGroup.Disabled,
        QtGui.QPalette.ColorRole.Text,
    ): QtCore.Qt.GlobalColor.darkGray,
    (QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Light): QtGui.QColor(0, 0, 0, 0),
    (
        QtGui.QPalette.ColorGroup.Disabled,
        QtGui.QPalette.ColorRole.ButtonText,
    ): QtCore.Qt.GlobalColor.darkGray,
    (QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Base): QtGui.QColor(60, 60, 60),
    (
        QtGui.QPalette.ColorGroup.Inactive,
        QtGui.QPalette.ColorRole.Highlight,
    ): QtGui.QColor(51, 51, 51),
    (
        QtGui.QPalette.ColorGroup.Inactive,
        QtGui.QPalette.ColorRole.HighlightedText,
    ): QtCore.Qt.GlobalColor.white,
}


def assert_palette_matches_expected(palette, expected_colors):
    for key, expected in expected_colors.items():
        if isinstance(key, tuple):
            group, role = key
            actual = palette.color(group, role)
        else:
            actual = (
                palette.color(QtGui.QPalette.ColorGroup.Active, key)
                if isinstance(key, QtGui.QPalette.ColorRole)
                else palette.color(key)
            )
        if isinstance(expected, QtGui.QColor):
            # Compare by value, not object identity
            assert (
                actual.getRgb() == expected.getRgb()
            ), f"Color for {key} should be {expected.getRgb()}, got {actual.getRgb()}"
        else:
            assert actual == QtGui.QColor(expected), f"Color for {key} should be {expected}, got {actual}"


# Only check these roles for light mode, as they are guaranteed to differ
LIGHT_MODE_DISTINCT_ROLES = [
    QtGui.QPalette.ColorRole.Window,
    QtGui.QPalette.ColorRole.Base,
    QtGui.QPalette.ColorRole.Button,
    QtGui.QPalette.ColorRole.AlternateBase,
]


def assert_palette_not_dark(palette, expected_colors):
    for key, expected in expected_colors.items():
        # Only check the main roles for light mode
        if isinstance(key, tuple):
            continue
        if key not in LIGHT_MODE_DISTINCT_ROLES:
            continue
        actual = palette.color(QtGui.QPalette.ColorGroup.Active, key)
        if isinstance(expected, QtGui.QColor):
            assert (
                actual.getRgb() != expected.getRgb()
            ), f"Color for {key} should differ from dark mode in light mode; got {actual.getRgb()}"
        else:
            assert actual != QtGui.QColor(
                expected
            ), f"Color for {key} should differ from dark mode in light mode; got {actual}"


@pytest.mark.parametrize(
    ("already_dark_theme", "dark_mode", "expect_dark_palette"),
    [
        (True, True, False),  # Already dark, detection True: do NOT override
        (True, False, False),  # Already dark, detection False: do NOT override
        (False, True, True),  # Not dark, detection True: override
        (False, False, False),  # Not dark, detection False: do NOT override
    ],
)
def test_linux_dark_theme_palette(monkeypatch, already_dark_theme, dark_mode, expect_dark_palette):
    # Simulate Linux (not Windows, not macOS, not Haiku)
    monkeypatch.setattr(theme_mod, "IS_WIN", False)
    monkeypatch.setattr(theme_mod, "IS_MACOS", False)
    monkeypatch.setattr(theme_mod, "IS_HAIKU", False)
    # Set config to SYSTEM
    config_mock = MagicMock()
    config_mock.setting = {"ui_theme": "system"}
    monkeypatch.setattr(theme_mod, "get_config", lambda: config_mock)
    # Patch _detect_linux_dark_mode to return dark_mode
    theme = theme_mod.BaseTheme()
    theme._detect_linux_dark_mode = lambda: dark_mode

    # Mock app and palette
    app = DummyApp(already_dark_theme)
    theme.setup(app)
    palette = app._palette
    if expect_dark_palette:
        assert_palette_matches_expected(palette, EXPECTED_DARK_PALETTE_COLORS)
    else:
        # The Window color should remain the unique color if not overridden
        window_color = palette.color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Window)
        assert window_color == QtGui.QColor(123, 123, 123), (
            f"Palette should not be overridden, got {window_color.getRgb()}"
        )


@pytest.mark.parametrize(
    ("apps_use_light_theme", "expected_dark"),
    [
        (0, True),
        (1, False),
    ],
)
def test_windows_dark_theme_palette(monkeypatch, apps_use_light_theme, expected_dark):
    import picard.ui.theme as theme_mod

    # Patch winreg
    winreg_mock = types.SimpleNamespace()
    monkeypatch.setattr(theme_mod, "winreg", winreg_mock)

    # Mock OpenKey and QueryValueEx for dark mode
    class DummyKey:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    def openkey_side_effect(key, subkey):
        if "Personalize" in subkey:
            return DummyKey()
        if "DWM" in subkey:
            return DummyKey()
        raise FileNotFoundError

    def queryvalueex_side_effect(key, value):
        if value == "AppsUseLightTheme":
            return (apps_use_light_theme,)
        if value == "ColorizationColor":
            return (0x123456,)
        raise FileNotFoundError

    winreg_mock.HKEY_CURRENT_USER = 0
    winreg_mock.OpenKey = openkey_side_effect
    winreg_mock.QueryValueEx = queryvalueex_side_effect
    # Patch config
    config_mock = MagicMock()
    config_mock.setting = {"ui_theme": "default"}
    monkeypatch.setattr(theme_mod, "get_config", lambda: config_mock)
    # Instantiate WindowsTheme and run setup
    theme = theme_mod.WindowsTheme()

    app = DummyApp()
    theme.setup(app)
    palette = app._palette
    if expected_dark:
        assert_palette_matches_expected(palette, EXPECTED_DARK_PALETTE_COLORS)
    else:
        assert_palette_not_dark(palette, EXPECTED_DARK_PALETTE_COLORS)


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({"XDG_CURRENT_DESKTOP": "GNOME"}, "gnome"),
        ({"XDG_CURRENT_DESKTOP": "KDE"}, "kde"),
        ({"KDE_FULL_SESSION": "true"}, "kde"),
        ({"XDG_SESSION_DESKTOP": "xfce"}, "xfce"),
        ({"DESKTOP_SESSION": "lxqt"}, "lxqt"),
        ({}, ""),
    ],
)
def test_get_current_desktop_environment_param(env, expected):
    with patch.dict(os.environ, env, clear=True):
        assert theme_detect.get_current_desktop_environment() == expected


@pytest.mark.parametrize(
    "args",
    [
        (
            "gnome",
            theme_detect.detect_gnome_dark_wrapper,
            "picard.ui.theme_detect.detect_gnome_color_scheme_dark",
            True,
        ),
        (
            "kde",
            theme_detect.detect_kde_dark_wrapper,
            "picard.ui.theme_detect.detect_kde_colorscheme_dark",
            True,
        ),
        (
            "xfce",
            theme_detect.detect_xfce_dark_wrapper,
            "picard.ui.theme_detect.detect_xfce_dark_theme",
            True,
        ),
        (
            "lxqt",
            theme_detect.detect_lxqt_dark_wrapper,
            "picard.ui.theme_detect.detect_lxqt_dark_theme",
            True,
        ),
        (
            "other",
            theme_detect.detect_gnome_dark_wrapper,
            "picard.ui.theme_detect.detect_gnome_color_scheme_dark",
            False,
        ),
        (
            "other",
            theme_detect.detect_kde_dark_wrapper,
            "picard.ui.theme_detect.detect_kde_colorscheme_dark",
            False,
        ),
        (
            "other",
            theme_detect.detect_xfce_dark_wrapper,
            "picard.ui.theme_detect.detect_xfce_dark_theme",
            False,
        ),
        (
            "other",
            theme_detect.detect_lxqt_dark_wrapper,
            "picard.ui.theme_detect.detect_lxqt_dark_theme",
            False,
        ),
    ],
)
def test_de_specific_wrappers_only_run_for_matching_de_param(args):
    de, wrapper, detect_func, should_call = args
    env = {"XDG_CURRENT_DESKTOP": de} if de != "other" else {"XDG_CURRENT_DESKTOP": "somethingelse"}
    with (
        patch.dict(os.environ, env, clear=True),
        patch(detect_func, return_value=True) as mock_detect,
    ):
        result = wrapper()
        if should_call:
            mock_detect.assert_called()
            assert result is True
        else:
            mock_detect.assert_not_called()
            assert result is False


@pytest.mark.parametrize(
    ("already_dark_theme", "linux_dark_mode_detected", "expect_dark_palette"),
    [
        (True, True, False),  # Already dark, detection True: do NOT override
        (True, False, False),  # Already dark, detection False: do NOT override
        (False, True, True),  # Not dark, detection True: override
        (False, False, False),  # Not dark, detection False: do NOT override
    ],
)
def test_linux_dark_palette_override_only_if_not_already_dark(
    monkeypatch, already_dark_theme, linux_dark_mode_detected, expect_dark_palette
):
    monkeypatch.setattr(theme_mod, "IS_WIN", False)
    monkeypatch.setattr(theme_mod, "IS_MACOS", False)
    monkeypatch.setattr(theme_mod, "IS_HAIKU", False)
    config_mock = MagicMock()
    config_mock.setting = {"ui_theme": "system"}
    monkeypatch.setattr(theme_mod, "get_config", lambda: config_mock)

    app = DummyApp(already_dark_theme)
    theme = theme_mod.BaseTheme()
    theme._detect_linux_dark_mode = lambda: linux_dark_mode_detected
    theme.setup(app)
    palette = app._palette
    if expect_dark_palette:
        assert_palette_matches_expected(palette, EXPECTED_DARK_PALETTE_COLORS)
    else:
        # The Window color should remain the unique color if not overridden
        window_color = palette.color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Window)
        assert window_color == QtGui.QColor(123, 123, 123), (
            f"Palette should not be overridden, got {window_color.getRgb()}"
        )
