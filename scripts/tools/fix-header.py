#!/usr/bin/env python
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020-2021, 2023, 2025-2026 Laurent Monin
# Copyright (C) 2020-2022, 2026 Philipp Wolfer
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


import argparse
from collections import defaultdict
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
    'bob': 'Bob Swift',
    'Lukas Lalinsky <lalinsky@gmail.com>': 'Lukáš Lalinský',
    'petitminion': 'Petit Minion',
    'Philipp Wolfer <ph.wolfer@gmail.com>': 'Philipp Wolfer',
    'Ray': 'Ray Bouchard',
    'RaysDev': 'Ray Bouchard',
    'Sophist': 'Sophist-UK',
    'twodoorcoupe': 'Giorgio Fontanive',
    'vishal choudhary': 'Vishal Choudhary',
    'vishichoudhary': 'Vishal Choudhary',
    'yvanzo': 'Yvan Rivière',
    'knguyen': 'Khoa Nguyen',
    'iron-prog': 'Deepak Tiwari',
    'Stevil Knevil': 'StevilKnevil',
    'deepakss-74': 'Deepak Kumar',
    'Thuna': 'Thuna-Cing',
    'Frederik "Freso" S. Olesen': 'Frederik "Freso" S. Olesen',
}

# Directories excluded by default when recursively scanning for files.
# These typically contain generated, third-party, or non-project code.
DEFAULT_EXCLUDED_DIRS = frozenset(
    {
        '.git',
        '.venv*',
        '.tox',
        '.nox',
        '.mypy_cache',
        '.ruff_cache',
        '.pytest_cache',
        '.eggs',
        '__pycache__',
        'build',
        'dist',
        'htmlcov',
        'locale',
        'node_modules',
        '*.egg-info',
    }
)


def _is_excluded_dir(dirname, excluded_dirs):
    """Check if a directory name matches any exclusion pattern."""
    for pattern in excluded_dirs:
        if '*' in pattern:
            # Simple glob matching (e.g., "*.egg-info")
            # Only supports leading or trailing wildcards
            if pattern.startswith('*') and dirname.endswith(pattern[1:]):
                return True
            if pattern.endswith('*') and dirname.startswith(pattern[:-1]):
                return True
        elif dirname == pattern:
            return True
    return False


# https://stackoverflow.com/a/4629241
def ranges(i):
    for _a, b in itertools.groupby(enumerate(i), lambda pair: pair[1] - pair[0]):
        b = list(b)
        yield b[0][1], b[-1][1]


def extract_authors_from_gitlog(path):
    """Extract authors and their contribution years from git log for a single file."""
    authors = {}
    cmd = [
        'git',
        'log',
        r'--invert-grep',
        r'--grep=fix-header:\ skip',
        r'--pretty=format:%ad¤%aN¤%aE',
        r'--date=format:%Y',
        r'--',
        path,
    ]
    try:
        result = subprocess.run(  # nosec: B603
            cmd,
            capture_output=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        logging.warning("git log timed out for %s", path)
        return {}
    except OSError as e:
        logging.error("Failed to run git log for %s: %s", path, e)
        return {}

    if result.returncode != 0:
        stderr_text = result.stderr.decode('utf-8', errors='replace').strip()
        if stderr_text:
            logging.warning("git log failed for %s: %s", path, stderr_text)
        return {}

    aliased = set()
    pattern = re.compile(r'^(?P<year>\d+)¤(?P<name>[^¤]*)¤(?P<email>.*)$')
    try:
        output = result.stdout.decode('utf-8')
    except UnicodeDecodeError:
        output = result.stdout.decode('utf-8', errors='replace')
        logging.warning("Encoding issues in git log output for %s", path)

    for line in output.split("\n"):
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
        logging.debug("Alias found: %s", a)

    return authors


def batch_extract_authors_from_gitlog(paths):
    """Extract authors for multiple files in a single git log call.

    This is significantly faster than calling git log per-file when
    processing many files, as it avoids the overhead of spawning a
    subprocess for each file.

    Returns a dict mapping each path to its authors dict.
    """
    if not paths:
        return {}

    cmd = [
        'git',
        'log',
        r'--invert-grep',
        r'--grep=fix-header:\ skip',
        r'--pretty=format:%H¤%ad¤%aN¤%aE',
        r'--date=format:%Y',
        r'--name-only',
        r'--',
    ] + list(paths)

    try:
        result = subprocess.run(  # nosec: B603
            cmd,
            capture_output=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        logging.warning("Batch git log timed out, falling back to per-file extraction")
        return None
    except OSError as e:
        logging.error("Failed to run batch git log: %s", e)
        return None

    if result.returncode != 0:
        stderr_text = result.stderr.decode('utf-8', errors='replace').strip()
        if stderr_text:
            logging.warning("Batch git log failed: %s", stderr_text)
        return None

    try:
        output = result.stdout.decode('utf-8')
    except UnicodeDecodeError:
        output = result.stdout.decode('utf-8', errors='replace')

    # Parse the output: each commit block is separated by a blank line.
    # Format: HASH¤YEAR¤NAME¤EMAIL\nFILE1\nFILE2\n...\n\n
    authors_by_path = defaultdict(dict)
    commit_pattern = re.compile(r'^[0-9a-f]+¤(?P<year>\d+)¤(?P<name>[^¤]*)¤(?P<email>.*)$')

    current_year = None
    current_author = None
    path_set = set(paths)

    for line in output.split("\n"):
        if not line:
            current_year = None
            current_author = None
            continue

        commit_match = commit_pattern.match(line)
        if commit_match:
            current_year = int(commit_match.group('year'))
            author = commit_match.group('name')
            email = commit_match.group('email')
            for c in (f"{author} <{email}>", email, author):
                if c in ALIASES:
                    author = ALIASES[c]
                    break
            current_author = author
        elif current_year is not None and current_author is not None:
            # This is a filename line
            file_path = line.strip()
            if file_path in path_set:
                author_years = authors_by_path[file_path]
                if current_author in author_years:
                    if current_year not in author_years[current_author]:
                        author_years[current_author].append(current_year)
                else:
                    author_years[current_author] = [current_year]

    return dict(authors_by_path)


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
                    for y in range(min(year1, year2), max(year1, year2) + 1):
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


def parse_file(path, encoding='utf-8', authors_from_log=None):
    if authors_from_log is None:
        authors_from_log = extract_authors_from_gitlog(path)
    start = end = None
    authors_from_file = {}

    fix_header_pattern = re.compile(r'^(?:#|/\*|//)\s+(fix-header:)\s*(.*)$', re.IGNORECASE)
    skip_pattern = re.compile(
        r'^(?:#|/\*|//)\s+(Automatically\s+generated|Created\s+by:\s+The\s+Resource\s+Compiler\s+for\s+Qt)',
        re.IGNORECASE,
    )
    try:
        with open(path, encoding=encoding) as f:
            lines = f.readlines()
    except OSError as e:
        logging.error("Failed to read %s: %s", path, e)
        return (defaultdict(lambda: None), {}, {}, '', '')
    except UnicodeDecodeError as e:
        logging.error("Encoding error reading %s with %s: %s", path, encoding, e)
        return (defaultdict(lambda: None), {}, {}, '', '')

    found = defaultdict(lambda: None)
    if lines and lines[0].startswith('#!'):
        found["shebang"] = lines[0].rstrip()
        del lines[0]
    for line in lines:
        skip_matched = skip_pattern.search(line)
        if skip_matched:
            found['skip'] = skip_matched.group(1)
            logging.debug("Found skip indicator: %s", found['skip'])
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
            if lines[i - 1] in EMPTY_LINE:
                i -= 1
            else:
                break
        start = i
        i = starting_pos
        while lines[i].startswith("#"):
            if i == len(lines) - 1:
                break
            # Detect end of license block: old-style (FSF address ending
            # in "USA.") or new-style (URL ending in "licenses/>.").
            if lines[i].endswith(" USA.\n") or lines[i].endswith("licenses/>.\n"):
                break
            i += 1
        while True:
            if i == len(lines) - 1:
                break
            if lines[i + 1] in EMPTY_LINE:
                i += 1
            else:
                break
        end = i
        authors_from_file = parse_copyright_text("".join(lines[start:end]))
        before = lines[:start]
        after = lines[end + 1 :]
    else:
        before = []
        after = lines
    return found, authors_from_file, authors_from_log, "".join(before), "".join(after)


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
# along with this program; if not, see <https://www.gnu.org/licenses/>.
"""


def fix_header(path, encoding='utf-8', authors_from_log=None):
    found, authors_from_file, authors_from_log, before, after = parse_file(
        path, encoding, authors_from_log=authors_from_log
    )
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

    parts = list(
        filter(
            None,
            [
                found["shebang"],
                LICENSE_TOP.strip() if not found['nolicense'] else None,
                new_copyright.strip() if not found['nolicense'] else None,
                (LICENSE_BOTTOM.strip() + ("\n\n" if has_content else "")) if not found['nolicense'] else None,
                before.strip(),
                after.strip(),
            ],
        )
    )
    return "\n".join(parts), None


def collect_files(paths, extension, recursive, excluded_dirs):
    """Collect files to process using os.walk for efficient directory traversal.

    Uses os.walk with in-place modification of dirs list to skip excluded
    directories, which is more efficient than recursive glob as it avoids
    descending into irrelevant subtrees entirely.
    """
    files = set()
    for path in paths:
        if os.path.isfile(path):
            _name, ext = os.path.splitext(path)
            if extension in {'', ext}:
                files.add(path)
        elif os.path.isdir(path) and recursive:
            for dirpath, dirnames, filenames in os.walk(path):
                # Modify dirnames in-place to skip excluded directories.
                # This prevents os.walk from descending into them.
                dirnames[:] = [d for d in dirnames if not _is_excluded_dir(d, excluded_dirs)]
                for filename in filenames:
                    _name, ext = os.path.splitext(filename)
                    if extension in {'', ext}:
                        files.add(os.path.join(dirpath, filename))
    return files


def main():
    parser = argparse.ArgumentParser(
        description='Generate source file header with copyrights & license from existing header and git log',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('path', nargs='+', help='Path of a file or a folder of files')
    parser.add_argument('-e', '--extension', default='.py', help='File extension to filter by')
    parser.add_argument('-i', '--in-place', action='store_true', default=False, help='Edit files in place')
    parser.add_argument('-r', '--recursive', action='store_true', default=False, help='Search through subfolders')
    parser.add_argument('--encoding', default='utf-8', help='File encoding of the source files')
    parser.add_argument(
        '--exclude',
        action='append',
        default=None,
        metavar='DIR',
        help='Directory name to exclude (can be specified multiple times). '
        'Supports simple glob patterns like "*.egg-info". '
        'Defaults: ' + ', '.join(sorted(DEFAULT_EXCLUDED_DIRS)),
    )
    parser.add_argument(
        '--no-default-excludes',
        action='store_true',
        default=False,
        help='Do not use the default exclusion list',
    )
    parser.add_argument(
        '--no-batch',
        action='store_true',
        default=False,
        help='Disable batch git log (use per-file git log instead)',
    )
    args = parser.parse_args()

    # Build the exclusion set
    if args.no_default_excludes:
        excluded_dirs = frozenset(args.exclude) if args.exclude else frozenset()
    else:
        base = set(DEFAULT_EXCLUDED_DIRS)
        if args.exclude:
            base.update(args.exclude)
        excluded_dirs = frozenset(base)

    files = collect_files(args.path, args.extension, args.recursive, excluded_dirs)

    if not files:
        logging.info("No valid file found")
        sys.exit(0)

    logging.info("Found %d file(s) to process", len(files))

    # Try batch git log for all files at once (much faster for large sets)
    authors_cache = {}
    if not args.no_batch and len(files) > 1:
        logging.debug("Attempting batch git log for %d files", len(files))
        batch_result = batch_extract_authors_from_gitlog(list(files))
        if batch_result is not None:
            authors_cache = batch_result
            logging.debug("Batch git log succeeded, got data for %d files", len(authors_cache))
        else:
            logging.debug("Batch git log failed, falling back to per-file extraction")

    for path in sorted(files):
        authors_from_log = authors_cache.get(path)
        new_content, info = fix_header(path, encoding=args.encoding, authors_from_log=authors_from_log)
        if new_content is None:
            logging.info("Skipping %s (%s)", path, info)
            continue
        if args.in_place:
            logging.info("Parsing and fixing %s (in place)", path)
            try:
                with open(path, 'w', encoding=args.encoding) as f:
                    print(new_content, file=f)
            except OSError as e:
                logging.error("Failed to write %s: %s", path, e)
        else:
            # by default, we just output to stdout
            logging.info("Parsing and fixing %s (stdout)", path)
            print(new_content)


if __name__ == '__main__':
    logging.debug("Starting...")

    main()
