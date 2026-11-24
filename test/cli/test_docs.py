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
# along with this program; if not, see <https://www.gnu.org/licenses/>.

"""Tests for the `picard-cli docs` subcommand.

The topics, the formatters and the command handlers are tested in-process.
The end-to-end tests run the CLI as a subprocess: the command builds a
HeadlessTagger (a QCoreApplication), and only one Qt application may exist per
process, so it cannot run alongside the suite's QApplication.
"""

from io import StringIO
import json
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from test.cli.test_tag import _run_cli
from test.picardtestcase import PicardTestCase

from picard.cli.base import ExitCode
from picard.cli.doc_formatters import (
    FORMATTERS,
    DocFormatError,
    markdown,
    render_console,
    render_html,
    render_json,
    render_markdown,
)
from picard.cli.doc_topics import (
    DOC_TOPICS,
    DocEntry,
    DocNotFoundError,
    DocTopic,
    ScriptFunctionsTopic,
    ScriptVariablesTopic,
    get_topic,
)
from picard.cli.docs import (
    cmd_list,
    cmd_show,
)
from picard.cli.output import CliOutput
from picard.extension_points.script_functions import FunctionRegistryItem
from picard.tags.tagvar import TagVar


class FakeTopic(DocTopic):
    def __init__(self):
        super().__init__(name='fake', title='Fake topic', help='a fake topic')

    def entries(self):
        return [
            DocEntry(
                'alpha',
                '$alpha(x)',
                'Does **alpha** with `x`.\nSee [the docs](https://example.org/a) and \\* stars.\n\n'
                '    $alpha(one)\n\n    $alpha(two)\n\nResult: `\\$`\n\n_Since Picard 9.9_',
                code_title=True,
            ),
            DocEntry('beta', 'Beta', 'Plain text.'),
        ]


def _make_output(color=False):
    stdout = StringIO()
    stderr = StringIO()
    return CliOutput(stdout=stdout, stderr=stderr, color=color), stdout, stderr


def _function_item(name, signature, documentation):
    return FunctionRegistryItem(
        lambda parser: '',
        True,
        None,
        documentation=documentation,
        name=name,
        module='test',
        signature=signature,
    )


class DocTopicTest(PicardTestCase):
    def test_select_all(self):
        entries = FakeTopic().select()
        self.assertEqual(['alpha', 'beta'], [entry.name for entry in entries])

    def test_select_keeps_topic_order_and_ignores_duplicates(self):
        entries = FakeTopic().select(['beta', 'alpha', 'beta'])
        self.assertEqual(['alpha', 'beta'], [entry.name for entry in entries])

    def test_select_unknown_names(self):
        with self.assertRaises(DocNotFoundError) as cm:
            FakeTopic().select(['alpha', 'zeta', 'gamma'])
        self.assertEqual(('gamma', 'zeta'), cm.exception.names)

    def test_registry_names_are_unique_and_found(self):
        names = [topic.name for topic in DOC_TOPICS]
        self.assertEqual(len(names), len(set(names)))
        for name in names:
            self.assertEqual(name, get_topic(name).name)

    def test_get_topic_unknown(self):
        with self.assertRaises(KeyError):
            get_topic('nosuchtopic')


class ScriptFunctionsTopicTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        items = [
            ('zed', _function_item('zed', '$zed(x)', 'Last one.')),
            ('alpha', _function_item('alpha', '$alpha()', '  First one.  \n')),
            ('nodoc', _function_item('nodoc', '$nodoc()', None)),
        ]
        patcher = patch('picard.cli.doc_topics.ext_point_script_functions', items)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.topic = ScriptFunctionsTopic()

    def test_entries_are_sorted_with_title_and_body(self):
        entries = self.topic.entries()
        self.assertEqual(['alpha', 'nodoc', 'zed'], [entry.name for entry in entries])
        alpha = entries[0]
        self.assertEqual('$alpha()', alpha.title)
        self.assertEqual('First one.', alpha.body)
        self.assertTrue(alpha.code_title)
        self.assertEqual('', entries[1].body)

    def test_select_accepts_leading_dollar(self):
        entries = self.topic.select(['$zed', 'alpha'])
        self.assertEqual(['alpha', 'zed'], [entry.name for entry in entries])

    def test_select_unknown_function(self):
        with self.assertRaises(DocNotFoundError):
            self.topic.select(['$nosuchfunction'])


class ScriptVariablesTopicTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        hidden = TagVar(name='hidden_var', longdesc='A hidden one.', is_hidden=True, is_multi_value=True)
        visible = TagVar(name='visible_var', longdesc='A **visible** one.')
        patcher = patch('picard.cli.doc_topics.documented_script_variables', return_value=[hidden, visible])
        patcher.start()
        self.addCleanup(patcher.stop)
        self.topic = ScriptVariablesTopic()

    def test_entries(self):
        hidden, visible = self.topic.entries()
        self.assertEqual(
            DocEntry('_hidden_var', '%_hidden_var%', 'A hidden one.\n\n**Notes:** multi-value variable.', True), hidden
        )
        self.assertEqual(DocEntry('visible_var', '%visible_var%', 'A **visible** one.', True), visible)

    def test_select_accepts_percent_signs(self):
        entries = self.topic.select(['%visible_var%', '_hidden_var'])
        self.assertEqual(['_hidden_var', 'visible_var'], [entry.name for entry in entries])

    def test_select_unknown_variable(self):
        with self.assertRaises(DocNotFoundError):
            self.topic.select(['%hidden_var%'])


class DocFormattersTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.topic = FakeTopic()
        self.entries = self.topic.entries()

    def test_formats_are_registered(self):
        self.assertEqual({'console', 'markdown', 'html', 'json'}, set(FORMATTERS))

    def test_markdown(self):
        output, _stdout, _stderr = _make_output()
        text = render_markdown(self.topic, self.entries, output)
        self.assertTrue(text.startswith('# Fake topic\n\n## `$alpha(x)`\n\nDoes **alpha**'))
        self.assertIn('\n\n## Beta\n\nPlain text.\n', text)
        self.assertTrue(text.endswith('\n'))

    def test_json(self):
        output, _stdout, _stderr = _make_output()
        data = json.loads(render_json(self.topic, self.entries, output))
        self.assertEqual('fake', data['topic'])
        self.assertEqual('Fake topic', data['title'])
        self.assertEqual(['alpha', 'beta'], [entry['name'] for entry in data['entries']])
        alpha = data['entries'][0]
        self.assertEqual('$alpha(x)', alpha['title'])
        self.assertTrue(alpha['code_title'])
        self.assertTrue(alpha['body'].startswith('Does **alpha**'))
        self.assertFalse(data['entries'][1]['code_title'])

    def test_console_without_color_keeps_markers(self):
        output, _stdout, _stderr = _make_output(color=False)
        text = render_console(self.topic, self.entries, output)
        self.assertNotIn('\033', text)
        self.assertTrue(text.startswith('$alpha(x)\n\nDoes **alpha** with `x`.'))
        # links show the target, escapes are removed outside of code
        self.assertIn('See the docs (https://example.org/a) and * stars.', text)
        # code blocks and code spans are kept as is
        self.assertIn('\n    $alpha(one)\n\n    $alpha(two)\n', text)
        self.assertIn('Result: `\\$`', text)
        # emphasis markers are kept
        self.assertIn('\n_Since Picard 9.9_\n', text)
        self.assertIn('\n\nBeta\n\nPlain text.\n', text)

    def test_console_with_color(self):
        output, _stdout, _stderr = _make_output(color=True)
        text = render_console(self.topic, self.entries, output)
        self.assertIn(output.d_command('$alpha(x)'), text)
        self.assertIn(output.bold('alpha'), text)
        self.assertIn(output.cyan('x'), text)
        self.assertIn(output.cyan('\\$'), text)
        self.assertIn(output.dim('    $alpha(one)'), text)
        # a line made only of emphasized text is dimmed, without its markers
        self.assertIn(output.dim('Since Picard 9.9'), text)
        self.assertNotIn('_Since', text)
        # non-code titles are not styled as commands
        self.assertIn(output.d_name('Beta'), text)

    def test_console_reflows_paragraphs(self):
        output, _stdout, _stderr = _make_output(color=False)
        body = (
            'Short line\nand its `inline code` continuation, then a much longer sentence that has\n'
            'to be wrapped somewhere.\n\n    $code(not,wrapped,even,if,this,line,is,longer,than,the,width)'
        )
        entries = [DocEntry('x', 'X', body)]
        text = render_console(self.topic, entries, output, width=30)
        lines = text.splitlines()
        self.assertEqual('X', lines[0])
        self.assertEqual(
            [
                'Short line and its',
                '`inline code` continuation,',
                'then a much longer sentence',
                'that has to be wrapped',
                'somewhere.',
            ],
            lines[2:7],
        )
        # code blocks are not wrapped
        self.assertIn('    $code(not,wrapped,even,if,this,line,is,longer,than,the,width)', lines)

    @unittest.skipUnless(markdown, "markdown module missing")
    def test_html(self):
        output, _stdout, _stderr = _make_output()
        text = render_html(self.topic, self.entries, output)
        self.assertTrue(text.startswith('<!DOCTYPE html>'))
        self.assertIn('<title>Fake topic</title>', text)
        self.assertIn('<h2><code>$alpha(x)</code></h2>', text)
        self.assertIn('<strong>alpha</strong>', text)
        self.assertIn('<a href="https://example.org/a">the docs</a>', text)
        self.assertIn('<h2>Beta</h2>', text)

    def test_html_without_markdown_module(self):
        output, _stdout, _stderr = _make_output()
        with patch('picard.cli.doc_formatters.markdown', None):
            with self.assertRaises(DocFormatError):
                render_html(self.topic, self.entries, output)


class DocsCommandTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        patcher = patch('picard.cli.docs.get_topic', return_value=FakeTopic())
        patcher.start()
        self.addCleanup(patcher.stop)
        self.tmpdir = self.mktmpdir()

    @staticmethod
    def _args(**kwargs):
        defaults = {'topic': 'fake', 'names': [], 'format': 'markdown', 'output': None, 'yes': False}
        return SimpleNamespace(**{**defaults, **kwargs})

    def test_list_topics(self):
        output, stdout, _stderr = _make_output()
        self.assertEqual(ExitCode.SUCCESS, cmd_list(self._args(topic=None), output))
        for topic in DOC_TOPICS:
            self.assertIn(topic.name, stdout.getvalue())

    def test_list_entries(self):
        output, stdout, _stderr = _make_output()
        self.assertEqual(ExitCode.SUCCESS, cmd_list(self._args(), output))
        self.assertEqual('alpha\nbeta\n', stdout.getvalue())

    def test_show_to_stdout(self):
        output, stdout, _stderr = _make_output()
        self.assertEqual(ExitCode.SUCCESS, cmd_show(self._args(names=['beta']), output))
        self.assertEqual('# Fake topic\n\n## Beta\n\nPlain text.\n', stdout.getvalue())

    def test_show_unknown_entry(self):
        output, stdout, stderr = _make_output()
        self.assertEqual(ExitCode.NOT_FOUND, cmd_show(self._args(names=['nosuch']), output))
        self.assertEqual('', stdout.getvalue())
        self.assertIn('nosuch', stderr.getvalue())

    def test_show_format_error(self):
        output, _stdout, stderr = _make_output()
        with patch('picard.cli.doc_formatters.markdown', None):
            self.assertEqual(ExitCode.ERROR, cmd_show(self._args(format='html'), output))
        self.assertIn('markdown', stderr.getvalue())

    def test_show_to_file_is_not_colored(self):
        path = os.path.join(self.tmpdir, 'out.txt')
        output, stdout, _stderr = _make_output(color=True)
        self.assertEqual(ExitCode.SUCCESS, cmd_show(self._args(format='console', output=path), output))
        with open(path, encoding='utf-8') as f:
            self.assertNotIn('\033', f.read())
        self.assertIn(path, stdout.getvalue())

    def test_show_to_file_asks_before_overwriting(self):
        path = os.path.join(self.tmpdir, 'out.md')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('existing')
        output, _stdout, _stderr = _make_output()
        with patch.object(CliOutput, 'yesno', return_value=False) as yesno:
            self.assertEqual(ExitCode.SUCCESS, cmd_show(self._args(output=path), output))
        yesno.assert_called_once()
        with open(path, encoding='utf-8') as f:
            self.assertEqual('existing', f.read())

    def test_show_to_file_overwrites_with_yes(self):
        path = os.path.join(self.tmpdir, 'out.md')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('existing')
        output, _stdout, _stderr = _make_output()
        self.assertEqual(ExitCode.SUCCESS, cmd_show(self._args(output=path, yes=True), output))
        with open(path, encoding='utf-8') as f:
            self.assertTrue(f.read().startswith('# Fake topic'))

    def test_show_to_unwritable_file(self):
        output, _stdout, stderr = _make_output()
        path = os.path.join(self.tmpdir, 'nosuchdir', 'out.md')
        self.assertEqual(ExitCode.ERROR, cmd_show(self._args(output=path), output))
        self.assertIn('Cannot write file', stderr.getvalue())


class DocsCliTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        # Isolated, writable config file so the command never touches the
        # developer's real configuration.
        self.config_file = os.path.join(self.mktmpdir(), 'config.ini')

    def test_list_script_functions(self):
        result = _run_cli('docs', 'list', 'script-functions', config_file=self.config_file)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('sortmulti', result.stdout.splitlines())

    def test_show_markdown(self):
        result = _run_cli(
            'docs', 'show', 'script-functions', '$sortmulti', 'unique', '-f', 'markdown', config_file=self.config_file
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.stdout.startswith('# Script functions\n\n## `$sortmulti(multi[,separator=; ])`\n'))
        self.assertIn('## `$unique(multi[,case_sensitive[,separator=; ]])`', result.stdout)
        self.assertNotIn('$cleanmulti', result.stdout)

    def test_show_script_variable(self):
        result = _run_cli('docs', 'show', 'script-variables', '%album%', '-f', 'markdown', config_file=self.config_file)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('# Script variables\n\n## `%album%`\n\nThe title of the release.\n', result.stdout)

    def test_show_unknown_function(self):
        result = _run_cli('docs', 'show', 'script-functions', 'nosuchfunction', config_file=self.config_file)
        self.assertEqual(ExitCode.NOT_FOUND, result.returncode)
        self.assertIn('nosuchfunction', result.stderr)
