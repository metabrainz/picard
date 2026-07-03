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

"""Profile management subcommand for picard-cli.

Usage:
    picard-cli profiles list
    picard-cli profiles export <profile> [-o output.toml] [--mode backup]
    picard-cli profiles import <file> [--enable] [--replace <profile>]
"""

from picard.cli.base import ExitCode
from picard.config import get_config


class ResolveResult:
    """Result of profile resolution.

    Attributes:
        profile: The matched profile dict, or None if not found/ambiguous.
        candidates: List of candidate profiles when ambiguous, empty otherwise.
    """

    __slots__ = ('candidates', 'profile')

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


def _print_resolve_error(query: str, result: ResolveResult, output):
    """Print an error message for a failed profile resolution."""
    if not result.candidates:
        output.error(f"No profile found matching '{query}'")
    else:
        output.error(f"'{query}' is ambiguous, matches multiple profiles:")
        for p in result.candidates:
            output.info(f"{p['title']} (id: {p['id']})")


def register_subcommand(subparsers):
    """Register the 'profiles' subcommand with all its verbs."""
    profiles_parser = subparsers.add_parser(
        'profiles',
        help='manage Picard profiles',
        description='Export, import, and list Picard profiles.',
    )

    # Profile sub-subcommands (verbs)
    verb_parsers = profiles_parser.add_subparsers(
        dest='verb',
        title='profile commands',
        metavar='<command>',
    )

    # --- list ---
    p_list = verb_parsers.add_parser('list', help='list all configured profiles')
    p_list.set_defaults(run_command=_run_profiles)

    # --- export ---
    p_export = verb_parsers.add_parser('export', help='export a profile to TOML')
    p_export.add_argument('profile', metavar='TITLE_OR_ID', help="profile title or UUID (partial match allowed)")
    p_export.add_argument('-o', '--output', metavar='FILE', help="output file (default: stdout)")
    p_export.add_argument(
        '--mode',
        choices=['share', 'backup'],
        default='share',
        help="export mode (default: share)",
    )
    p_export.set_defaults(run_command=_run_profiles)

    # --- import ---
    p_import = verb_parsers.add_parser('import', help='import a profile from a TOML file')
    p_import.add_argument('file', metavar='FILE', help="TOML file to import")
    p_import.add_argument('--enable', action='store_true', help="enable the profile after import")
    p_import.add_argument(
        '--replace',
        metavar='TITLE_OR_ID',
        help="replace an existing profile (match by title or UUID, partial allowed)",
    )
    p_import.set_defaults(run_command=_run_profiles)

    # Default handler when no verb is given
    profiles_parser.set_defaults(run_command=_run_profiles)


def cmd_list(output):
    """List all user profiles."""
    config = get_config()
    profiles = config.profiles['user_profiles']

    if not profiles:
        output.print("No profiles configured.")
        return ExitCode.SUCCESS

    output.print("Configured profiles:")
    output.nl()

    for profile in profiles:
        status = output.d_status_enabled() if profile['enabled'] else output.d_status_disabled()
        output.print(f"  {output.d_name(profile['title'])} [{status}] (id: {output.d_uuid(profile['id'])})")

    output.nl()
    total = len(profiles)
    enabled = sum(1 for p in profiles if p['enabled'])
    disabled = total - enabled
    output.print(
        f"Total: {output.d_number(total)} profile{'s' if total != 1 else ''} "
        f"({output.d_status_enabled(str(enabled))} enabled, "
        f"{output.d_status_disabled(str(disabled))} disabled)"
    )

    return ExitCode.SUCCESS


def cmd_export(args, output):
    """Export a profile to a TOML file."""
    import os

    from picard.profiles.exporter import export_profile

    config = get_config()

    resolve = _resolve_profile_query(config, args.profile)
    if not resolve.profile:
        _print_resolve_error(args.profile, resolve, output)
        return ExitCode.NOT_FOUND

    profile = resolve.profile
    toml_string = export_profile(
        config,
        profile_id=profile['id'],
        title=profile['title'],
        mode=args.mode,
    )

    if args.output:
        if os.path.exists(args.output) and not getattr(args, 'yes', False):
            if not output.yesno(f"Overwrite {args.output}?"):
                output.print("Export cancelled.")
                return ExitCode.SUCCESS
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(toml_string)
        output.success(f"Profile exported to: {output.d_path(args.output)}")
    else:
        print(toml_string)

    return ExitCode.SUCCESS


def cmd_import(args, output):
    """Import a profile from a TOML file."""
    from picard.profiles.importer import (
        ProfileImportError,
        import_profile,
    )

    config = get_config()

    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            toml_string = f.read()
    except OSError as e:
        output.error(f"Cannot read file: {e}")
        return ExitCode.ERROR

    # Resolve --replace to an actual UUID
    replace_id = None
    if getattr(args, 'replace', None):
        resolve = _resolve_profile_query(config, args.replace)
        if not resolve.profile:
            _print_resolve_error(args.replace, resolve, output)
            return ExitCode.NOT_FOUND
        replace_profile = resolve.profile
        if not getattr(args, 'yes', False):
            if not output.yesno(f"Replace profile {output.d_name(replace_profile['title'])}?"):
                output.print("Import cancelled.")
                return ExitCode.SUCCESS
        replace_id = replace_profile['id']

    try:
        result = import_profile(config, toml_string, enabled=args.enable, replace_id=replace_id)
    except ProfileImportError as e:
        output.error(str(e))
        return ExitCode.ERROR

    output.success(f"Profile imported: {output.d_name(result.title)}")
    if result.warnings:
        for warning in result.warnings:
            output.warning(warning)

    # Save config to persist the imported profile
    config.sync()

    return ExitCode.SUCCESS


def _run_profiles(args):
    """Initialize and run the profiles CLI."""
    from picard.cli._bootstrap import (
        init_cli,
        is_color_disabled,
    )
    from picard.cli.output import CliOutput

    # No verb specified - show help
    verb = getattr(args, 'verb', None)
    if not verb:
        print("Usage: picard-cli profiles <command> [options]")
        print()
        print("Run 'picard-cli profiles --help' for available commands.")
        return ExitCode.SUCCESS

    # Bootstrap app
    app = init_cli(args)  # noqa: F841

    # Create output
    output = CliOutput(color=False if is_color_disabled(args) else None)

    if verb == 'list':
        return cmd_list(output)
    elif verb == 'export':
        return cmd_export(args, output)
    elif verb == 'import':
        return cmd_import(args, output)

    return ExitCode.ERROR
