#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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

"""The ports Picard listens on for the browser (picard.browser.ports)."""

import errno
from unittest.mock import (
    MagicMock,
    call,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.browser.ports import (
    create_listening_server,
    listening_ports,
    port_range,
)
from picard.config import Option


FIRST, LAST = port_range()
ALL_PORTS = list(range(FIRST, LAST + 1))


def _in_use():
    return OSError(errno.EADDRINUSE, "Address already in use")


class PortRangeTest(PicardTestCase):
    def test_the_bounds_of_the_option(self):
        bounds = Option.get('setting', 'browser_integration_port').bounds
        self.assertEqual((bounds.minimum, bounds.maximum), port_range())
        self.assertLess(FIRST, LAST)


class ListeningPortsTest(PicardTestCase):
    def test_from_the_port_of_the_browser_integration(self):
        middle = FIRST + 5
        for port, expected in (
            (FIRST, ALL_PORTS),
            (middle, [*range(middle, LAST + 1), *range(FIRST, middle)]),
            (LAST, [LAST, *ALL_PORTS[:-1]]),
        ):
            with self.subTest(port=port):
                self.set_config_values(setting={'browser_integration_port': port})
                ports = listening_ports()
                self.assertEqual(expected, ports)
                self.assertEqual(ALL_PORTS, sorted(ports))


class CreateListeningServerTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.start = FIRST + 5
        self.set_config_values(setting={'browser_integration_port': self.start})
        self.handler = MagicMock()

    def test_a_busy_port_is_skipped(self):
        server = MagicMock()
        server_class = MagicMock(side_effect=[_in_use(), server])
        self.assertIs(server, create_listening_server(server_class, '127.0.0.1', self.handler))
        self.assertEqual(
            [call(('127.0.0.1', self.start), self.handler), call(('127.0.0.1', self.start + 1), self.handler)],
            server_class.call_args_list,
        )

    def test_the_ports_before_are_tried_last(self):
        server_class = MagicMock(side_effect=[_in_use()] * (LAST - self.start + 1) + [MagicMock()])
        create_listening_server(server_class, '0.0.0.0', self.handler)
        self.assertEqual(('0.0.0.0', FIRST), server_class.call_args.args[0])

    def test_no_free_port(self):
        server_class = MagicMock(side_effect=_in_use())
        self.assertIsNone(create_listening_server(server_class, '127.0.0.1', self.handler))
        self.assertEqual(len(ALL_PORTS), server_class.call_count)

    def test_a_port_in_use_is_not_a_warning(self):
        server_class = MagicMock(side_effect=[_in_use(), MagicMock()])
        with patch('picard.browser.ports.log') as log:
            create_listening_server(server_class, '127.0.0.1', self.handler)
        log.warning.assert_not_called()
        log.debug.assert_called_once()
        self.assertIn(self.start, log.debug.call_args.args)

    def test_another_error_is_a_warning(self):
        # A port reserved by the system, say (WSAEACCES on Windows).
        denied = OSError(errno.EACCES, "Permission denied")
        server_class = MagicMock(side_effect=[denied, MagicMock()])
        with patch('picard.browser.ports.log') as log:
            self.assertIsNotNone(create_listening_server(server_class, '127.0.0.1', self.handler))
        log.warning.assert_called_once()
        args = log.warning.call_args.args
        self.assertIn('127.0.0.1', args)
        self.assertIn(self.start, args)
        self.assertIn(denied, args)
