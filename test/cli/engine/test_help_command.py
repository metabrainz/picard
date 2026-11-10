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
# along with this program; if not, see <https://www.gnu.org/licenses/>.

import io
import json

from test.picardtestcase import PicardTestCase

from picard.cli.engine.builtins import register_builtins
from picard.cli.engine.commands import EngineCommandRegistry
from picard.cli.engine.dispatch import dispatch
from picard.cli.engine.render import render_result
from picard.cli.engine.session import LocalEngineSession
from picard.cli.engine.topics import TOPICS
from picard.cli.output import CliOutput


def _names(result):
    return [item.data['name'] for item in result.items]


class _HelpTestBase(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.reg = EngineCommandRegistry()
        register_builtins(self.reg)
        self.session = LocalEngineSession(object())


class HelpCommandTest(_HelpTestBase):
    def _help(self, line='help'):
        return dispatch(self.session, self.reg, line)

    def test_without_argument_lists_the_commands_and_the_topics(self):
        result = self._help()
        self.assertTrue(result.ok)
        names = _names(result)
        self.assertEqual(sorted(self.reg.names()), [name for name in names if name in self.reg])
        for topic in TOPICS:
            self.assertIn(topic.name, names)
        self.assertTrue(all(not item.data['detail'] for item in result.items))
        self.assertTrue(all(item.data['summary'] for item in result.items))

    def test_a_command_is_explained_with_its_usage_and_description(self):
        (item,) = self._help('help ls').items
        command = self.reg.get('ls')
        self.assertEqual('command', item.data['kind'])
        self.assertTrue(item.data['detail'])
        self.assertEqual(command.usage, item.data['usage'])
        self.assertEqual(command.description, item.data['description'])

    def test_commands_of_the_registry_only(self):
        # help describes the registry it was made for, not all the built-in commands.
        other = EngineCommandRegistry()
        register_builtins(other)
        del other._commands['tree']
        result = dispatch(self.session, other, 'help tree')
        self.assertFalse(result.ok)

    def test_a_topic_is_explained(self):
        for topic in TOPICS:
            with self.subTest(topic=topic.name):
                (item,) = self._help(f'help {topic.name}').items
                self.assertEqual('topic', item.data['kind'])
                self.assertEqual(topic.text, item.data['description'])

    def test_an_unknown_name_is_refused_with_suggestions(self):
        result = self._help('help selector')
        self.assertFalse(result.ok)
        self.assertIn("'selector'", result.error)
        self.assertIn('selectors', result.error)

    def test_the_result_is_serializable(self):
        json.dumps(self._help('help move').to_dict())


class HelpRenderTest(_HelpTestBase):
    def _text(self, line='help'):
        buf = io.StringIO()
        render_result(dispatch(self.session, self.reg, line), CliOutput(stdout=buf, stderr=buf, color=False))
        return buf.getvalue()

    def test_the_list_has_commands_then_topics(self):
        text = self._text()
        self.assertLess(text.index('Commands:'), text.index('ls '))
        self.assertLess(text.index('ls '), text.index('Topics:'))
        self.assertIn('selectors', text)

    def test_selectors_name_every_kind_of_handle(self):
        lines = self._text('help selectors').splitlines()
        for handle, kind in (('f1', 'file'), ('c1', 'cluster'), ('a1', 'album'), ('t1', 'track'), ('m1', 'candidate')):
            with self.subTest(handle=handle):
                line = next(line for line in lines if line.startswith(f'  {handle} '))
                self.assertIn(kind, line)

    def test_a_command_shows_usage_then_description(self):
        text = self._text('help ls')
        self.assertTrue(text.startswith('ls [selector]\n\n'))
        self.assertIn('List the objects of the working set', text)

    def test_a_topic_shows_its_text(self):
        self.assertIn('A selector names the objects', self._text('help selectors'))
