# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2022, 2024-2026 Philipp Wolfer
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2021-2026 Laurent Monin
# Copyright (C) 2025 Khoa Nguyen
# Copyright (C) 2025 ripstream
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
from picard.debug_opts import DebugOpt
from picard.env import parse_bool_env

from picard.ui.theme_detect import get_linux_dark_mode_strategies


# DRY: Common dark background color
DARK_BG_COLOR = QtGui.QColor(51, 51, 51)


def _should_use_fusion_style() -> bool:
    """Whether the Qt "Fusion" style should be applied.

    Fusion is used on all platforms except macOS and Haiku, which keep their
    native style. Setting the ``PICARD_FORCE_FUSION`` environment variable to a
    truthy value forces Fusion everywhere (notably useful on macOS).
    """
    if parse_bool_env('PICARD_FORCE_FUSION'):
        return True
    return not IS_MACOS and not IS_HAIKU


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

# Light palette colors matching Fusion's standard light appearance.
# Used as a fallback when setColorScheme does not take effect (e.g., Linux
# without QT_PLATFORM_THEME=gnome) and standardPalette() remains dark.
LIGHT_BG_COLOR = QtGui.QColor(239, 239, 239)

LIGHT_PALETTE_COLORS = {
    QtGui.QPalette.ColorRole.Window: LIGHT_BG_COLOR,
    QtGui.QPalette.ColorRole.WindowText: QtCore.Qt.GlobalColor.black,
    QtGui.QPalette.ColorRole.Base: QtCore.Qt.GlobalColor.white,
    QtGui.QPalette.ColorRole.AlternateBase: LIGHT_BG_COLOR,
    QtGui.QPalette.ColorRole.ToolTipBase: QtGui.QColor(255, 255, 220),
    QtGui.QPalette.ColorRole.ToolTipText: QtCore.Qt.GlobalColor.black,
    QtGui.QPalette.ColorRole.Text: QtCore.Qt.GlobalColor.black,
    QtGui.QPalette.ColorRole.Button: LIGHT_BG_COLOR,
    QtGui.QPalette.ColorRole.ButtonText: QtCore.Qt.GlobalColor.black,
    QtGui.QPalette.ColorRole.BrightText: QtCore.Qt.GlobalColor.red,
    (QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Text): QtCore.Qt.GlobalColor.darkGray,
    (QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.ButtonText): QtCore.Qt.GlobalColor.darkGray,
    (QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Base): LIGHT_BG_COLOR,
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

    @classmethod
    def from_color_scheme(cls, color_scheme: QtCore.Qt.ColorScheme) -> 'UiTheme':
        """Convert a Qt ColorScheme to a UiTheme."""
        return cls.DARK if color_scheme == QtCore.Qt.ColorScheme.Dark else cls.LIGHT

    def to_color_scheme(self) -> QtCore.Qt.ColorScheme:
        """Convert to a Qt ColorScheme."""
        return QtCore.Qt.ColorScheme.Dark if self == UiTheme.DARK else QtCore.Qt.ColorScheme.Light


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

    def styleHint(self, hint, option=None, widget=None, returnData=None):
        # This is disabled on macOS, but prevents collapsing tree view items easily with
        # left arrow key. Enable this consistently on all platforms.
        # See https://tickets.metabrainz.org/browse/PICARD-2417
        # and https://bugreports.qt.io/browse/QTBUG-100305
        if hint == QtWidgets.QStyle.StyleHint.SH_ItemView_ArrowKeysNavigateIntoChildren:
            return True
        return super().styleHint(hint, option, widget, returnData)


def _apply_palette_colors(palette: QtGui.QPalette, colors: dict) -> None:
    """Apply a set of color definitions to the given palette."""
    for key, value in colors.items():
        if isinstance(key, tuple):
            group, role = key
            palette.setColor(group, role, value)
        else:
            palette.setColor(key, value)


def apply_dark_palette_colors(palette: QtGui.QPalette) -> None:
    """Apply dark palette colors to the given palette."""
    _apply_palette_colors(palette, DARK_PALETTE_COLORS)


def apply_light_palette_colors(palette: QtGui.QPalette) -> None:
    """Apply light palette colors to the given palette."""
    _apply_palette_colors(palette, LIGHT_PALETTE_COLORS)


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


def apply_light_theme_to_palette(palette: QtGui.QPalette) -> None:
    """Apply light theme colors to the given palette.

    The function applies a lightness check on the existing palette's base color. Only
    if the base color appears to be dark, light colors are applied to the palette.

    Args:
        palette: The palette to apply light colors to
    """
    # If setColorScheme worked, standardPalette() already returns a light palette.
    # But if it didn't (e.g., Linux without proper platform theme integration),
    # the palette may still be dark. Explicitly apply light colors in that case.
    if palette_is_dark(palette):
        apply_light_palette_colors(palette)


def get_accent_color_from_palette(palette: QtGui.QPalette) -> QtGui.QColor:
    """Returns the accent color from the palette."""
    return palette.color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Highlight)


def apply_accent_color_to_palette(palette: QtGui.QPalette, accent_color: QtGui.QColor) -> None:
    """Updates the palette to use the accent color."""
    palette.setColor(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Highlight, accent_color)
    palette.setColor(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.Highlight, accent_color)
    accent_text_color = QtCore.Qt.GlobalColor.white if accent_color.lightness() < 160 else QtCore.Qt.GlobalColor.black
    palette.setColor(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.HighlightedText, accent_text_color)
    palette.setColor(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.HighlightedText, accent_text_color)
    # Accent is available since Qt 6.6
    if hasattr(QtGui.QPalette.ColorRole, 'Accent'):
        palette.setColor(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Accent, accent_color)
        palette.setColor(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.Accent, accent_color)

    link_color = QtGui.QColor()
    link_color.setHsl(accent_color.hue(), accent_color.saturation(), 160, accent_color.alpha())
    palette.setColor(QtGui.QPalette.ColorRole.Link, link_color)


class BaseTheme(QtCore.QObject):
    # Emitted after a full theme switch (dark↔light). Implies colors also changed.
    theme_changed = QtCore.pyqtSignal()

    # Emitted when interface colors change without a full theme switch.
    colors_changed = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self._loaded_config_theme: UiTheme = UiTheme.DEFAULT
        self._applied_theme: UiTheme = UiTheme.DEFAULT
        self._accent_color: QtGui.QColor | None = None
        self._accent_color_is_system: bool = False
        self._applying_theme: bool = False
        self._dark_mode_strategies: list[Callable[[], bool]] = []
        # The OS color scheme as reported by Qt's style hints, captured at
        # setup *before* Picard ever calls setColorScheme(). Calling
        # setColorScheme() (done by apply_theme) mutates what colorScheme()
        # subsequently returns, so we must not read it back to detect the OS
        # theme once a runtime theme switch happened. Refreshed on genuine OS
        # changes via the colorSchemeChanged signal.
        self._system_color_scheme: QtCore.Qt.ColorScheme | None = None

    def setup(self, app: QtWidgets.QApplication) -> None:
        self._app = app
        config = get_config()
        wanted_theme = UiTheme(config.setting['ui_theme'])
        self._loaded_config_theme = wanted_theme
        # Use the new fusion style from PyQt6 for a modern and consistent look
        # across all OSes, except for macOS and Haiku.
        #
        # The PICARD_FORCE_FUSION environment variable forces the Fusion style
        # on every platform, including macOS and Haiku. This is mainly useful on
        # macOS, where Fusion is otherwise not used; it has no visible effect on
        # platforms that already default to Fusion.
        if _should_use_fusion_style():
            app.setStyle('Fusion')
        elif IS_MACOS:
            app.setStyle(MacOverrideStyle(app.style()))

        app.setStyleSheet(
            'QGroupBox::title { /* PICARD-1206, Qt bug workaround */ }',
        )

        if style_hints := get_style_hints():
            # Capture the OS color scheme now, before apply_theme() calls
            # setColorScheme() below and thereby overwrites what colorScheme()
            # reports. This cached value is what get_system_theme() trusts.
            self._system_color_scheme = style_hints.colorScheme()
            style_hints.colorSchemeChanged.connect(self._on_color_scheme_changed)

        # Determine the system accent color before applying the theme,
        # so apply_theme() can include it in the palette.
        system_accent_color = self.get_system_accent_color()
        if system_accent_color:
            self._accent_color = system_accent_color
            self._accent_color_is_system = True

        # If no system accent color was found, use whatever the palette provides
        if not self._accent_color:
            self._accent_color = get_accent_color_from_palette(app.palette())

        if self._accent_color:
            accent_color_str = self._accent_color.name(QtGui.QColor.NameFormat.HexArgb)
        else:
            accent_color_str = "None"

        # Apply dark/light theme based on configuration or system settings
        if wanted_theme == UiTheme.DEFAULT:
            wanted_theme = self.get_system_theme(app)
        self.apply_theme(app, wanted_theme)

        log.debug(
            "Theme (%s): config=%s applied=%s accent_color=%s",
            self.__class__.__name__,
            self._loaded_config_theme.value,
            self._applied_theme.value,
            accent_color_str,
        )

        if DebugOpt.THEME.enabled:
            self._log_setup_diagnostics(app)

    def _on_color_scheme_changed(self, color_scheme: QtCore.Qt.ColorScheme) -> None:
        if self._applying_theme:
            return
        # This fired outside of our own apply_theme() (Qt delivers the echo
        # from our setColorScheme() synchronously, while _applying_theme is
        # still set, so it is filtered above). Treat it as a genuine OS change
        # and refresh the cached OS scheme so get_system_theme() keeps tracking
        # the operating system.
        self._system_color_scheme = color_scheme
        log.debug_if(
            DebugOpt.THEME,
            "Theme: system colorSchemeChanged signal received: %s",
            color_scheme.name,
        )
        config = get_config()
        wanted_theme = UiTheme(config.setting['ui_theme'])
        if wanted_theme == UiTheme.DEFAULT:
            ui_theme = UiTheme.from_color_scheme(color_scheme)
            if ui_theme != self._applied_theme:
                log.debug_if(
                    DebugOpt.THEME,
                    "Theme: applying system theme change to %s",
                    ui_theme.value,
                )
                self.apply_theme(self._app, ui_theme)

    def _log_setup_diagnostics(self, app: QtWidgets.QApplication) -> None:
        """Log detailed theme diagnostics at startup."""
        palette = app.palette()
        base_color = palette.color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Base)
        highlight_color = palette.color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Highlight)
        window_color = palette.color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Window)
        text_color = palette.color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Text)
        style_hints = get_style_hints()
        color_scheme_supported = style_hints is not None
        app_style = app.style()
        if color_scheme_supported and hasattr(style_hints, 'colorScheme'):
            current_scheme = style_hints.colorScheme().name
        else:
            current_scheme = "N/A"
        log.debug(
            "Theme diagnostics: style=%s platform=%s "
            "color_scheme_supported=%s current_scheme=%s "
            "accent_color_is_system=%s",
            app_style.objectName() if app_style else "None",
            QtGui.QGuiApplication.platformName(),
            color_scheme_supported,
            current_scheme,
            self._accent_color_is_system,
        )
        log.debug(
            "Theme palette: base=%s (lightness=%d) window=%s text=%s highlight=%s",
            base_color.name(),
            base_color.lightness(),
            window_color.name(),
            text_color.name(),
            highlight_color.name(),
        )

    def _log_apply_theme_diagnostics(self, palette: QtGui.QPalette, ui_theme: UiTheme) -> None:
        """Log palette info after theme application."""
        base_color = palette.color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Base)
        highlight_color = palette.color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Highlight)
        log.debug(
            "Theme apply_theme: target=%s base=%s (lightness=%d) highlight=%s",
            ui_theme.value,
            base_color.name(),
            base_color.lightness(),
            highlight_color.name(),
        )

    def get_system_theme(self, app: QtWidgets.QApplication) -> Literal[UiTheme.DARK, UiTheme.LIGHT]:
        # Iterate through all registered strategies
        if any(strategy() for strategy in self._dark_mode_strategies):
            return UiTheme.DARK

        # Use the OS color scheme captured at setup (and refreshed on genuine
        # OS changes via colorSchemeChanged), NOT the live colorScheme().
        # Picard calls setColorScheme() when applying a theme, which overwrites
        # what colorScheme() reports; reading it back here would make us detect
        # the *last applied* theme rather than the operating system's theme.
        # See PICARD-2442: switching Dark -> Default used to stay dark because
        # the live colorScheme() still reported the Dark value Picard had set.
        color_scheme = self._system_color_scheme
        if color_scheme is not None:
            if color_scheme == QtCore.Qt.ColorScheme.Dark:
                log.debug("System color scheme reported as dark.")
                return UiTheme.DARK
            if color_scheme == QtCore.Qt.ColorScheme.Light:
                log.debug("System color scheme reported as light.")
                return UiTheme.LIGHT
            # Unknown/unspecified: fall through to the palette-based heuristic.

        # Fallback for platforms/Qt versions without a usable color scheme hint.
        # Use the style's standard palette rather than the live application
        # palette: app.palette() may have been overridden by a runtime theme
        # switch (e.g. the user selected Dark and then switched back to
        # Default), which would otherwise make us misdetect the system theme.
        style = app.style()
        reference_palette = style.standardPalette() if style else app.palette()
        if palette_is_dark(reference_palette):
            log.debug("No system dark mode detected, but standard palette is dark.")
            return UiTheme.DARK

        log.debug("No system dark mode detected, defaulting to light mode.")
        return UiTheme.LIGHT

    def get_system_accent_color(self) -> QtGui.QColor | None:
        return None

    def apply_theme(self, app: QtWidgets.QApplication, ui_theme: UiTheme) -> None:
        """Apply a theme to the application.

        This method is safe to call multiple times at runtime to switch
        between dark and light themes.  Emits theme_changed after the
        palette has been updated.
        """
        if ui_theme == self._applied_theme:
            return
        self._applying_theme = True
        # setColorScheme tells Qt which color scheme we want. On Linux this
        # is unreliable for native widgets but still needed so that
        # style.standardPalette() returns the correct base palette.
        set_color_scheme(ui_theme.to_color_scheme())
        # Get a fresh base palette from the style (preferred) or create a new one
        style = app.style()
        palette = style.standardPalette() if style else QtGui.QPalette()
        if ui_theme == UiTheme.DARK:
            apply_dark_theme_to_palette(palette)
        else:
            apply_light_theme_to_palette(palette)
        if self._accent_color:
            apply_accent_color_to_palette(palette, self._accent_color)
        app.setPalette(palette)

        if DebugOpt.THEME.enabled:
            self._log_apply_theme_diagnostics(palette, ui_theme)
        # Force all widgets to refresh their style and repaint.
        # Unpolish + polish forces the style to recompute, and update()
        # schedules a repaint. Use QWidget.update() directly to avoid
        # calling overridden update() methods with different signatures.
        if style and hasattr(app, 'allWidgets'):
            for widget in app.allWidgets():
                style.unpolish(widget)
                style.polish(widget)
                QtWidgets.QWidget.update(widget)
        self._applied_theme = ui_theme
        self._applying_theme = False
        self.theme_changed.emit()

    @property
    def is_dark_theme(self) -> bool:
        return self._applied_theme == UiTheme.DARK

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
        assert winreg, "winreg is required on Windows"
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
        assert winreg, "winreg is required on Windows"
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

    def apply_theme(self, app: QtWidgets.QApplication, ui_theme: UiTheme) -> None:
        super().apply_theme(app, ui_theme)

        # MacOS uses a NSAppearance object to change the current application appearance
        # We call this even if UiTheme is the default, preventing MacOS from switching on-the-fly
        if OS_SUPPORTS_THEMES and AppKit:
            try:
                if ui_theme == UiTheme.DARK:
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
