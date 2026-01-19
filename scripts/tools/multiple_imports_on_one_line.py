# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Bob Swift
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


import argparse
import os
import re
import sys


# Used to determine the base directory for relative paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BASE_DIR_LENGTH = len(BASE_DIR) + 1

# Top-level directories to scan and directories to ignore
ROOT_DIRS = ['picard', 'scripts', 'test']
IGNORE_DIR = '__pycache__'

RE_IMPORT_LINE = re.compile(r'^(from\s+\S+\s+import\s+)([^(].*,.*[^\\])$')


class OUTPUT_LEVEL:
    SILENT = 0
    WARNING = 1
    NORMAL = 2
    VERBOSE = 3


class Print:
    _level = OUTPUT_LEVEL.NORMAL

    @classmethod
    def set_level(cls, level):
        """Set the output level for printing."""
        cls._level = level

    @classmethod
    def print(cls, message, level=OUTPUT_LEVEL.NORMAL):
        """Print message if level is appropriate."""
        if cls._level >= level:
            print(message)

    @classmethod
    def verbose(cls, message):
        """Print message if level is VERBOSE."""
        cls.print(message, OUTPUT_LEVEL.VERBOSE)

    @classmethod
    def normal(cls, message):
        """Print message if level is NORMAL or higher."""
        cls.print(message, OUTPUT_LEVEL.NORMAL)

    @classmethod
    def warning(cls, message):
        """Print message if level is WARNING or higher."""
        cls.print(message, OUTPUT_LEVEL.WARNING)


def make_plural(count: int) -> str:
    """Makes plural suffix string.

    Args:
        count (int): Count of items.

    Returns:
        str: 's' if count is not 1, else empty string.
    """
    return '' if count == 1 else 's'


def parse_command_line():
    """Parse the command line arguments."""
    arg_parser = argparse.ArgumentParser(description="Checks for multiple imports on one line in Python files.")

    level_group = arg_parser.add_mutually_exclusive_group()

    level_group.add_argument(
        '-q',
        '--quiet',
        action='store_true',
        dest='quiet',
        help="suppress information messages",
    )

    level_group.add_argument(
        '-w',
        '--warning',
        action='store_true',
        dest='warning',
        help="show warnings only",
    )

    level_group.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        dest='verbose',
        help="show detailed processing information",
    )

    arg_parser.add_argument(
        '-f',
        '--fix',
        action='store_true',
        dest='fix',
        help="automatically fix issues found",
    )

    args = arg_parser.parse_args()
    return args


def get_python_files():
    """Generator to yield all Python files recursively from the top dir, skipping IGNORE_DIR."""
    for root_dir in ROOT_DIRS:
        top_dir = os.path.join(BASE_DIR, root_dir)

        if not os.path.isdir(top_dir):
            Print.warning(f"Warning: Root directory '{root_dir}' does not exist, skipping.")
            continue

        for dirpath, _dirnames, filenames in os.walk(top_dir):
            if IGNORE_DIR in dirpath:
                continue

            for filename in filenames:
                if filename.endswith('.py'):
                    filepath = os.path.join(dirpath, filename)
                    short_path = filepath[BASE_DIR_LENGTH:]
                    yield filepath, short_path


def process_file(filepath, short_path, fix):
    """Process a single file to replace multiple imports on one line."""
    modified = False

    try:
        with open(filepath, 'r', encoding='utf8') as f:
            file_lines = f.readlines()

    except OSError as e:
        Print.warning(f"Error reading file '{short_path}': {e}")
        return False

    new_file_text = ''
    for line in file_lines:
        line = line.rstrip()
        matches = RE_IMPORT_LINE.match(line)

        if matches:
            if not fix:
                return True
            line = matches.group(1) + "(\n"
            import_items = [item.strip() for item in matches.group(2).split(',')]
            for item in sorted(import_items):
                line += f"    {item},\n"
            line += ')'
            modified = True

        new_file_text += line + '\n'

    if modified:
        try:
            with open(filepath, 'w', encoding='utf8') as f:
                f.write(new_file_text)

        except OSError as e:
            Print.warning(f"Error writing file '{short_path}': {e}")
            return False

    return modified


def main():
    """Checks for references to undefined option settings."""
    args = parse_command_line()
    file_count = 0
    updated_count = 0

    fix = args.fix

    if args.quiet:
        level = OUTPUT_LEVEL.SILENT
    elif args.warning:
        level = OUTPUT_LEVEL.WARNING
    elif args.verbose:
        level = OUTPUT_LEVEL.VERBOSE
    else:
        level = OUTPUT_LEVEL.NORMAL
    Print.set_level(level)

    Print.normal("Checking python imports")

    for filepath, short_path in get_python_files():
        file_count += 1

        Print.verbose(f"Processing file: {short_path}")

        if process_file(filepath, short_path, fix):
            Print.warning(f"Multiple imports found in: {short_path}")
            updated_count += 1

    if level > OUTPUT_LEVEL.WARNING or updated_count:
        print(
            f"Checked {file_count:,} file{make_plural(file_count)} ({updated_count:,} "
            f"issue{make_plural(updated_count)} {'fixed' if fix else 'found'})"
        )
        if not fix and updated_count:
            print(
                "Run the script with the --fix option to automatically fix "
                f"{'these issues' if updated_count > 1 else 'this issue'}."
            )

    sys.exit(min(updated_count, 1))


if __name__ == '__main__':
    main()
