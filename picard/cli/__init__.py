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


"""picard-cli: Modern subcommand-based CLI for MusicBrainz Picard.

Usage:
    picard-cli <command> [options]
    picard-cli --version

Commands:
    plugins     Manage Picard plugins
    profiles    Manage Picard profiles
"""

import argparse
from collections import namedtuple
from importlib import import_module
import sys

from picard import (
    PICARD_APP_NAME,
    PICARD_FANCY_VERSION_STR,
    PICARD_ORG_NAME,
)
from picard.util import versions


# Subcommand registry.
# Adding an entry here automatically updates both picard-cli and picard --help.
# Each module_path must contain a register_subcommand(subparsers) function.
Subcommand = namedtuple('Subcommand', ('name', 'help', 'module_path', 'examples'))

SUBCOMMANDS = (
    Subcommand(
        name='completions',
        help='generate shell completion scripts',
        module_path='picard.cli.completions',
        examples=(
            'completions bash',
            'completions zsh',
        ),
    ),
    Subcommand(
        name='plugins',
        help='manage Picard plugins',
        module_path='picard.cli.plugins',
        examples=(
            'plugins list',
            'plugins --help',
        ),
    ),
    Subcommand(
        name='profiles',
        help='manage Picard profiles',
        module_path='picard.cli.profiles',
        examples=(
            'profiles list',
            'profiles export "My Profile" -o profile.toml',
        ),
    ),
)


def get_subcommands_help():
    """Return a formatted string listing picard-cli subcommands for use in epilogs."""
    lines = ["Additional commands available via picard-cli:"]
    max_name_len = max(len(cmd.name) for cmd in SUBCOMMANDS)
    for cmd in SUBCOMMANDS:
        lines.append(f"  {cmd.name:<{max_name_len}}  {cmd.help}")
    lines.append("")
    lines.append("Use 'picard-cli <command> --help' for more information.")
    return "\n".join(lines)


def _build_examples_epilog():
    """Build the examples epilog from SUBCOMMANDS entries."""
    lines = ["examples:"]
    for cmd in SUBCOMMANDS:
        for example in cmd.examples:
            lines.append(f"  picard-cli {example}")
    return "\n".join(lines)


def build_root_parser():
    """Build the root argument parser with global options and subcommands."""
    parser = argparse.ArgumentParser(
        prog='picard-cli',
        description='MusicBrainz Picard command-line interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_build_examples_epilog(),
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
        action='version',
        version=f"{PICARD_ORG_NAME} {PICARD_APP_NAME} {PICARD_FANCY_VERSION_STR}",
    )
    parser.add_argument(
        '-V',
        '--long-version',
        action='version',
        version=versions.as_string(),
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

    # Register available subcommands (lazy import to avoid heavy deps at parse time)
    for cmd in SUBCOMMANDS:
        _register_subcommand(subparsers, cmd)

    return parser


def _register_subcommand(subparsers, cmd):
    """Register a single subcommand from its metadata.

    Creates the subparser with name/help from SUBCOMMANDS, then delegates
    to the module's setup_parser() to populate arguments and verbs.
    Sets a default run_command that prints help when no verb is given.
    """
    module = import_module(cmd.module_path)
    parser = subparsers.add_parser(cmd.name, help=cmd.help)
    module.setup_parser(parser)
    # If no verb is given, print this subcommand's help.
    # Only set the fallback if setup_parser() didn't already set run_command.
    if not parser.get_default('run_command'):
        parser.set_defaults(run_command=lambda args, p=parser: p.print_help() or 0)


def main():
    """Entry point for picard-cli."""
    parser = build_root_parser()
    args = parser.parse_args()

    # Handle --debug-opts help request early (before init)
    if args.debug_opts is not None and not args.debug_opts.strip():
        from picard.debug_opts import DebugOpt

        DebugOpt.print_help_and_exit()

    # No subcommand given
    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Dispatch to the subcommand handler
    sys.exit(args.run_command(args))


if __name__ == "__main__":
    main()
