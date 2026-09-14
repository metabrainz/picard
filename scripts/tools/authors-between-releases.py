#!/usr/bin/env python3
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
# Copyright (C) 2026 Philipp Wolfer
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


"""List authors between two releases for use in blog posts and release notes.

Outputs code contributors and translators (with languages) based on git log.
Translators are identified by "Translated using Weblate (Language)" commit
messages and are listed separately from code contributors.

When available, GitHub profile URLs are included for code contributors and
Weblate profile URLs for translators.

Set WEBLATE_API_KEY environment variable to resolve Weblate usernames via
the project credits API. Set GITHUB_TOKEN to avoid GitHub API rate limits
when resolving contributor display names (a fine-grained personal access
token with no permissions is sufficient).

Examples:
    # Between the last two tagged releases (default)
    python scripts/tools/authors-between-releases.py

    # Between specific releases
    python scripts/tools/authors-between-releases.py --from release-3.0.0a4 --to release-3.0.0b1

    # With Weblate API for translator profile links
    WEBLATE_API_KEY=your-token python scripts/tools/authors-between-releases.py
"""

import argparse
from datetime import (
    date,
    timedelta,
)
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
from urllib.parse import quote as url_quote
from urllib.request import (
    Request,
    urlopen,
)


try:
    from wlc.config import WeblateConfig
except ImportError:
    WeblateConfig = None  # type: ignore


EXCLUDE = {'Weblate', 'dependabot[bot]', 'Automatic translation add-on'}

# Human-maintained normalization map for language names. Different Weblate
# commit-message labels can name the same language differently (e.g. an older
# "(Simplified)" label vs the current "(Simplified Han script)" for the same
# zh_Hans/zh_CN translation). Map variant spellings to a single canonical name.
# Add entries here when the same language shows up under more than one name.
LANGUAGE_ALIASES = {
    'Chinese (Simplified)': 'Chinese (Simplified Han script)',
    'Chinese (Traditional)': 'Chinese (Traditional Han script)',
}


def canonical_language(name):
    """Return the canonical language name for a possibly-variant spelling."""
    return LANGUAGE_ALIASES.get(name, name)


# Human-maintained map crediting code authors for languages they genuinely
# translated. Code authors are otherwise excluded from the translator list
# (they appear in the code-contributions line, and the commit-message language
# labels over-attribute maintainers who merely merged translation PRs). Use
# canonical language names (post LANGUAGE_ALIASES). Only affects --by-language.
#
# 'weblate' is the contributor's Weblate username, used for the profile link
# when their git author name differs from their Weblate account name (so the
# automatic name-based lookup would miss it).
CODE_AUTHOR_TRANSLATIONS = {
    'Laurent Monin': {'langs': {'French'}, 'weblate': 'Zas'},
    'Philipp Wolfer': {'langs': {'German'}, 'weblate': 'outsidecontext'},
}

# Human-maintained map of translator name -> Weblate username, for translators
# whose Weblate account cannot be resolved automatically (their git commit
# email is not a Weblate noreply address and they are absent from the credits
# API window). Consulted when building profile links.
TRANSLATOR_WEBLATE_USERS = {
    'Nicolás Tamargo': 'reosarevok',
}


def is_weblate_bot_username(username):
    """Return True for automated Weblate accounts (addon:, mt:, webhook:, ...).

    All such system accounts use a 'prefix:' form in their username; human
    usernames never contain a colon.
    """
    return ':' in username


# Paths containing translation files managed via Weblate.
# Used to separate translators from code contributors.
TRANSLATION_PATHS = ('po/', 'installer/i18n/sources/')

WEBLATE_BASE_URL = 'https://translations.metabrainz.org'
WEBLATE_API_URL = f'{WEBLATE_BASE_URL}/api'
WEBLATE_USER_URL = f'{WEBLATE_BASE_URL}/user'
GITHUB_URL = 'https://github.com'


QUIET = False


# Pre-compiled regex patterns used in loops
RE_MERGE_PR = re.compile(r'^[0-9a-f]+ ([0-9a-f]+) Merge pull request #\d+ from ([^/]+)/')
RE_GITHUB_NOREPLY = re.compile(r'^(?:\d+\+)?(.+)@users\.noreply\.github\.com$')
RE_WEBLATE_NOREPLY = re.compile(r'^(.+)@users\.noreply\.translations\.metabrainz\.org$')
RE_WEBLATE_LANG = re.compile(r'Translated using Weblate \((.+)\)')


def debug(msg):
    """Print a debug message to stderr unless quiet mode is enabled."""
    if not QUIET:
        print(f"  {msg}", file=sys.stderr)


def _find_git():
    """Find the git executable on the system."""
    path = shutil.which('git')
    if not path:
        raise SystemExit("git executable not found in PATH")
    return path


GIT = _find_git()


def git(*args, **kwargs):
    """Run a git command and return stripped stdout."""
    return subprocess.check_output([GIT, *args], text=True, **kwargs)


def get_release_tags():
    """Return release tags sorted by date, most recent first."""
    return git('tag', '--sort=-creatordate', '--list', 'release-[0-9]*').splitlines()


def get_tag_date(tag):
    """Return the ISO date (YYYY-MM-DD) of a tag."""
    return git('log', '-1', '--format=%aI', tag).strip()[:10]


def git_log_lines(fmt, rev_range=None, extra_flags=(), pathspecs=()):
    """Run 'git log' and return its output lines.

    Centralizes the common invocation shape: optional flags, a --format
    string, an optional revision range (None/empty scans full history), and
    optional pathspecs (added after a '--' separator).
    """
    args = ['log', *extra_flags, f'--format={fmt}']
    if rev_range:
        args.append(rev_range)
    if pathspecs:
        args.extend(('--', *pathspecs))
    return git(*args).splitlines()


def get_github_users_from_merges(rev_range=None):
    """Map author names to GitHub usernames from PR merge commits.

    With rev_range=None, scans the full repository history.
    """
    pr_parents = {}
    for line in git_log_lines('%P %s', rev_range, extra_flags=('--merges',)):
        match = RE_MERGE_PR.search(line)
        if match:
            pr_parents[match.group(1)] = match.group(2)

    if not pr_parents:
        return {}

    debug(f"Resolving {len(pr_parents)} merge commits to GitHub usernames")
    github_users = {}
    result = git(
        'log',
        '--format=%H %aN',
        '--stdin',
        '--no-walk=unsorted',
        input='\n'.join(pr_parents),
    )
    for line in result.splitlines():
        if ' ' not in line:
            continue
        sha, author = line.split(' ', 1)
        if author and author not in EXCLUDE:
            github_users.setdefault(author, pr_parents[sha])
    debug(f"Found {len(github_users)} GitHub users from merge commits")
    return github_users


def iter_git_log(rev_range, format_fields, *pathspecs):
    """Yield tuples from git log with tab-separated format fields.

    Args:
        rev_range: Git revision range (e.g. 'tag1..tag2'), or None/empty to
            scan the full repository history.
        format_fields: Git format placeholders (e.g. '%aN', '%aE', '%s')
        *pathspecs: Optional pathspec arguments for git log
    """
    fmt = '\t'.join(format_fields)
    num_fields = len(format_fields)
    for line in git_log_lines(fmt, rev_range, pathspecs=pathspecs):
        if '\t' not in line:
            continue
        yield line.split('\t', num_fields - 1)


def _map_names_by_email(rev_range, pattern, pathspecs=(), label=None):
    """Map author names to usernames extracted from noreply emails via git log.

    Scans '%aN'/'%aE' pairs (optionally restricted to pathspecs), applies
    pattern to each email, and maps the author name to the first capture group
    of the first matching email, skipping EXCLUDE names. With rev_range=None,
    scans the full repository history.
    """
    users = {}
    for name, email in iter_git_log(rev_range, ('%aN', '%aE'), *pathspecs):
        match = pattern.search(email)
        if match and name not in EXCLUDE:
            users.setdefault(name, match.group(1))
    if users and label:
        debug(f"Found {len(users)} {label}")
    return users


def get_github_users_from_emails(rev_range=None):
    """Map author names to GitHub usernames from noreply emails.

    With rev_range=None, scans the full repository history.
    """
    return _map_names_by_email(rev_range, RE_GITHUB_NOREPLY, label="GitHub users from noreply emails")


_known_github_users_cache = None


def get_known_github_users():
    """Derive a name->GitHub username map from the full repository history.

    Scans all PR merge commits and GitHub noreply emails across the entire
    history (not just the selected range). This provides a fallback for
    contributors whose username cannot be derived from the range alone (e.g.
    commits authored with a real email address and not merged via a
    "Merge pull request" commit within the range).

    Noreply emails take precedence over merge-commit fork owners, because the
    email encodes the actual GitHub username while a PR's source branch owner
    may use a different fork slug.

    The result is cached for the lifetime of the process.
    """
    global _known_github_users_cache
    if _known_github_users_cache is not None:
        return _known_github_users_cache
    debug("Deriving known GitHub users from full history")
    users = get_github_users_from_merges()
    for name, username in get_github_users_from_emails().items():
        users[name] = username  # email wins over merge fork-owner slug
    debug(f"Derived {len(users)} known GitHub users from full history")
    _known_github_users_cache = users
    return users


def get_github_users(rev_range):
    """Map author names to GitHub usernames from merge commits and noreply emails.

    Falls back to usernames derived from the full repository history for
    contributors whose username cannot be resolved from the range alone. The
    fallback is consulted last so it never overrides data from the range.
    """
    users = get_github_users_from_merges(rev_range)
    for name, username in get_github_users_from_emails(rev_range).items():
        users.setdefault(name, username)
    for name, username in get_known_github_users().items():
        users.setdefault(name, username)
    return users


def get_weblate_users_from_emails(rev_range):
    """Map author names to Weblate usernames from noreply emails in git log."""
    return _map_names_by_email(
        rev_range,
        RE_WEBLATE_NOREPLY,
        pathspecs=TRANSLATION_PATHS,
        label="Weblate users from noreply emails",
    )


WEBLATE_REPORT_POLL_INTERVAL = 2  # seconds between task polls
WEBLATE_REPORT_TIMEOUT = 30  # max seconds to wait for report generation


def _weblate_api_request(api_key, url, method='GET', data=None):
    """Make an authenticated request to the Weblate API."""
    headers = {
        'Authorization': f'Token {api_key}',
        'Accept': 'application/json',
    }
    if data is not None:
        body = json.dumps(data).encode()
        headers['Content-Type'] = 'application/json'
    else:
        body = None
    req = Request(url, data=body, headers=headers, method=method)
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def _weblate_credits_report(api_key, rev_range):
    """Fetch the raw Weblate credits report for the given release range.

    Schedules a credits report, polls for completion, and returns the parsed
    JSON (a list of single-key {language: [user, ...]} dicts), or None on
    error/timeout. The end date is set to the day after the target tag to
    ensure translations made on the tag date are included.
    """
    from_tag, to_tag = rev_range.split('..', 1)
    start = get_tag_date(from_tag)
    end = (date.fromisoformat(get_tag_date(to_tag)) + timedelta(days=1)).isoformat()

    debug(f"Fetching Weblate credits for {start}..{end}")
    try:
        # Schedule the credits report
        report = _weblate_api_request(
            api_key,
            f'{WEBLATE_API_URL}/reports/',
            method='POST',
            data={'kind': 'credits', 'start': start, 'end': end, 'project': 'picard'},
        )
        task_path = report.get('task_url', '')
        if not task_path:
            debug("Weblate API: no task_url in response")
            return None

        # Poll until the task completes
        task_url = WEBLATE_BASE_URL + task_path
        elapsed = 0
        while elapsed < WEBLATE_REPORT_TIMEOUT:
            time.sleep(WEBLATE_REPORT_POLL_INTERVAL)
            elapsed += WEBLATE_REPORT_POLL_INTERVAL
            task = _weblate_api_request(api_key, task_url)
            if task.get('completed'):
                break
        else:
            debug("Weblate API: report generation timed out")
            return None

        # Fetch the report JSON data
        report_path = task.get('result', {}).get('url', '')
        if not report_path:
            debug("Weblate API: no report URL in task result")
            return None
        report_url = WEBLATE_BASE_URL + report_path + 'json/'
        return _weblate_api_request(api_key, report_url)
    except Exception as e:
        debug(f"Weblate API error: {e}")
        return None


def get_weblate_users_from_api(api_key, rev_range):
    """Return a flat dict mapping translator full_name to Weblate username.

    Uses the Weblate credits report for the range. Automated accounts
    (addon:, mt:, webhook:, ... usernames contain a colon) and EXCLUDE names
    are filtered out.
    """
    data = _weblate_credits_report(api_key, rev_range)
    credits = {}
    if not data:
        return credits
    for lang_entry in data:
        for users in lang_entry.values():
            for user in users:
                full_name = user.get('full_name', '')
                username = user.get('username', '')
                if not full_name or not username:
                    continue
                if is_weblate_bot_username(username) or full_name in EXCLUDE:
                    continue
                credits.setdefault(full_name, username)
    debug(f"Found {len(credits)} translators from Weblate API")
    return credits


def get_weblate_api_key() -> str | None:
    api_key = os.environ.get('WEBLATE_API_KEY')
    if not api_key and WeblateConfig:
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', '.weblate.ini')
        if os.path.exists(config_path):
            try:
                config = WeblateConfig()
                config.load(config_path)
                url, key = config.get_url_key()
                if url.rstrip('/') == WEBLATE_API_URL:
                    api_key = key
            except Exception as e:
                debug(f"Warning: Failed to read Weblate config: {e}")
    return api_key


def get_weblate_users(rev_range, email_users=None):
    """Map author names to Weblate usernames from noreply emails and API credits.

    If email_users (the result of get_weblate_users_from_emails) is provided,
    it is reused instead of scanning the git log again.
    """
    users = dict(email_users) if email_users is not None else get_weblate_users_from_emails(rev_range)
    api_key = get_weblate_api_key()
    if api_key:
        for name, username in get_weblate_users_from_api(api_key, rev_range).items():
            users.setdefault(name, username)
    else:
        debug("Warning: WEBLATE_API_KEY not set, translator profile links may be incomplete")
    return users


def get_code_authors(rev_range):
    """Return set of author names who committed changes outside translation paths."""
    excludes = [f':!{path}' for path in TRANSLATION_PATHS]
    lines = git('log', '--format=%aN', rev_range, '--', *excludes).splitlines()
    authors = {a for a in lines if a and a not in EXCLUDE}
    debug(f"Found {len(authors)} code authors")
    return authors


def get_translator_langs(rev_range):
    """Map translator names to their translated languages.

    Parses "Translated using Weblate (Language)" commit messages.
    """
    translator_langs = {}
    for author, subject in iter_git_log(rev_range, ('%aN', '%s'), *TRANSLATION_PATHS):
        if author in EXCLUDE:
            continue
        match = RE_WEBLATE_LANG.search(subject)
        if match:
            translator_langs.setdefault(author, set()).add(match.group(1))
    debug(f"Found {len(translator_langs)} translators from commit messages")
    return translator_langs


def html_link(url, text):
    """Format an HTML anchor tag."""
    return f'<a href="{url}">{text}</a>'


def quote_name(name):
    """Enclose name in quotes if it contains a comma."""
    if ',' in name:
        return f'"{name}"'
    return name


def linked_name(url, text):
    """Return text (comma-quoted) wrapped in an HTML link, or plain if url is falsy."""
    text = quote_name(text)
    return html_link(url, text) if url else text


RE_EMAIL = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def display_from_name(name):
    """Return a display string for an author name, obfuscating raw emails.

    If the name is a bare email address (e.g. a translator with no full name),
    return only the local part before the '@' so the contributor is still
    credited without publishing a scrapeable address.
    """
    if RE_EMAIL.match(name):
        return name.split('@', 1)[0]
    return name


def join_names(names):
    """Join names with commas and 'and' before the last one."""
    if len(names) <= 1:
        return ''.join(names)
    return ', '.join(names[:-1]) + ' and ' + names[-1]


MAX_RATE_LIMIT_WAIT = 10  # seconds; give up if wait is longer


def _get_rate_limit_wait(headers):
    """Extract wait time in seconds from rate-limit response headers.

    Returns None if the wait would exceed MAX_RATE_LIMIT_WAIT.
    """
    wait = None
    retry_after = headers.get('Retry-After')
    if retry_after:
        try:
            wait = int(retry_after)
        except ValueError:
            pass
    if wait is None:
        reset = headers.get('X-RateLimit-Reset')
        if reset:
            try:
                wait = max(0, int(reset) - int(time.time())) + 1
            except ValueError:
                pass
    if wait is None:
        wait = MAX_RATE_LIMIT_WAIT
    if wait > MAX_RATE_LIMIT_WAIT:
        return None
    return wait


MAX_RATE_LIMIT_RETRIES = 2


def _get_github_token():
    """Get GitHub token from environment or gh CLI."""
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        return token
    gh = shutil.which('gh')
    if gh:
        try:
            token = subprocess.check_output([gh, 'auth', 'token'], text=True, stderr=subprocess.DEVNULL).strip()
            if token:
                return token
        except (subprocess.CalledProcessError, OSError):
            pass
    return None


def get_github_display_names(github_users):
    """Fetch real names from GitHub API for all known GitHub users."""
    if not github_users:
        return {}
    debug(f"Fetching display names for {len(github_users)} GitHub users")
    display_names = {}
    headers = {'Accept': 'application/json'}
    token = _get_github_token()
    if token:
        headers['Authorization'] = f'token {token}'
    else:
        debug("Warning: No GitHub token found, API rate limits may apply")
    retries_left = MAX_RATE_LIMIT_RETRIES
    for git_name, gh_user in github_users.items():
        while True:  # retry loop for rate limiting; break to advance to next user
            try:
                url = f'https://api.github.com/users/{url_quote(gh_user)}'
                req = Request(url, headers=headers)
                with urlopen(req, timeout=5) as resp:
                    name = json.loads(resp.read()).get('name')
                if name:
                    display_names[git_name] = name
                break
            except urllib.error.HTTPError as e:
                is_rate_limit = e.code == 429 or (e.code == 403 and e.headers.get('X-RateLimit-Remaining') == '0')
                if is_rate_limit and retries_left > 0:
                    wait = _get_rate_limit_wait(e.headers)
                    if wait is not None:
                        debug(f"Rate limited, waiting {wait}s ({retries_left} retries left)")
                        time.sleep(wait)
                        retries_left -= 1
                        continue
                if is_rate_limit:
                    debug(f"Rate limited on {gh_user}, skipping remaining")
                    if display_names:
                        debug(f"Resolved {len(display_names)} display names from GitHub")
                    return display_names
                debug(f"GitHub API error for {gh_user}: {e}")
                break
            except Exception as e:
                debug(f"GitHub API error for {gh_user}: {e}")
                break
    if display_names:
        debug(f"Resolved {len(display_names)} display names from GitHub")
    return display_names


def format_code_authors(code_authors, github_users, display_names, translator_langs, weblate_users):
    """Format code contributors with optional GitHub links.

    For authors who also contributed translations (confirmed via Weblate
    user identification), their translated languages are shown.
    """
    names = []
    for name in sorted(code_authors, key=str.casefold):
        gh_user = github_users.get(name)
        display = display_from_name(display_names.get(name, name))
        url = f'{GITHUB_URL}/{url_quote(gh_user)}' if gh_user else None
        entry = linked_name(url, display)
        # Only show translation languages if the person is a confirmed
        # Weblate translator (not just the merge author of squashed commits)
        if name in weblate_users and name in translator_langs:
            langs = ', '.join(sorted(translator_langs[name]))
            entry += f" ({langs}+)"
        names.append(entry)
    return f"Code contributions by {join_names(names)}."


def resolve_weblate_username(name, weblate_users):
    """Resolve a translator name to a Weblate username.

    Prefers curated overrides (for contributors whose git name differs from
    their Weblate account, or who are absent from the auto-derived sources),
    then falls back to the auto-derived name->username mapping.
    """
    curated = CODE_AUTHOR_TRANSLATIONS.get(name, {}).get('weblate') or TRANSLATOR_WEBLATE_USERS.get(name)
    return curated or weblate_users.get(name)


def format_translators(translators, translator_langs, weblate_users):
    """Format translators with languages and optional Weblate links."""
    parts = []
    for name in sorted(translators, key=str.casefold):
        wb_user = resolve_weblate_username(name, weblate_users)
        url = f'{WEBLATE_USER_URL}/{url_quote(wb_user)}/' if wb_user else None
        langs = ', '.join(sorted(translator_langs[name]))
        parts.append(f"{linked_name(url, display_from_name(name))} ({langs})")
    return f"Translations were updated by {join_names(parts)}."


def format_translators_by_language(translators, translator_langs, weblate_users):
    """Format translators grouped by language, one line per language (HTML).

    Inverts the same translator->languages data used by format_translators
    (so the translator set and links stay consistent with the default view),
    normalizes language names via LANGUAGE_ALIASES, and emits a bold language
    label followed by its translators, one language per line.
    """
    by_language = {}
    for name in translators:
        for language in translator_langs[name]:
            by_language.setdefault(canonical_language(language), set()).add(name)

    # Credit code authors for languages they genuinely translated (curated).
    for name, info in CODE_AUTHOR_TRANSLATIONS.items():
        for language in info['langs']:
            by_language.setdefault(canonical_language(language), set()).add(name)

    lines = []
    for language in sorted(by_language, key=str.casefold):
        names = []
        for name in sorted(by_language[language], key=str.casefold):
            wb_user = resolve_weblate_username(name, weblate_users)
            url = f'{WEBLATE_USER_URL}/{url_quote(wb_user)}/' if wb_user else None
            names.append(linked_name(url, display_from_name(name)))
        lines.append(f"<strong>{language}:</strong> {join_names(names)}")
    return '\nTranslations were updated by:<br>\n' + '<br>\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--from',
        dest='from_tag',
        default=None,
        help="starting release tag (default: second most recent release)",
    )
    parser.add_argument(
        '--to',
        dest='to_tag',
        default=None,
        help="ending release tag (default: most recent release)",
    )
    parser.add_argument(
        '-q',
        '--quiet',
        action='store_true',
        help="suppress progress messages on stderr",
    )
    parser.add_argument(
        '--by-language',
        action='store_true',
        help="group translators by language (one line per language); "
        "requires Weblate API access, falls back to the default format otherwise",
    )
    args = parser.parse_args()

    global QUIET
    QUIET = args.quiet

    if not args.from_tag or not args.to_tag:
        tags = get_release_tags()
        if len(tags) < 2:
            raise SystemExit("Need at least 2 release tags")
        if not args.to_tag:
            args.to_tag = tags[0]
        if not args.from_tag:
            args.from_tag = tags[1]

    rev_range = f'{args.from_tag}..{args.to_tag}'
    debug(f"{rev_range}:")

    github_users = get_github_users(rev_range)
    weblate_email_users = get_weblate_users_from_emails(rev_range)
    weblate_users = get_weblate_users(rev_range, email_users=weblate_email_users)
    code_authors = get_code_authors(rev_range)
    translator_langs = get_translator_langs(rev_range)
    translators = set(translator_langs.keys()) - code_authors
    debug(f"{len(translators)} translators (excluding code authors)")
    display_names = get_github_display_names(
        {name: github_users[name] for name in code_authors if name in github_users}
    )

    if code_authors:
        # Use email-confirmed users only for dual-contributor check to avoid
        # crediting admins who appear in API credits from merge operations
        print(format_code_authors(code_authors, github_users, display_names, translator_langs, weblate_email_users))
    if translators:
        if args.by_language:
            print(format_translators_by_language(translators, translator_langs, weblate_users))
        else:
            print(format_translators(translators, translator_langs, weblate_users))


if __name__ == '__main__':
    main()
