# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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

"""CLI for profile export/import/list operations.

Usage:
    picard-profiles --list
    picard-profiles --export "Profile Title" [-o output.toml] [--mode backup]
    picard-profiles --import input.toml [--enable] [--replace UUID]
"""

import argparse
import sys

from PyQt6 import QtCore

from picard import (
    PICARD_APP_NAME,
    PICARD_FANCY_VERSION_STR,
    PICARD_ORG_NAME,
)
from picard.config import (
    get_config,
    setup_config,
)
from picard.options import init_options


class ResolveResult:
    """Result of profile resolution.

    Attributes:
        profile: The matched profile dict, or None if not found/ambiguous.
        candidates: List of candidate profiles when ambiguous, empty otherwise.
    """

    __slots__ = ('profile', 'candidates')

    def __init__(self, profile=None, candidates=None):
        self.profile = profile
        self.candidates = candidates or []


def _resolve_profile_query(config, query: str) -> ResolveResult:
    """Resolve a query (title, UUID, or partial match) to a profile.

    Returns a ResolveResult with either a single matched profile or
    a list of candidates (empty if no match, multiple if ambiguous).
    """
    profiles = config.profiles['user_profiles']

    # Exact match first
    matching = [p for p in profiles if p['title'] == query or p['id'] == query]
    if not matching:
        # Partial match
        matching = [p for p in profiles if query.lower() in p['title'].lower() or p['id'].startswith(query)]

    if len(matching) == 1:
        return ResolveResult(profile=matching[0])
    return ResolveResult(candidates=matching)


def _print_resolve_error(query: str, result: ResolveResult):
    """Print an error message for a failed profile resolution."""
    if not result.candidates:
        print(f"Error: No profile found matching '{query}'", file=sys.stderr)
    else:
        print(f"Error: '{query}' is ambiguous, matches multiple profiles:", file=sys.stderr)
        for p in result.candidates:
            print(f"  {p['title']} (id: {p['id']})", file=sys.stderr)


def cmd_list(args):
    """List all user profiles."""
    config = get_config()
    profiles = config.profiles['user_profiles']

    if not profiles:
        print("No profiles configured.")
        return 0

    for profile in profiles:
        status = "enabled" if profile['enabled'] else "disabled"
        print(f"  {profile['title']} [{status}] (id: {profile['id']})")

    return 0


def cmd_export(args):
    """Export a profile to a TOML file."""
    from picard.profiles.exporter import export_profile

    config = get_config()

    # Find profile by exact or partial match on title or UUID
    resolve = _resolve_profile_query(config, args.export)
    if not resolve.profile:
        _print_resolve_error(args.export, resolve)
        return 1

    profile = resolve.profile
    toml_string = export_profile(
        config,
        profile_id=profile['id'],
        title=profile['title'],
        mode=args.mode,
    )

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(toml_string)
        print(f"Profile exported to: {args.output}")
    else:
        print(toml_string)

    return 0


def cmd_import(args):
    """Import a profile from a TOML file."""
    from picard.profiles.importer import (
        ProfileImportError,
        import_profile,
    )

    config = get_config()

    try:
        with open(args.import_file, 'r', encoding='utf-8') as f:
            toml_string = f.read()
    except OSError as e:
        print(f"Error: Cannot read file: {e}", file=sys.stderr)
        return 1

    # Resolve --replace to an actual UUID
    replace_id = None
    if getattr(args, 'replace', None):
        resolve = _resolve_profile_query(config, args.replace)
        if not resolve.profile:
            _print_resolve_error(args.replace, resolve)
            return 1
        replace_id = resolve.profile['id']

    try:
        result = import_profile(config, toml_string, enabled=args.enable, replace_id=replace_id)
    except ProfileImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Profile imported: {result.title}")
    if result.warnings:
        for warning in result.warnings:
            print(f"  Warning: {warning}")

    # Save config to persist the imported profile
    config.sync()

    return 0


def process_cmdline_args():
    parser = argparse.ArgumentParser(
        prog='picard-profiles',
        description='MusicBrainz Picard profile management',
    )
    parser.add_argument('-c', '--config-file', action='store', default=None, help="configuration file location")
    parser.add_argument('-v', '--version', action='store_true', help="display version and exit")

    group = parser.add_argument_group("Profile Management")
    group.add_argument('-l', '--list', action='store_true', help="list all configured profiles")
    group.add_argument(
        '-e',
        '--export',
        metavar='TITLE_OR_ID',
        help="export a profile by title or UUID (output to stdout or -o file)",
    )
    group.add_argument('-i', '--import', metavar='FILE', dest='import_file', help="import a profile from a TOML file")
    group.add_argument('-o', '--output', metavar='FILE', help="output file for export (default: stdout)")
    group.add_argument('--mode', choices=['share', 'backup'], default='share', help="export mode (default: share)")
    group.add_argument('--enable', action='store_true', help="enable the profile after import")
    group.add_argument(
        '--replace',
        metavar='TITLE_OR_ID',
        help="replace an existing profile on import (match by title or UUID, partial allowed)",
    )

    return parser.parse_args(), parser


def minimal_init(config_file=None):
    """Minimal initialization for CLI commands without GUI."""
    QtCore.QCoreApplication.setApplicationName(PICARD_APP_NAME)
    QtCore.QCoreApplication.setOrganizationName(PICARD_ORG_NAME)

    app = QtCore.QCoreApplication(sys.argv)

    init_options()
    setup_config(app=app, filename=config_file)

    return app


def main():
    cmdline_args, parser = process_cmdline_args()

    app = minimal_init(cmdline_args.config_file)  # noqa: F841 - app must stay alive for QCoreApplication

    if cmdline_args.version:
        print(f"{PICARD_ORG_NAME} {PICARD_APP_NAME} {PICARD_FANCY_VERSION_STR}")
        sys.exit(0)

    if cmdline_args.list:
        sys.exit(cmd_list(cmdline_args))
    elif cmdline_args.export:
        sys.exit(cmd_export(cmdline_args))
    elif cmdline_args.import_file:
        sys.exit(cmd_import(cmdline_args))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
