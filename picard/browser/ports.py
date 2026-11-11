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

"""The ports Picard listens on for the browser.

Picard listens on a port of a fixed range: MusicBrainz only accepts the
redirect URIs of a login registered for Picard, one for each port of that
range (PICARD-2772). The range is that of the bounds of
the option ``browser_integration_port``.
"""

import errno
from http.server import (
    BaseHTTPRequestHandler,
    HTTPServer,
)
from typing import TypeVar

from picard import log
from picard.config import (
    IntOption,
    Option,
    get_config,
)


ServerT = TypeVar('ServerT', bound=HTTPServer)


def port_range() -> tuple[int, int]:
    """The first and the last port Picard may listen on: the bounds of ``browser_integration_port``."""
    option = Option.get('setting', 'browser_integration_port')
    if not isinstance(option, IntOption) or option.bounds.minimum is None or option.bounds.maximum is None:
        raise RuntimeError("the option browser_integration_port has no bounds")
    return int(option.bounds.minimum), int(option.bounds.maximum)


def listening_ports() -> list[int]:
    """The ports to try, in order.

    From ``browser_integration_port`` to the end of the range, then the ports
    before it, so that any free port of the range can be used. The value of the
    option is kept within its bounds when it is read.
    """
    first, last = port_range()
    start = get_config().setting['browser_integration_port']
    return [*range(start, last + 1), *range(first, start)]


def create_listening_server(
    server_class: type[ServerT],
    host_address: str,
    handler_class: type[BaseHTTPRequestHandler],
) -> 'ServerT | None':
    """A server bound to ``host_address`` on the first free port of :func:`listening_ports`, or None.

    A port that is in use (by another program, or another Picard) is skipped.
    So is one that cannot be used for another reason (a port reserved by the
    system, an address that is not available, ...), with a warning that says why.
    """
    for port in listening_ports():
        try:
            return server_class((host_address, port), handler_class)
        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                log.debug("Port %d of %s is in use", port, host_address)
            else:
                log.warning("Cannot listen on %s port %d: %s", host_address, port, e)
    return None
