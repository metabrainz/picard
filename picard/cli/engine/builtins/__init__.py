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

"""Built-in engine commands.

Each command is a small adapter over the session / Workspace that returns an
:class:`~picard.cli.engine.result.EngineResult`. Commands never print; a
frontend renders the result.

A command is declared where it is implemented, with the ``command`` decorator
of :mod:`~picard.cli.engine.builtins.registry`. The modules of this package
group them by what they act on:

- :mod:`~picard.cli.engine.builtins.listing`: ``ls``, ``tree``
- :mod:`~picard.cli.engine.builtins.files`: ``file add``, ``save``, ``move``, ``remove``, ``trash``
- :mod:`~picard.cli.engine.builtins.identify`: ``cluster``
- :mod:`~picard.cli.engine.builtins.help`: ``help``, which describes the others

:mod:`~picard.cli.engine.builtins.helpers` has what they share. Importing the
modules declares the commands, and :func:`register_builtins` populates a registry
with them; both frontends call it so they share one vocabulary.
"""

import picard.cli.engine.builtins.files  # noqa: F401
from picard.cli.engine.builtins.help import make_help_command
import picard.cli.engine.builtins.identify  # noqa: F401
import picard.cli.engine.builtins.listing  # noqa: F401
from picard.cli.engine.builtins.registry import BUILTIN_COMMANDS
from picard.cli.engine.commands import (
    EngineCommandRegistry,
)


def register_builtins(registry: EngineCommandRegistry) -> None:
    """Register the built-in commands into ``registry``, and the ``help`` that describes them."""
    for command in BUILTIN_COMMANDS:
        registry.register(command)
    registry.register(make_help_command(registry))
