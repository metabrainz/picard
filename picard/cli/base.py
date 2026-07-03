# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
# Copyright (C) 2025-2026 Laurent Monin
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

"""Base class and exit codes for Picard CLI subcommand handlers."""

from enum import IntEnum
import traceback

from picard.cli.output import CliOutput


class ExitCode(IntEnum):
    """Standard exit codes for CLI commands."""

    SUCCESS = 0
    ERROR = 1
    NOT_FOUND = 2
    CANCELLED = 130


class BaseCLI:
    """Base class for CLI subcommand handlers.

    Provides common infrastructure: output, debug mode detection,
    exception handling with optional traceback, and keyboard interrupt handling.

    Subclasses should override run() to implement their command dispatch.
    """

    def __init__(self, args, output=None):
        self._args = args
        self._out = output or CliOutput()

    def _is_debug_mode(self):
        """Check if debug mode is enabled."""
        return getattr(self._args, 'debug', False)

    def _handle_exception(self, e, message=None):
        """Handle exception with optional traceback in debug mode.

        Args:
            e: Exception to handle.
            message: Optional custom error message prefix.
        """
        if message:
            self._out.error(f'{message}: {e}')
        else:
            self._out.error(f'Error: {e}')

        if self._is_debug_mode():
            self._out.nl()
            self._out.error('Traceback:')
            for line in traceback.format_exc().splitlines():
                self._out.error(f'  {line}')

    def run(self):
        """Run the CLI command and return an ExitCode.

        Wraps execution with keyboard interrupt handling.
        Subclasses should override _dispatch() instead of run().
        """
        try:
            return self._dispatch()
        except KeyboardInterrupt:
            self._out.nl()
            self._out.error('Operation cancelled by user')
            return ExitCode.CANCELLED
        except Exception as e:
            self._handle_exception(e)
            return ExitCode.ERROR

    def _dispatch(self):
        """Dispatch to the appropriate command handler.

        Subclasses must override this method.
        """
        raise NotImplementedError
