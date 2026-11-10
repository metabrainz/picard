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

"""``metadata set``, ``add`` and ``rm``: change the tags that would be saved."""

import io
from unittest.mock import (
    MagicMock,
    patch,
)

from test.cli.engine.helpers import EngineCommandTestCase
from test.cli.engine.test_metadata_command import _file as _new_file

from picard.cli.engine.candidates import Candidate
from picard.cli.engine.render import render_result
from picard.cli.output import CliOutput
from picard.cluster import Cluster
from picard.file import File


def _file(*args, **kwargs):
    """A file that has finished loading, so that a change to its tags makes it changed."""
    file = _new_file(*args, **kwargs)
    file.state = File.State.NORMAL
    return file


class _EditTestCase(EngineCommandTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values(
            setting={
                'metadatabox_top_tags': ['title', 'artist', 'album'],
                'rename_files': False,
                'move_files': False,
                'clear_existing_tags': False,
                'ignore_track_duration_difference_under': 2,
            },
            persist={'show_changes_first': False},
        )

    def _run(self, line):
        self.run_command('ls')  # gives the entities their handles, as a user would see them
        return self.run_command(line)

    def _cluster_of(self, *files):
        cluster = Cluster('Album', 'Artist')
        cluster.add_files(list(files))
        self.wks.clusters.append(cluster)
        return cluster


class MetadataSetTest(_EditTestCase):
    def test_the_tag_is_replaced_and_the_file_is_changed(self):
        file = _file(self.wks, 'a.flac', {'title': 'Old'})
        result = self._run('metadata set f1 title New')
        self.assertTrue(result.ok, result.error)
        self.assertEqual(['New'], file.metadata.getall('title'))
        # What was loaded is untouched: only what would be saved changes.
        self.assertEqual(['Old'], file.orig_metadata.getall('title'))
        self.assertEqual(File.State.CHANGED, file.state)
        self.assertEqual(('changed', 'f1'), (result.items[0].status, result.items[0].handle))
        self.assertEqual(['f1'], result.resolved)

    def test_it_shows_as_changed_in_metadata_show(self):
        _file(self.wks, 'a.flac', {'title': 'Old'})
        self._run('metadata set f1 title New')
        (row,) = [r for r in self.run_command('metadata show f1 title').items[0].data['tags']]
        self.assertEqual(('changed', 'Old', 'New'), (row['status'], row['orig'], row['new']))

    def test_every_word_after_the_tag_is_a_value(self):
        file = _file(self.wks, 'a.flac', {'genre': 'Rock'})
        self._run('metadata set f1 genre Pop "Hip Hop"')
        self.assertEqual(['Pop', 'Hip Hop'], file.metadata.getall('genre'))

    def test_a_tag_with_the_same_values_is_unchanged(self):
        file = _file(self.wks, 'a.flac', {'title': 'Song'})
        result = self._run('metadata set f1 title Song')
        self.assertEqual('unchanged', result.items[0].status)
        self.assertEqual(File.State.NORMAL, file.state)

    def test_a_new_tag_is_added(self):
        file = _file(self.wks, 'a.flac', {'title': 'Song'})
        self._run('metadata set f1 album LP')
        self.assertEqual(['LP'], file.metadata.getall('album'))
        self.assertNotIn('album', file.orig_metadata)

    def test_a_cluster_is_changed_with_its_files(self):
        files = [_file(self.wks, f'{n}.flac', {'artist': 'Old'}) for n in 'ab']
        cluster = self._cluster_of(*files)
        handle = self.session.handle_for(cluster)
        result = self._run(f'metadata set {handle} artist New')
        self.assertTrue(result.ok, result.error)
        self.assertEqual([['New'], ['New']], [f.metadata.getall('artist') for f in files])
        self.assertEqual(['New'], cluster.metadata.getall('artist'))

    def test_a_file_that_cannot_hold_the_tag_is_left_alone_and_reported(self):
        file = _file(self.wks, 'a.flac', {'title': 'Song'})
        with patch.object(File, 'supports_tag', return_value=False):
            result = self._run('metadata set f1 totaldiscs 2')
        self.assertEqual('unsupported', result.items[0].status)
        self.assertNotIn('totaldiscs', file.metadata)

    def test_a_pattern_a_script_variable_and_an_empty_value_are_refused(self):
        _file(self.wks, 'a.flac', {'title': 'Song'})
        for line, word in (
            ('metadata set f1 art* X', 'pattern'),
            ('metadata set f1 ~length 5', 'variable'),
            ('metadata set f1 title ""', 'empty'),
        ):
            with self.subTest(line=line):
                result = self._run(line)
                self.assertFalse(result.ok)
                self.assertIn(word, result.error)

    def test_usage(self):
        for line in ('metadata set', 'metadata set f1', 'metadata set f1 title'):
            with self.subTest(line=line):
                result = self._run(line)
                self.assertFalse(result.ok)
                self.assertIn('usage: metadata set <selector> <tag> <value>...', result.error)

    def test_a_lookup_candidate_has_no_tags(self):
        cluster = self._cluster_of()
        (handle,) = self.session.set_candidates(cluster, [Candidate(MagicMock())])
        result = self._run(f'metadata set {handle} title X')
        self.assertFalse(result.ok)
        self.assertIn('has no tags', result.error)

    def test_what_matches_nothing_is_reported(self):
        result = self._run('metadata set f9 title X')
        self.assertTrue(result.ok)
        self.assertEqual(['f9'], result.unresolved)


class MetadataAddTest(_EditTestCase):
    def test_values_are_added_after_the_ones_the_tag_has(self):
        file = _file(self.wks, 'a.flac', {'genre': ['Rock']})
        result = self._run('metadata add f1 genre Pop Jazz')
        self.assertEqual('changed', result.items[0].status)
        self.assertEqual(['Rock', 'Pop', 'Jazz'], file.metadata.getall('genre'))

    def test_a_value_that_is_there_is_not_repeated(self):
        file = _file(self.wks, 'a.flac', {'genre': ['Rock', 'Pop']})
        result = self._run('metadata add f1 genre Pop')
        self.assertEqual('unchanged', result.items[0].status)
        self.assertEqual(['Rock', 'Pop'], file.metadata.getall('genre'))

    def test_each_file_gets_the_values_to_add_to_its_own(self):
        a = _file(self.wks, 'a.flac', {'genre': ['Rock']})
        b = _file(self.wks, 'b.flac', {'genre': ['Pop']})
        cluster = self._cluster_of(a, b)
        self._run(f'metadata add {self.session.handle_for(cluster)} genre Jazz')
        self.assertEqual([['Rock', 'Jazz'], ['Pop', 'Jazz']], [a.metadata.getall('genre'), b.metadata.getall('genre')])

    def test_usage(self):
        result = self._run('metadata add f1 genre')
        self.assertIn('usage: metadata add <selector> <tag> <value>...', result.error)


class MetadataRenderTest(_EditTestCase):
    def _render(self, line):
        buf = io.StringIO()
        render_result(self._run(line), CliOutput(stdout=buf, stderr=buf, color=False))
        return buf.getvalue()

    def test_the_console_says_which_tag_was_changed_or_removed(self):
        _file(self.wks, 'a.flac', {'title': 'Song', 'comment': 'Hi'})
        self.assertIn('tag=genre', self._render('metadata set f1 genre Rock'))
        self.assertIn('removed=comment', self._render('metadata rm f1 comment'))


class MetadataRmValueTest(_EditTestCase):
    def test_the_values_given_are_taken_out_in_the_order_of_the_others(self):
        file = _file(self.wks, 'a.flac', {'genre': ['Rock', 'Pop', 'Jazz', 'Folk']})
        result = self._run('metadata rm-value f1 genre Pop Folk')
        self.assertTrue(result.ok, result.error)
        self.assertEqual('changed', result.items[0].status)
        self.assertEqual(['Rock', 'Jazz'], file.metadata.getall('genre'))
        self.assertEqual(['Rock', 'Pop', 'Jazz', 'Folk'], file.orig_metadata.getall('genre'))
        self.assertEqual(File.State.CHANGED, file.state)

    def test_a_tag_with_no_value_left_is_removed(self):
        file = _file(self.wks, 'a.flac', {'genre': ['Rock']})
        self._run('metadata rm-value f1 genre Rock')
        self.assertNotIn('genre', file.metadata)
        self.assertIn('genre', file.metadata.deleted_tags)

    def test_a_value_that_is_not_there_changes_nothing(self):
        file = _file(self.wks, 'a.flac', {'genre': ['Rock']})
        result = self._run('metadata rm-value f1 genre Pop')
        self.assertEqual('unchanged', result.items[0].status)
        self.assertEqual(['Rock'], file.metadata.getall('genre'))
        self.assertEqual(File.State.NORMAL, file.state)

    def test_a_value_that_contains_the_joiner_is_one_value(self):
        file = _file(self.wks, 'a.flac', {'genre': ['Rock; Pop', 'Pop']})
        self._run('metadata rm-value f1 genre "Rock; Pop"')
        self.assertEqual(['Pop'], file.metadata.getall('genre'))

    def test_each_file_of_a_cluster_loses_the_values_it_has(self):
        a = _file(self.wks, 'a.flac', {'genre': ['Rock', 'Pop']})
        b = _file(self.wks, 'b.flac', {'genre': ['Pop', 'Jazz']})
        cluster = self._cluster_of(a, b)
        self._run(f'metadata rm-value {self.session.handle_for(cluster)} genre Pop')
        self.assertEqual([['Rock'], ['Jazz']], [a.metadata.getall('genre'), b.metadata.getall('genre')])

    def test_a_value_is_required_and_a_tag_is_a_name(self):
        _file(self.wks, 'a.flac', {'genre': ['Rock']})
        result = self._run('metadata rm-value f1 genre')
        self.assertIn('usage: metadata rm-value <selector> <tag> <value>...', result.error)
        self.assertIn('pattern', self._run('metadata rm-value f1 gen* Rock').error)


class MetadataRmTest(_EditTestCase):
    def test_the_tag_is_removed_and_shows_as_removed(self):
        file = _file(self.wks, 'a.flac', {'title': 'Song', 'comment': 'Hi'})
        result = self._run('metadata rm f1 comment')
        self.assertTrue(result.ok, result.error)
        self.assertEqual(('removed', ['comment']), (result.items[0].status, result.items[0].data['removed']))
        self.assertNotIn('comment', file.metadata)
        self.assertIn('comment', file.metadata.deleted_tags)
        self.assertEqual(File.State.CHANGED, file.state)
        (row,) = self.run_command('metadata show f1 comment').items[0].data['tags']
        self.assertEqual('removed', row['status'])

    def test_a_pattern_removes_all_the_tags_it_matches(self):
        file = _file(self.wks, 'a.flac', {'musicbrainz_albumid': 'x', 'musicbrainz_trackid': 'y', 'title': 'Song'})
        result = self._run('metadata rm f1 musicbrainz_*')
        self.assertEqual(['musicbrainz_albumid', 'musicbrainz_trackid'], sorted(result.items[0].data['removed']))
        self.assertEqual(['Song'], file.metadata.getall('title'))

    def test_the_length_and_the_file_path_cannot_be_removed(self):
        _file(self.wks, 'a.flac', {'title': 'Song'}, length=1000)
        result = self._run('metadata rm f1 ~*')
        self.assertEqual('unchanged', result.items[0].status)
        self.assertIn('no tag removed for: ~*', result.message)

    def test_a_tag_that_is_not_there_is_reported(self):
        _file(self.wks, 'a.flac', {'title': 'Song'})
        result = self._run('metadata rm f1 comment')
        self.assertTrue(result.ok)
        self.assertEqual('unchanged', result.items[0].status)
        self.assertIn('no tag removed for: comment', result.message)

    def test_a_cluster_loses_the_tag_with_its_files(self):
        files = [_file(self.wks, f'{n}.flac', {'comment': 'Hi', 'title': n}) for n in 'ab']
        cluster = self._cluster_of(*files)
        self._run(f'metadata rm {self.session.handle_for(cluster)} comment')
        self.assertTrue(all('comment' not in f.metadata for f in files))

    def test_usage(self):
        for line in ('metadata rm', 'metadata rm f1'):
            with self.subTest(line=line):
                result = self._run(line)
                self.assertFalse(result.ok)
                self.assertIn('usage: metadata rm <selector> <tag>...', result.error)
