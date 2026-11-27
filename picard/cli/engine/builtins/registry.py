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

"""Where the built-in commands are declared.

Each module of this package declares its commands with :data:`command`, next to
the functions that implement them. :func:`~picard.cli.engine.builtins.register_builtins`
copies them into the registry of a frontend.
"""

from picard.cli.engine.commands import EngineCommandRegistry


BUILTIN_COMMANDS = EngineCommandRegistry()

# The decorator that declares a built-in command (see EngineCommandRegistry.command).
command = BUILTIN_COMMANDS.command
