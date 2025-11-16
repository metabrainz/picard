# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Bob Swift
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


ROOT_DIR = 'picard'
IGNORE_DIR = '__pycache__'

OPTION_TYPES_TO_CHECK = {'setting', 'persist'}

# Identify options created
RE_CREATE_OPTION = re.compile(
    "Option\\(\\s*['\"](" + '|'.join(OPTION_TYPES_TO_CHECK) + ")['\"\\s]*,\\s*['\"]([^'\"\\s,]*)", re.MULTILINE
)

# Ignore option checking in these files
CHECK_OPTION_FILES_TO_IGNORE = {'config_upgrade.py'}

# Identify options accessed
RE_CHECK_OPTION = re.compile(
    "(\\.(" + '|'.join(OPTION_TYPES_TO_CHECK) + ")\\[\\s*['\"]([^\\s'\"]*)[\\s'\"]*\\])", re.MULTILINE
)

# Ignore Option keys that start with any of the strings in the set()
CHECK_OPTION_PREFIXES_TO_IGNORE = {'splitters_'}
RE_CHECK_PREFIXES = re.compile("^(" + '|'.join(CHECK_OPTION_PREFIXES_TO_IGNORE) + ").*$")

# Ignore Option keys that contain any of the strings in the set()
CHECK_OPTION_CONTAINS_TO_IGNORE = {}
RE_CHECK_CONTAINS = re.compile("^.*(" + '|'.join(CHECK_OPTION_CONTAINS_TO_IGNORE) + ").*$")

# Ignore Option keys that end with any of the strings in the set()
CHECK_OPTION_SUFFIXES_TO_IGNORE = {}
RE_CHECK_SUFFIXES = re.compile("^.*(" + '|'.join(CHECK_OPTION_SUFFIXES_TO_IGNORE) + ")$")

# Dictionary containing defined options
options = {}


##############################################################################


def main():
    """Checks for references to undefined option settings."""
    args = sys.argv
    silent = '--silent' in args
    errors_only = '--errors-only' in args
    if not silent and not errors_only:
        print("Getting defined options.")
    file_text = ''
    file_count = 0
    for dirpath, _dirnames, filenames in os.walk(ROOT_DIR):
        if IGNORE_DIR in dirpath:
            continue

        for filename in filenames:
            if not filename.endswith('.py'):
                continue

            file_count += 1
            filepath = os.path.join(dirpath, filename)
            with open(filepath, 'r', encoding='utf8') as f:
                file_text = f.read()

            matches = RE_CREATE_OPTION.findall(file_text)
            for option_type, option_key in matches:
                if option_type not in options:
                    options[option_type] = set()
                options[option_type].add(option_key)

    count = 0
    for option_type in options.keys():
        count += len(options[option_type])

    if not silent and not errors_only:
        print(
            f"Checked {file_count:,} file{'' if file_count == 1 else 's'}. "
            f"Found {count:,} option key{'' if count == 1 else 's'} defined."
        )

        print("\nChecking option references.")

    count = 0
    error_count = 0
    file_text = ''
    for dirpath, _dirnames, filenames in os.walk(ROOT_DIR):
        if IGNORE_DIR in dirpath:
            continue

        for filename in filenames:
            if not filename.endswith('.py'):
                continue

            if filename in CHECK_OPTION_FILES_TO_IGNORE:
                continue

            filepath = os.path.join(dirpath, filename)

            with open(filepath, 'r', encoding='utf8') as f:
                file_text = f.read()

            matches = RE_CHECK_OPTION.findall(file_text)
            for match_text, match_type, match_key in matches:
                if CHECK_OPTION_PREFIXES_TO_IGNORE and RE_CHECK_PREFIXES.match(match_key):
                    continue

                if CHECK_OPTION_CONTAINS_TO_IGNORE and RE_CHECK_CONTAINS.match(match_key):
                    continue

                if CHECK_OPTION_SUFFIXES_TO_IGNORE and RE_CHECK_SUFFIXES.match(match_key):
                    continue

                count += 1
                if match_type not in options or match_key not in options[match_type]:
                    error_count += 1
                    if not silent:
                        print(f"* Invalid option: {match_text} in {filepath}")

    if not silent and not errors_only:
        print(
            f"Found {error_count:,} error{'' if error_count == 1 else 's'} in "
            f"{count} option reference{'' if count == 1 else 's'}."
        )

    sys.exit(min(1, error_count))


##############################################################################

if __name__ == '__main__':
    main()
