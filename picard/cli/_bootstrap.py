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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


"""Shared helpers for Picard CLI commands (picard-cli).

Logging and color-detection helpers shared by the CLI subcommand handlers.
Headless application bootstrap lives in picard.cli.headless.HeadlessTagger.
"""

import logging
import os


def init_logging(args):
    """Configure logging for CLI commands.

    Sets up console handler and verbosity based on --debug / --debug-opts flags.

    Args:
        args: Parsed argparse namespace with 'debug' and 'debug_opts' attributes.
    """
    from picard import log
    from picard.debug_opts import DebugOpt

    log.enable_console_handler()

    debug = getattr(args, 'debug', False)
    debug_opts = getattr(args, 'debug_opts', None)

    if debug_opts:
        DebugOpt.from_string(debug_opts)

    # Enabling any debug option implies debug-level logging, otherwise its
    # log.debug() output would be silently discarded.
    if debug or DebugOpt.any_enabled():
        log.set_verbosity(logging.DEBUG)
    else:
        log.set_verbosity(logging.WARNING)


def is_color_disabled(args):
    """Determine whether colored output should be disabled.

    Checks both the --no-color flag and the NO_COLOR environment variable.

    Args:
        args: Parsed argparse namespace with 'no_color' attribute.

    Returns:
        True if color should be disabled, False otherwise.
    """
    return getattr(args, 'no_color', False) or 'NO_COLOR' in os.environ
