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
import difflib
import fnmatch
import itertools
import logging
import os
import re
import subprocess  # nosec: B404
import sys


logging.basicConfig(
    force=True,
    format="%(asctime)s:%(levelname)s: %(message)s",
    level=logging.INFO,
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

# Pre-compiled regex patterns
_RE_GITLOG_LINE = re.compile(r'^(\d+)¤([^¤]*)¤(.*)$')
_RE_GITLOG_BATCH_LINE = re.compile(r'^[0-9a-f]+¤(\d+)¤([^¤]*)¤(.*)$')
_RE_COPYRIGHT = re.compile(r'^# Copyright \D*((?:\d{4}(?:,? *|-))+) (.+)\s*$')
_RE_YEAR_RANGE = re.compile(r'^\s*(\d{4})\s*-\s*(\d{4})\s*$')
_RE_FIX_HEADER = re.compile(r'^(?:#|/\*|//)\s+(fix-header:)\s*(.*)$', re.IGNORECASE)
_RE_SKIP_INDICATOR = re.compile(
    r'^(?:#|/\*|//)\s+(Automatically\s+generated|Created\s+by:\s+The\s+Resource\s+Compiler\s+for\s+Qt)',
    re.IGNORECASE,
)


def _compile_exclusion_patterns(patterns):
    """Pre-compile exclusion patterns into a single combined regex for fast matching."""
    if not patterns:
        return None
    regex_parts = [fnmatch.translate(p) for p in patterns]
    return re.compile('|'.join(regex_parts))


def _is_excluded_dir(dirname, exclusion_regex):
    """Check if a directory name matches the pre-compiled exclusion regex."""
    if exclusion_regex is None:
        return False
    return exclusion_regex.match(dirname) is not None


def _resolve_alias(author, email):
    """Resolve an author name/email combination through ALIASES."""
    for key in (f"{author} <{email}>", email, author):
        if key in ALIASES:
            return ALIASES[key]
    return author


def _run_git(cmd, timeout=30):
    """Run a git command and return decoded stdout, or None on failure."""
    try:
        result = subprocess.run(  # nosec: B603
            cmd,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        logging.warning("git command timed out: %s", ' '.join(cmd[:3]))
        return None
    except OSError as e:
        logging.error("Failed to run git: %s", e)
        return None

    if result.returncode != 0:
        stderr_text = result.stderr.decode('utf-8', errors='replace').strip()
        if stderr_text:
            logging.warning("git failed: %s", stderr_text)
        return None

    return result.stdout.decode('utf-8', errors='replace')


# https://stackoverflow.com/a/4629241
def _year_ranges(years):
    """Collapse a sorted list of years into range strings (e.g. [2020,2021,2023] -> ['2020-2021','2023'])."""
    result = []
    for _a, b in itertools.groupby(enumerate(sorted(years)), lambda pair: pair[1] - pair[0]):
        b = list(b)
        y1, y2 = b[0][1], b[-1][1]
        result.append(str(y1) if y1 == y2 else f"{y1}-{y2}")
    return result


def extract_authors_from_gitlog(path):
    """Extract authors and their contribution years from git log for a single file."""
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
    output = _run_git(cmd)
    if output is None:
        return {}

    authors = {}
    for line in output.split("\n"):
        m = _RE_GITLOG_LINE.match(line)
        if m:
            year = int(m.group(1))
            author = _resolve_alias(m.group(2), m.group(3))
            authors.setdefault(author, set()).add(year)
    return authors


def batch_extract_authors_from_gitlog(paths):
    """Extract authors for multiple files in a single git log call.

    Returns a dict mapping each path to its {author: set(years)} dict,
    or None on failure.
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

    output = _run_git(cmd, timeout=120)
    if output is None:
        return None

    authors_by_path = {}
    path_set = set(paths)

    current_year = None
    current_author = None

    for line in output.split("\n"):
        if not line:
            current_year = None
            current_author = None
            continue

        m = _RE_GITLOG_BATCH_LINE.match(line)
        if m:
            current_year = int(m.group(1))
            current_author = _resolve_alias(m.group(2), m.group(3))
        elif current_year is not None and current_author is not None:
            file_path = line.strip()
            if file_path in path_set:
                file_authors = authors_by_path.setdefault(file_path, {})
                file_authors.setdefault(current_author, set()).add(current_year)

    return authors_by_path


def parse_copyright_text(text):
    """Parse existing copyright lines into {author: set(years)}."""
    authors = {}

    for line in text.split("\n"):
        matched = _RE_COPYRIGHT.match(line)
        if not matched:
            continue
        years_group = matched.group(1)
        author = ALIASES.get(matched.group(2), matched.group(2))

        all_years = set()
        for part in years_group.split(','):
            m = _RE_YEAR_RANGE.match(part.strip())
            if m:
                all_years.update(range(int(m.group(1)), int(m.group(2)) + 1))
            else:
                all_years.add(int(part.strip()))

        authors.setdefault(author, set()).update(all_years)
    return authors


EMPTY_LINE = ("\n", "#\n")


def parse_file(path, encoding='utf-8', authors_from_log=None):
    if authors_from_log is None:
        authors_from_log = extract_authors_from_gitlog(path)

    try:
        with open(path, encoding=encoding) as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError) as e:
        logging.error("Failed to read %s: %s", path, e)
        return ({'skip': str(e)}, {}, {}, '', '')

    found = {}
    if lines and lines[0].startswith('#!'):
        found["shebang"] = lines[0].rstrip()
        del lines[0]

    for line in lines:
        skip_matched = _RE_SKIP_INDICATOR.search(line)
        if skip_matched:
            found['skip'] = skip_matched.group(1)
            logging.debug("Found skip indicator: %s", found['skip'])
            return (found, {}, {}, '', "".join(lines))
        fix_header_matched = _RE_FIX_HEADER.search(line)
        if fix_header_matched:
            words = fix_header_matched.group(2).lower().split()
            if 'nolicense' in words:
                logging.debug("Found fix-header: nolicense")
                found['nolicense'] = True
            if 'skip' in words:
                found['skip'] = fix_header_matched.group(1) + ' ' + fix_header_matched.group(2)
                logging.debug("Found fix-header: skip")
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

    start = end = None
    for num, line in enumerate(lines):
        if not line.startswith("#") and line not in EMPTY_LINE:
            break
        if "GNU General Public License" in line:
            # Find start of license block (search backwards)
            i = num
            while lines[i].startswith("#") and i > 0 and not lines[i].startswith("# Picard"):
                i -= 1
            while i > 0 and lines[i - 1] in EMPTY_LINE:
                i -= 1
            start = i

            # Find end of license block (search forwards)
            i = num
            while i < len(lines) - 1 and lines[i].startswith("#"):
                # Detect end: old-style (FSF address "USA.") or new-style ("licenses/>.").
                if lines[i].endswith(" USA.\n") or lines[i].endswith("licenses/>.\n"):
                    break
                i += 1
            while i < len(lines) - 1 and lines[i + 1] in EMPTY_LINE:
                i += 1
            end = i
            break

    if start is not None and end is not None:
        authors_from_file = parse_copyright_text("".join(lines[start:end]))
        before = lines[:start]
        after = lines[end + 1 :]
    else:
        authors_from_file = {}
        before = []
        after = lines

    return found, authors_from_file, authors_from_log, "".join(before), "".join(after)


LICENSE_TOP = "# Picard, the next-generation MusicBrainz tagger\n#\n"

LICENSE_BOTTOM = """\
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
"""


def fix_header(path, encoding='utf-8', authors_from_log=None):
    found, authors_from_file, authors_from_log, before, after = parse_file(
        path, encoding, authors_from_log=authors_from_log
    )
    if found.get('skip') is not None:
        return None, found['skip']

    # Merge authors from git log and file header
    authors = {}
    for source in (authors_from_log, authors_from_file):
        for author, years in source.items():
            authors.setdefault(author, set()).update(years)

    # Build copyright lines sorted by earliest year then name
    copyright_lines = []
    for author, years in sorted(authors.items(), key=lambda x: (sorted(_year_ranges(x[1])), x[0])):
        copyright_lines.append(f"# Copyright (C) {', '.join(_year_ranges(years))} {author}")
    new_copyright = "\n".join(copyright_lines)

    before = before.strip()
    after = after.strip()
    has_content = bool(before + after)
    nolicense = found.get('nolicense')

    parts = []
    if found.get("shebang"):
        parts.append(found["shebang"])
    if not nolicense:
        parts.append(LICENSE_TOP.strip())
        parts.append(new_copyright)
        parts.append(LICENSE_BOTTOM.strip() + ("\n\n" if has_content else ""))
    if before:
        parts.append(before)
    if after:
        parts.append(after)

    return "\n".join(parts), None


def collect_files(paths, extension, recursive, exclusion_regex, use_git=True):
    """Collect files to process.

    When use_git is True (default), uses 'git ls-files' which automatically
    respects .gitignore and only returns tracked/staged files. Falls back
    to os.walk if git is unavailable or the path is outside a git repo.
    """
    files = set()
    for path in paths:
        if os.path.isfile(path):
            _name, ext = os.path.splitext(path)
            if extension in {'', ext}:
                files.add(path)
        elif os.path.isdir(path) and recursive:
            if use_git:
                git_files = _collect_files_git(path, extension)
                if git_files is not None:
                    files.update(git_files)
                    continue
            # Fallback: os.walk with exclusion patterns
            for dirpath, dirnames, filenames in os.walk(path):
                dirnames[:] = [d for d in dirnames if not _is_excluded_dir(d, exclusion_regex)]
                for filename in filenames:
                    _name, ext = os.path.splitext(filename)
                    if extension in {'', ext}:
                        files.add(os.path.join(dirpath, filename))
    return files


def _collect_files_git(path, extension):
    """Use git ls-files to discover tracked files matching the extension."""
    cmd = ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '--']
    if extension:
        # Use glob pathspec to match the extension recursively
        cmd.append(f'{path}/**/*{extension}')
    else:
        cmd.append(path)
    output = _run_git(cmd)
    if output is None:
        return None
    return {f for f in output.splitlines() if f}


def main():
    parser = argparse.ArgumentParser(
        description='Generate source file header with copyrights & license from existing header and git log',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('path', nargs='+', help='Path of a file or a folder of files')
    parser.add_argument('-e', '--extension', default='.py', help='File extension to filter by')
    parser.add_argument('-i', '--in-place', action='store_true', default=False, help='Edit files in place')
    parser.add_argument(
        '-n',
        '--dry-run',
        action='store_true',
        default=False,
        help='Show unified diff of changes without writing files',
    )
    parser.add_argument('-r', '--recursive', action='store_true', default=False, help='Search through subfolders')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Enable debug logging')
    parser.add_argument('--encoding', default='utf-8', help='File encoding of the source files')
    parser.add_argument(
        '--exclude',
        action='append',
        default=None,
        metavar='DIR',
        help='Directory name to exclude (can be specified multiple times). '
        'Supports glob patterns (fnmatch). '
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
    parser.add_argument(
        '--no-git-ls',
        action='store_true',
        default=False,
        help='Disable git ls-files for file discovery (use os.walk with exclusions instead)',
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Build the exclusion set
    if args.no_default_excludes:
        excluded_dirs = frozenset(args.exclude) if args.exclude else frozenset()
    else:
        base = set(DEFAULT_EXCLUDED_DIRS)
        if args.exclude:
            base.update(args.exclude)
        excluded_dirs = frozenset(base)
    exclusion_regex = _compile_exclusion_patterns(excluded_dirs)

    files = collect_files(args.path, args.extension, args.recursive, exclusion_regex, use_git=not args.no_git_ls)

    if not files:
        logging.info("No valid file found")
        sys.exit(0)

    logging.info("Found %d file(s) to process", len(files))

    # Try batch git log for all files at once (much faster for large sets)
    authors_cache = None
    if not args.no_batch and len(files) > 1:
        logging.debug("Attempting batch git log for %d files", len(files))
        batch_result = batch_extract_authors_from_gitlog(list(files))
        if batch_result is not None:
            authors_cache = batch_result
            logging.debug("Batch git log succeeded, got data for %d files", len(authors_cache))
        else:
            logging.debug("Batch git log failed, falling back to per-file extraction")

    for path in sorted(files):
        # If batch succeeded, use its result (even if empty for this path).
        # Only fall back to per-file git log if batch didn't run at all.
        if authors_cache is not None:
            authors_from_log = authors_cache.get(path, {})
        else:
            authors_from_log = None
        new_content, info = fix_header(path, encoding=args.encoding, authors_from_log=authors_from_log)
        if new_content is None:
            logging.info("Skipping %s (%s)", path, info)
            continue
        if args.dry_run:
            try:
                with open(path, encoding=args.encoding) as f:
                    original = f.read()
            except (OSError, UnicodeDecodeError):
                original = ''
            if original.rstrip('\n') != new_content.rstrip('\n'):
                diff = difflib.unified_diff(
                    original.splitlines(keepends=True),
                    (new_content + '\n').splitlines(keepends=True),
                    fromfile=f'a/{path}',
                    tofile=f'b/{path}',
                )
                sys.stdout.writelines(diff)
        elif args.in_place:
            logging.info("Parsing and fixing %s (in place)", path)
            try:
                with open(path, 'w', encoding=args.encoding) as f:
                    print(new_content, file=f)
            except OSError as e:
                logging.error("Failed to write %s: %s", path, e)
        else:
            logging.info("Parsing and fixing %s (stdout)", path)
            print(new_content)


if __name__ == '__main__':
    logging.debug("Starting...")
    main()
