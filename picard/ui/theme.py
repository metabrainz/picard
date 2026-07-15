# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2022, 2024-2026 Philipp Wolfer
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


from collections.abc import Callable
from enum import Enum
from typing import Literal

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import log
from picard.config import get_config
from picard.const.sys import (
    IS_HAIKU,
    IS_MACOS,
    IS_WIN,
)

from picard.ui.theme_detect import get_linux_dark_mode_strategies


# DRY: Common dark background color
DARK_BG_COLOR = QtGui.QColor(51, 51, 51)

# Centralized dark mode palette for Windows and Linux
DARK_PALETTE_COLORS = {
    QtGui.QPalette.ColorRole.Window: DARK_BG_COLOR,
    QtGui.QPalette.ColorRole.WindowText: QtCore.Qt.GlobalColor.white,
    QtGui.QPalette.ColorRole.Base: QtGui.QColor(31, 31, 31),
    QtGui.QPalette.ColorRole.AlternateBase: DARK_BG_COLOR,
    QtGui.QPalette.ColorRole.ToolTipBase: DARK_BG_COLOR,
    QtGui.QPalette.ColorRole.ToolTipText: QtCore.Qt.GlobalColor.white,
    QtGui.QPalette.ColorRole.Text: QtCore.Qt.GlobalColor.white,
    QtGui.QPalette.ColorRole.Button: DARK_BG_COLOR,
    QtGui.QPalette.ColorRole.ButtonText: QtCore.Qt.GlobalColor.white,
    QtGui.QPalette.ColorRole.BrightText: QtCore.Qt.GlobalColor.red,
    (QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Text): QtCore.Qt.GlobalColor.darkGray,
    (QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Light): QtGui.QColor(0, 0, 0, 0),
    (QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.ButtonText): QtCore.Qt.GlobalColor.darkGray,
    (QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Base): QtGui.QColor(60, 60, 60),
    (QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.Highlight): DARK_BG_COLOR,
    (QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.HighlightedText): QtCore.Qt.GlobalColor.white,
}


OS_SUPPORTS_THEMES = True
AppKit = None
winreg = None
if IS_MACOS:
    try:
        import AppKit  # type: ignore[unresolved-import,no-redef,import-not-found]
    except ImportError:
        pass

    OS_SUPPORTS_THEMES = AppKit is not None and hasattr(AppKit.NSAppearance, '_darkAquaAppearance')

elif IS_HAIKU:
    OS_SUPPORTS_THEMES = False
elif IS_WIN:
    import winreg  # type: ignore[assignment]


# Those are values stored in config file:
class UiTheme(Enum):
    DEFAULT = 'default'
    DARK = 'dark'
    LIGHT = 'light'

    def __str__(self):
        return self.value

    @classmethod
    def _missing_(cls, value):
        return cls.DEFAULT


def get_style_hints() -> QtGui.QStyleHints | None:
    """Get style hints from QGuiApplication, returning None if unavailable."""
    style_hints = QtGui.QGuiApplication.styleHints()
    # setColorScheme was added in Qt 6.8
    if not hasattr(style_hints, 'setColorScheme'):
        return None
    return style_hints


def _style_hints_available() -> bool:
    """Check if style hints are available on the current system."""
    return get_style_hints() is not None


# Theme availability based on platform capabilities
if IS_HAIKU:
    # Haiku doesn't support themes - UI is hidden anyway, but keep empty for consistency
    AVAILABLE_UI_THEMES = []
elif IS_WIN or IS_MACOS or _style_hints_available():
    AVAILABLE_UI_THEMES = [UiTheme.DEFAULT, UiTheme.LIGHT, UiTheme.DARK]
else:
    # Use only default theme on platforms without style hints
    AVAILABLE_UI_THEMES = [UiTheme.DEFAULT]


class MacOverrideStyle(QtWidgets.QProxyStyle):
    """Override the default style to fix some platform specific issues"""

    def styleHint(self, hint, option, widget, returnData):
        # This is disabled on macOS, but prevents collapsing tree view items easily with
        # left arrow key. Enable this consistently on all platforms.
        # See https://tickets.metabrainz.org/browse/PICARD-2417
        # and https://bugreports.qt.io/browse/QTBUG-100305
        if hint == QtWidgets.QStyle.StyleHint.SH_ItemView_ArrowKeysNavigateIntoChildren:
            return True
        return super().styleHint(hint, option, widget, returnData)


def apply_dark_palette_colors(palette: QtGui.QPalette) -> None:
    """Apply dark palette colors to the given palette."""
    for key, value in DARK_PALETTE_COLORS.items():
        if isinstance(key, tuple):
            group, role = key
            palette.setColor(group, role, value)
        else:
            palette.setColor(key, value)


def set_color_scheme(color_scheme: QtCore.Qt.ColorScheme) -> None:
    """Set the color scheme using style hints if available.

    Args:
        color_scheme: The Qt color scheme to set (Qt.ColorScheme enum, Qt 6.5+)
    """
    # ColorScheme was added in Qt 6.5
    if not hasattr(QtCore.Qt, 'ColorScheme'):
        return

    style_hints = get_style_hints()
    if style_hints is not None:
        style_hints.setColorScheme(color_scheme)


def palette_is_dark(palette: QtGui.QPalette) -> bool:
    """Determine if the given palette is dark based on its base color."""
    base_color = palette.color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Base)
    return base_color.lightness() < 128


def apply_dark_theme_to_palette(palette: QtGui.QPalette) -> None:
    """Apply dark theme colors to the given palette.

    The function applies a lightness check on the existing palette's base color. Only
    if the base color appears to be light, dark colors are applied to the palette.

    Args:
        palette: The palette to apply dark colors to
    """
    # Modern Qt should already set dark colors based on the color scheme.
    # But if the current palette color appear to be light, explicitly apply dark
    # colors to the palette.
    if not palette_is_dark(palette):
        apply_dark_palette_colors(palette)


def get_accent_color_from_palette(palette: QtGui.QPalette) -> QtGui.QColor:
    """Returns the accent color from the palette."""
    if hasattr(QtGui.QPalette.ColorRole, 'Accent'):
        accent_color = palette.color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Accent)
    else:
        accent_color = palette.color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Highlight)
    return accent_color


def apply_accent_color_to_palette(palette: QtGui.QPalette, accent_color: QtGui.QColor) -> None:
    """Updates the palette to use the accent color."""
    palette.setColor(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Highlight, accent_color)
    accent_text_color = QtCore.Qt.GlobalColor.white if accent_color.lightness() < 160 else QtCore.Qt.GlobalColor.black
    palette.setColor(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.HighlightedText, accent_text_color)
    # Accent is available since Qt 6.6
    if hasattr(QtGui.QPalette.ColorRole, 'Accent'):
        palette.setColor(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Accent, accent_color)

    link_color = QtGui.QColor()
    link_color.setHsl(accent_color.hue(), accent_color.saturation(), 160, accent_color.alpha())
    palette.setColor(QtGui.QPalette.ColorRole.Link, link_color)


class BaseTheme:
    def __init__(self):
        self._loaded_config_theme: UiTheme = UiTheme.DEFAULT
        self._applied_theme: UiTheme = UiTheme.DEFAULT
        self._accent_color: QtGui.QColor | None = None
        self._dark_mode_strategies: list[Callable[[], bool]] = []

    def setup(self, app: QtWidgets.QApplication) -> None:
        config = get_config()
        wanted_theme = UiTheme(config.setting['ui_theme'])
        self._loaded_config_theme = wanted_theme
        # Use the new fusion style from PyQt6 for a modern and consistent look
        # across all OSes, except for macOS and Haiku.
        if not IS_MACOS and not IS_HAIKU:
            app.setStyle('Fusion')
        elif IS_MACOS:
            app.setStyle(MacOverrideStyle(app.style()))

        app.setStyleSheet(
            'QGroupBox::title { /* PICARD-1206, Qt bug workaround */ }',
        )

        # Apply dark/light theme based on configuration or system settings
        if wanted_theme == UiTheme.DEFAULT:
            wanted_theme = self.get_system_theme(app)
        self.apply_theme(app, wanted_theme)

        # Get the system accent color, if available, and apply if to the palette
        system_accent_color = self.get_system_accent_color()
        if system_accent_color:
            self._accent_color = system_accent_color
            palette = app.palette()
            apply_accent_color_to_palette(palette, self._accent_color)
            app.setPalette(palette)
        else:
            self._accent_color = get_accent_color_from_palette(app.palette())

        if self._accent_color:
            accent_color_str = self._accent_color.name(QtGui.QColor.NameFormat.HexArgb)
        else:
            accent_color_str = "None"

        log.debug(
            "Theme (%s): config=%s applied=%s accent_color=%s",
            self.__class__.__name__,
            self._loaded_config_theme.value,
            self._applied_theme.value,
            accent_color_str,
        )

    def get_system_theme(self, app: QtWidgets.QApplication) -> Literal[UiTheme.DARK, UiTheme.LIGHT]:
        # Iterate through all registered strategies
        for strategy in self._dark_mode_strategies:
            if strategy():
                return UiTheme.DARK

        if palette_is_dark(app.palette()):
            log.debug("No system dark mode detected, but palette is already dark.")
            return UiTheme.DARK

        log.debug("No system dark mode detected, defaulting to light mode.")
        return UiTheme.LIGHT

    def get_system_accent_color(self) -> QtGui.QColor | None:
        return None

    def apply_theme(self, app: QtWidgets.QApplication, theme: UiTheme) -> None:
        qt_color_theme = QtCore.Qt.ColorScheme.Dark if theme == UiTheme.DARK else QtCore.Qt.ColorScheme.Light
        set_color_scheme(qt_color_theme)
        if theme == UiTheme.DARK:
            palette = app.palette()
            apply_dark_theme_to_palette(palette)
            app.setPalette(palette)
        self._applied_theme = theme

    @property
    def is_dark_theme(self) -> bool:
        if self._applied_theme == UiTheme.DARK:
            return True
        else:
            return False

    @property
    def accent_color(self) -> QtGui.QColor | None:  # pylint: disable=no-self-use
        return self._accent_color


class GenericTheme(BaseTheme):
    """Generic theme detection."""

    def __init__(self):
        super().__init__()
        # Registry of dark mode detection strategies for Linux DEs
        self._dark_mode_strategies = get_linux_dark_mode_strategies()


class WindowsTheme(BaseTheme):
    """Windows dark mode theme detection."""

    def get_system_theme(self, app: QtWidgets.QApplication) -> Literal[UiTheme.DARK, UiTheme.LIGHT]:
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            ) as key:
                dark_theme = winreg.QueryValueEx(key, "AppsUseLightTheme")[0] == 0
                return UiTheme.DARK if dark_theme else UiTheme.LIGHT
        except OSError:
            log.warning("Failed reading AppsUseLightTheme from registry")
            return UiTheme.LIGHT

    def get_system_accent_color(self) -> QtGui.QColor | None:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM") as key:
                accent_color_dword = winreg.QueryValueEx(key, "ColorizationColor")[0]
                accent_color_hex = '#{:06x}'.format(accent_color_dword & 0xFFFFFF)
                return QtGui.QColor(accent_color_hex)
        except OSError:
            log.warning("Failed reading ColorizationColor from registry")
            return None


class MacTheme(BaseTheme):
    """macOS dark mode theme detection."""

    def get_system_theme(self, app: QtWidgets.QApplication) -> Literal[UiTheme.DARK, UiTheme.LIGHT]:
        if OS_SUPPORTS_THEMES and AppKit:
            # Default procedure to identify the current appearance (theme)
            appearance = AppKit.NSAppearance.currentAppearance()
            try:
                basic_appearance = appearance.bestMatchFromAppearancesWithNames_(
                    [
                        AppKit.NSAppearanceNameAqua,
                        AppKit.NSAppearanceNameDarkAqua,
                    ]
                )
                dark_appearance = basic_appearance == AppKit.NSAppearanceNameDarkAqua
                return UiTheme.DARK if dark_appearance else UiTheme.LIGHT
            except AttributeError:
                return UiTheme.LIGHT
        else:
            return UiTheme.LIGHT

    def apply_theme(self, app: QtWidgets.QApplication, theme: UiTheme) -> None:
        super().apply_theme(app, theme)

        # MacOS uses a NSAppearance object to change the current application appearance
        # We call this even if UiTheme is the default, preventing MacOS from switching on-the-fly
        if OS_SUPPORTS_THEMES and AppKit:
            try:
                if theme == UiTheme.DARK:
                    appearance = AppKit.NSAppearance._darkAquaAppearance()
                else:
                    appearance = AppKit.NSAppearance._aquaAppearance()
                AppKit.NSApplication.sharedApplication().setAppearance_(appearance)
            except AttributeError:
                pass


if IS_WIN:
    theme = WindowsTheme()
elif IS_MACOS:
    theme = MacTheme()
else:
    theme = GenericTheme()


def setup(app: QtWidgets.QApplication) -> None:
    theme.setup(app)
