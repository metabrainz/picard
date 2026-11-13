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

"""Unit tests for file-add path resolution (globs, directories, spaces)."""

import os
import shlex
import unittest

from test.picardtestcase import PicardTestCase

from picard.cli.engine.builtins.files import (
    _expand_input_paths,
    _named_files,
)
from picard.const.sys import IS_WIN
from picard.util import (
    normpath,
    resolve_fs_path,
)


def _resolved(paths):
    """``paths`` as the real paths they lead to: a temporary directory can be reached by more than one name.

    That is the case on macOS (/var is /private/var) and on Windows (a short
    8.3 name of the user directory), and the paths that come back are resolved.
    """
    return sorted(os.path.realpath(path) for path in paths)


class ExpandInputPathsTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values(setting={'recursively_add_files': True, 'ignore_hidden_files': True})
        self.root = self.mktmpdir()

    def _touch(self, rel):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(rel) else None
        open(path, 'w').close()
        return path

    def test_single_file(self):
        f = self._touch('a.mp3')
        files, unmatched = _expand_input_paths([f])
        self.assertEqual(_resolved([f]), _resolved(files))
        self.assertEqual([], unmatched)

    def test_directory_is_walked(self):
        self._touch('a.mp3')
        self._touch('b.flac')
        files, unmatched = _expand_input_paths([self.root])
        self.assertEqual({'a.mp3', 'b.flac'}, {os.path.basename(f) for f in files})
        self.assertEqual([], unmatched)

    def test_glob_expansion(self):
        self._touch('a.mp3')
        self._touch('b.mp3')
        self._touch('c.flac')
        files, unmatched = _expand_input_paths([os.path.join(self.root, '*.mp3')])
        self.assertEqual({'a.mp3', 'b.mp3'}, {os.path.basename(f) for f in files})
        self.assertEqual([], unmatched)

    def test_unmatched_token_reported(self):
        files, unmatched = _expand_input_paths([os.path.join(self.root, 'nope.mp3')])
        self.assertEqual([], files)
        self.assertEqual([os.path.join(self.root, 'nope.mp3')], unmatched)

    def test_unquoted_spaces_path_fallback(self):
        # Simulate the shell having split "<root>/Second tour/x.mp3" on spaces.
        subdir = os.path.join(self.root, 'Second tour')
        os.mkdir(subdir)
        self._touch(os.path.join('Second tour', 'song.mp3'))
        tokens = (os.path.join(self.root, 'Second') + ' tour').split(' ')
        # tokens == ['<root>/Second', 'tour'] — neither exists alone.
        files, unmatched = _expand_input_paths(tokens)
        self.assertEqual(['song.mp3'], [os.path.basename(f) for f in files])
        self.assertEqual([], unmatched)

    def test_spaces_glob_fallback(self):
        subdir = os.path.join(self.root, 'Second tour')
        os.mkdir(subdir)
        self._touch(os.path.join('Second tour', 'song.mp3'))
        tokens = (os.path.join(self.root, 'Second') + ' tour/*.mp3').split(' ')
        files, unmatched = _expand_input_paths(tokens)
        self.assertEqual(['song.mp3'], [os.path.basename(f) for f in files])
        self.assertEqual([], unmatched)


class ExpandInputPathsSpecialCharactersTest(PicardTestCase):
    """Names with characters that are also glob syntax ([, ], *, ?).

    The command line is not expanded by a shell, so a path that exists must be
    taken as it is: `[1998]` in a folder name is not a character class.
    """

    def setUp(self):
        super().setUp()
        self.set_config_values(setting={'recursively_add_files': True, 'ignore_hidden_files': True})
        self.root = self.mktmpdir()
        self.album = os.path.join(self.root, 'Billy Joel - [1998] Storm Front')
        os.mkdir(self.album)
        self.song = os.path.join(self.album, '01 Song.flac')
        open(self.song, 'w').close()
        self.other = os.path.join(self.album, '02 Other.mp3')
        open(self.other, 'w').close()

    def _names(self, files):
        return sorted(os.path.basename(f) for f in files)

    def test_folder_with_square_brackets(self):
        files, unmatched = _expand_input_paths([self.album + os.sep])
        self.assertEqual(['01 Song.flac', '02 Other.mp3'], self._names(files))
        self.assertEqual([], unmatched)

    def test_folder_with_square_brackets_without_trailing_separator(self):
        files, unmatched = _expand_input_paths([self.album])
        self.assertEqual(['01 Song.flac', '02 Other.mp3'], self._names(files))
        self.assertEqual([], unmatched)

    @unittest.skipIf(IS_WIN, "a backslash is the path separator on Windows")
    def test_backslash_escaped_brackets_are_accepted(self):
        # What a user types after bash habits: "...\[1998\] Storm Front/".
        escaped = self.album.replace('[', '\\[').replace(']', '\\]')
        files, unmatched = _expand_input_paths([escaped + os.sep])
        self.assertEqual(['01 Song.flac', '02 Other.mp3'], self._names(files))
        self.assertEqual([], unmatched)

    @unittest.skipIf(IS_WIN, "a backslash is the path separator on Windows")
    def test_the_spellings_tried_on_the_command_line(self):
        # As typed after `file add `, through the same tokenizer the shell uses.
        album = self.album
        escaped = album.replace('[', '\\[').replace(']', '\\]')
        double_escaped = album.replace('[', '\\\\[').replace(']', '\\\\]')
        lines = (
            f'"{album}/"',
            f"'{album}/'",
            f'"{escaped}/"',
            f"'{escaped}/'",
            album.replace(' ', '\\ ') + '/',
            escaped.replace(' ', '\\ ') + '/',
        )
        for line in lines:
            with self.subTest(line=line):
                files, unmatched = _expand_input_paths(shlex.split(line))
                self.assertEqual(['01 Song.flac', '02 Other.mp3'], self._names(files))
                self.assertEqual([], unmatched)
        # Doubled backslashes inside double quotes reach us as one backslash per bracket.
        with self.subTest(line='doubled'):
            files, unmatched = _expand_input_paths(shlex.split(f'"{double_escaped}/"'))
            self.assertEqual(['01 Song.flac', '02 Other.mp3'], self._names(files))

    def test_pattern_inside_a_folder_with_square_brackets(self):
        files, unmatched = _expand_input_paths([os.path.join(self.album, '*.flac')])
        self.assertEqual(['01 Song.flac'], self._names(files))
        self.assertEqual([], unmatched)

    def test_file_with_square_brackets(self):
        path = os.path.join(self.root, '[Live] song.flac')
        open(path, 'w').close()
        files, unmatched = _expand_input_paths([path])
        self.assertEqual(_resolved([path]), _resolved(files))
        self.assertEqual([], unmatched)

    @unittest.skipIf(IS_WIN, "? and * cannot be in a file name on Windows")
    def test_file_with_other_pattern_characters(self):
        paths = [os.path.join(self.root, name) for name in ('what?.flac', 'a*b.flac')]
        for path in paths:
            open(path, 'w').close()
        files, unmatched = _expand_input_paths(paths)
        self.assertEqual(_resolved(paths), _resolved(files))
        self.assertEqual([], unmatched)

    def test_character_class_still_works_as_a_pattern_when_no_such_path_exists(self):
        for name in ('a.mp3', 'b.mp3', 'c.mp3'):
            open(os.path.join(self.root, name), 'w').close()
        files, unmatched = _expand_input_paths([os.path.join(self.root, '[ab].mp3')])
        self.assertEqual(['a.mp3', 'b.mp3'], self._names(files))
        self.assertEqual([], unmatched)

    def test_an_existing_path_wins_over_the_pattern_it_could_also_be(self):
        literal = os.path.join(self.root, '[ab].mp3')
        open(literal, 'w').close()
        open(os.path.join(self.root, 'a.mp3'), 'w').close()
        files, unmatched = _expand_input_paths([literal])
        self.assertEqual(_resolved([literal]), _resolved(files))

    def test_missing_path_with_brackets_is_still_reported(self):
        token = os.path.join(self.root, 'Nothing - [1998]')
        files, unmatched = _expand_input_paths([token])
        self.assertEqual([], files)
        self.assertEqual([token], unmatched)

    def test_unquoted_spaces_and_brackets_fallback(self):
        # The tokenizer split "<album>" on its spaces.
        tokens = self.album.split(' ')
        files, unmatched = _expand_input_paths(tokens)
        self.assertEqual(['01 Song.flac', '02 Other.mp3'], self._names(files))
        self.assertEqual([], unmatched)


class NamedFilesSpecialCharactersTest(PicardTestCase):
    def test_named_file_with_square_brackets(self):
        root = self.mktmpdir()
        path = os.path.join(root, '[Cover] front.jpg')
        open(path, 'w').close()
        self.assertEqual({normpath(resolve_fs_path(path))}, _named_files([path]))

    def test_pattern_and_folder_are_not_named(self):
        root = self.mktmpdir()
        open(os.path.join(root, 'a.jpg'), 'w').close()
        self.assertEqual(set(), _named_files([os.path.join(root, '*.jpg'), root]))
