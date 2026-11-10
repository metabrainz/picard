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


"""``metadata show``: the tags of the entities of the working set, as the metadata box shows them."""

from unittest.mock import MagicMock

from test.cli.engine.helpers import EngineCommandTestCase

from picard.album import Album
from picard.cli.engine.candidates import Candidate
from picard.cli.engine.render import render_result
from picard.cluster import Cluster
from picard.file import File
from picard.track import Track


def _file(wks, name, orig=None, new=None, length=0):
    """A file that was loaded with the tags ``orig`` and would be saved with ``new``."""
    file = File(name)
    for tag, value in (orig or {}).items():
        file.orig_metadata[tag] = value
    for tag, value in {**(orig or {}), **(new or {})}.items():
        file.metadata[tag] = value
    file.orig_metadata.length = file.metadata.length = length
    wks.files[file.filename] = file
    wks.unclustered_files.add_file(file)
    return file


class _MetadataShowTestCase(EngineCommandTestCase):
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

    def _show(self, line):
        self.run_command('ls')  # gives the entities their handles, as a user would see them
        return self.run_command('metadata show ' + line)

    @staticmethod
    def _rows(result, index=0):
        return {row['tag']: row for row in result.items[index].data['tags']}


class MetadataShowFileTest(_MetadataShowTestCase):
    def test_the_tags_of_a_file_in_the_order_of_the_metadata_box(self):
        _file(self.wks, 'a.flac', {'zebra': 'z', 'artist': 'Band', 'title': 'Song', 'album': 'LP', 'date': '1999'})
        result = self._show('f1')
        self.assertTrue(result.ok, result.error)
        # The top tags first, then the others by display name; the length and the file name are tags too.
        self.assertEqual(
            ['title', 'artist', 'album', 'date', '~filepath', '~length', 'zebra'],
            [row['tag'] for row in result.items[0].data['tags']],
        )
        self.assertEqual(
            ('shown', 'file', ['f1']), (result.items[0].status, result.items[0].data['kind'], result.resolved)
        )

    def test_hidden_tags_other_than_the_length_and_the_file_name_are_not_shown(self):
        _file(self.wks, 'a.flac', {'title': 'Song', '~bitrate': '320'})
        self.assertNotIn('~bitrate', self._rows(self._show('f1')))

    def test_a_tag_that_is_not_changed(self):
        _file(self.wks, 'a.flac', {'title': 'Song'})
        self.assertEqual(
            {
                'tag': 'title',
                'orig': 'Song',
                'new': 'Song',
                'status': 'unchanged',
                'orig_values': ['Song'],
                'new_values': ['Song'],
            },
            self._rows(self._show('f1'))['title'],
        )

    def test_values_are_given_as_lists_too(self):
        _file(self.wks, 'a.flac', {'genre': ['Rock', 'Pop']}, {'genre': ['Rock', 'Jazz'], 'album': 'LP'})
        rows = self._rows(self._show('f1'))
        self.assertEqual(
            (['Rock', 'Pop'], ['Rock', 'Jazz']), (rows['genre']['orig_values'], rows['genre']['new_values'])
        )
        # The text joins them, and a tag that is not there has no value.
        self.assertEqual('Rock; Jazz', rows['genre']['new'])
        self.assertEqual(([], ['LP']), (rows['album']['orig_values'], rows['album']['new_values']))

    def test_a_value_with_the_joiner_is_not_two_values(self):
        _file(self.wks, 'a.flac', {'genre': ['Rock; Pop']})
        row = self._rows(self._show('f1'))['genre']
        self.assertEqual('Rock; Pop', row['new'])
        self.assertEqual(['Rock; Pop'], row['new_values'])

    def test_values_that_differ_between_files_are_not_given_as_a_list(self):
        a = _file(self.wks, 'a.flac', {'genre': ['Rock']})
        b = _file(self.wks, 'b.flac', {'genre': ['Pop']})
        cluster = Cluster('Album', 'Artist')
        cluster.add_files([a, b])
        self.wks.clusters.append(cluster)
        row = self._rows(self._show(self.session.handle_for(cluster)))['genre']
        self.assertEqual('(different across 2 items)', row['new'])
        self.assertNotIn('new_values', row)
        self.assertNotIn('orig_values', row)

    def test_changed_added_and_removed_tags(self):
        file = _file(
            self.wks, 'a.flac', {'title': 'Old', 'genre': 'Rock', 'date': '1999'}, {'title': 'New', 'album': 'LP'}
        )
        file.metadata.delete('genre')
        rows = self._rows(self._show('f1'))
        self.assertEqual(
            ('changed', 'Old', 'New'), (rows['title']['status'], rows['title']['orig'], rows['title']['new'])
        )
        self.assertEqual(('added', '', 'LP'), (rows['album']['status'], rows['album']['orig'], rows['album']['new']))
        self.assertEqual('removed', rows['genre']['status'])
        self.assertEqual('unchanged', rows['date']['status'])

    def test_changes_come_first_when_the_box_is_set_to_show_them(self):
        _file(self.wks, 'a.flac', {'album': 'LP', 'genre': 'Rock', 'title': 'Song'}, {'genre': 'Jazz'})
        self.assertEqual('title', self._show('f1').items[0].data['tags'][0]['tag'])
        self.set_config_values(persist={'show_changes_first': True})
        self.assertEqual('genre', self._show('f1').items[0].data['tags'][0]['tag'])

    def test_multi_valued_tags_are_joined_as_in_the_box(self):
        _file(self.wks, 'a.flac', {'artist': ['One', 'Two']})
        self.assertEqual('One; Two', self._rows(self._show('f1'))['artist']['new'])

    def test_the_length_is_shown_as_a_time(self):
        _file(self.wks, 'a.flac', {'title': 'Song'}, length=185000)
        self.assertEqual('3:05', self._rows(self._show('f1'))['~length']['new'])

    def test_the_file_name_it_would_be_saved_with(self):
        file = _file(self.wks, 'a.flac', {'title': 'Song'})
        self.assertEqual(
            ('unchanged', file.filename), tuple(self._rows(self._show('f1'))['~filepath'][k] for k in ('status', 'new'))
        )

    def test_a_format_that_cannot_save_a_tag_does_not_show_it(self):
        file = _file(self.wks, 'a.flac', {'title': 'Song', 'genre': 'Rock'})
        file.supports_tag = lambda tag: tag != 'genre'
        self.assertNotIn('genre', self._rows(self._show('f1')))

    def test_format_specific_values_are_shown(self):
        file = _file(self.wks, 'a.flac', {'date': '1999-05-01'})
        file.format_specific_metadata = lambda metadata, tag, settings=None: [v[:4] for v in metadata.getall(tag)]
        self.assertEqual('1999', self._rows(self._show('f1'))['date']['new'])


class MetadataShowTagsTest(_MetadataShowTestCase):
    def test_one_tag_by_name(self):
        _file(self.wks, 'a.flac', {'title': 'Song', 'artist': 'Band'})
        self.assertEqual(['artist'], list(self._rows(self._show('f1 artist'))))

    def test_several_tags_and_patterns(self):
        _file(
            self.wks,
            'a.flac',
            {'title': 'Song', 'musicbrainz_albumid': 'x', 'musicbrainz_trackid': 'y', 'date': '1999'},
        )
        result = self._show('f1 title musicbrainz_*')
        self.assertEqual({'title', 'musicbrainz_albumid', 'musicbrainz_trackid'}, set(self._rows(result)))

    def test_tags_with_a_colon_in_their_name(self):
        _file(self.wks, 'a.flac', {'performer:guitar': 'Someone', 'comment:lyrics': 'la'})
        self.assertEqual(['performer:guitar'], list(self._rows(self._show('f1 performer:*'))))
        self.assertEqual(['comment:lyrics'], list(self._rows(self._show('f1 comment:lyrics'))))

    def test_the_length_and_the_file_name_can_be_asked_for(self):
        _file(self.wks, 'a.flac', {'title': 'Song'}, length=60000)
        self.assertEqual({'~length', '~filepath'}, set(self._rows(self._show('f1 ~*'))))

    def test_a_tag_the_entity_does_not_have_is_not_shown_and_is_said(self):
        _file(self.wks, 'a.flac', {'title': 'Song'})
        result = self._show('f1 date lyrics*')
        self.assertTrue(result.ok, result.error)
        self.assertEqual([], result.items[0].data['tags'])
        self.assertEqual('no tag matches: date, lyrics*', result.message)

    def test_a_pattern_matching_for_one_entity_only_is_not_reported(self):
        _file(self.wks, 'a.flac', {'title': 'Song'})
        _file(self.wks, 'b.flac', {'date': '1999'})
        result = self._show('f1,f2 date')
        self.assertEqual('', result.message)
        self.assertEqual([[], ['date']], [[row['tag'] for row in item.data['tags']] for item in result.items])

    def test_several_entities_one_item_each(self):
        _file(self.wks, 'a.flac', {'title': 'A'})
        _file(self.wks, 'b.flac', {'title': 'B'})
        result = self._show('f*  title')
        self.assertEqual(['f1', 'f2'], [item.handle for item in result.items])
        self.assertEqual(['A', 'B'], [self._rows(result, i)['title']['new'] for i in range(2)])


class MetadataShowContainersTest(_MetadataShowTestCase):
    """A track, an album or a cluster is shown as the metadata box shows it when it is selected."""

    def setUp(self):
        super().setUp()
        self.album = Album('rel-1')
        self.album.loaded = True
        self.wks.albums['rel-1'] = self.album
        self.tracks = []
        for number, title in enumerate(('One', 'Two'), 1):
            track = Track(f'rec-{number}', self.album)
            track.metadata['title'] = title
            track.orig_metadata['title'] = title
            self.album.tracks.append(track)
            self.tracks.append(track)

    def _link(self, track, name, title):
        file = _file(self.wks, name, {'title': title, 'artist': 'Band'})
        self.wks.unclustered_files.remove_file(file)
        file.move(track)
        return file

    def test_a_track_without_a_file_shows_its_own_tags(self):
        self.run_command('ls')
        handle = self.session.handle_for(self.tracks[0])
        result = self.run_command(f'metadata show {handle} title')
        self.assertEqual(('track', 'One'), (result.items[0].data['kind'], self._rows(result)['title']['new']))

    def test_a_track_with_a_file_shows_the_tags_of_its_file(self):
        # Matching a file to a track gives it the tags of the track: they are what it would be saved with.
        self._link(self.tracks[0], 'one.flac', 'Tagged')
        self.run_command('ls')
        handle = self.session.handle_for(self.tracks[0])
        result = self.run_command(f'metadata show {handle}')
        row = self._rows(result)['title']
        self.assertEqual(('changed', 'Tagged', 'One'), (row['status'], row['orig'], row['new']))
        self.assertIn('~filepath', self._rows(result))

    def test_an_album_shows_the_tags_of_its_tracks_and_their_files_grouped(self):
        self._link(self.tracks[0], 'one.flac', 'One')
        self._link(self.tracks[1], 'two.flac', 'Two')
        result = self._show('a1')
        self.assertEqual('album', result.items[0].data['kind'])
        rows = self._rows(result)
        self.assertEqual('(different across 2 items)', rows['title']['new'])
        self.assertEqual('Band', rows['artist']['new'])

    def test_a_cluster_shows_the_tags_of_its_files(self):
        cluster = Cluster('Cluster', 'Artist')
        self.wks.clusters.append(cluster)
        for name, title in (('a.flac', 'A'), ('b.flac', 'A')):
            file = _file(self.wks, name, {'title': title})
            self.wks.unclustered_files.remove_file(file)
            cluster.add_file(file)
        result = self._show('c1 title')
        self.assertEqual(('cluster', 'A'), (result.items[0].data['kind'], self._rows(result)['title']['new']))

    def test_a_path_reaches_the_files_of_a_container(self):
        cluster = Cluster('Cluster', 'Artist')
        self.wks.clusters.append(cluster)
        file = _file(self.wks, 'a.flac', {'title': 'Song'})
        self.wks.unclustered_files.remove_file(file)
        cluster.add_file(file)
        self.assertEqual('Song', self._rows(self._show('c1.f* title'))['title']['new'])

    def test_an_empty_cluster_has_nothing_to_show(self):
        cluster = Cluster('Cluster', 'Artist')
        self.wks.clusters.append(cluster)
        result = self._show('c1')
        self.assertTrue(result.ok, result.error)
        self.assertEqual([], result.items[0].data['tags'])


class MetadataShowErrorsTest(_MetadataShowTestCase):
    def test_a_selector_is_required(self):
        result = self._show('')
        self.assertFalse(result.ok)
        self.assertIn('usage', result.error)

    def test_unresolved_selector_is_reported(self):
        result = self._show('f9')
        self.assertTrue(result.ok, result.error)
        self.assertEqual((['f9'], []), (result.unresolved, result.items))

    def test_a_lookup_candidate_has_no_tags(self):
        cluster = Cluster('Cluster', 'Artist')
        self.wks.clusters.append(cluster)
        self.session.handle_for(cluster)
        (handle,) = self.session.set_candidates(cluster, [Candidate(MagicMock(release=None, similarity=0.5))])
        result = self._show(handle)
        self.assertFalse(result.ok)
        self.assertIn('is a lookup candidate, it has no tags', result.error)


class MetadataShowRenderTest(_MetadataShowTestCase):
    """What the console prints."""

    def _printed(self, line):
        lines = []
        output = MagicMock()
        output.print.side_effect = lines.append
        output.d_id.side_effect = output.dim.side_effect = output.d_name.side_effect = lambda text: text
        output.d_arrow.return_value = '->'
        self.run_command('ls')
        render_result(self.run_command(line), output)
        return lines

    def test_each_tag_has_a_line_under_the_entity(self):
        file = _file(self.wks, 'a.flac', {'title': 'Old', 'artist': 'Band'}, {'title': 'New', 'album': 'LP'})
        file.metadata.delete('artist')
        lines = self._printed('metadata show f1 title artist album')
        self.assertTrue(lines[0].startswith('f1'))
        self.assertEqual(['    title   Old -> New', '    artist  - Band', '    album   + LP'], lines[1:4])

    def test_values_of_a_tag_are_joined(self):
        _file(self.wks, 'a.flac', {'artist': ['One', 'Two']})
        self.assertIn('    artist  One; Two', self._printed('metadata show f1 artist'))
