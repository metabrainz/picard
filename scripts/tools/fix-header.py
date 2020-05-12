#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020 Laurent Monin
# Copyright (C) 2020 Philipp Wolfer
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
import os
import re
import subprocess  # nosec: B404
import sys


ALIASES = {
    'abhi-ohri': 'Abhinav Ohri',
    'Antonio Larrosa <alarrosa@suse.com>': 'Antonio Larrosa',
    'Lukas Lalinsky <lalinsky@gmail.com>': 'Lukáš Lalinský',
    'Philipp Wolfer <ph.wolfer@gmail.com>': 'Philipp Wolfer',
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
    cmd = ['git', 'log', r'--pretty=format:%ad %aN', r'--date=format:%Y', r'--', path]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, timeout=30)  # nosec: B603
    if result.returncode == 0:
        pattern = re.compile(r'^(\d+) (.*)$')
        for line in result.stdout.decode('utf-8').split("\n"):
            match = pattern.search(line)
            if match:
                year = int(match.group(1))
                author = match.group(2)
                author = ALIASES.get(author, author)
                if author in authors:
                    if year not in authors[author]:
                        authors[author].append(year)
                else:
                    authors[author] = [year]
    return authors


def parse_copyright_text(text):
    authors = {}
    pattern_copyright = re.compile(r'^# Copyright \D*((?:\d{4}(?:,? *|-))+) (.+)\s*$')
    range_pattern = re.compile(r'^\s*(\d{4})\s*-\s*(\d{4})\s*$')

    for line in text.split("\n"):
        match = pattern_copyright.search(line)
        if match:
            all_years = []
            years_group = match.group(1)
            author = match.group(2)
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


def parse_file(path):
    authors_from_log = extract_authors_from_gitlog(path)
    start = end = None
    authors_from_file = {}

    skip_pattern = re.compile(r'^(?:#|/\*|//)\s+(fix-header:\s*skip|Automatically\s+generated)', re.IGNORECASE)
    with open(path) as f:
        lines = f.readlines()
        found = defaultdict(lambda: None)
        if lines and lines[0].startswith('#!'):
            found["shebang"] = lines[0].rstrip()
            del lines[0]
        for num, line in enumerate(lines):
            match = skip_pattern.search(line)
            if match:
                found['skip'] = match.group(1)
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


def fix_header(path):
    found, authors_from_file, authors_from_log, before, after = parse_file(path)
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
        LICENSE_TOP.strip(),
        new_copyright.strip(),
        LICENSE_BOTTOM.strip() + ("\n\n" if has_content else ""),
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
    args = parser.parse_args()

    paths = list(args.path)
    files = set()
    for path in paths:
        if os.path.isfile(path):
            name, ext = os.path.splitext(path)
            if args.extension in ('', ext):
                files.add(path)
        else:
            if args.recursive:
                paths += glob.glob(path + '/*')
    if not files:
        print("No valid file found", file=sys.stderr)
        sys.exit(0)

    for path in files:
        new_content, info = fix_header(path)
        if new_content is None:
            print("Skipping %s (%s)" % (path, info), file=sys.stderr)
            continue
        if args.in_place:
            print("Parsing and fixing %s (in place)" % path, file=sys.stderr)
            with open(path, 'w') as f:
                print(new_content, file=f)
        else:
            # by default, we just output to stdout
            print("Parsing and fixing %s (stdout)" % path, file=sys.stderr)
            print(new_content)


if __name__ == '__main__':
    main()
