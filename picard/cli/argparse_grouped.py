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

"""Argparse extensions for grouped subcommand help output.

Provides a SubParsersAction subclass that supports grouping commands under
titled sections in help output, and a matching HelpFormatter.

Usage:
    parser = argparse.ArgumentParser(formatter_class=GroupedHelpFormatter)
    sp = parser.add_subparsers(action=GroupedSubParsersAction, ...)

    sp.add_parser('list', help='list items')
    sp.add_parser('install', help='install item')

    sp.start_group('development commands')
    sp.add_parser('init', help='create a project')
    sp.add_parser('validate', help='validate a manifest')
"""

import argparse


class GroupedSubParsersAction(argparse._SubParsersAction):
    """SubParsersAction that groups commands under titled sections in help.

    Commands added before the first start_group() call appear in the
    default section (whose title is set via add_subparsers(title=...)).
    Commands added after a start_group() call appear in a separate
    titled section in help output.

    All commands share the same namespace and dispatch mechanism regardless
    of their group — grouping is purely visual.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._group_map = {}  # parser_name -> group_title
        self._groups = {}  # group_title -> [parser_names] (ordered)
        self._current_group = None

    def start_group(self, title):
        """Start a new group for subsequent add_parser() calls."""
        self._current_group = title
        if title not in self._groups:
            self._groups[title] = []

    def add_parser(self, name, **kwargs):
        if self._current_group:
            self._group_map[name] = self._current_group
            self._groups[self._current_group].append(name)
        parser = super().add_parser(name, **kwargs)
        return parser

    def _get_subactions(self):
        """Yield only ungrouped actions for the default section."""
        for choice_action in self._choices_actions:
            if choice_action.dest not in self._group_map:
                yield choice_action


class GroupedHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Help formatter that renders grouped subparser sections.

    Works with GroupedSubParsersAction to display commands in
    multiple titled sections.
    """

    def _format_action(self, action):
        if not isinstance(action, GroupedSubParsersAction):
            return super()._format_action(action)

        # Format the main (ungrouped) subparsers section
        parts = [super()._format_action(action)]

        # Add additional sections for each group
        for group_title, names in action._groups.items():
            t = self._theme
            parts.append(f'\n{t.heading}{group_title}:{t.reset}\n')
            parts.append(self._current_indent * ' ')
            parts.append(self._format_action_invocation(action))
            parts.append('\n')

            self._indent()
            for name in names:
                for choice_action in action._choices_actions:
                    if choice_action.dest == name:
                        parts.append(self._format_action(choice_action))
                        break
            self._dedent()

        return ''.join(parts)
