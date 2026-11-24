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


"""Documentation subcommand for picard-cli.

Dumps Picard's internal documentation (e.g. the scripting functions) in
several formats.

Usage:
    picard-cli docs list [TOPIC]
    picard-cli docs show TOPIC [NAME ...] [-f console|markdown|html|json] [-o FILE]
"""

from argparse import ArgumentParser
import os

from picard.cli.base import ExitCode
from picard.cli.doc_formatters import (
    FORMATTERS,
    DocFormatError,
)
from picard.cli.doc_topics import (
    DOC_TOPICS,
    DocNotFoundError,
    get_topic,
)
from picard.cli.output import CliOutput
from picard.cli.subcommand import Subcommand


class DocsSubcommand(Subcommand):
    def __init__(self):
        super().__init__(
            name='docs',
            help='show or export Picard documentation',
            examples=(
                'docs list',
                'docs show script-functions',
                'docs show script-functions sortmulti unique',
                'docs show script-variables album artist',
                'docs show script-functions -f markdown -o functions.md',
            ),
        )

    def setup_parser(self, parser: ArgumentParser):
        """Configure the 'docs' subcommand parser with all its verbs."""
        parser.description = 'Show or export the documentation built into Picard.'

        verb_parsers = parser.add_subparsers(
            dest='verb',
            title='docs commands',
            metavar='<command>',
        )
        topic_names = [topic.name for topic in DOC_TOPICS]

        # --- list ---
        p_list = verb_parsers.add_parser('list', help='list topics, or the entries of a topic')
        p_list.add_argument(
            'topic',
            nargs='?',
            choices=topic_names,
            metavar='TOPIC',
            help="list the entries of this topic (topics: %s)" % ', '.join(topic_names),
        )
        p_list.set_defaults(run_command=_run_docs, handler=cmd_list)

        # --- show ---
        p_show = verb_parsers.add_parser('show', help='show the documentation of a topic')
        p_show.add_argument(
            'topic',
            choices=topic_names,
            metavar='TOPIC',
            help="documentation topic (%s)" % ', '.join(topic_names),
        )
        p_show.add_argument(
            'names',
            nargs='*',
            metavar='NAME',
            help="only show these entries (default: all)",
        )
        p_show.add_argument(
            '-f',
            '--format',
            choices=list(FORMATTERS),
            default='console',
            help="output format (default: console)",
        )
        p_show.add_argument('-o', '--output', metavar='FILE', help="output file (default: stdout)")
        p_show.set_defaults(run_command=_run_docs, handler=cmd_show)


def cmd_list(args, output):
    """List the topics, or the entries of a topic."""
    if not args.topic:
        width = max(len(topic.name) for topic in DOC_TOPICS)
        for topic in DOC_TOPICS:
            output.print(f"{output.d_name(topic.name.ljust(width))}  {topic.help}")
        return ExitCode.SUCCESS

    for entry in get_topic(args.topic).entries():
        output.print(entry.name)
    return ExitCode.SUCCESS


def cmd_show(args, output):
    """Render the documentation of a topic, to stdout or to a file."""
    # The rendering depends on the destination: colors only make sense on a terminal
    render_output = CliOutput(color=False) if args.output else output

    topic = get_topic(args.topic)
    try:
        entries = topic.select(args.names)
        text = FORMATTERS[args.format](topic, entries, render_output)
    except DocNotFoundError as e:
        output.error(f"No such {topic.name} entry: {', '.join(e.names)}")
        return ExitCode.NOT_FOUND
    except DocFormatError as e:
        output.error(str(e))
        return ExitCode.ERROR

    if not args.output:
        output.print(text.rstrip('\n'))
        return ExitCode.SUCCESS

    if os.path.exists(args.output) and not getattr(args, 'yes', False):
        if not output.yesno(f"Overwrite {args.output}?"):
            output.print("Export cancelled.")
            return ExitCode.SUCCESS
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(text)
    except OSError as e:
        output.error(f"Cannot write file: {e}")
        return ExitCode.ERROR
    output.success(f"Documentation written to: {output.d_path(args.output)}")
    return ExitCode.SUCCESS


def _run_docs(args):
    """Initialize and run the docs CLI."""
    # Lazy imports: avoid loading heavy dependencies at parse time
    from picard.cli._bootstrap import (
        init_logging,
        is_color_disabled,
    )
    from picard.cli.headless import HeadlessTagger

    # Headless application: sets up config, which listing the script functions needs
    app = HeadlessTagger([], config_file=getattr(args, 'config_file', None))
    init_logging(args)

    output = CliOutput(color=False if is_color_disabled(args) else None)

    try:
        return args.handler(args, output)
    finally:
        app.run_cleanup()
