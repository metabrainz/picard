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

"""Dark mode detection for Linux desktop environments using D-Bus."""

# D-Bus imports - PyQt6 is already a dependency
from PyQt6.QtDBus import (
    QDBusConnection,
    QDBusInterface,
    QDBusMessage,
)


class DBusThemeDetector:
    """D-Bus-based theme detection for Linux desktop environments."""

    def __init__(self):
        self.session_bus = None
        self.portal_interface = None
        self.gnome_interface = None
        self._initialize_dbus()

    def _initialize_dbus(self) -> None:
        """Initialize D-Bus connection and interfaces."""
        try:
            self.session_bus = QDBusConnection.sessionBus()
            if not self.session_bus.isConnected():
                return

            # Only initialize interfaces for available services
            if self._is_service_available("org.freedesktop.portal.Desktop"):
                self.portal_interface = QDBusInterface(
                    "org.freedesktop.portal.Desktop",
                    "/org/freedesktop/portal/desktop",
                    "org.freedesktop.portal.Settings",
                    self.session_bus,
                )

            if self._is_service_available("ca.desrt.dconf"):
                self.gnome_interface = QDBusInterface(
                    "ca.desrt.dconf",
                    "/ca/desrt/dconf/Writer/user",
                    "ca.desrt.dconf.Writer",
                    self.session_bus,
                )

        except Exception:  # noqa: BLE001
            self.session_bus = None
            self.portal_interface = None
            self.gnome_interface = None

    def _is_service_available(self, service_name: str) -> bool:
        """Check if a D-Bus service is available."""
        try:
            if not self.session_bus or not self.session_bus.isConnected():
                return False

            # List all available services and check if our target is there
            interface = QDBusInterface(
                "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", self.session_bus
            )

            reply = interface.call("ListNames")
            if reply.type() == QDBusMessage.MessageType.ErrorMessage:
                return False

            services = reply.arguments()[0] if reply.arguments() else []
        except Exception:
            return False
        else:
            return service_name in services

    def detect_freedesktop_portal_color_scheme(self) -> bool | None:
        """
        Detect color scheme using org.freedesktop.portal.Settings interface.
        Returns
        -------
            True for dark theme, False for light theme, None if unavailable
        """
        try:
            if not self.portal_interface or not self.portal_interface.isValid():
                return None
            # Call the Read method to get color-scheme setting
            reply = self.portal_interface.call("Read", "org.freedesktop.appearance", "color-scheme")

            if reply.type() == QDBusMessage.MessageType.ErrorMessage:
                return None

            # The reply should contain a variant with the color scheme value
            # 0 = no preference, 1 = prefer dark, 2 = prefer light
            value = reply.arguments()[0] if reply.arguments() else None

            if value == 1:
                return True
            if value == 2:
                return False

        except (RuntimeError, AttributeError, TypeError):
            return None
        else:
            return None

    def detect_gnome_color_scheme_dbus(self) -> bool | None:
        """
        Detect GNOME color scheme using D-Bus dconf interface.
        Returns
        -------
            True for dark theme, False for light theme, None if unavailable
        """
        try:
            if not self.gnome_interface or not self.gnome_interface.isValid():
                return None
            # Get the color-scheme property from org.gnome.desktop.interface using dconf
            reply = self.gnome_interface.call("Read", "/org/gnome/desktop/interface/color-scheme")

            if reply.type() != QDBusMessage.MessageType.ErrorMessage:
                value = reply.arguments()[0] if reply.arguments() else None
                if value and isinstance(value, str) and "dark" in value.lower():
                    return True
                if value:
                    return False

        except (RuntimeError, AttributeError, TypeError):
            pass

        # Try gtk-theme as fallback
        try:
            reply = self.gnome_interface.call("Read", "/org/gnome/desktop/interface/gtk-theme")

            if reply.type() != QDBusMessage.MessageType.ErrorMessage:
                value = reply.arguments()[0] if reply.arguments() else None
                if value and isinstance(value, str) and "dark" in value.lower():
                    return True

        except (RuntimeError, AttributeError, TypeError):
            pass

        return None


# Global D-Bus detector instance
_dbus_detector = None


def get_dbus_detector() -> DBusThemeDetector:
    """Get or create the global D-Bus theme detector instance."""
    global _dbus_detector
    if _dbus_detector is None:
        _dbus_detector = DBusThemeDetector()
    return _dbus_detector


def detect_freedesktop_color_scheme_dbus() -> bool:
    """Detect dark mode using D-Bus freedesktop.org portal interface."""
    try:
        detector = get_dbus_detector()
        result = detector.detect_freedesktop_portal_color_scheme()
    except (RuntimeError, AttributeError, TypeError):
        return False
    else:
        return result is True


def detect_gnome_color_scheme_dbus() -> bool:
    """Detect GNOME color scheme using D-Bus interface."""
    try:
        detector = get_dbus_detector()
        result = detector.detect_gnome_color_scheme_dbus()
    except (RuntimeError, AttributeError, TypeError):
        return False
    else:
        return result is True
