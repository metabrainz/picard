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


"""Shell completion generation subcommand for picard-cli.

Generates shell completion scripts using shtab.
Supported shells depend on the installed shtab version.

Usage:
    picard-cli completions <shell>
"""

try:
    import shtab

    SUPPORTED_SHELLS = tuple(shtab.SUPPORTED_SHELLS)
except ImportError:
    shtab = None  # type: ignore[assignment]
    SUPPORTED_SHELLS = ()

from picard.cli.base import ExitCode


def setup_parser(completions_parser):
    """Configure the 'completions' subcommand parser."""
    if SUPPORTED_SHELLS:
        shell_list = ', '.join(SUPPORTED_SHELLS)
    else:
        shell_list = '(shtab not installed)'

    completions_parser.description = (
        f'Generate shell completion scripts for picard-cli. Supported shells: {shell_list}.'
    )

    completions_parser.add_argument(
        'shell',
        choices=SUPPORTED_SHELLS or None,
        metavar='SHELL',
        help=f'target shell ({shell_list})',
    )
    completions_parser.set_defaults(run_command=_run_completions)


def _run_completions(args):
    """Generate and print shell completion script."""
    from picard.cli._bootstrap import is_color_disabled
    from picard.cli.output import CliOutput

    output = CliOutput(color=False if is_color_disabled(args) else None)

    if shtab is None:
        output.error("shtab is required for completion generation.\n  Install it with: pip install \"picard[cli]\"")
        return ExitCode.ERROR

    if args.shell not in SUPPORTED_SHELLS:
        output.error(f"Unsupported shell '{args.shell}'.\n  Supported shells: {', '.join(SUPPORTED_SHELLS)}")
        return ExitCode.ERROR

    # Inline import: picard.cli imports this module during setup,
    # so importing build_root_parser at top level would be circular.
    from picard.cli import build_root_parser

    parser = build_root_parser()
    output.print(shtab.complete(parser, args.shell))
    return ExitCode.SUCCESS
