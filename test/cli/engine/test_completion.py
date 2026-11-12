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

import os
import unittest
from unittest.mock import (
    MagicMock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.album import Album
from picard.cli.engine.builtins import register_builtins
from picard.cli.engine.commands import (
    EngineCommand,
    EngineCommandRegistry,
)
from picard.cli.engine.completion import (
    _complete_path_word,
    complete,
)
from picard.cli.engine.dispatch import split_line
from picard.cli.engine.session import LocalEngineSession
from picard.cluster import Cluster
from picard.const.sys import IS_WIN
from picard.track import Track
from picard.workspace import workspace


class CompleteTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.reg = EngineCommandRegistry()
        register_builtins(self.reg)
        self.session = LocalEngineSession(MagicMock())
        wks = workspace()
        wks.albums = {'rel-1': Album('rel-1')}
        wks.clusters.append(Cluster('A Cluster', 'An Artist'))

    def _complete(self, line):
        # Emulate readline: text is the trailing whitespace-delimited token
        # ('' when the line ends with a space, i.e. starting a new token).
        text = '' if (not line or line.endswith(' ')) else line.split(' ')[-1]
        return complete(line, text, self.reg, self.session)

    def test_empty_completes_command_names(self):
        matches = self._complete('')
        self.assertIn('ls', matches)
        self.assertIn('file add', matches)
        self.assertIn('quit', matches)

    def test_prefix_filters_command_names(self):
        matches = self._complete('cl')
        self.assertIn('cluster', matches)
        self.assertIn('cluster lookup', matches)
        self.assertNotIn('ls', matches)

    def test_two_word_verb_completion(self):
        # "cluster " -> offer BOTH the verb of the two-word command (lookup)
        # and the one-word command's selector args, because 'cluster' is both a
        # command and the noun of 'cluster lookup'.
        matches = self._complete('cluster ')
        self.assertIn('lookup', matches)
        self.assertIn('a*', matches)

    def test_second_word_completes_verb_when_first_word_is_also_command(self):
        # Regression: 'cluster loo<TAB>' must complete to 'lookup' even though
        # 'cluster' is itself a valid command (its arg0 is a selector).
        matches = self._complete('cluster loo')
        self.assertEqual(['lookup'], matches)

    def test_second_word_verb_completion_filters_by_prefix(self):
        # A prefix that matches no verb (and no handle) yields nothing.
        matches = self._complete('cluster zzz')
        self.assertEqual([], matches)

    def test_selector_arg_completes_handles_and_wildcards(self):
        # Mint handles first so they are live.
        self.session.resolve('a*')
        self.session.resolve('c*')
        matches = self._complete('ls ')
        self.assertIn('a1', matches)
        self.assertIn('c1', matches)
        self.assertIn('*', matches)
        self.assertIn('a*', matches)

    def test_selector_prefix_filters(self):
        self.session.resolve('a*')
        matches = self._complete('ls a')
        self.assertIn('a1', matches)
        self.assertIn('a*', matches)
        self.assertNotIn('c*', matches)

    def test_every_word_of_the_last_argument_is_completed(self):
        # 'move' takes sources and a destination, all selectors in one argument.
        self.assertIn('c1', self._complete('move c'))
        self.assertIn('c1', self._complete('move c1 c'))
        self.assertIn('u', self._complete('move c1 f1 '))

    def test_path_completion_for_a_later_word(self):
        self._load_album()
        self.assertIn('a1.t1', self._complete('move c1 a1.'))

    def test_later_words_of_a_path_argument_are_completed(self):
        # Several paths can be given to 'file add'.
        with patch('picard.cli.engine.completion._complete_path', return_value=['/music/b']) as complete_path:
            self.assertEqual(['/music/b'], self._complete('file add /music/a /m'))
        complete_path.assert_called_once_with('/m')

    def test_no_completion_for_a_command_without_arguments(self):
        registry = EngineCommandRegistry()
        registry.register(EngineCommand(name='noop', run=lambda session, args: None))
        self.assertEqual([], complete('noop x', 'x', registry, self.session))

    def test_setting_names_are_completed_for_shell_set_and_get(self):
        for command in ('shell set', 'shell get'):
            with self.subTest(command=command):
                self.assertEqual(['minted_max', 'open_max'], self._complete(f'{command} '))
                self.assertEqual(['open_max'], self._complete(f'{command} op'))
                self.assertEqual([], self._complete(f'{command} zzz'))

    def test_kinds_of_handles_are_completed_for_shell_remint(self):
        self.assertEqual(['a', 'c', 'f', 'k', 'm', 't', 'v'], self._complete('shell remint '))
        self.assertEqual(['c'], self._complete('shell remint f c'))

    def test_the_value_of_a_setting_is_not_completed(self):
        self.assertEqual([], self._complete('shell set open_max '))

    def test_selector_offers_the_unclustered_bucket(self):
        self.assertIn('u', self._complete('ls '))

    def test_path_segments_after_a_dot(self):
        self._load_album()
        matches = self._complete('ls a1.')
        self.assertEqual(['a1.d*', 'a1.d1', 'a1.f*', 'a1.t*', 'a1.t1', 'a1.t2', 'a1.u'], matches)

    def test_path_segments_are_filtered_by_what_is_typed(self):
        self._load_album()
        self.assertEqual(['a1.t*', 'a1.t1', 'a1.t2'], self._complete('ls a1.t'))
        self.assertEqual(['a1.d*', 'a1.d1'], self._complete('ls a1.d'))

    def test_path_completion_goes_deeper(self):
        self._load_album()
        self.assertEqual(['a1.d1.f*', 'a1.d1.t*', 'a1.d1.t1', 'a1.d1.t2'], self._complete('ls a1.d1.'))

    def test_path_completion_applies_to_any_selector_argument(self):
        self._load_album()
        self.assertIn('a1.t1', self._complete('save a1.'))
        self.assertIn('a1.t1', self._complete('tree a1.'))
        # 'match' takes a target and a candidate; both are selectors.
        self.assertIn('a1.t1', self._complete('match a1.'))

    def test_only_the_last_term_of_a_union_is_completed(self):
        self._load_album()
        self.assertEqual(
            ['a1.d1,a1.t*', 'a1.d1,a1.t1', 'a1.d1,a1.t2'],
            self._complete('ls a1.d1,a1.t'),
        )

    def test_union_of_handles_is_completed(self):
        self.assertIn('a1,c1', self._complete('ls a1,c'))

    def test_unknown_path_base_completes_nothing(self):
        self.assertEqual([], self._complete('ls a9.'))
        self.assertEqual([], self._complete('ls a1.k1.'))

    def _load_album(self):
        album = workspace().albums['rel-1']
        album.loaded = True
        for number in (1, 2):
            track = Track(f'trk-{number}', album)
            track.metadata['discnumber'] = '1'
            track.metadata['tracknumber'] = str(number)
            album.tracks.append(track)
        self.session.handle_for(album)

    def test_path_arg_completes_filesystem(self):
        tmp = self.mktmpdir()
        open(os.path.join(tmp, 'song.flac'), 'w').close()
        open(os.path.join(tmp, 'other.mp3'), 'w').close()
        prefix = os.path.join(tmp, 's')
        matches = complete('file add ' + prefix, prefix, self.reg, self.session)
        self.assertEqual([os.path.join(tmp, 'song.flac')], matches)

    def test_path_completion_treats_brackets_as_part_of_the_name(self):
        tmp = self.mktmpdir()
        album = os.path.join(tmp, 'Billy Joel - [1998] Storm Front')
        os.mkdir(album)
        open(os.path.join(album, 'song.flac'), 'w').close()

        def complete_word(typed):
            # Readline gives what follows the last space; the path is typed in an
            # open double quote, which reads the same on every platform.
            text = typed.rsplit(' ', 1)[-1]
            return complete('file add ' + typed, text, self.reg, self.session), len(typed) - len(text)

        quoted_album = '"' + album + os.sep
        for typed in ('"' + os.path.join(tmp, 'Billy Joel - [19'), '"' + os.path.join(tmp, 'Billy Joel - [1998] St')):
            with self.subTest(typed=typed):
                matches, start = complete_word(typed)
                self.assertEqual([quoted_album[start:]], matches)
        matches, start = complete_word(quoted_album + 's')
        self.assertEqual([('"' + os.path.join(album, 'song.flac') + '"')[start:]], matches)

    def test_tag_arg_completes_tag_names(self):
        self.set_config_values(setting={'va_name': 'Various Artists'})
        with patch('picard.tags.tag_names', return_value=iter(['album', 'albumartist', 'artist'])):
            matches = self._complete('metadata show f1 alb')
        self.assertEqual(['album', 'albumartist'], matches)

    def test_path_completes_directory_with_sep(self):
        tmp = self.mktmpdir()
        os.mkdir(os.path.join(tmp, 'sub'))
        prefix = os.path.join(tmp, 'su')
        matches = complete('file add ' + prefix, prefix, self.reg, self.session)
        self.assertEqual([os.path.join(tmp, 'sub') + os.sep], matches)

    def test_disc_read_device_completes_cdrom_drives(self):
        with patch('picard.util.cdrom.get_cdrom_drives', return_value=['/dev/cdrom', '/dev/sr0']):
            matches = self._complete('disc read ')
        self.assertIn('/dev/cdrom', matches)
        self.assertIn('/dev/sr0', matches)

    def test_disc_read_device_filters_by_prefix(self):
        with patch('picard.util.cdrom.get_cdrom_drives', return_value=['/dev/cdrom', '/dev/sr0']):
            matches = complete('disc read /dev/sr', '/dev/sr', self.reg, self.session)
        self.assertEqual(['/dev/sr0'], matches)

    def test_unknown_command_no_matches(self):
        self.assertEqual([], self._complete('bogus '))


class SystemCommandCompletionTest(PicardTestCase):
    """After ``!command``, the words of a line for the system shell are paths."""

    def setUp(self):
        super().setUp()
        self.reg = EngineCommandRegistry()
        register_builtins(self.reg)
        self.session = LocalEngineSession(MagicMock())
        self.tmp = self.mktmpdir()
        open(os.path.join(self.tmp, 'song.flac'), 'w').close()

    def _complete(self, line):
        text = '' if line.endswith(' ') else line.split(' ')[-1]
        return complete(line, text, self.reg, self.session)

    def test_the_arguments_are_paths(self):
        self.assertEqual([os.path.join(self.tmp, 'song.flac')], self._complete(f'!ls {self.tmp}{os.sep}so'))

    def test_the_command_itself_is_not_completed(self):
        self.assertEqual([], self._complete('!l'))
        self.assertEqual([], self._complete('! l'))

    def test_engine_commands_are_not_offered(self):
        self.assertNotIn('ls', self._complete('!ls '))


@unittest.skipIf(IS_WIN, "the POSIX rules: the paths of Windows have backslashes, see WindowsPathCompletionTest")
class PathWithSpacesCompletionTest(PicardTestCase):
    """A path with spaces is completed as one word, written as it would be typed (POSIX rules)."""

    def setUp(self):
        super().setUp()
        self.tmp = self.mktmpdir()
        os.mkdir(os.path.join(self.tmp, 'Black Sabbath'))
        os.mkdir(os.path.join(self.tmp, 'Blackwater Holylight'))
        open(os.path.join(self.tmp, 'Black Sabbath', '01 Paranoid.flac'), 'w').close()
        open(os.path.join(self.tmp, "it's.flac"), 'w').close()

    def _complete(self, typed):
        line = 'file add ' + typed
        text = line.rsplit(' ', 1)[-1]
        return _complete_path_word(line, text, posix=True), line[: len(line) - len(text)]

    def _check(self, typed, expected_completions, expected_path):
        matches, head = self._complete(typed)
        self.assertEqual(expected_completions, matches)
        if expected_path is not None:
            # The line, completed, is read back as the path.
            self.assertEqual(expected_path, split_line(head + matches[0], posix=True)[-1])

    def test_the_names_with_spaces_are_offered_escaped(self):
        matches, _head = self._complete(self.tmp + '/Black')
        self.assertEqual([self.tmp + '/Black\\ Sabbath/', self.tmp + '/Blackwater\\ Holylight/'], matches)

    def test_an_escaped_space_is_part_of_the_word(self):
        self._check(self.tmp + '/Black\\ S', ['Sabbath/'], self.tmp + '/Black Sabbath/')

    def test_in_an_open_double_quote(self):
        self._check('"' + self.tmp + '/Black S', ['Sabbath/'], None)
        self._check(
            '"' + self.tmp + '/Black Sabbath/01 P', ['Paranoid.flac"'], self.tmp + '/Black Sabbath/01 Paranoid.flac'
        )

    def test_a_file_in_escaped_words(self):
        self._check(
            self.tmp + '/Black\\ Sabbath/01\\ P', ['Paranoid.flac'], self.tmp + '/Black Sabbath/01 Paranoid.flac'
        )

    def test_a_single_quote_in_a_name(self):
        self._check(self.tmp + '/it', [self.tmp + "/it\\'s.flac"], self.tmp + "/it's.flac")
        self._check("'" + self.tmp + '/it', ["'" + self.tmp + "/it'\\''s.flac'"], self.tmp + "/it's.flac")

    def test_a_space_that_is_not_escaped_ends_the_word(self):
        # As in a shell: 'Black S' is two words, and nothing starts with S here.
        self._check(self.tmp + '/Black S', [], None)

    def test_a_backslash_at_the_end_of_an_open_double_quote(self):
        # As without a quote, it has nothing to escape yet and is left out.
        self._check(
            '"' + self.tmp + '/Black Sabbath/01 Paranoid\\',
            ['Paranoid.flac"'],
            self.tmp + '/Black Sabbath/01 Paranoid.flac',
        )

    def test_a_backslash_at_the_end_is_waiting_for_what_it_escapes(self):
        matches, _head = self._complete(self.tmp + '/Black\\')
        self.assertEqual([self.tmp + '/Black\\ Sabbath/', self.tmp + '/Blackwater\\ Holylight/'], matches)


class WindowsPathCompletionTest(PicardTestCase):
    """The same on Windows, where a backslash is a separator: a path with spaces is put in double quotes."""

    def _complete(self, line, paths):
        text = line.rsplit(' ', 1)[-1]
        with patch('picard.cli.engine.completion._complete_path', return_value=paths) as complete_path:
            matches = _complete_path_word(line, text, posix=False)
        return matches, complete_path.call_args.args[0]

    def test_a_path_without_spaces_is_as_it_is(self):
        matches, value = self._complete('file add C:\\Mus', ['C:\\Music' + os.sep])
        self.assertEqual((['C:\\Music' + os.sep], 'C:\\Mus'), (matches, value))

    def test_a_directory_with_spaces_opens_a_double_quote(self):
        matches, _value = self._complete('file add C:\\My', ['C:\\My Music' + os.sep])
        self.assertEqual(['"C:\\My Music' + os.sep], matches)

    def test_in_the_open_double_quote(self):
        matches, value = self._complete('file add "C:\\My Mu', ['C:\\My Music' + os.sep])
        self.assertEqual((['Music' + os.sep], 'C:\\My Mu'), (matches, value))

    def test_the_content_of_a_directory_left_open_in_quotes(self):
        # The backslash that ends the directory does not escape the closing quote.
        matches, value = self._complete('file add "C:\\My Music\\', ['C:\\My Music\\a b.flac'])
        self.assertEqual((['Music\\a b.flac"'], 'C:\\My Music\\'), (matches, value))

    def test_a_file_closes_the_double_quote(self):
        matches, value = self._complete('file add "C:\\My Music\\a', ['C:\\My Music\\a b.flac'])
        self.assertEqual((['Music\\a b.flac"'], 'C:\\My Music\\a'), (matches, value))
        self.assertEqual(
            ['file', 'add', 'C:\\My Music\\a b.flac'], split_line('file add "C:\\My ' + matches[0], posix=False)
        )
