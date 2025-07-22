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

from pathlib import Path
import subprocess

from picard import log


def gsettings_get(key: str) -> str | None:
    """Helper to get a gsettings value. Returns string or None."""
    try:
        result = subprocess.run(
            [
                'gsettings', 'get', 'org.gnome.desktop.interface', key,
            ], capture_output=True, text=True, check=True,
        )
        return result.stdout.strip().strip("'\"")
    except (subprocess.CalledProcessError, FileNotFoundError):
        log.debug(f"gsettings get {key} failed.")
        return None

def detect_gnome_color_scheme_dark() -> bool:
    value = gsettings_get('color-scheme')
    if value and 'dark' in value.lower():
        log.debug("Detected GNOME color-scheme: dark")
        return True
    return False

def detect_gnome_gtk_theme_dark() -> bool:
    theme = gsettings_get('gtk-theme')
    if theme and 'dark' in theme.lower():
        log.debug(f"Detected GNOME gtk-theme: {theme} (dark)")
        return True
    return False

def detect_kde_colorscheme_dark() -> bool:
    kdeglobals = Path.home() / ".config" / "kdeglobals"
    if kdeglobals.exists():
        try:
            with open(kdeglobals, 'r') as f:
                for line in f:
                    if line.strip().startswith("ColorScheme="):
                        scheme = line.split('=', 1)[1].strip().lower()
                        if 'dark' in scheme:
                            log.debug(f"Detected KDE ColorScheme: {scheme} (dark)")
                            return True
        except OSError as e:
            log.debug(f"KDE ColorScheme detection failed: {e}")
    return False

def detect_xfce_dark_theme() -> bool:
    try:
        result = subprocess.run(
            [
                'xfconf-query', '-c', 'xsettings', '-p', '/Net/ThemeName',
            ], capture_output=True, text=True, check=True,
        )
        theme = result.stdout.strip().lower()
        if 'dark' in theme:
            log.debug(f"Detected XFCE theme: {theme} (dark)")
            return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        log.debug("xfconf-query detection failed.")
    return False

def detect_lxqt_dark_theme() -> bool:
    lxqt_conf = Path.home() / ".config" / "lxqt" / "session.conf"
    if lxqt_conf.exists():
        try:
            with open(lxqt_conf, 'r') as f:
                for line in f:
                    if line.strip().startswith("theme="):
                        theme = line.split('=', 1)[1].strip().lower()
                        if 'dark' in theme:
                            log.debug(f"Detected LXQt theme: {theme} (dark)")
                            return True
        except OSError as e:
            log.debug(f"LXQt theme detection failed: {e}")
    return False

def get_linux_dark_mode_strategies() -> list:
    """Return the list of dark mode detection strategies in order of priority."""
    return [
        detect_gnome_color_scheme_dark,
        detect_gnome_gtk_theme_dark,
        detect_kde_colorscheme_dark,
        detect_xfce_dark_theme,
        detect_lxqt_dark_theme,
    ]
