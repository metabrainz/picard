# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2022, 2024 Philipp Wolfer
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


from enum import Enum

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


OS_SUPPORTS_THEMES = True
if IS_MACOS:
    try:
        import AppKit
    except ImportError:
        AppKit = None

    OS_SUPPORTS_THEMES = bool(AppKit) and hasattr(AppKit.NSAppearance, '_darkAquaAppearance')

elif IS_HAIKU:
    OS_SUPPORTS_THEMES = False


# Those are values stored in config file:
class UiTheme(Enum):
    DEFAULT = 'default'
    DARK = 'dark'
    LIGHT = 'light'
    SYSTEM = 'system'

    def __str__(self):
        return self.value

    @classmethod
    def _missing_(cls, value):
        return cls.DEFAULT


AVAILABLE_UI_THEMES = [UiTheme.DEFAULT]
if IS_WIN or IS_MACOS:
    AVAILABLE_UI_THEMES.extend([UiTheme.LIGHT, UiTheme.DARK])
elif not IS_HAIKU:
    AVAILABLE_UI_THEMES.extend([UiTheme.SYSTEM])


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


class BaseTheme:
    def __init__(self):
        self._dark_theme = False
        self._loaded_config_theme = UiTheme.DEFAULT

    def setup(self, app):
        config = get_config()
        self._loaded_config_theme = UiTheme(config.setting['ui_theme'])

        # Use the new fusion style from PyQt6 for a modern and consistent look
        # across all OSes.
        if not IS_MACOS and not IS_HAIKU and self._loaded_config_theme != UiTheme.SYSTEM:
            app.setStyle('Fusion')
        elif IS_MACOS:
            app.setStyle(MacOverrideStyle(app.style()))

        app.setStyleSheet(
            'QGroupBox::title { /* PICARD-1206, Qt bug workaround */ }'
        )

        palette = QtGui.QPalette(app.palette())
        base_color = palette.color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Base)
        self._dark_theme = base_color.lightness() < 128
        self.update_palette(palette, self.is_dark_theme, self.accent_color)
        app.setPalette(palette)

    @property
    def is_dark_theme(self):
        if self._loaded_config_theme == UiTheme.DARK:
            return True
        elif self._loaded_config_theme == UiTheme.LIGHT:
            return False
        else:
            return self._dark_theme

    @property
    def accent_color(self):  # pylint: disable=no-self-use
        return None

    # pylint: disable=no-self-use
    def update_palette(self, palette, dark_theme, accent_color):
        if accent_color:
            accent_text_color = QtCore.Qt.GlobalColor.white if accent_color.lightness() < 160 else QtCore.Qt.GlobalColor.black
            palette.setColor(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Highlight, accent_color)
            palette.setColor(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.HighlightedText, accent_text_color)

            link_color = QtGui.QColor()
            link_color.setHsl(accent_color.hue(), accent_color.saturation(), 160, accent_color.alpha())
            palette.setColor(QtGui.QPalette.ColorRole.Link, link_color)


if IS_WIN:
    import winreg

    class WindowsTheme(BaseTheme):
        def setup(self, app):
            app.setStyle('Fusion')
            super().setup(app)

        @property
        def is_dark_theme(self):
            if self._loaded_config_theme != UiTheme.DEFAULT:
                return self._loaded_config_theme == UiTheme.DARK
            dark_theme = False
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
                    dark_theme = winreg.QueryValueEx(key, "AppsUseLightTheme")[0] == 0
            except OSError:
                log.warning("Failed reading AppsUseLightTheme from registry")
            return dark_theme

        @property
        def accent_color(self):
            accent_color = None
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM") as key:
                    accent_color_dword = winreg.QueryValueEx(key, "ColorizationColor")[0]
                    accent_color_hex = '#{:06x}'.format(accent_color_dword & 0xffffff)
                    accent_color = QtGui.QColor(accent_color_hex)
            except OSError:
                log.warning("Failed reading ColorizationColor from registry")
            return accent_color

        def update_palette(self, palette, dark_theme, accent_color):
            # Adapt to Windows 10 color scheme (dark / light theme and accent color)
            super().update_palette(palette, dark_theme, accent_color)
            if dark_theme:
                palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(51, 51, 51))
                palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtCore.Qt.GlobalColor.white)
                palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(31, 31, 31))
                palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(51, 51, 51))
                palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase, QtGui.QColor(51, 51, 51))
                palette.setColor(QtGui.QPalette.ColorRole.ToolTipText, QtCore.Qt.GlobalColor.white)
                palette.setColor(QtGui.QPalette.ColorRole.Text, QtCore.Qt.GlobalColor.white)
                palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(51, 51, 51))
                palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtCore.Qt.GlobalColor.white)
                palette.setColor(QtGui.QPalette.ColorRole.BrightText, QtCore.Qt.GlobalColor.red)
                palette.setColor(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Text, QtCore.Qt.GlobalColor.darkGray)
                palette.setColor(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Light, QtGui.QColor(0, 0, 0, 0))
                palette.setColor(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.ButtonText, QtCore.Qt.GlobalColor.darkGray)
                palette.setColor(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Base, QtGui.QColor(60, 60, 60))
                palette.setColor(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(51, 51, 51))
                palette.setColor(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.HighlightedText, QtCore.Qt.GlobalColor.white)

    theme = WindowsTheme()

elif IS_MACOS:
    dark_appearance = False
    if OS_SUPPORTS_THEMES and AppKit:
        # Default procedure to identify the current appearance (theme)
        appearance = AppKit.NSAppearance.currentAppearance()
        try:
            basic_appearance = appearance.bestMatchFromAppearancesWithNames_([
                AppKit.NSAppearanceNameAqua,
                AppKit.NSAppearanceNameDarkAqua
            ])
            dark_appearance = basic_appearance == AppKit.NSAppearanceNameDarkAqua
        except AttributeError:
            pass

    class MacTheme(BaseTheme):
        def setup(self, app):
            super().setup(app)

            if self._loaded_config_theme != UiTheme.DEFAULT:
                dark_theme = self._loaded_config_theme == UiTheme.DARK
            else:
                dark_theme = dark_appearance

            # MacOS uses a NSAppearance object to change the current application appearance
            # We call this even if UiTheme is the default, preventing MacOS from switching on-the-fly
            if OS_SUPPORTS_THEMES and AppKit:
                try:
                    if dark_theme:
                        appearance = AppKit.NSAppearance._darkAquaAppearance()
                    else:
                        appearance = AppKit.NSAppearance._aquaAppearance()
                    AppKit.NSApplication.sharedApplication().setAppearance_(appearance)
                except AttributeError:
                    pass

        @property
        def is_dark_theme(self):
            if not OS_SUPPORTS_THEMES:
                # Fall back to generic dark color palette detection
                return super().is_dark_theme
            elif self._loaded_config_theme == UiTheme.DEFAULT:
                return dark_appearance
            else:
                return self._loaded_config_theme == UiTheme.DARK

        # pylint: disable=no-self-use
        def update_palette(self, palette, dark_theme, accent_color):
            pass  # No palette changes, theme is fully handled by Qt

    theme = MacTheme()

else:
    theme = BaseTheme()


def setup(app):
    theme.setup(app)
