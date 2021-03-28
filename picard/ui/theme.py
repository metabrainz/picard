# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2020 Philipp Wolfer
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2021 Laurent Monin
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

from collections import namedtuple
from enum import Enum

from PyQt5 import (
    QtCore,
    QtGui,
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
    def is_dark_theme_supported():
        import platform
        try:
            current_version = tuple(map(int, platform.mac_ver()[0].split(".")))[:2]
        except ValueError:
            log.warning("Error while converting the MacOS version string into a tuple: %s" % platform.mac_ver()[0])
            return False

        mojave_version = (10, 14)  # Dark theme support was introduced in Mojave
        return current_version >= mojave_version
    OS_SUPPORTS_THEMES = is_dark_theme_supported()

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

SyntaxTheme = namedtuple('SyntaxTheme', 'func var escape special noop')

light_syntax_theme = SyntaxTheme(
    func=QtGui.QColor(QtCore.Qt.blue),
    var=QtGui.QColor(QtCore.Qt.darkCyan),
    escape=QtGui.QColor(QtCore.Qt.darkRed),
    special=QtGui.QColor(QtCore.Qt.blue),
    noop=QtGui.QColor(QtCore.Qt.darkGray),
)

dark_syntax_theme = SyntaxTheme(
    func=QtGui.QColor(255, 87, 160, 255),  # magenta
    var=QtGui.QColor(252, 187, 81, 255),  # orange
    escape=QtGui.QColor(75, 239, 31, 255),  # green
    special=QtGui.QColor(255, 87, 160, 255),  # blue
    noop=QtGui.QColor(4, 231, 213, 255),  # cyan
)


class BaseTheme:
    def __init__(self):
        self._dark_theme = False
        self._loaded_config_theme = UiTheme.DEFAULT

    def setup(self, app):
        config = get_config()
        self._loaded_config_theme = UiTheme(config.setting['ui_theme'])

        # Use the new fusion style from PyQt5 for a modern and consistent look
        # across all OSes.
        if not IS_MACOS and not IS_HAIKU and self._loaded_config_theme != UiTheme.SYSTEM:
            app.setStyle('Fusion')

        app.setStyleSheet(
            'QGroupBox::title { /* PICARD-1206, Qt bug workaround */ }'
        )

        palette = QtGui.QPalette(app.palette())
        base_color = palette.color(QtGui.QPalette.Active, QtGui.QPalette.Base)
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

    @property
    def syntax_theme(self):
        return dark_syntax_theme if self.is_dark_theme else light_syntax_theme

    # pylint: disable=no-self-use
    def update_palette(self, palette, dark_theme, accent_color):
        if accent_color:
            accent_text_color = QtCore.Qt.white if accent_color.lightness() < 160 else QtCore.Qt.black
            palette.setColor(QtGui.QPalette.Active, QtGui.QPalette.Highlight, accent_color)
            palette.setColor(QtGui.QPalette.Active, QtGui.QPalette.HighlightedText, accent_text_color)

            link_color = QtGui.QColor()
            link_color.setHsl(accent_color.hue(), accent_color.saturation(), 160, accent_color.alpha())
            palette.setColor(QtGui.QPalette.Link, link_color)


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
                log.warning('Failed reading AppsUseLightTheme from registry')
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
                log.warning('Failed reading ColorizationColor from registry')
            return accent_color

        def update_palette(self, palette, dark_theme, accent_color):
            # Adapt to Windows 10 color scheme (dark / light theme and accent color)
            super().update_palette(palette, dark_theme, accent_color)
            if dark_theme:
                palette.setColor(QtGui.QPalette.Window, QtGui.QColor(51, 51, 51))
                palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
                palette.setColor(QtGui.QPalette.Base, QtGui.QColor(31, 31, 31))
                palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(51, 51, 51))
                palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(51, 51, 51))
                palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
                palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
                palette.setColor(QtGui.QPalette.Button, QtGui.QColor(51, 51, 51))
                palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
                palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
                palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, QtCore.Qt.darkGray)
                palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Light, QtGui.QColor(0, 0, 0, 0))
                palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, QtCore.Qt.darkGray)
                palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Base, QtGui.QColor(60, 60, 60))
                palette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Highlight, QtGui.QColor(51, 51, 51))
                palette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.HighlightedText, QtCore.Qt.white)

    theme = WindowsTheme()

elif IS_MACOS:
    try:
        import AppKit
    except ImportError:
        AppKit = None

    dark_appearance = False
    if AppKit:
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
            if dark_theme:
                appearance = AppKit.NSAppearance._darkAquaAppearance()
            else:
                appearance = AppKit.NSAppearance._aquaAppearance()
            AppKit.NSApplication.sharedApplication().setAppearance_(appearance)

        @property
        def is_dark_theme(self):
            dark_theme = False
            if self._loaded_config_theme == UiTheme.DEFAULT:
                dark_theme = dark_appearance
            elif self._loaded_config_theme == UiTheme.DARK:
                dark_theme = True
            return dark_theme

        # pylint: disable=no-self-use
        def update_palette(self, palette, dark_theme, accent_color):
            pass  # No palette changes, theme is fully handled by Qt

    theme = MacTheme()

else:
    theme = BaseTheme()


def setup(app):
    theme.setup(app)
