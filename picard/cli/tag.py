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


"""Tag reading subcommand for picard-cli.

A first, headless end-to-end use of the tagging core: load local audio files
with Picard's format handlers and print their tags, without a GUI.

Usage:
    picard-cli tag read <file> [<file> ...]
"""

from argparse import ArgumentParser

from picard.cli.base import ExitCode
from picard.cli.subcommand import Subcommand


class TagSubcommand(Subcommand):
    def __init__(self):
        super().__init__(
            name='tag',
            help='manage tags',
            examples=(
                'tag read song.flac',
                'tag read *.mp3',
            ),
        )

    def setup_parser(self, parser: ArgumentParser):
        parser.description = 'Read tags from local audio files (headless).'

        verb_parsers = parser.add_subparsers(
            dest='verb',
            title='tag commands',
            metavar='<command>',
        )

        p_read = verb_parsers.add_parser('read', help='read and print tags from audio files')
        p_read.add_argument('files', metavar='FILE', nargs='+', help="audio file(s) to read")
        p_read.set_defaults(run_command=_run_tag)


def _load_file(app, path):
    """Load a single file headlessly and return the File, or None on failure.

    Opens the file with the format registry, drives the async load to
    completion on the headless event loop, and returns the loaded File.
    """
    from picard.file import File

    file = app.format_registry.open(path)
    if file is None:
        return None

    # File.load schedules work on a thread pool and reports completion via a
    # main-thread callback; pump the event loop until it finishes.
    file.load(lambda _file: None)
    app.run_until_idle(timeout=60)
    if file.state == File.State.ERROR:
        return None
    return file


def cmd_read(app, args, output):
    """Load the given files and print their tags."""
    exit_code = ExitCode.SUCCESS
    for index, path in enumerate(args.files):
        if index:
            output.nl()
        file = _load_file(app, path)
        if file is None:
            output.error(f"Could not read: {output.d_path(path)}")
            exit_code = ExitCode.ERROR
            continue

        output.print(output.d_path(file.filename))
        for name, values in sorted(file.orig_metadata.rawitems()):
            # Skip Picard-internal hidden tags (leading '~') for a clean view.
            if name.startswith('~'):
                continue
            for value in values:
                output.info(f"{output.d_name(name)}: {value}")

    return exit_code


def _run_tag(args):
    """Initialize the headless tagger and dispatch the tag verb."""
    from picard.cli._bootstrap import (
        init_logging,
        is_color_disabled,
    )
    from picard.cli.headless import HeadlessTagger
    from picard.cli.output import CliOutput

    config_file = getattr(args, 'config_file', None)
    app = HeadlessTagger([], config_file=config_file)
    init_logging(args)

    output = CliOutput(color=False if is_color_disabled(args) else None)

    try:
        if args.verb == 'read':
            return cmd_read(app, args, output)
        return ExitCode.ERROR
    finally:
        app.run_cleanup()
