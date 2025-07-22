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

"""Dark mode detection utilities for various Linux desktop environments."""

import os
import subprocess  # noqa: S404
from pathlib import Path

from picard import log


def gsettings_get(key: str) -> str | None:
    """Get a gsettings value as a string or None."""
    try:
        result = subprocess.run(
            [
                "gsettings",
                "get",
                "org.gnome.desktop.interface",
                key,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip().strip("'\"")
    except (subprocess.CalledProcessError, FileNotFoundError):
        log.debug(f"gsettings get {key} failed.")
        return None


def detect_gnome_color_scheme_dark() -> bool:
    """Detect if GNOME color-scheme is set to dark."""
    value = gsettings_get("color-scheme")
    if value and "dark" in value.lower():
        log.debug("Detected GNOME color-scheme: dark")
        return True
    return False


def detect_gnome_gtk_theme_dark() -> bool:
    """Detect if GNOME gtk-theme is set to dark."""
    theme = gsettings_get("gtk-theme")
    if theme and "dark" in theme.lower():
        log.debug(f"Detected GNOME gtk-theme: {theme} (dark)")
        return True
    return False


def detect_kde_colorscheme_dark() -> bool:
    """Detect if KDE ColorScheme is set to dark."""
    kdeglobals = Path.home() / ".config" / "kdeglobals"
    if kdeglobals.exists():
        try:
            with kdeglobals.open() as f:
                for line in f:
                    if line.strip().startswith("ColorScheme="):
                        scheme = line.split("=", 1)[1].strip().lower()
                        if "dark" in scheme:
                            log.debug(f"Detected KDE ColorScheme: {scheme} (dark)")
                            return True
        except OSError as e:
            log.debug(f"KDE ColorScheme detection failed: {e}")
    return False


def detect_xfce_dark_theme() -> bool:
    """Detect if XFCE theme is set to dark."""
    try:
        result = subprocess.run(  # nosec B603 B607
            [
                "xfconf-query",
                "-c",
                "xsettings",
                "-p",
                "/Net/ThemeName",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        theme = result.stdout.strip().lower()
        if "dark" in theme:
            log.debug(f"Detected XFCE theme: {theme} (dark)")
            return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        log.debug("xfconf-query detection failed.")
    return False


def detect_lxqt_dark_theme() -> bool:
    """Detect if LXQt theme is set to dark."""
    lxqt_conf = Path.home() / ".config" / "lxqt" / "session.conf"
    if lxqt_conf.exists():
        try:
            with lxqt_conf.open() as f:
                for line in f:
                    if line.strip().startswith("theme="):
                        theme = line.split("=", 1)[1].strip().lower()
                        if "dark" in theme:
                            log.debug(f"Detected LXQt theme: {theme} (dark)")
                            return True
        except OSError as e:
            log.debug(f"LXQt theme detection failed: {e}")
    return False


def detect_freedesktop_color_scheme_dark() -> bool:
    """Detect dark mode using org.freedesktop.appearance.color-scheme (XDG portal, cross-desktop)."""
    value = gsettings_get("color-scheme")
    # Try org.freedesktop.appearance first
    try:
        result = subprocess.run(  # nosec B603 B607
            [
                "gsettings",
                "get",
                "org.freedesktop.appearance",
                "color-scheme",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        value = result.stdout.strip().strip("'\"")
        if value == "1":
            log.debug("Detected org.freedesktop.appearance.color-scheme: dark (1)")
            return True
        if value == "0":
            log.debug("Detected org.freedesktop.appearance.color-scheme: light (0)")
            return False
    except (subprocess.CalledProcessError, FileNotFoundError):
        log.debug("gsettings get org.freedesktop.appearance.color-scheme failed.")
    return False


def get_current_desktop_environment() -> str:
    """Detect the current desktop environment (DE) as a lowercase string."""
    de = os.environ.get("XDG_CURRENT_DESKTOP")
    if de:
        return de.lower()
    # Fallbacks for KDE, XFCE, LXQt
    if os.environ.get("KDE_FULL_SESSION") == "true":
        return "kde"
    if os.environ.get("XDG_SESSION_DESKTOP"):
        return os.environ["XDG_SESSION_DESKTOP"].lower()
    if os.environ.get("DESKTOP_SESSION"):
        return os.environ["DESKTOP_SESSION"].lower()
    return ""


# Wrappers for DE-specific detection


def detect_gnome_dark_wrapper() -> bool:
    """Detect dark mode for GNOME or Unity desktop environments."""
    if get_current_desktop_environment() in {"gnome", "unity"}:
        return detect_gnome_color_scheme_dark() or detect_gnome_gtk_theme_dark()
    return False


def detect_kde_dark_wrapper() -> bool:
    """Detect dark mode for KDE desktop environment."""
    if get_current_desktop_environment() == "kde":
        return detect_kde_colorscheme_dark()
    return False


def detect_xfce_dark_wrapper() -> bool:
    """Detect dark mode for XFCE desktop environment."""
    if get_current_desktop_environment() == "xfce":
        return detect_xfce_dark_theme()
    return False


def detect_lxqt_dark_wrapper() -> bool:
    """Detect dark mode for LXQt desktop environment."""
    if get_current_desktop_environment() == "lxqt":
        return detect_lxqt_dark_theme()
    return False


def get_linux_dark_mode_strategies() -> list:
    """Return the list of dark mode detection strategies in order of priority."""
    return [
        detect_freedesktop_color_scheme_dark,
        detect_gnome_dark_wrapper,
        detect_kde_dark_wrapper,
        detect_xfce_dark_wrapper,
        detect_lxqt_dark_wrapper,
    ]
