#!/usr/bin/env python3
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


EXCLUDE = {'Weblate', 'dependabot[bot]'}

# Paths containing translation files managed via Weblate.
# Used to separate translators from code contributors.
TRANSLATION_PATHS = ('po/', 'installer/i18n/sources/')

WEBLATE_API_URL = 'https://translations.metabrainz.org/api'
WEBLATE_URL = 'https://translations.metabrainz.org/user'
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


def get_github_users_from_merges(rev_range):
    """Map author names to GitHub usernames from PR merge commits."""
    pr_parents = {}
    for line in git('log', '--merges', '--format=%P %s', rev_range).splitlines():
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
        rev_range: Git revision range (e.g. 'tag1..tag2')
        format_fields: Git format placeholders (e.g. '%aN', '%aE', '%s')
        *pathspecs: Optional pathspec arguments for git log
    """
    fmt = '\t'.join(format_fields)
    args = ['log', f'--format={fmt}', rev_range]
    if pathspecs:
        args.extend(('--', *pathspecs))
    num_fields = len(format_fields)
    for line in git(*args).splitlines():
        if '\t' not in line:
            continue
        yield line.split('\t', num_fields - 1)


def get_github_users_from_emails(rev_range):
    """Map author names to GitHub usernames from noreply emails."""
    github_users = {}
    for name, email in iter_git_log(rev_range, ('%aN', '%aE')):
        match = RE_GITHUB_NOREPLY.search(email)
        if match and name not in EXCLUDE:
            github_users.setdefault(name, match.group(1))
    if github_users:
        debug(f"Found {len(github_users)} GitHub users from noreply emails")
    return github_users


def get_github_users(rev_range):
    """Map author names to GitHub usernames from merge commits and noreply emails."""
    users = get_github_users_from_merges(rev_range)
    for name, username in get_github_users_from_emails(rev_range).items():
        users.setdefault(name, username)
    return users


def get_weblate_users_from_emails(rev_range):
    """Map author names to Weblate usernames from noreply emails in git log."""
    weblate_users = {}
    for name, email in iter_git_log(rev_range, ('%aN', '%aE'), *TRANSLATION_PATHS):
        match = RE_WEBLATE_NOREPLY.search(email)
        if match and name not in EXCLUDE:
            weblate_users.setdefault(name, match.group(1))
    if weblate_users:
        debug(f"Found {len(weblate_users)} Weblate users from noreply emails")
    return weblate_users


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


def get_weblate_users_from_api(api_key, rev_range):
    """Fetch translator usernames from the Weblate Reports API.

    Schedules a credits report, polls for completion, and parses the result.
    The end date is set to the day after the target tag to ensure
    translations made on the tag date are included.
    Returns a dict mapping full_name to Weblate username.
    """
    from_tag, to_tag = rev_range.split('..', 1)
    start = get_tag_date(from_tag)
    end_date = date.fromisoformat(get_tag_date(to_tag)) + timedelta(days=1)
    end = end_date.isoformat()

    debug(f"Fetching Weblate credits for {start}..{end}")
    credits = {}
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
            return credits

        # Poll until the task completes
        task_url = WEBLATE_API_URL.rsplit('/api', 1)[0] + task_path
        elapsed = 0
        while elapsed < WEBLATE_REPORT_TIMEOUT:
            time.sleep(WEBLATE_REPORT_POLL_INTERVAL)
            elapsed += WEBLATE_REPORT_POLL_INTERVAL
            task = _weblate_api_request(api_key, task_url)
            if task.get('completed'):
                break
        else:
            debug("Weblate API: report generation timed out")
            return credits

        # Fetch the report JSON data
        report_path = task.get('result', {}).get('url', '')
        if not report_path:
            debug("Weblate API: no report URL in task result")
            return credits
        report_url = WEBLATE_API_URL.rsplit('/api', 1)[0] + report_path + 'json/'
        data = _weblate_api_request(api_key, report_url)

        for lang_entry in data:
            for users in lang_entry.values():
                for user in users:
                    full_name = user.get('full_name', '')
                    username = user.get('username', '')
                    if full_name and username:
                        credits.setdefault(full_name, username)
        debug(f"Found {len(credits)} translators from Weblate API")
    except Exception as e:
        debug(f"Weblate API error: {e}")
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


def get_weblate_users(rev_range):
    """Map author names to Weblate usernames from noreply emails and API credits."""
    users = get_weblate_users_from_emails(rev_range)
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
    authors = set(a for a in lines if a and a not in EXCLUDE)
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
    users_iter = iter(github_users.items())
    git_name, gh_user = None, None
    while True:
        if git_name is None:
            item = next(users_iter, None)
            if item is None:
                break
            git_name, gh_user = item
        try:
            url = f'https://api.github.com/users/{url_quote(gh_user)}'
            req = Request(url, headers=headers)
            with urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                name = data.get('name')
                if name:
                    display_names[git_name] = name
            git_name, gh_user = None, None  # advance to next user
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
                break
            debug(f"GitHub API error for {gh_user}: {e}")
            git_name, gh_user = None, None  # skip this user, continue
        except Exception as e:
            debug(f"GitHub API error for {gh_user}: {e}")
            git_name, gh_user = None, None  # skip this user, continue
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
        display = display_names.get(name, name)
        if gh_user:
            entry = html_link(f'{GITHUB_URL}/{url_quote(gh_user)}', quote_name(display))
        else:
            entry = quote_name(display)
        # Only show translation languages if the person is a confirmed
        # Weblate translator (not just the merge author of squashed commits)
        if name in weblate_users and name in translator_langs:
            langs = ', '.join(sorted(translator_langs[name]))
            entry += f" ({langs}+)"
        names.append(entry)
    return f"Code contributions by {join_names(names)}."


def format_translators(translators, translator_langs, weblate_users):
    """Format translators with languages and optional Weblate links."""
    parts = []
    for name in sorted(translators, key=str.casefold):
        wb_user = weblate_users.get(name)
        if wb_user:
            linked_name = html_link(f'{WEBLATE_URL}/{url_quote(wb_user)}/', quote_name(name))
        else:
            linked_name = quote_name(name)
        langs = ', '.join(sorted(translator_langs[name]))
        parts.append(f"{linked_name} ({langs})")
    return f"Translations were updated by {join_names(parts)}."


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
    weblate_users = get_weblate_users(rev_range)
    weblate_email_users = get_weblate_users_from_emails(rev_range)
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
        print(format_translators(translators, translator_langs, weblate_users))


if __name__ == '__main__':
    main()
