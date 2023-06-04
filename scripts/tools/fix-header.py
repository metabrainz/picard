#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020-2021 Laurent Monin
# Copyright (C) 2020-2021 Philipp Wolfer
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
from collections import defaultdict
import glob
import itertools
import logging
import os
import re
import subprocess  # nosec: B404
import sys


logging.basicConfig(
    force=True,
    format="%(asctime)s:%(levelname)s: %(message)s",
    level=logging.DEBUG,
    stream=sys.stderr,
)


ALIASES = {
    'abhi-ohri': 'Abhinav Ohri',
    'Antonio Larrosa <alarrosa@suse.com>': 'Antonio Larrosa',
    'Lukas Lalinsky <lalinsky@gmail.com>': 'Lukáš Lalinský',
    'petitminion': 'Petit Minion',
    'Philipp Wolfer <ph.wolfer@gmail.com>': 'Philipp Wolfer',
    'Ray': 'Ray Bouchard',
    'RaysDev': 'Ray Bouchard',
    'Sophist': 'Sophist-UK',
    'vishal choudhary': 'Vishal Choudhary',
    'vishichoudhary': 'Vishal Choudhary',
    'yvanzo': 'Yvan Rivière',
}


# https://stackoverflow.com/a/4629241
def ranges(i):
    for a, b in itertools.groupby(enumerate(i), lambda pair: pair[1] - pair[0]):
        b = list(b)
        yield b[0][1], b[-1][1]


def extract_authors_from_gitlog(path):
    authors = {}
    cmd = ['git', 'log', r'--pretty=format:%ad¤%aN¤%aE', r'--date=format:%Y', r'--', path]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, timeout=30)  # nosec: B603
    aliased = set()
    if result.returncode == 0:
        pattern = re.compile(r'^(?P<year>\d+)¤(?P<name>[^¤]*)¤(?P<email>.*)$')
        for line in result.stdout.decode('utf-8').split("\n"):
            matched = pattern.search(line)
            if matched:
                year = int(matched.group('year'))
                author = matched.group('name')
                email = matched.group('email')
                for c in (f"{author} <{email}>", email, author):
                    if c in ALIASES:
                        alias = ALIASES[c]
                        aliased.add(f"{author} <{email}> -> {alias}")
                        author = alias
                        break
                if author in authors:
                    if year not in authors[author]:
                        authors[author].append(year)
                else:
                    authors[author] = [year]
    for a in aliased:
        logging.debug(f"Alias found: {a}")

    return authors


def parse_copyright_text(text):
    authors = {}
    pattern_copyright = re.compile(r'^# Copyright \D*((?:\d{4}(?:,? *|-))+) (.+)\s*$')
    range_pattern = re.compile(r'^\s*(\d{4})\s*-\s*(\d{4})\s*$')

    for line in text.split("\n"):
        matched = pattern_copyright.search(line)
        if matched:
            all_years = []
            years_group = matched.group(1)
            author = matched.group(2)
            author = ALIASES.get(author, author)
            comma_years = []
            if ',' in years_group:
                for year in years_group.split(','):
                    comma_years.append(year.strip())
            else:
                comma_years.append(years_group.strip())

            for years in comma_years:
                m = range_pattern.search(years)
                if m:
                    year1 = int(m.group(1))
                    year2 = int(m.group(2))
                    for y in range(min(year1, year2), max(year1, year2)+1):
                        all_years.append(y)
                else:
                    all_years.append(int(years))
            if author in authors:
                for y in all_years:
                    if y not in authors[author]:
                        authors[author].append(y)
            else:
                authors[author] = all_years
    return authors


EMPTY_LINE = ("\n", "#\n")


def parse_file(path, encoding='utf-8'):
    authors_from_log = extract_authors_from_gitlog(path)
    start = end = None
    authors_from_file = {}

    fix_header_pattern = re.compile(r'^(?:#|/\*|//)\s+(fix-header:)\s*(.*)$', re.IGNORECASE)
    skip_pattern = re.compile(r'^(?:#|/\*|//)\s+(Automatically\s+generated|Created\s+by:\s+The\s+Resource\s+Compiler\s+for\s+PyQt5)', re.IGNORECASE)
    with open(path, encoding=encoding) as f:
        lines = f.readlines()
        found = defaultdict(lambda: None)
        if lines and lines[0].startswith('#!'):
            found["shebang"] = lines[0].rstrip()
            del lines[0]
        for num, line in enumerate(lines):
            skip_matched = skip_pattern.search(line)
            if skip_matched:
                found['skip'] = skip_matched.group(1)
                logging.debug("Found skip indicator: {}".format(found['skip']))
                return (found, {}, {}, '', "".join(lines))
            fix_header_matched = fix_header_pattern.search(line)
            if fix_header_matched:
                words = fix_header_matched.group(2).lower().split()
                if 'nolicense' in words:
                    # do not add a license header
                    logging.debug("Found fix-header: nolicense")
                    found['nolicense'] = True
                if 'skip' in words:
                    logging.debug("Found fix-header: skip")
                    found['skip'] = fix_header_matched.group(1) + ' ' + fix_header_matched.group(2)
                    return (found, {}, {}, '', "".join(lines))

        for num, line in enumerate(lines):
            if not line.startswith("#") and line not in EMPTY_LINE:
                break
            if "coding: utf-8" in line:
                del lines[num]
                i = num + 1
                while i < len(lines) and lines[i] in EMPTY_LINE:
                    del lines[i]
                break
        for num, line in enumerate(lines):
            if not line.startswith("#") and line not in EMPTY_LINE:
                break
            if "GNU General Public License" in line:
                found['license'] = num
                break
        if found['license'] is not None:
            i = starting_pos = found['license']
            while lines[i].startswith("#"):
                if i == 0:
                    break
                if lines[i].startswith("# Picard"):
                    break
                i -= 1
            while True:
                if i == 0:
                    break
                if lines[i-1] in EMPTY_LINE:
                    i -= 1
                else:
                    break
            start = i
            i = starting_pos
            while lines[i].startswith("#"):
                if i == len(lines) - 1:
                    break
                if lines[i].endswith(" USA.\n"):
                    break
                i += 1
            while True:
                if i == len(lines) - 1:
                    break
                if lines[i+1] in EMPTY_LINE:
                    i += 1
                else:
                    break
            end = i
            authors_from_file = parse_copyright_text("".join(lines[start:end]))
            before = lines[:start]
            after = lines[end+1:]
        else:
            before = []
            after = lines
        return found, authors_from_file, authors_from_log, "".join(before), "".join(after)


CODING_TEXT = """# -*- coding: utf-8 -*-
#
"""

LICENSE_TOP = """# Picard, the next-generation MusicBrainz tagger
#
"""

LICENSE_BOTTOM = """#
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
"""


def fix_header(path, encoding='utf-8'):
    found, authors_from_file, authors_from_log, before, after = parse_file(path, encoding)
    if found['skip'] is not None:
        return None, found['skip']

    authors = {}
    for a in authors_from_log:
        if a not in authors:
            authors[a] = set(authors_from_log[a])
    for b in authors_from_file:
        if b not in authors:
            authors[b] = set(authors_from_file[b])
        else:
            authors[b] = authors[b].union(authors_from_file[b])

    new_authors = {}
    for a in authors:
        new_authors[a] = []
        for y1, y2 in list(ranges(sorted(authors[a]))):
            if y1 == y2:
                new_authors[a].append(str(y1))
            else:
                new_authors[a].append("%d-%d" % (y1, y2))

    new_copyright = ""
    for author, years in sorted(new_authors.items(), key=lambda x: (sorted(x[1]), x[0])):
        new_copyright += "# Copyright (C) %s %s\n" % (", ".join(years), author)

    before = before.strip()
    after = after.strip()
    has_content = bool(before + after)

    parts = list(filter(None, [
        found["shebang"],
        CODING_TEXT.strip(),
        LICENSE_TOP.strip() if not found['nolicense'] else None,
        new_copyright.strip() if not found['nolicense'] else None,
        (LICENSE_BOTTOM.strip() + ("\n\n" if has_content else "")) if not found['nolicense'] else None,
        before.strip(),
        after.strip(),
    ]))
    return "\n".join(parts), None


def main():
    parser = argparse.ArgumentParser(
        description='Generate source file header with copyrights & license from existing header and git log',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('path', nargs='+', help='Path of a file or a folder of files')
    parser.add_argument('-e', '--extension', default='.py', help='File extension to filter by')
    parser.add_argument('-i', '--in-place', action='store_true', default=False, help='Edit files in place')
    parser.add_argument('-r', '--recursive', action='store_true', default=False, help='Search through subfolders')
    parser.add_argument('--encoding', default='utf-8', help='File encoding of the source files')
    args = parser.parse_args()

    paths = list(args.path)
    files = set()
    for path in paths:
        if os.path.isfile(path):
            name, ext = os.path.splitext(path)
            if args.extension in {'', ext}:
                files.add(path)
        else:
            if args.recursive:
                paths += glob.glob(path + '/*')
    if not files:
        logging.info("No valid file found")
        sys.exit(0)

    for path in files:
        new_content, info = fix_header(path, encoding=args.encoding)
        if new_content is None:
            logging.info("Skipping %s (%s)" % (path, info))
            continue
        if args.in_place:
            logging.info("Parsing and fixing %s (in place)" % path)
            with open(path, 'w', encoding=args.encoding) as f:
                print(new_content, file=f)
        else:
            # by default, we just output to stdout
            logging.info("Parsing and fixing %s (stdout)" % path)
            print(new_content)


if __name__ == '__main__':

    logging.debug("Starting...")

    main()
