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
    picard-profiles list
    picard-profiles export "Profile Title" [-o output.toml] [--mode backup]
    picard-profiles import input.toml [--enable]
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
    from picard.profile_export import export_profile

    config = get_config()
    profiles = config.profiles['user_profiles']

    # Find profile by title
    matching = [p for p in profiles if p['title'] == args.title]
    if not matching:
        print(f"Error: No profile found with title '{args.title}'", file=sys.stderr)
        print("Available profiles:", file=sys.stderr)
        for p in profiles:
            print(f"  {p['title']}", file=sys.stderr)
        return 1

    profile = matching[0]
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
    from picard.profile_import import (
        ProfileImportError,
        import_profile,
    )

    config = get_config()

    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            toml_string = f.read()
    except OSError as e:
        print(f"Error: Cannot read file: {e}", file=sys.stderr)
        return 1

    try:
        result = import_profile(config, toml_string, enabled=args.enable)
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

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # list
    subparsers.add_parser('list', help='List all configured profiles')

    # export
    export_parser = subparsers.add_parser('export', help='Export a profile to TOML')
    export_parser.add_argument('title', help='Title of the profile to export')
    export_parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    export_parser.add_argument(
        '--mode',
        choices=['share', 'backup'],
        default='share',
        help='Export mode (default: share)',
    )

    # import
    import_parser = subparsers.add_parser('import', help='Import a profile from TOML')
    import_parser.add_argument('file', help='TOML file to import')
    import_parser.add_argument('--enable', action='store_true', help='Enable the profile after import')

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

    commands = {
        'list': cmd_list,
        'export': cmd_export,
        'import': cmd_import,
    }

    if cmdline_args.command is None:
        parser.print_help()
        sys.exit(0)

    handler = commands.get(cmdline_args.command)
    if handler:
        sys.exit(handler(cmdline_args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
