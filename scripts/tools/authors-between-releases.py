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
import json
import os
import re
import shutil
import subprocess
import sys
from urllib.parse import (
    quote,
    urlencode,
)
from urllib.request import (
    Request,
    urlopen,
)


try:
    from wlc.config import WeblateConfig
except ImportError:
    WeblateConfig = None  # type: ignore


EXCLUDE = {'Weblate', 'dependabot[bot]'}

WEBLATE_API_URL = 'https://translations.metabrainz.org/api'
WEBLATE_URL = 'https://translations.metabrainz.org/user'
GITHUB_URL = 'https://github.com'


def debug(msg):
    """Print a debug message to stderr."""
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
        match = re.match(r'\w+ (\w+) Merge pull request #\d+ from ([^/]+)/', line)
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
        sha, author = line.split(' ', 1)
        if author and author not in EXCLUDE:
            github_users.setdefault(author, pr_parents[sha])
    debug(f"Found {len(github_users)} GitHub users from merge commits")
    return github_users


def get_github_users_from_emails(rev_range):
    """Map author names to GitHub usernames from noreply emails."""
    github_users = {}
    for line in git('log', '--format=%aN\t%aE', rev_range).splitlines():
        if '\t' not in line:
            continue
        name, email = line.split('\t', 1)
        match = re.match(r'(?:\d+\+)?(.+)@users\.noreply\.github\.com$', email)
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
    for line in git('log', '--format=%aN\t%aE', rev_range, '--', 'po/').splitlines():
        if '\t' not in line:
            continue
        name, email = line.split('\t', 1)
        match = re.match(r'(.+)@users\.noreply\.translations\.metabrainz\.org$', email)
        if match and name not in EXCLUDE:
            weblate_users.setdefault(name, match.group(1))
    if weblate_users:
        debug(f"Found {len(weblate_users)} Weblate users from noreply emails")
    return weblate_users


def get_weblate_users_from_api(api_key, rev_range):
    """Fetch translator usernames from the Weblate project credits API.

    Uses the date range of the two release tags to query credits.
    Returns a dict mapping full_name to Weblate username.
    """
    from_tag, to_tag = rev_range.split('..', 1)
    start = get_tag_date(from_tag)
    end = get_tag_date(to_tag)

    debug(f"Fetching Weblate credits for {start}..{end}")
    credits = {}
    try:
        url = f'{WEBLATE_API_URL}/projects/picard/credits/?{urlencode({"start": start, "end": end})}'
        req = Request(
            url,
            headers={
                'Authorization': f'Token {api_key}',
                'Accept': 'application/json',
            },
        )
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
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
        if os.path.exists:
            config = WeblateConfig()
            config.load(config_path)
            url, key = config.get_url_key()
            if url.rstrip('/') == WEBLATE_API_URL:
                api_key = key
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
    """Return set of author names who committed changes outside po/."""
    lines = git('log', '--format=%aN', rev_range, '--', ':!po/').splitlines()
    authors = set(a for a in lines if a and a not in EXCLUDE)
    debug(f"Found {len(authors)} code authors")
    return authors


def get_translator_langs(rev_range):
    """Map translator names to their translated languages.

    Parses "Translated using Weblate (Language)" commit messages.
    """
    translator_langs = {}
    for line in git('log', '--format=%aN\t%s', rev_range, '--', 'po/').splitlines():
        if '\t' not in line:
            continue
        author, subject = line.split('\t', 1)
        if author in EXCLUDE:
            continue
        match = re.search(r'Translated using Weblate \((.+)\)', subject)
        if match:
            translator_langs.setdefault(author, set()).add(match.group(1))
    debug(f"Found {len(translator_langs)} translators from commit messages")
    return translator_langs


def html_link(url, text):
    """Format an HTML anchor tag."""
    return f'<a href="{url}">{text}</a>'


def join_names(names):
    """Join names with commas and 'and' before the last one."""
    if len(names) <= 1:
        return ''.join(names)
    return ', '.join(names[:-1]) + ' and ' + names[-1]


def get_github_display_names(github_users):
    """Fetch real names from GitHub API for all known GitHub users."""
    if not github_users:
        return {}
    debug(f"Fetching display names for {len(github_users)} GitHub users")
    display_names = {}
    headers = {'Accept': 'application/json'}
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = f'token {token}'
    else:
        debug("Warning: GITHUB_TOKEN not set, GitHub API rate limits may apply")
    for git_name, gh_user in github_users.items():
        try:
            url = f'https://api.github.com/users/{quote(gh_user)}'
            req = Request(url, headers=headers)
            with urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                name = data.get('name')
                if name:
                    display_names[git_name] = name
        except Exception as e:
            debug(f"GitHub API error for {gh_user}: {e}")
            break  # likely rate limited, skip remaining
    if display_names:
        debug(f"Resolved {len(display_names)} display names from GitHub")
    return display_names


def format_code_authors(code_authors, github_users, display_names):
    """Format code contributors with optional GitHub links."""
    names = []
    for name in sorted(code_authors, key=str.casefold):
        gh_user = github_users.get(name)
        display = display_names.get(name, name)
        if gh_user:
            names.append(html_link(f'{GITHUB_URL}/{quote(gh_user)}', display))
        else:
            names.append(display)
    return f"Code contributions by {join_names(names)}."


def format_translators(translators, translator_langs, weblate_users):
    """Format translators with languages and optional Weblate links."""
    parts = []
    for name in sorted(translators, key=str.casefold):
        wb_user = weblate_users.get(name)
        if wb_user:
            linked_name = html_link(f'{WEBLATE_URL}/{quote(wb_user)}/', name)
        else:
            linked_name = name
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
    args = parser.parse_args()

    if not args.from_tag or not args.to_tag:
        tags = get_release_tags()
        if len(tags) < 2:
            raise SystemExit("Need at least 2 release tags")
        if not args.to_tag:
            args.to_tag = tags[0]
        if not args.from_tag:
            args.from_tag = tags[1]

    rev_range = f'{args.from_tag}..{args.to_tag}'
    print(f"{rev_range}:", file=sys.stderr)

    github_users = get_github_users(rev_range)
    weblate_users = get_weblate_users(rev_range)
    code_authors = get_code_authors(rev_range)
    translator_langs = get_translator_langs(rev_range)
    translators = set(translator_langs.keys()) - code_authors
    debug(f"{len(translators)} translators (excluding code authors)")
    display_names = get_github_display_names(
        {name: github_users[name] for name in code_authors if name in github_users}
    )

    if code_authors:
        print(format_code_authors(code_authors, github_users, display_names))
    if translators:
        print(format_translators(translators, translator_langs, weblate_users))


if __name__ == '__main__':
    main()
