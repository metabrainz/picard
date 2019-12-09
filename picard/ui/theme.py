# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2020 Philipp Wolfer
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

from PyQt5 import (
    QtCore,
    QtGui,
)

from picard import (
    config,
    log,
)
from picard.const.sys import (
    IS_HAIKU,
    IS_MACOS,
    IS_WIN,
)


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

    def setup(self, app):
        # Use the new fusion style from PyQt5 for a modern and consistent look
        # across all OSes.
        if not IS_MACOS and not IS_HAIKU and not config.setting['use_system_theme']:
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
            dark_theme = False
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
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

    class MacTheme(BaseTheme):
        @property
        def is_dark_theme(self):
            if not AppKit:
                return False

            appearance = AppKit.NSAppearance.currentAppearance()
            try:
                basic_appearance = appearance.bestMatchFromAppearancesWithNames_([
                    AppKit.NSAppearanceNameAqua,
                    AppKit.NSAppearanceNameDarkAqua
                ])
                return basic_appearance == AppKit.NSAppearanceNameDarkAqua
            except AttributeError:
                return False

        # pylint: disable=no-self-use
        def update_palette(self, palette, dark_theme, accent_color):
            pass  # No palette changes, theme is fully handled by Qt

    theme = MacTheme()

else:
    theme = BaseTheme()


def setup(app):
    theme.setup(app)
