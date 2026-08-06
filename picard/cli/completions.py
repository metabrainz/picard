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

"""Shell completion generation subcommand for picard-cli.

Generates shell completion scripts using shtab.
Supported shells depend on the installed shtab version.

Usage:
    picard-cli completions <shell>
"""

import sys


try:
    import shtab
except ImportError:
    shtab = None  # type: ignore[assignment]

from picard.cli.base import ExitCode


def _get_supported_shells():
    """Get list of supported shells from shtab, or None if not available."""
    if shtab is None:
        return None
    return shtab.SUPPORTED_SHELLS


def setup_parser(completions_parser):
    """Configure the 'completions' subcommand parser."""
    shells = _get_supported_shells()
    if shells:
        shell_list = ', '.join(shells)
        choices = shells
    else:
        shell_list = '(shtab not installed)'
        choices = None

    completions_parser.description = (
        f'Generate shell completion scripts for picard-cli. Supported shells: {shell_list}.'
    )

    completions_parser.add_argument(
        'shell',
        choices=choices,
        metavar='SHELL',
        help=f'target shell ({shell_list})',
    )
    completions_parser.set_defaults(run_command=_run_completions)


def _run_completions(args):
    """Generate and print shell completion script."""
    if shtab is None:
        print(
            "Error: shtab is required for completion generation.\nInstall it with: pip install \"picard[cli]\"",
            file=sys.stderr,
        )
        return ExitCode.ERROR

    if args.shell not in shtab.SUPPORTED_SHELLS:
        print(
            f"Error: unsupported shell '{args.shell}'.\nSupported shells: {', '.join(shtab.SUPPORTED_SHELLS)}",
            file=sys.stderr,
        )
        return ExitCode.ERROR

    # Inline import: picard.cli imports this module during setup,
    # so importing build_root_parser at top level would be circular.
    from picard.cli import build_root_parser

    parser = build_root_parser()
    print(shtab.complete(parser, args.shell))
    return ExitCode.SUCCESS
