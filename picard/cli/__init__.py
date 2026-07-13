# -*- coding: utf-8 -*-
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

"""picard-cli: Modern subcommand-based CLI for MusicBrainz Picard.

Usage:
    picard-cli plugins <command> [options]
    picard-cli --version
"""

import argparse
import sys

from picard import (
    PICARD_APP_NAME,
    PICARD_FANCY_VERSION_STR,
    PICARD_ORG_NAME,
)
from picard.util import (
    cli,
    versions,
)


def build_root_parser():
    """Build the root argument parser with global options and subcommands."""
    parser = argparse.ArgumentParser(
        prog='picard-cli',
        description='MusicBrainz Picard command-line interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global options (shared by all subcommands)
    parser.add_argument(
        '-c',
        '--config-file',
        action='store',
        default=None,
        help="location of the configuration file",
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help="enable debug-level logging",
    )
    parser.add_argument(
        '-v',
        '--version',
        action='store_true',
        help="display version information and exit",
    )
    parser.add_argument(
        '-V',
        '--long-version',
        action='store_true',
        help="display long version information and exit",
    )
    parser.add_argument(
        '--debug-opts',
        action='store',
        default=None,
        nargs='?',
        const='',
        metavar='OPTIONS',
        help="comma-separated list of debug options (use without value to list available options)",
    )
    parser.add_argument(
        '--no-color',
        action='store_true',
        help="disable colored output",
    )
    parser.add_argument(
        '--yes',
        '-y',
        action='store_true',
        help="skip confirmation prompts",
    )

    # Subcommands
    subparsers = parser.add_subparsers(
        dest='command',
        title='commands',
        metavar='<command>',
    )

    # Register available subcommands
    _register_plugins_subcommand(subparsers)
    _register_profiles_subcommand(subparsers)

    return parser


def _register_plugins_subcommand(subparsers):
    """Register the 'plugins' subcommand group."""
    # Lazy import to avoid loading heavy dependencies at parse time
    from picard.cli.plugins import register_subcommand

    register_subcommand(subparsers)


def _register_profiles_subcommand(subparsers):
    """Register the 'profiles' subcommand group."""
    from picard.profiles.cli import register_subcommand

    register_subcommand(subparsers)


def main():
    """Entry point for picard-cli."""
    parser = build_root_parser()
    args = parser.parse_args()

    # Handle --debug-opts help request early (before init)
    if args.debug_opts is not None and not args.debug_opts.strip():
        from picard.debug_opts import DebugOpt

        DebugOpt.print_help_and_exit()

    # Handle version flags early (before init)
    if getattr(args, 'long_version', False):
        cli.print_message_and_exit(versions.as_string())
    if getattr(args, 'version', False):
        cli.print_message_and_exit(f"{PICARD_ORG_NAME} {PICARD_APP_NAME} {PICARD_FANCY_VERSION_STR}")

    # No subcommand given
    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Dispatch to the subcommand handler
    if hasattr(args, 'run_command'):
        sys.exit(args.run_command(args))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
