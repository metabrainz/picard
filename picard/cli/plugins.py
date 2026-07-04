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

"""Plugin management subcommand for picard-cli.

Usage:
    picard-cli plugins list
    picard-cli plugins install <source> [--ref <ref>] [--reinstall]
    picard-cli plugins remove <plugin> [--purge]
    picard-cli plugins update <plugin>... | --all
    picard-cli plugins enable <plugin>...
    picard-cli plugins disable <plugin>...
    picard-cli plugins info <plugin>
    picard-cli plugins search <query>
    picard-cli plugins browse
    picard-cli plugins init [<name>]
    picard-cli plugins validate <path-or-url>
    picard-cli plugins refs <plugin>
    picard-cli plugins switch-ref <plugin> <ref>
    picard-cli plugins manifest [<plugin>]
    picard-cli plugins check-blacklist [<url>]
    picard-cli plugins clean-config [<plugin>]
    picard-cli plugins refresh-registry
    picard-cli plugins check-updates
"""

from picard.plugin3.constants import DEFAULT_SOURCE_LOCALE


def register_subcommand(subparsers):
    """Register the 'plugins' subcommand with all its verbs."""
    plugins_parser = subparsers.add_parser(
        'plugins',
        help='manage Picard plugins',
        description='Install, update, enable, and manage Picard plugins.',
        formatter_class=_argparse().RawDescriptionHelpFormatter,
        epilog=(
            "Trust Levels:\n"
            "  🛡️ official: Reviewed by Picard team (highest trust)\n"
            "  ✓ trusted: Known authors, not reviewed (high trust)\n"
            "  ⚠️ community: Other authors, not reviewed (use caution)\n"
            "  🔓 unregistered: Not in registry (local/unknown source - lowest trust)\n"
            "\nFor more information, visit: https://picard.musicbrainz.org/docs/plugins/"
        ),
    )

    # Common options for the plugins group
    plugins_parser.add_argument(
        '--locale',
        metavar='LOCALE',
        default='en',
        help="locale for displaying plugin info (e.g., 'fr', 'de', 'en')",
    )

    # Plugin sub-subcommands (verbs)
    verb_parsers = plugins_parser.add_subparsers(
        dest='verb',
        title='plugin commands',
        metavar='<command>',
    )

    # --- list ---
    p_list = verb_parsers.add_parser('list', help='list all installed plugins')
    p_list.set_defaults(run_command=_run_plugins)

    # --- install ---
    p_install = verb_parsers.add_parser('install', help='install plugin(s) from git URL(s) or registry ID')
    p_install.add_argument('source', nargs='+', metavar='SOURCE', help="git URL(s) or registry plugin ID(s)")
    p_install.add_argument('--ref', metavar='REF', help="git ref (branch/tag/commit) to checkout")
    p_install.add_argument('--reinstall', action='store_true', help="force reinstall")
    p_install.add_argument('--force-blacklisted', action='store_true', help="bypass blacklist check (dangerous!)")
    p_install.add_argument('--trust-community', action='store_true', help="skip warnings for community plugins")
    p_install.add_argument(
        '--no-git',
        action='store_true',
        help="load plugin in local mode (no git updates/refs)",
    )
    p_install.set_defaults(run_command=_run_plugins)

    # --- remove (alias: uninstall) ---
    p_remove = verb_parsers.add_parser('remove', aliases=['uninstall'], help='uninstall plugin(s)')
    p_remove.add_argument('plugin', nargs='+', metavar='PLUGIN', help="plugin name(s), ID(s), or UUID(s)")
    p_remove.add_argument('--purge', action='store_true', help="also delete plugin saved options")
    p_remove.set_defaults(run_command=_run_plugins)

    # --- enable ---
    p_enable = verb_parsers.add_parser('enable', help='enable plugin(s)')
    p_enable.add_argument('plugin', nargs='+', metavar='PLUGIN', help="plugin name(s), ID(s), or UUID(s)")
    p_enable.set_defaults(run_command=_run_plugins)

    # --- disable ---
    p_disable = verb_parsers.add_parser('disable', help='disable plugin(s)')
    p_disable.add_argument('plugin', nargs='+', metavar='PLUGIN', help="plugin name(s), ID(s), or UUID(s)")
    p_disable.set_defaults(run_command=_run_plugins)

    # --- update ---
    p_update = verb_parsers.add_parser('update', help='update plugin(s) to latest version')
    p_update.add_argument('plugin', nargs='*', metavar='PLUGIN', help="plugin name(s) to update (omit for --all)")
    p_update.add_argument('--all', action='store_true', dest='update_all', help="update all installed plugins")
    p_update.set_defaults(run_command=_run_plugins)

    # --- info ---
    p_info = verb_parsers.add_parser('info', help='show detailed plugin information')
    p_info.add_argument('plugin', metavar='PLUGIN', help="plugin name, ID, or UUID")
    p_info.set_defaults(run_command=_run_plugins)

    # --- search ---
    p_search = verb_parsers.add_parser('search', help='search plugins in registry')
    p_search.add_argument('query', metavar='QUERY', help="search query")
    p_search.add_argument('--category', metavar='CATEGORY', help="filter by category")
    p_search.add_argument('--trust', metavar='LEVEL', help="filter by trust level")
    p_search.set_defaults(run_command=_run_plugins)

    # --- browse ---
    p_browse = verb_parsers.add_parser('browse', help='browse all plugins from registry')
    p_browse.add_argument('--category', metavar='CATEGORY', help="filter by category")
    p_browse.add_argument('--trust', metavar='LEVEL', help="filter by trust level")
    p_browse.set_defaults(run_command=_run_plugins)

    # --- init ---
    p_init = verb_parsers.add_parser('init', help='create a new plugin project')
    p_init.add_argument('name', nargs='?', default='', metavar='NAME', help="plugin name (interactive if omitted)")
    p_init.add_argument('--author', metavar='NAME', help="author name")
    p_init.add_argument('--category', metavar='CATEGORY', help="plugin category")
    p_init.add_argument('--target-dir', metavar='DIR', help="override directory name")
    p_init.add_argument('--parent-dir', metavar='DIR', help="parent directory (default: current directory)")
    p_init.add_argument('--with-translations', action='store_true', help="include translation support")
    p_init.add_argument('--no-git', action='store_true', help="skip git initialization")
    p_init.add_argument('--no-commit', action='store_true', help="skip initial git commit")
    p_init.add_argument(
        '--source-locale',
        metavar='LOCALE',
        default=DEFAULT_SOURCE_LOCALE,
        help=f"source locale for translations (default: {DEFAULT_SOURCE_LOCALE})",
    )
    p_init.set_defaults(run_command=_run_plugins)

    # --- validate ---
    p_validate = verb_parsers.add_parser('validate', help='validate a plugin MANIFEST')
    p_validate.add_argument('source', metavar='PATH_OR_URL', help="local path or git URL to validate")
    p_validate.add_argument('--ref', metavar='REF', help="git ref to checkout for validation")
    p_validate.set_defaults(run_command=_run_plugins)

    # --- refs ---
    p_refs = verb_parsers.add_parser('refs', help='list available git refs for a plugin')
    p_refs.add_argument('plugin', metavar='PLUGIN', help="plugin name, ID, URL, or UUID")
    p_refs.set_defaults(run_command=_run_plugins)

    # --- switch-ref ---
    p_switch_ref = verb_parsers.add_parser('switch-ref', help='switch plugin to a different git ref')
    p_switch_ref.add_argument('plugin', metavar='PLUGIN', help="plugin name, ID, or UUID")
    p_switch_ref.add_argument('ref', metavar='REF', help="target branch, tag, or commit")
    p_switch_ref.set_defaults(run_command=_run_plugins)

    # --- manifest ---
    p_manifest = verb_parsers.add_parser('manifest', help='show MANIFEST.toml (template if no argument)')
    p_manifest.add_argument(
        'target', nargs='?', default='', metavar='PLUGIN_OR_PATH', help="plugin, path, or URL (omit for template)"
    )
    p_manifest.set_defaults(run_command=_run_plugins)

    # --- check-blacklist ---
    p_blacklist = verb_parsers.add_parser('check-blacklist', help='check if URL/UUID is blacklisted')
    p_blacklist.add_argument('url', nargs='?', default='', metavar='URL', help="git URL to check")
    p_blacklist.add_argument('--uuid', metavar='UUID', help="plugin UUID to check")
    p_blacklist.set_defaults(run_command=_run_plugins)

    # --- clean-config ---
    p_clean = verb_parsers.add_parser('clean-config', help='delete saved options for a plugin')
    p_clean.add_argument(
        'plugin', nargs='?', default='', metavar='PLUGIN', help="plugin to clean (omit to list orphaned configs)"
    )
    p_clean.set_defaults(run_command=_run_plugins)

    # --- refresh-registry ---
    p_refresh = verb_parsers.add_parser('refresh-registry', help='force refresh of plugin registry cache')
    p_refresh.set_defaults(run_command=_run_plugins)

    # --- check-updates ---
    p_check = verb_parsers.add_parser('check-updates', help='check for available updates')
    p_check.set_defaults(run_command=_run_plugins)

    # Default handler when no verb is given
    plugins_parser.set_defaults(run_command=_run_plugins)


def _run_plugins(args):
    """Initialize and run the plugin CLI with subcommand args."""
    from picard.cli._bootstrap import (
        init_cli,
        is_color_disabled,
    )
    from picard.const import USER_PLUGIN_DIR
    from picard.git.factory import has_git_backend
    from picard.plugin3.cli import PluginCLI
    from picard.plugin3.manager import PluginManager
    from picard.plugin3.output import PluginOutput
    from picard.util import cli

    # Check git backend
    try:
        if not has_git_backend():
            cli.print_message_and_exit("git backend not available", status=1)
    except ImportError as err:
        cli.print_message_and_exit("failed importing git backend", str(err), status=1)

    # No verb specified - show help
    verb = getattr(args, 'verb', None)
    if not verb:
        print("Usage: picard-cli plugins <command> [options]")
        print()
        print("Run 'picard-cli plugins --help' for available commands.")
        return 0

    # Bootstrap app, logging, and debug options
    app = init_cli(args, with_webservice=True)  # noqa: F841

    # Create plugin manager
    manager = PluginManager()
    manager.add_directory(USER_PLUGIN_DIR, primary=True)

    # Create output
    output = PluginOutput(color=False if is_color_disabled(args) else None)

    return PluginCLI(manager, args, output=output).run()


def _argparse():
    """Lazy import of argparse."""
    import argparse

    return argparse
