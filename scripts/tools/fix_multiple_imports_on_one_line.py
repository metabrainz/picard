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


import os
import re
import sys


ROOT_DIRS = ['picard', 'scripts', 'test']
IGNORE_DIR = '__pycache__'

RE_IMPORT_LINE = re.compile(r'^(from\s+\S+\s+import\s+)([^(].*,.*[^\\])$')


def get_python_files():
    """Generator to yield all Python files recursively from the top dir, skipping IGNORE_DIR."""
    for top_dir in ROOT_DIRS:
        for dirpath, _dirnames, filenames in os.walk(top_dir):
            if IGNORE_DIR in dirpath:
                continue

            for filename in filenames:
                if filename.endswith('.py'):
                    yield os.path.join(dirpath, filename)


def process_file(filepath):
    """Process a single file to replace multiple imports on one line."""
    modified = False

    with open(filepath, 'r', encoding='utf8') as f:
        file_lines = f.readlines()

    new_file_text = ''
    for line in file_lines:
        line = line.rstrip()
        matches = RE_IMPORT_LINE.match(line)

        if matches:
            line = matches.group(1) + "(\n"
            import_items = [item.strip() for item in matches.group(2).split(',')]
            for item in sorted(import_items):
                line += f"    {item},\n"
            line += ')'
            modified = True

        new_file_text += line + '\n'

    if modified:
        with open(filepath, 'w', encoding='utf8') as f:
            f.write(new_file_text)

    return modified


class OUTPUT_LEVEL:
    SILENT = 0
    CHANGES_ONLY = 1
    NORMAL = 2
    VERBOSE = 3


def main():
    """Checks for references to undefined option settings."""
    args = sys.argv
    file_count = 0
    updated_count = 0
    level = OUTPUT_LEVEL.NORMAL

    if '--silent' in args:
        level = OUTPUT_LEVEL.SILENT
    elif '--changes-only' in args:
        level = OUTPUT_LEVEL.CHANGES_ONLY
    elif '--verbose' in args:
        level = OUTPUT_LEVEL.VERBOSE

    if level > OUTPUT_LEVEL.CHANGES_ONLY:
        print("Checking python imports.")

    for filepath in get_python_files():
        file_count += 1

        if level > OUTPUT_LEVEL.NORMAL:
            print(f"Processing file: {filepath}")

        if process_file(filepath):
            if level > OUTPUT_LEVEL.SILENT:
                print(f"Updated imports in: {filepath}")
            updated_count += 1

    if level > OUTPUT_LEVEL.CHANGES_ONLY or updated_count:
        print(f"Checked {file_count:,} file{'' if file_count == 1 else 's'} ({updated_count:,} updated).")

    sys.exit(min(updated_count, 1))


if __name__ == '__main__':
    main()
