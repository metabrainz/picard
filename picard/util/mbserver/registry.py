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


"""Registry of MusicBrainz servers and their capabilities.

This module is intentionally dependency-light (no config or Qt imports) so it
can be imported from anywhere without risking circular imports. It describes the
servers Picard knows about — their host, port, protocol, whether they are
official MusicBrainz database servers, and which authentication schemes they
accept.

The registry data introduced here is descriptive; consuming it to drive request
authentication or logout behavior is done elsewhere.
"""

from dataclasses import (
    dataclass,
    field,
)
from enum import Enum

from picard.const import MUSICBRAINZ_SERVERS


class AuthScheme(Enum):
    """An authentication scheme a MusicBrainz server may accept.

    Members identify a *specific* scheme (not just the protocol family), because
    credentials are only valid for the exact provider that issued them. Only
    ``MEB_OAUTH2`` (the MetaBrainz OAuth 2 provider) exists today; new schemes
    (a different OAuth provider, OpenID Connect, HTTP basic auth, an API key, ...)
    can be added as Picard grows support for authenticating other servers.
    """

    MEB_OAUTH2 = 'meb_oauth2'


# Auth schemes Picard actually knows how to perform. A server's advertised
# schemes are intersected with this set to decide how (or whether) to log in.
PICARD_SUPPORTED_AUTH_SCHEMES = frozenset({AuthScheme.MEB_OAUTH2})


@dataclass(frozen=True)
class MBServer:
    """A known (or, in the future, user-configured) MusicBrainz server.

    Attributes:
        host: hostname
        port: TCP port
        protocol: URL scheme, ``'https'`` or ``'http'``
        official: True for the official servers backing the primary MusicBrainz
            database. Used for submission routing and UI hints; note that being
            official is independent of whether the server accepts a login.
        auth_schemes: authentication schemes the server accepts. An empty set
            means the server accepts no authentication Picard can use. A server
            may advertise more than one scheme.
    """

    host: str
    port: int = 443
    protocol: str = 'https'
    official: bool = False
    auth_schemes: frozenset[AuthScheme] = field(default_factory=frozenset)

    def __post_init__(self):
        # The instance is immutable, but callers (and, later, user configuration)
        # may pass any iterable of schemes. Normalize to a frozenset so the stored
        # value is always immutable and hashable, without requiring a factory.
        if not isinstance(self.auth_schemes, frozenset):
            object.__setattr__(self, 'auth_schemes', frozenset(self.auth_schemes))

    @property
    def supports_auth(self) -> bool:
        """True if the server accepts at least one authentication scheme."""
        return bool(self.auth_schemes)

    def usable_auth_scheme(self) -> AuthScheme | None:
        """The auth scheme Picard should use for this server, or None.

        Returns the scheme to use when the server advertises one that Picard can
        perform; otherwise None, meaning requests must be sent unauthenticated.
        The choice is deterministic when several schemes match.
        """
        candidates = self.auth_schemes & PICARD_SUPPORTED_AUTH_SCHEMES
        if not candidates:
            return None
        return min(candidates, key=lambda scheme: scheme.value)


# Built-in registry of well-known servers and their capabilities.
#
# The official MusicBrainz database servers are derived from MUSICBRAINZ_SERVERS
# (the single source of truth for official hostnames) and all use the shared
# MetaBrainz OAuth 2 provider.
#
# Any other host is treated as an unknown, non-official server with no
# authentication (see get_server()). User-configured servers, when supported,
# will be layered on top of these built-in defaults.
def _build_builtin_servers() -> dict[str, MBServer]:
    return {
        host: MBServer(
            host=host,
            official=True,
            auth_schemes=frozenset({AuthScheme.MEB_OAUTH2}),
        )
        for host in MUSICBRAINZ_SERVERS
    }


_BUILTIN_SERVERS: dict[str, MBServer] = _build_builtin_servers()


def get_server(host: str, port: int | None = None) -> MBServer:
    """Returns the MBServer describing `host`.

    Built-in servers come from the registry with their fixed capabilities. Any
    other host is an unknown, non-official server with no authentication; its
    port defaults to the given `port` (typically the configured ``server_port``)
    or 443.
    """
    server = _BUILTIN_SERVERS.get(host)
    if server is not None:
        return server
    return MBServer(host=host, port=port if port is not None else 443)


def server_usable_auth_scheme(host: str) -> AuthScheme | None:
    """Returns the auth scheme Picard should use for `host`, or None for unauthenticated."""
    return get_server(host).usable_auth_scheme()


def server_change_requires_logout(old_host: str, new_host: str) -> bool:
    """Returns True if changing the server from `old_host` to `new_host` invalidates the login.

    A login is obtained against `old_host` using the authentication scheme Picard
    uses for it. That login stays valid only if `new_host` also accepts that same
    scheme; otherwise the stored credentials are no longer usable and the user
    must be logged out.

    If Picard would not authenticate against `old_host` at all (no usable scheme,
    e.g. a local replica or the test server), there is no login tied to it, so no
    logout is required.

    Args:
        old_host: the previously configured hostname
        new_host: the newly configured hostname

    Returns: True if the change requires a logout, False if the login stays valid
    """
    old_scheme = get_server(old_host).usable_auth_scheme()
    if old_scheme is None:
        return False
    return old_scheme not in get_server(new_host).auth_schemes


def official_servers() -> tuple[str, ...]:
    """Returns the official MusicBrainz database server hostnames, in order.

    The first entry is the primary server.
    """
    return tuple(MUSICBRAINZ_SERVERS)


def is_official_server(host: str) -> bool:
    """Returns True if host is an official MusicBrainz server for the primary database.

    Args:
        host: the hostname

    Returns: True if host is an official MusicBrainz server, False otherwise
    """
    return host in MUSICBRAINZ_SERVERS
