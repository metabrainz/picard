# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2022, 2024-2026 Philipp Wolfer
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2021-2025 Laurent Monin
# Copyright (C) 2025 Khoa Nguyen
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
        patch("picard.ui.theme_detect_qtdbus.get_dbus_detector") as mock_get_detector,
        patch("picard.ui.theme_detect_qtdbus.detect_freedesktop_color_scheme_dbus", return_value=False),
    ):
        # Mock D-Bus detector to return None (force fallback to subprocess)
        mock_detector = Mock()
        mock_detector.freedesktop_portal_color_scheme_is_dark.return_value = None
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
        patch("picard.ui.theme_detect_qtdbus.get_dbus_detector") as mock_get_detector,
        patch("subprocess.run") as mock_run,
    ):
        # Mock D-Bus to fail so we test subprocess fallback
        with patch("picard.ui.theme_detect_qtdbus.get_dbus_detector") as mock_get_detector:
            # Mock D-Bus detector to raise exception (simulating D-Bus unavailable)
            mock_get_detector.side_effect = RuntimeError("D-Bus unavailable")

            with patch("subprocess.run") as mock_run:
                # First call: gnome gsettings
                # Other calls: return '' (should not be called, but if so, not dark)
                mock_run.return_value.stdout = "dark"
                mock_run.return_value.returncode = 0

                # Test the specific function that should work with subprocess fallback
                result = theme_detect.detect_gnome_color_scheme_dark()
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
    ): QtGui.QColor(235, 116, 59),
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
            assert actual.getRgb() == expected.getRgb(), (
                f"Color for {key} should be {expected.getRgb()}, got {actual.getRgb()}"
            )
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
            assert actual.getRgb() != expected.getRgb(), (
                f"Color for {key} should differ from dark mode in light mode; got {actual.getRgb()}"
            )
        else:
            assert actual != QtGui.QColor(expected), (
                f"Color for {key} should differ from dark mode in light mode; got {actual}"
            )


def _make_light_standard_palette():
    """A light palette as a style's standardPalette() would report on a light OS."""
    palette = QtGui.QPalette()
    palette.setColor(
        QtGui.QPalette.ColorGroup.Active,
        QtGui.QPalette.ColorRole.Base,
        QtGui.QColor(255, 255, 255),
    )
    return palette


class _StyleWithStandardPalette:
    """Minimal style stub exposing a fixed standardPalette()."""

    def __init__(self, standard_palette):
        self._standard_palette = standard_palette

    def standardPalette(self):
        return self._standard_palette


class _AppWithStyle(DummyApp):
    """DummyApp variant whose style() returns a style with a standardPalette().

    Models the real runtime state: the live application palette may have been
    overridden (e.g. dark, after the user picked the Dark theme), while the
    style's standard palette still reflects the true OS theme.
    """

    def __init__(self, live_dark, standard_palette):
        super().__init__(already_dark_theme=live_dark)
        self._style = _StyleWithStandardPalette(standard_palette)

    def style(self):
        return self._style


def test_get_system_theme_ignores_runtime_applied_dark_palette(monkeypatch):
    """Regression test for PICARD-2442 dynamic theme switch bug.

    Reproduces the scenario reported by rdswift: on a system whose real theme
    is light, switching the UI theme option from "Dark" back to "Default" had
    no effect until restart.

    Root cause: ``get_system_theme()`` used to fall back to
    ``palette_is_dark(app.palette())`` when no OS dark-mode strategy reported
    dark. That live palette reflects whatever theme Picard applied at runtime.
    After the user manually selected the Dark theme, ``app.palette()`` is dark,
    so the old code wrongly reported the system theme as DARK, and
    ``apply_theme(DARK)`` then early-returned because dark was already applied,
    so nothing repainted.

    ``get_system_theme()`` must report the real OS theme (LIGHT here),
    independent of whatever palette Picard has applied at runtime.
    """
    # Force the style-hints path off so we exercise the standard-palette fallback.
    monkeypatch.setattr(QtGui.QGuiApplication, "styleHints", lambda: None)

    theme = theme_mod.GenericTheme()
    # No OS dark-mode strategy reports dark (system default is light).
    theme._dark_mode_strategies = [lambda: False]

    # Live palette is dark (Picard applied Dark at runtime), but the style's
    # standard palette still reflects the true OS theme (light).
    app = _AppWithStyle(live_dark=True, standard_palette=_make_light_standard_palette())
    assert theme_mod.palette_is_dark(app.palette())
    assert not theme_mod.palette_is_dark(app.style().standardPalette())

    detected = theme.get_system_theme(app)

    assert detected == theme_mod.UiTheme.LIGHT, (
        "get_system_theme must report the real OS theme (light) and not be "
        "fooled by a dark palette that Picard applied at runtime"
    )


def test_get_system_theme_uses_style_hints_color_scheme(monkeypatch):
    """When available, get_system_theme should trust the cached OS color scheme.

    Even if the live application palette is dark (runtime override), a light OS
    color scheme must be reported as LIGHT.
    """

    class _StyleHints:
        def __init__(self, scheme):
            self._scheme = scheme

        def setColorScheme(self, scheme):  # presence gates get_style_hints()
            self._scheme = scheme

        def colorScheme(self):
            return self._scheme

    monkeypatch.setattr(
        QtGui.QGuiApplication,
        "styleHints",
        lambda: _StyleHints(QtCore.Qt.ColorScheme.Light),
    )

    theme = theme_mod.GenericTheme()
    theme._dark_mode_strategies = [lambda: False]
    # setup() would capture this; set it directly for this focused unit test.
    theme._system_color_scheme = QtCore.Qt.ColorScheme.Light

    # Live palette is dark, but the OS reports a light scheme.
    app = _AppWithStyle(live_dark=True, standard_palette=_make_light_standard_palette())

    assert theme.get_system_theme(app) == theme_mod.UiTheme.LIGHT


def test_get_system_theme_ignores_color_scheme_polluted_by_apply_theme(monkeypatch):
    """Regression test for PICARD-2442 follow-up (rdswift report).

    Reproduces: on a light system, select the Dark theme, then switch the
    option back to "Default". The display wrongly stayed dark until restart.

    Root cause: ``apply_theme()`` calls ``setColorScheme()``, which mutates
    what ``QStyleHints.colorScheme()`` subsequently returns. ``get_system_theme()``
    then read that polluted live value back and reported DARK, so
    ``apply_theme(DARK)`` early-returned and nothing switched back to light.

    The fix caches the OS color scheme captured at setup (before any
    ``setColorScheme()`` call) and refreshes it only on genuine OS changes, so
    ``get_system_theme()`` keeps reporting the true OS theme (LIGHT here).
    """

    class _StyleHints:
        """Models real Qt: setColorScheme() changes what colorScheme() returns."""

        colorSchemeChanged = MagicMock()

        def __init__(self, scheme):
            self._scheme = scheme

        def setColorScheme(self, scheme):
            self._scheme = scheme

        def colorScheme(self):
            return self._scheme

    # OS theme is light.
    style_hints = _StyleHints(QtCore.Qt.ColorScheme.Light)
    monkeypatch.setattr(QtGui.QGuiApplication, "styleHints", lambda: style_hints)

    theme = theme_mod.GenericTheme()
    theme._dark_mode_strategies = [lambda: False]

    # Simulate the capture that setup() performs before applying any theme.
    theme._system_color_scheme = style_hints.colorScheme()

    app = _AppWithStyle(live_dark=False, standard_palette=_make_light_standard_palette())

    # User selects Dark: apply_theme() calls setColorScheme(Dark), polluting
    # the live colorScheme() value.
    theme.apply_theme(app, theme_mod.UiTheme.DARK)
    assert style_hints.colorScheme() == QtCore.Qt.ColorScheme.Dark

    # User switches back to Default: get_system_theme() must still report the
    # true OS theme (light), not the polluted Dark value.
    assert theme.get_system_theme(app) == theme_mod.UiTheme.LIGHT


def test_on_color_scheme_changed_refreshes_cached_os_scheme(monkeypatch):
    """A genuine OS color scheme change must update the cached OS scheme.

    Ensures get_system_theme() continues to track the OS after the user
    changes their desktop theme while Picard is running.
    """

    class _StyleHints:
        colorSchemeChanged = MagicMock()

        def __init__(self, scheme):
            self._scheme = scheme

        def setColorScheme(self, scheme):
            self._scheme = scheme

        def colorScheme(self):
            return self._scheme

    style_hints = _StyleHints(QtCore.Qt.ColorScheme.Light)
    monkeypatch.setattr(QtGui.QGuiApplication, "styleHints", lambda: style_hints)

    theme = theme_mod.GenericTheme()
    theme._dark_mode_strategies = [lambda: False]
    theme._system_color_scheme = QtCore.Qt.ColorScheme.Light
    theme._app = _AppWithStyle(live_dark=False, standard_palette=_make_light_standard_palette())

    # OS switches to dark: the signal fires outside of apply_theme().
    theme._applying_theme = False
    theme._on_color_scheme_changed(QtCore.Qt.ColorScheme.Dark)

    assert theme._system_color_scheme == QtCore.Qt.ColorScheme.Dark
    assert theme.get_system_theme(theme._app) == theme_mod.UiTheme.DARK


@pytest.mark.parametrize(
    ("already_dark_theme", "system_theme", "expect_dark_palette"),
    [
        (True, theme_mod.UiTheme.DARK, True),  # System dark: apply dark palette
        (True, theme_mod.UiTheme.LIGHT, False),  # System light: use fresh light palette
        (False, theme_mod.UiTheme.DARK, True),  # System dark: apply dark palette
        (False, theme_mod.UiTheme.LIGHT, False),  # System light: use fresh light palette
    ],
)
def test_linux_dark_theme_palette(monkeypatch, already_dark_theme, system_theme, expect_dark_palette):
    # Simulate Linux (not Windows, not macOS, not Haiku)
    monkeypatch.setattr(theme_mod, "IS_WIN", False)
    monkeypatch.setattr(theme_mod, "IS_MACOS", False)
    monkeypatch.setattr(theme_mod, "IS_HAIKU", False)
    # Set config to SYSTEM
    config_mock = MagicMock()
    config_mock.setting = {"ui_theme": "default"}
    monkeypatch.setattr(theme_mod, "get_config", lambda: config_mock)
    monkeypatch.setattr(theme_mod, "palette_is_dark", lambda palette: not expect_dark_palette)
    # Patch get_system_theme to return dark_mode
    theme = theme_mod.BaseTheme()
    theme.get_system_theme = lambda app: system_theme
    theme.get_system_accent_color = lambda: QtGui.QColor(235, 116, 59)

    # Mock QGuiApplication.styleHints() to return None to force manual fallback
    monkeypatch.setattr(QtGui.QGuiApplication, "styleHints", lambda: None)

    # Mock app and palette
    app = DummyApp(already_dark_theme)
    theme.setup(app)
    palette = app._palette
    if expect_dark_palette:
        assert_palette_matches_expected(palette, EXPECTED_DARK_PALETTE_COLORS)
    else:
        # For light theme, verify the palette is NOT dark.
        base_color = palette.color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Base)
        assert base_color.lightness() >= 128, (
            f"Light theme should produce a light palette, got base lightness {base_color.lightness()}"
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

    monkeypatch.setattr(theme_mod, "IS_WIN", True)
    monkeypatch.setattr(theme_mod, "IS_MACOS", False)
    monkeypatch.setattr(theme_mod, "IS_HAIKU", False)
    monkeypatch.setattr(theme_mod, "palette_is_dark", lambda palette: not expected_dark)

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
    theme.get_system_accent_color = lambda: QtGui.QColor(235, 116, 59)
    # Force manual fallback for palette changes
    monkeypatch.setattr(QtGui.QGuiApplication, "styleHints", lambda: None)
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
        ({"XDG_CURRENT_DESKTOP": "ubuntu:GNOME"}, "gnome"),
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
    ("force_env", "is_macos", "is_haiku", "expected"),
    [
        # No override: Fusion everywhere except macOS and Haiku.
        (None, False, False, True),
        (None, True, False, False),
        (None, False, True, False),
        # Truthy override forces Fusion on every platform.
        ("1", True, False, True),
        ("true", True, False, True),
        ("on", False, True, True),
        # Falsy override keeps the default per-platform behavior.
        ("0", True, False, False),
        ("false", False, False, True),
    ],
)
def test_should_use_fusion_style(force_env, is_macos, is_haiku, expected):
    env = {} if force_env is None else {"PICARD_FORCE_FUSION": force_env}
    with (
        patch.dict(os.environ, env, clear=True),
        patch.object(theme_mod, "IS_MACOS", is_macos),
        patch.object(theme_mod, "IS_HAIKU", is_haiku),
    ):
        assert theme_mod._should_use_fusion_style() is expected
