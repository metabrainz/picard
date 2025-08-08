# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024-2025 Philipp Wolfer
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

"""Unit tests for theme detection using D-Bus."""

from unittest.mock import (
    Mock,
    patch,
)

from PyQt6.QtDBus import QDBusMessage

import pytest

from picard.ui.theme_detect_qtdbus import (
    DBusThemeDetector,
    detect_freedesktop_color_scheme_dbus,
    detect_gnome_color_scheme_dbus,
    get_dbus_detector,
)


@pytest.fixture
def mock_dbus_connection() -> Mock:
    """Create a mock D-Bus connection."""
    mock_connection = Mock()
    mock_connection.isConnected.return_value = True
    return mock_connection


@pytest.fixture
def mock_portal_interface() -> Mock:
    """Create a mock freedesktop portal interface."""
    mock_interface = Mock()
    mock_interface.isValid.return_value = True
    return mock_interface


@pytest.fixture
def mock_gnome_interface() -> Mock:
    """Create a mock GNOME dconf interface."""
    mock_interface = Mock()
    mock_interface.isValid.return_value = True
    return mock_interface


@pytest.fixture
def mock_dbus_detector(
    mock_dbus_connection: Mock,
    mock_portal_interface: Mock,
    mock_gnome_interface: Mock,
) -> DBusThemeDetector:
    """Create a DBusThemeDetector with mocked D-Bus components."""
    with (
        patch("picard.ui.theme_detect_qtdbus.QDBusConnection") as mock_qdbus_connection,
        patch("picard.ui.theme_detect_qtdbus.QDBusInterface") as mock_qdbus_interface,
    ):
        mock_qdbus_connection.sessionBus.return_value = mock_dbus_connection

        # Configure QDBusInterface to return different mocks for different calls
        def qdbus_interface_side_effect(*args, **kwargs):
            if "org.freedesktop.portal.Settings" in args:
                return mock_portal_interface
            elif "ca.desrt.dconf.Writer" in args:
                return mock_gnome_interface
            elif "org.freedesktop.DBus" in args:
                # Mock for service availability checking
                mock_db_interface = Mock()
                mock_db_message = Mock()
                mock_db_message.type.return_value = QDBusMessage.MessageType.ReplyMessage
                mock_db_message.arguments.return_value = [["org.freedesktop.portal.Desktop", "ca.desrt.dconf"]]
                mock_db_interface.call.return_value = mock_db_message
                return mock_db_interface
            return Mock()

        mock_qdbus_interface.side_effect = qdbus_interface_side_effect

        detector = DBusThemeDetector()
        return detector


@pytest.fixture
def mock_dbus_message() -> Mock:
    """Create a mock D-Bus message."""
    mock_message = Mock()
    mock_message.type.return_value = QDBusMessage.MessageType.ReplyMessage
    mock_message.arguments.return_value = []
    return mock_message


class TestDBusThemeDetector:
    """Test the DBusThemeDetector class."""

    @pytest.mark.parametrize(
        ("connection_connected", "expected_session_bus"),
        [
            (True, Mock()),
            (False, None),
        ],
    )
    def test_initialize_dbus_success(
        self,
        connection_connected: bool,
        expected_session_bus: Mock | None,
    ) -> None:
        """Test successful D-Bus initialization."""
        with (
            patch("picard.ui.theme_detect_qtdbus.QDBusConnection") as mock_qdbus_connection,
            patch("picard.ui.theme_detect_qtdbus.QDBusInterface") as mock_qdbus_interface,
        ):
            mock_connection = Mock()
            mock_connection.isConnected.return_value = connection_connected
            mock_qdbus_connection.sessionBus.return_value = mock_connection

            # Mock service availability checking
            mock_db_interface = Mock()
            mock_db_message = Mock()
            mock_db_message.type.return_value = QDBusMessage.MessageType.ReplyMessage
            mock_db_message.arguments.return_value = [["org.freedesktop.portal.Desktop", "ca.desrt.dconf"]]
            mock_db_interface.call.return_value = mock_db_message

            # Configure QDBusInterface to return different mocks for different calls
            def qdbus_interface_side_effect(*args, **kwargs):
                if "org.freedesktop.DBus" in args:
                    return mock_db_interface
                return Mock()

            mock_qdbus_interface.side_effect = qdbus_interface_side_effect

            detector = DBusThemeDetector()

            if connection_connected:
                assert detector.session_bus is not None
                assert detector.portal_interface is not None
                assert detector.gnome_interface is not None
            else:
                # When connection is not connected, the session_bus is still set but interfaces are None
                assert detector.session_bus is not None
                assert detector.portal_interface is None
                assert detector.gnome_interface is None

    def test_initialize_dbus_exception(self) -> None:
        """Test D-Bus initialization with exception."""
        with patch("picard.ui.theme_detect_qtdbus.QDBusConnection") as mock_qdbus_connection:
            # Make sessionBus() raise an exception
            mock_qdbus_connection.sessionBus.side_effect = Exception("DBus error")

            detector = DBusThemeDetector()

            # When an exception occurs during initialization, all interfaces should be None
            assert detector.session_bus is None
            assert detector.portal_interface is None
            assert detector.gnome_interface is None

    @pytest.mark.parametrize(
        ("portal_valid", "message_type", "arguments", "expected"),
        [
            (True, QDBusMessage.MessageType.ReplyMessage, [1], True),  # Dark theme
            (True, QDBusMessage.MessageType.ReplyMessage, [2], False),  # Light theme
            (True, QDBusMessage.MessageType.ReplyMessage, [0], None),  # No preference
            (True, QDBusMessage.MessageType.ReplyMessage, [], None),  # No arguments
            (True, QDBusMessage.MessageType.ErrorMessage, [1], None),  # Error message
            (False, QDBusMessage.MessageType.ReplyMessage, [1], None),  # Invalid interface
        ],
    )
    def test_detect_freedesktop_portal_color_scheme(
        self,
        portal_valid: bool,
        message_type: QDBusMessage.MessageType,
        arguments: list[int],
        expected: bool | None,
        mock_dbus_detector: DBusThemeDetector,
        mock_portal_interface: Mock,
        mock_dbus_message: Mock,
    ) -> None:
        """Test freedesktop portal color scheme detection."""
        # Mock service availability to return True for portal service
        with patch.object(mock_dbus_detector, '_is_service_available', return_value=True):
            mock_portal_interface.isValid.return_value = portal_valid
            mock_dbus_message.type.return_value = message_type
            mock_dbus_message.arguments.return_value = arguments
            mock_portal_interface.call.return_value = mock_dbus_message

            result = mock_dbus_detector.freedesktop_portal_color_scheme_is_dark()
            assert result == expected

    @pytest.mark.parametrize(
        ("exception_type",),
        [
            (RuntimeError,),
            (AttributeError,),
            (TypeError,),
        ],
    )
    def test_detect_freedesktop_portal_color_scheme_exception(
        self,
        exception_type: type[Exception],
        mock_dbus_detector: DBusThemeDetector,
        mock_portal_interface: Mock,
    ) -> None:
        """Test freedesktop portal color scheme detection with exceptions."""
        mock_portal_interface.call.side_effect = exception_type("Test exception")

        result = mock_dbus_detector.freedesktop_portal_color_scheme_is_dark()
        assert result is None

    @pytest.mark.parametrize(
        (
            "gnome_valid",
            "color_scheme_message_type",
            "color_scheme_args",
            "gtk_theme_message_type",
            "gtk_theme_args",
            "expected",
        ),
        [
            # Color scheme tests - when color scheme returns a valid response
            (True, QDBusMessage.MessageType.ReplyMessage, ["dark"], QDBusMessage.MessageType.ErrorMessage, [], True),
            (True, QDBusMessage.MessageType.ReplyMessage, ["light"], QDBusMessage.MessageType.ErrorMessage, [], False),
            (
                True,
                QDBusMessage.MessageType.ReplyMessage,
                ["default"],
                QDBusMessage.MessageType.ErrorMessage,
                [],
                False,
            ),
            # Color scheme fails, fallback to gtk theme
            (
                True,
                QDBusMessage.MessageType.ErrorMessage,
                [],
                QDBusMessage.MessageType.ReplyMessage,
                ["Adwaita-dark"],
                True,
            ),
            (True, QDBusMessage.MessageType.ErrorMessage, [], QDBusMessage.MessageType.ReplyMessage, ["Adwaita"], None),
            (True, QDBusMessage.MessageType.ErrorMessage, [], QDBusMessage.MessageType.ReplyMessage, ["default"], None),
            # Invalid interface
            (False, QDBusMessage.MessageType.ReplyMessage, ["dark"], QDBusMessage.MessageType.ErrorMessage, [], None),
        ],
    )
    def test_detect_gnome_color_scheme_dbus(
        self,
        gnome_valid: bool,
        color_scheme_message_type: QDBusMessage.MessageType,
        color_scheme_args: list[str],
        gtk_theme_message_type: QDBusMessage.MessageType,
        gtk_theme_args: list[str],
        expected: bool | None,
        mock_dbus_detector: DBusThemeDetector,
        mock_gnome_interface: Mock,
    ) -> None:
        """Test GNOME color scheme detection via D-Bus."""
        # Mock service availability to return True for GNOME service
        with patch.object(mock_dbus_detector, '_is_service_available', return_value=True):
            mock_gnome_interface.isValid.return_value = gnome_valid

            # Create mock messages for color scheme and gtk theme calls
            color_scheme_message = Mock()
            color_scheme_message.type.return_value = color_scheme_message_type
            color_scheme_message.arguments.return_value = color_scheme_args

            gtk_theme_message = Mock()
            gtk_theme_message.type.return_value = gtk_theme_message_type
            gtk_theme_message.arguments.return_value = gtk_theme_args

            # Configure the call method to return different messages based on the argument
            def call_side_effect(method: str, *args: str) -> Mock:
                if "color-scheme" in args[0]:
                    return color_scheme_message
                else:
                    return gtk_theme_message

            mock_gnome_interface.call.side_effect = call_side_effect

            result = mock_dbus_detector.gnome_color_scheme_is_dark()
            assert result == expected

    @pytest.mark.parametrize(
        ("exception_type",),
        [
            (RuntimeError,),
            (AttributeError,),
            (TypeError,),
        ],
    )
    def test_detect_gnome_color_scheme_dbus_exception(
        self,
        exception_type: type[Exception],
        mock_dbus_detector: DBusThemeDetector,
        mock_gnome_interface: Mock,
    ) -> None:
        """Test GNOME color scheme detection with exceptions."""
        mock_gnome_interface.call.side_effect = exception_type("Test exception")

        result = mock_dbus_detector.gnome_color_scheme_is_dark()
        assert result is None

    @pytest.mark.parametrize(
        ("portal_service_available", "gnome_service_available", "expected_portal", "expected_gnome"),
        [
            (True, True, True, True),  # Both services available
            (True, False, True, False),  # Only portal available
            (False, True, False, True),  # Only GNOME available
            (False, False, False, False),  # Neither service available
        ],
    )
    def test_detection_with_service_availability(
        self,
        portal_service_available: bool,
        gnome_service_available: bool,
        expected_portal: bool,
        expected_gnome: bool,
    ) -> None:
        """Test detection methods when services are not available."""
        with (
            patch("picard.ui.theme_detect_qtdbus.QDBusConnection") as mock_qdbus_connection,
            patch("picard.ui.theme_detect_qtdbus.QDBusInterface") as mock_qdbus_interface,
        ):
            mock_connection = Mock()
            mock_connection.isConnected.return_value = True
            mock_qdbus_connection.sessionBus.return_value = mock_connection

            # Mock service availability checking
            def service_availability_side_effect(service_name: str) -> bool:
                if "portal" in service_name:
                    return portal_service_available
                elif "dconf" in service_name:
                    return gnome_service_available
                return False

            # Mock the D-Bus interface for service listing
            mock_db_interface = Mock()
            mock_db_message = Mock()
            mock_db_message.type.return_value = QDBusMessage.MessageType.ReplyMessage
            mock_db_message.arguments.return_value = [["org.freedesktop.portal.Desktop", "ca.desrt.dconf"]]
            mock_db_interface.call.return_value = mock_db_message

            # Configure QDBusInterface to return different mocks for different calls
            def qdbus_interface_side_effect(*args, **kwargs):
                if "org.freedesktop.DBus" in args:
                    return mock_db_interface
                elif "org.freedesktop.portal.Settings" in args:
                    mock_portal = Mock()
                    mock_portal.isValid.return_value = True
                    mock_portal_message = Mock()
                    mock_portal_message.type.return_value = QDBusMessage.MessageType.ReplyMessage
                    mock_portal_message.arguments.return_value = [1]  # Dark theme
                    mock_portal.call.return_value = mock_portal_message
                    return mock_portal
                elif "ca.desrt.dconf.Writer" in args:
                    mock_gnome = Mock()
                    mock_gnome.isValid.return_value = True
                    mock_gnome_message = Mock()
                    mock_gnome_message.type.return_value = QDBusMessage.MessageType.ReplyMessage
                    mock_gnome_message.arguments.return_value = ["dark"]
                    mock_gnome.call.return_value = mock_gnome_message
                    return mock_gnome
                return Mock()

            mock_qdbus_interface.side_effect = qdbus_interface_side_effect

            # Create detector with mocked service availability
            with patch.object(DBusThemeDetector, '_is_service_available', side_effect=service_availability_side_effect):
                detector = DBusThemeDetector()

                # Test portal detection
                portal_result = detector.freedesktop_portal_color_scheme_is_dark()
                assert portal_result == (True if expected_portal else None)

                # Test GNOME detection
                gnome_result = detector.gnome_color_scheme_is_dark()
                assert gnome_result == (True if expected_gnome else None)


class TestServiceAvailability:
    """Test the _is_service_available method."""

    @pytest.mark.parametrize(
        ("service_name", "available_services", "expected"),
        [
            ("org.freedesktop.portal.Desktop", ["org.freedesktop.portal.Desktop", "ca.desrt.dconf"], True),
            ("ca.desrt.dconf", ["org.freedesktop.portal.Desktop", "ca.desrt.dconf"], True),
            ("org.freedesktop.portal.Desktop", ["ca.desrt.dconf"], False),
            ("ca.desrt.dconf", ["org.freedesktop.portal.Desktop"], False),
            ("org.freedesktop.portal.Desktop", [], False),
        ],
    )
    def test_is_service_available(
        self,
        service_name: str,
        available_services: list[str],
        expected: bool,
    ) -> None:
        """Test service availability detection."""
        with (
            patch("picard.ui.theme_detect_qtdbus.QDBusConnection") as mock_qdbus_connection,
            patch("picard.ui.theme_detect_qtdbus.QDBusInterface") as mock_qdbus_interface,
        ):
            mock_connection = Mock()
            mock_connection.isConnected.return_value = True
            mock_qdbus_connection.sessionBus.return_value = mock_connection

            # Mock the D-Bus interface for service listing
            mock_db_interface = Mock()
            mock_db_message = Mock()
            mock_db_message.type.return_value = QDBusMessage.MessageType.ReplyMessage
            mock_db_message.arguments.return_value = [available_services]
            mock_db_interface.call.return_value = mock_db_message

            def qdbus_interface_side_effect(*args, **kwargs):
                if "org.freedesktop.DBus" in args:
                    return mock_db_interface
                return Mock()

            mock_qdbus_interface.side_effect = qdbus_interface_side_effect

            detector = DBusThemeDetector()
            result = detector._is_service_available(service_name)
            assert result == expected

    @pytest.mark.parametrize(
        ("connection_connected", "expected"),
        [
            (True, True),
            (False, False),
        ],
    )
    def test_is_service_available_connection_check(
        self,
        connection_connected: bool,
        expected: bool,
    ) -> None:
        """Test service availability when D-Bus connection is not available."""
        with (
            patch("picard.ui.theme_detect_qtdbus.QDBusConnection") as mock_qdbus_connection,
            patch("picard.ui.theme_detect_qtdbus.QDBusInterface") as mock_qdbus_interface,
        ):
            mock_connection = Mock()
            mock_connection.isConnected.return_value = connection_connected
            mock_qdbus_connection.sessionBus.return_value = mock_connection

            # Mock the D-Bus interface for service listing
            mock_db_interface = Mock()
            mock_db_message = Mock()
            mock_db_message.type.return_value = QDBusMessage.MessageType.ReplyMessage
            mock_db_message.arguments.return_value = [["org.freedesktop.portal.Desktop"]]
            mock_db_interface.call.return_value = mock_db_message

            def qdbus_interface_side_effect(*args, **kwargs):
                if "org.freedesktop.DBus" in args:
                    return mock_db_interface
                return Mock()

            mock_qdbus_interface.side_effect = qdbus_interface_side_effect

            detector = DBusThemeDetector()
            result = detector._is_service_available("org.freedesktop.portal.Desktop")
            assert result == expected

    @pytest.mark.parametrize(
        ("message_type", "expected"),
        [
            (QDBusMessage.MessageType.ReplyMessage, True),
            (QDBusMessage.MessageType.ErrorMessage, False),
        ],
    )
    def test_is_service_available_message_types(
        self,
        message_type: QDBusMessage.MessageType,
        expected: bool,
    ) -> None:
        """Test service availability with different message types."""
        with (
            patch("picard.ui.theme_detect_qtdbus.QDBusConnection") as mock_qdbus_connection,
            patch("picard.ui.theme_detect_qtdbus.QDBusInterface") as mock_qdbus_interface,
        ):
            mock_connection = Mock()
            mock_connection.isConnected.return_value = True
            mock_qdbus_connection.sessionBus.return_value = mock_connection

            # Mock the D-Bus interface for service listing
            mock_db_interface = Mock()
            mock_db_message = Mock()
            mock_db_message.type.return_value = message_type
            mock_db_message.arguments.return_value = [["org.freedesktop.portal.Desktop"]] if expected else []
            mock_db_interface.call.return_value = mock_db_message

            def qdbus_interface_side_effect(*args, **kwargs):
                if "org.freedesktop.DBus" in args:
                    return mock_db_interface
                return Mock()

            mock_qdbus_interface.side_effect = qdbus_interface_side_effect

            detector = DBusThemeDetector()
            result = detector._is_service_available("org.freedesktop.portal.Desktop")
            assert result == expected

    @pytest.mark.parametrize(
        ("exception_type",),
        [
            (RuntimeError,),
            (AttributeError,),
            (TypeError,),
        ],
    )
    def test_is_service_available_exception(
        self,
        exception_type: type[Exception],
    ) -> None:
        """Test service availability with exceptions."""
        with (
            patch("picard.ui.theme_detect_qtdbus.QDBusConnection") as mock_qdbus_connection,
            patch("picard.ui.theme_detect_qtdbus.QDBusInterface") as mock_qdbus_interface,
        ):
            mock_connection = Mock()
            mock_connection.isConnected.return_value = True
            mock_qdbus_connection.sessionBus.return_value = mock_connection

            mock_qdbus_interface.side_effect = exception_type("Test exception")

            detector = DBusThemeDetector()
            result = detector._is_service_available("org.freedesktop.portal.Desktop")
            assert result is False


class TestGlobalFunctions:
    """Test the global functions."""

    def test_get_dbus_detector_singleton(self) -> None:
        """Test that get_dbus_detector returns a singleton instance."""
        # Clear any existing global instance
        import picard.ui.theme_detect_qtdbus as module

        module._dbus_detector = None

        detector1 = get_dbus_detector()
        detector2 = get_dbus_detector()

        assert detector1 is detector2
        assert isinstance(detector1, DBusThemeDetector)

    @pytest.mark.parametrize(
        ("detector_result", "expected"),
        [
            (True, True),
            (False, False),
            (None, False),
        ],
    )
    def test_detect_freedesktop_color_scheme_dbus(
        self,
        detector_result: bool | None,
        expected: bool,
    ) -> None:
        """Test the global detect_freedesktop_color_scheme_dbus function."""
        with patch("picard.ui.theme_detect_qtdbus.get_dbus_detector") as mock_get_detector:
            mock_detector = Mock()
            mock_detector.freedesktop_portal_color_scheme_is_dark.return_value = detector_result
            mock_get_detector.return_value = mock_detector

            result = detect_freedesktop_color_scheme_dbus()
            assert result == expected

    @pytest.mark.parametrize(
        ("exception_type",),
        [
            (RuntimeError,),
            (AttributeError,),
            (TypeError,),
        ],
    )
    def test_detect_freedesktop_color_scheme_dbus_exception(
        self,
        exception_type: type[Exception],
    ) -> None:
        """Test detect_freedesktop_color_scheme_dbus with exceptions."""
        with patch("picard.ui.theme_detect_qtdbus.get_dbus_detector", side_effect=exception_type("Test exception")):
            result = detect_freedesktop_color_scheme_dbus()
            assert result is False

    @pytest.mark.parametrize(
        ("detector_result", "expected"),
        [
            (True, True),
            (False, False),
            (None, False),
        ],
    )
    def test_detect_gnome_color_scheme_dbus(
        self,
        detector_result: bool | None,
        expected: bool,
    ) -> None:
        """Test the global detect_gnome_color_scheme_dbus function."""
        with patch("picard.ui.theme_detect_qtdbus.get_dbus_detector") as mock_get_detector:
            mock_detector = Mock()
            mock_detector.gnome_color_scheme_is_dark.return_value = detector_result
            mock_get_detector.return_value = mock_detector

            result = detect_gnome_color_scheme_dbus()
            assert result == expected

    @pytest.mark.parametrize(
        ("exception_type",),
        [
            (RuntimeError,),
            (AttributeError,),
            (TypeError,),
        ],
    )
    def test_detect_gnome_color_scheme_dbus_exception(
        self,
        exception_type: type[Exception],
    ) -> None:
        """Test detect_gnome_color_scheme_dbus with exceptions."""
        with patch("picard.ui.theme_detect_qtdbus.get_dbus_detector", side_effect=exception_type("Test exception")):
            result = detect_gnome_color_scheme_dbus()
            assert result is False


class TestIntegration:
    """Integration tests for the D-Bus theme detection."""

    @pytest.mark.parametrize(
        ("portal_dark", "gnome_dark", "expected_dark"),
        [
            (True, False, True),  # Portal takes precedence
            (False, True, False),  # Portal takes precedence
            (None, True, True),  # Fallback to GNOME
            (None, False, False),  # Fallback to GNOME
            (None, None, False),  # No detection
        ],
    )
    def test_detection_priority(
        self,
        portal_dark: bool | None,
        gnome_dark: bool | None,
        expected_dark: bool,
    ) -> None:
        """Test that freedesktop portal detection takes priority over GNOME detection."""
        # Mock the detector methods to return the expected values
        with patch("picard.ui.theme_detect_qtdbus.get_dbus_detector") as mock_get_detector:
            mock_detector = Mock()

            # Configure the detector methods to return the test values
            def freedesktop_side_effect():
                return portal_dark

            def gnome_side_effect():
                return gnome_dark

            mock_detector.freedesktop_portal_color_scheme_is_dark.side_effect = freedesktop_side_effect
            mock_detector.gnome_color_scheme_is_dark.side_effect = gnome_side_effect
            mock_get_detector.return_value = mock_detector

            # Test portal detection
            portal_result = detect_freedesktop_color_scheme_dbus()
            assert portal_result == (portal_dark is True)

            # Test GNOME detection
            gnome_result = detect_gnome_color_scheme_dbus()
            assert gnome_result == (gnome_dark is True)

    def test_dbus_message_types(self) -> None:
        """Test handling of different D-Bus message types."""
        with (
            patch("picard.ui.theme_detect_qtdbus.QDBusConnection") as mock_qdbus_connection,
            patch("picard.ui.theme_detect_qtdbus.QDBusInterface") as mock_qdbus_interface,
        ):
            mock_connection = Mock()
            mock_connection.isConnected.return_value = True
            mock_qdbus_connection.sessionBus.return_value = mock_connection

            # Mock the D-Bus interface for service listing
            mock_db_interface = Mock()
            mock_db_message = Mock()
            mock_db_message.type.return_value = QDBusMessage.MessageType.ReplyMessage
            mock_db_message.arguments.return_value = [["org.freedesktop.portal.Desktop"]]
            mock_db_interface.call.return_value = mock_db_message

            # Configure QDBusInterface to return different mocks for different calls
            def qdbus_interface_side_effect(*args, **kwargs):
                if "org.freedesktop.DBus" in args:
                    return mock_db_interface
                elif "org.freedesktop.portal.Settings" in args:
                    mock_portal = Mock()
                    mock_portal.isValid.return_value = True
                    return mock_portal
                return Mock()

            mock_qdbus_interface.side_effect = qdbus_interface_side_effect

            # Test different message types
            for message_type in [QDBusMessage.MessageType.ReplyMessage, QDBusMessage.MessageType.ErrorMessage]:
                mock_message = Mock()
                mock_message.type.return_value = message_type
                mock_message.arguments.return_value = (
                    [1] if message_type == QDBusMessage.MessageType.ReplyMessage else []
                )

                # Update the portal interface call to return our test message
                def portal_call_side_effect(*args, **kwargs):
                    return mock_message

                with patch.object(DBusThemeDetector, '_is_service_available', return_value=True):
                    detector = DBusThemeDetector()
                    # Mock the portal interface call
                    with patch.object(detector.portal_interface, 'call', side_effect=portal_call_side_effect):
                        result = detector.freedesktop_portal_color_scheme_is_dark()

                        if message_type == QDBusMessage.MessageType.ReplyMessage:
                            assert result is True
                        else:
                            assert result is None
