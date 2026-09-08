# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Philipp Wolfer
# Copyright (C) 2021, 2026 Laurent Monin
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


"""MusicBrainz server registry and submission helpers.

Public API for describing MusicBrainz servers (:class:`MBServer`, the registry
lookups) and for building data submission URLs. Import from this package rather
than its submodules.
"""

from picard.util.mbserver.registry import (
    PICARD_SUPPORTED_AUTH_SCHEMES,
    AuthScheme,
    MBServer,
    get_server,
    is_official_server,
    official_servers,
    server_usable_auth_scheme,
)
from picard.util.mbserver.submission import (
    ServerTuple,
    build_submission_url,
    get_submission_server,
)


__all__ = (
    'AuthScheme',
    'MBServer',
    'PICARD_SUPPORTED_AUTH_SCHEMES',
    'ServerTuple',
    'build_submission_url',
    'get_server',
    'get_submission_server',
    'is_official_server',
    'official_servers',
    'server_usable_auth_scheme',
)
