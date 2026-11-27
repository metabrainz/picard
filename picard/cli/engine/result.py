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

"""Structured, serializable command results.

Every command returns an :class:`EngineResult`. Commands NEVER print or touch
transport — a frontend renders the result (the console as a table via
CliOutput, the MCP server as JSON). Because a result may cross a process
boundary (a future RemoteEngineSession driving a running GUI), it is plain data
only: entities are referenced by handle STRING, never by live object.

See ``docs/CommandEngine.md`` (Result contract).
"""

from dataclasses import (
    dataclass,
    field,
)
from typing import Any


@dataclass
class EngineItemResult:
    """Per-entity outcome of a command.

    ``handle`` is the entity's session handle (a string). ``status`` is a short
    machine-readable tag (e.g. ``'saved'``, ``'matched'``, ``'skipped'``).
    ``data`` carries any command-specific, JSON-serializable detail. ``path``
    is where the entity currently sits (``a1.d2.t3``, ``c1.f2``), filled in by
    the dispatcher; unlike the handle it is a position, so it can change.
    """

    handle: str
    status: str = 'ok'
    data: dict[str, Any] = field(default_factory=dict)
    path: str = ''

    def to_dict(self) -> dict[str, Any]:
        return {'handle': self.handle, 'path': self.path, 'status': self.status, 'data': self.data}


@dataclass
class EngineResult:
    """The structured result of running a command.

    - ``items``: per-entity outcomes (for selector-taking commands).
    - ``resolved``: handles the selector matched.
    - ``unresolved``: selector tokens that matched no live entity
      (machine-actionable: a non-empty list means the caller under-acted).
      ``resolved == [] and unresolved == []`` means "valid, nothing matched".
    - ``mints``: handles newly created by the command (add/cluster/lookup/...).
    - ``message``: optional human-oriented summary (a frontend may ignore it;
      it is NOT the data channel — put structured detail in items/data).
    - ``ok``: whether the command succeeded overall; ``error`` describes a
      failure.
    """

    ok: bool = True
    items: list[EngineItemResult] = field(default_factory=list)
    resolved: list[str] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    mints: list[str] = field(default_factory=list)
    message: str = ''
    error: str = ''

    @classmethod
    def failure(cls, error: str, **kwargs: Any) -> 'EngineResult':
        """Build a failed result carrying an error message."""
        return cls(ok=False, error=error, **kwargs)

    def to_dict(self) -> dict[str, Any]:
        """Return a plain JSON-serializable dict (MCP / cross-process transport)."""
        return {
            'ok': self.ok,
            'items': [item.to_dict() for item in self.items],
            'resolved': list(self.resolved),
            'unresolved': list(self.unresolved),
            'mints': list(self.mints),
            'message': self.message,
            'error': self.error,
        }
