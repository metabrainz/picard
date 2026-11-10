# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
# Copyright (C) 2025 StevilKnevil
# Copyright (C) 2025-2026 Laurent Monin
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


from unittest.mock import Mock

from test.picardtestcase import PicardTestCase

from picard.metadata import Metadata
from picard.tagdiff import (
    TagCounter,
    TagDiff,
    TagStatus,
    build_tag_diff,
)


class TestTagCounter(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.parent = TagDiff()
        self.parent.objects = 3
        self.counter = TagCounter(self.parent)

    def test_add_new_tag(self):
        self.counter.add("artist", ["Artist 1"])
        self.assertEqual(self.counter["artist"], ["Artist 1"])
        self.assertEqual(self.counter.counts["artist"], 1)
        self.assertNotIn("artist", self.counter.different)

    def test_add_same_tag_multiple_times(self):
        self.counter.add("artist", ["Artist 1"])
        self.counter.add("artist", ["Artist 1"])
        self.assertEqual(self.counter["artist"], ["Artist 1"])
        self.assertEqual(self.counter.counts["artist"], 2)
        self.assertNotIn("artist", self.counter.different)

    def test_add_different_tag_value(self):
        self.counter.add("artist", ["Artist 1"])
        self.counter.add("artist", ["Artist 2"])
        self.assertEqual(self.counter["artist"], [""])
        self.assertEqual(self.counter.counts["artist"], 2)
        self.assertIn("artist", self.counter.different)

    def test_get_missing_tag(self):
        self.assertEqual(self.counter["missing"], [""])

    def test_status_different(self):
        self.parent.objects = 2
        self.counter.add("artist", ["Artist 1"])
        self.counter.add("artist", ["Artist 2"])
        status = self.counter.status("artist")
        self.assertEqual(status.count, 2)
        self.assertTrue(status.is_different)
        self.assertEqual(status.missing, 0)
        self.assertTrue(status.is_grouped)

    def test_status_same(self):
        self.parent.objects = 2
        self.counter.add("artist", ["Artist 1"])
        self.counter.add("artist", ["Artist 1"])
        status = self.counter.status("artist")
        self.assertEqual(status.count, 2)
        self.assertFalse(status.is_different)
        self.assertEqual(status.missing, 0)
        self.assertFalse(status.is_grouped)

    def test_status_missing_and_different(self):
        self.parent.objects = 3
        self.counter.add("artist", ["Artist 1"])
        self.counter.add("artist", ["Artist 2"])
        status = self.counter.status("artist")
        self.assertEqual(status.count, 2)
        self.assertTrue(status.is_different)
        self.assertEqual(status.missing, 1)
        self.assertTrue(status.is_grouped)

    def test_display_value_different(self):
        self.counter.add("artist", ["Artist 1"])
        self.counter.add("artist", ["Artist 2"])
        display_value = self.counter.display_value("artist")
        self.assertEqual(display_value.text, "(different across 2 items)")
        self.assertTrue(display_value.is_grouped)

    def test_display_value_same(self):
        self.counter.add("artist", ["Artist 1"])
        self.counter.add("artist", ["Artist 1"])
        display_value = self.counter.display_value("artist")
        self.assertEqual(display_value.text, "Artist 1 (missing from 1 item)")
        self.assertTrue(display_value.is_grouped)

    def test_display_value_missing(self):
        self.counter.add("artist", ["Artist 1"])
        display_value = self.counter.display_value("artist")
        self.assertEqual(display_value.text, "Artist 1 (missing from 2 items)")
        self.assertTrue(display_value.is_grouped)

    def test_display_value_length(self):
        self.counter.add("~length", 60000)
        display_value = self.counter.display_value("~length")
        self.assertEqual(display_value.text, "1:00 (missing from 2 items)")
        self.assertTrue(display_value.is_grouped)

    def test_display_value_length_missing(self):
        self.counter.add("~length", "60000")
        self.parent.objects = 5
        display_value = self.counter.display_value("~length")
        self.assertEqual(display_value.text, "1:00 (missing from 4 items)")
        self.assertTrue(display_value.is_grouped)

    def test_display_value_nothing(self):
        self.counter.add("artist", ["Artist 1"])
        self.parent.objects = 0
        display_value = self.counter.display_value("artist")
        self.assertEqual(display_value.text, "Artist 1")
        self.assertFalse(display_value.is_grouped)


class TestTagDiff(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.tag_diff = TagDiff()
        self.tag_diff.objects = 3

    def test_add_new_tag(self):
        self.tag_diff.add("artist", new=["Artist 1"])
        self.assertEqual(self.tag_diff.tag_status("artist"), TagStatus.ADDED)
        self.assertEqual(self.tag_diff.new["artist"], ["Artist 1"])
        self.assertIsNone(self.tag_diff.old.get("artist"))

    def test_add_removed_tag(self):
        self.tag_diff.add("artist", old=["Artist 1"])
        self.assertEqual(self.tag_diff.tag_status("artist"), TagStatus.REMOVED)
        self.assertEqual(self.tag_diff.old["artist"], ["Artist 1"])
        self.assertIsNone(self.tag_diff.new.get("artist"))

    def test_add_removed_removed_tag(self):
        self.tag_diff.add("artist", old=["Artist 1"], removed=True)
        self.assertEqual(self.tag_diff.tag_status("artist"), TagStatus.REMOVED)
        self.assertEqual(self.tag_diff.old["artist"], ["Artist 1"])
        self.assertIsNone(self.tag_diff.new.get("artist"))

    def test_add_changed_tag(self):
        self.tag_diff.add("artist", old=["Artist 1"], new=["Artist 2"])
        self.assertEqual(self.tag_diff.tag_status("artist"), TagStatus.CHANGED)
        self.assertEqual(self.tag_diff.old["artist"], ["Artist 1"])
        self.assertEqual(self.tag_diff.new["artist"], ["Artist 2"])

    def test_add_changed_tag_multistep(self):
        self.tag_diff.add("artist", old=["Artist 1"])
        self.tag_diff.add("artist", new=["Artist 2"])
        self.assertEqual(self.tag_diff.tag_status("artist"), TagStatus.CHANGED)
        self.assertEqual(self.tag_diff.old["artist"], ["Artist 1"])
        self.assertEqual(self.tag_diff.new["artist"], ["Artist 2"])

    def test_add_changed_tag_multistep_reversed(self):
        self.tag_diff.add("artist", new=["Artist 2"])
        self.tag_diff.add("artist", old=["Artist 1"])
        self.assertEqual(self.tag_diff.tag_status("artist"), TagStatus.CHANGED)
        self.assertEqual(self.tag_diff.old["artist"], ["Artist 1"])
        self.assertEqual(self.tag_diff.new["artist"], ["Artist 2"])

    def test_add_nochange_tag(self):
        self.tag_diff.add("artist", old=["Artist 1"], new=["Artist 1"])
        self.assertEqual(self.tag_diff.tag_status("artist"), TagStatus.UNCHANGED)
        self.assertEqual(self.tag_diff.old["artist"], ["Artist 1"])
        self.assertEqual(self.tag_diff.new["artist"], ["Artist 1"])

    def test_add_nochange_no_values(self):
        self.tag_diff.add("artist")
        self.assertEqual(self.tag_diff.tag_status("artist"), TagStatus.EMPTY)

    def test_add_nochange_no_values_top(self):
        self.tag_diff.add("artist", top_tags={"artist"})
        self.assertEqual(self.tag_diff.tag_status("artist"), TagStatus.UNCHANGED)

    def test_add_length_changed_2s(self):
        self.tag_diff = TagDiff(max_length_diff=2)
        self.tag_diff.objects = 3
        self.tag_diff.add("~length", old="10000", new="15000")
        self.assertEqual(self.tag_diff.tag_status("~length"), TagStatus.CHANGED)
        self.assertEqual(self.tag_diff.old["~length"], "10000")
        self.assertEqual(self.tag_diff.new["~length"], "15000")

    def test_add_length_no_changed_2s(self):
        self.tag_diff = TagDiff(max_length_diff=2)
        self.tag_diff.objects = 3
        self.tag_diff.add("~length", old="10000", new="12000")
        self.assertEqual(self.tag_diff.tag_status("~length"), TagStatus.UNCHANGED)
        self.assertEqual(self.tag_diff.old["~length"], "10000")
        self.assertEqual(self.tag_diff.new["~length"], "12000")

    def test_add_length_no_changed_1s(self):
        self.tag_diff = TagDiff(max_length_diff=1)
        self.tag_diff.objects = 3
        self.tag_diff.add("~length", old="10000", new="12000")
        self.assertEqual(self.tag_diff.tag_status("~length"), TagStatus.CHANGED)
        self.assertEqual(self.tag_diff.old["~length"], "10000")
        self.assertEqual(self.tag_diff.new["~length"], "12000")

    def test_is_readonly(self):
        self.tag_diff.add("artist", old=["Artist 1"], new=["Artist 2"], readonly=True)
        self.assertTrue(self.tag_diff.is_readonly("artist"))
        self.assertFalse(self.tag_diff.is_readonly("unknown"))

    def test_add_not_removable(self):
        self.tag_diff.add("artist", old=["Artist 1"], new=["Artist 2"], removable=False)
        self.assertEqual(self.tag_diff.status["artist"], TagStatus.CHANGED | TagStatus.NOTREMOVABLE)

    def test_update_tag_names(self):
        self.tag_diff.add("title", old=["Title 1"], new=["Title 2"])
        self.tag_diff.add("artist", new=["Artist 2"])
        self.tag_diff.add("album", old=["Album 1"])
        self.tag_diff.update_tag_names()
        self.assertEqual(self.tag_diff.tag_names, ["album", "artist", "title"])

    def test_update_tag_names_top_tags(self):
        self.tag_diff.add("title", old=["Title 1"], new=["Title 2"])
        self.tag_diff.add("artist", new=["Artist 2"])
        self.tag_diff.add("album", old=["Album 1"])
        self.tag_diff.update_tag_names(top_tags={"title"})
        self.assertEqual(self.tag_diff.tag_names, ["title", "album", "artist"])

    def test_update_tag_names_changes_first(self):
        self.tag_diff.add("title", old=["Title 1"], new=["Title 2"])
        self.tag_diff.add("artist", old=["Artist 2"])
        self.tag_diff.add("album", old=["Album 1"])
        self.tag_diff.update_tag_names(changes_first=True)
        self.assertEqual(self.tag_diff.tag_names, ["title", "album", "artist"])

    def test_update_tag_names_top_tags_changed(self):
        self.tag_diff.add("title", old=["Title 1"], new=["Title 2"])
        self.tag_diff.add("artist", new=["Artist 2"])
        self.tag_diff.add("album", old=["Album 1"])
        self.tag_diff.update_tag_names(changes_first=True, top_tags={"title"})
        self.assertEqual(self.tag_diff.tag_names, ["title", "artist", "album"])

    @staticmethod
    def _special_handler(old, new):
        for old_value, new_value in zip(old, new, strict=True):
            try:
                if abs(int(old_value) - int(new_value)) > 2000:
                    return True
            except (ValueError, TypeError):
                return True
        return False

    def test_special_handler_changed(self):
        self.tag_diff = TagDiff()
        self.tag_diff.objects = 2

        self.tag_diff.tag_ne_handlers['~length_list'] = self._special_handler
        self.tag_diff.add("~length_list", old=["10000", "12000"], new=["11000", "14500"])
        self.assertEqual(self.tag_diff.tag_status("~length_list"), TagStatus.CHANGED)

    def test_special_handler_unchanged(self):
        self.tag_diff = TagDiff()
        self.tag_diff.objects = 2

        self.tag_diff.tag_ne_handlers['~length_list'] = self._special_handler
        self.tag_diff.add("~length_list", old=["10000", "12000"], new=["11000", "13500"])
        self.assertEqual(self.tag_diff.tag_status("~length_list"), TagStatus.UNCHANGED)

    def test_unchanged_tag_to_json(self):
        self.tag_diff.add("artist", ["Artist 1"])
        self.tag_diff.update_tag_names()
        tags = self.tag_diff.to_json()
        self.assertEqual(tags, '{"artist": {"old": ["Artist 1"]}}')

    def test_new_tag_to_json(self):
        self.tag_diff.add("artist", new=["Artist 1"])
        self.tag_diff.update_tag_names()
        tags = self.tag_diff.to_json()
        self.assertEqual(tags, '{"artist": {"new": ["Artist 1"]}}')

    def test_modified_tag_to_json(self):
        self.tag_diff.add("artist", ["Artist 1"], ["Artist 2"])
        self.tag_diff.update_tag_names()
        tags = self.tag_diff.to_json()
        self.assertEqual(tags, '{"artist": {"old": ["Artist 1"], "new": ["Artist 2"]}}')

    def test_multiple_tags_to_json(self):
        self.tag_diff.add("artist", ["Artist 1"], ["Artist 2"])
        self.tag_diff.add("album", ["Album 1"], ["Album 2"])
        self.tag_diff.update_tag_names()
        tags = self.tag_diff.to_json()
        self.assertEqual(
            tags,
            '{"album": {"old": ["Album 1"], "new": ["Album 2"]}, "artist": {"old": ["Artist 1"], "new": ["Artist 2"]}}',
        )

    def test_unchanged_tag_to_tsv(self):
        self.tag_diff.add("artist", ["Artist 1"])
        self.tag_diff.update_tag_names()
        tags = self.tag_diff.to_tsv()
        self.assertEqual(tags, 'artist\tArtist 1\t\r\n')

    def test_tabbed_tag_to_tsv(self):
        self.tag_diff.add("artist", ["Artist\t1"])
        self.tag_diff.update_tag_names()
        tags = self.tag_diff.to_tsv()
        self.assertEqual(tags, 'artist\t"Artist\t1"\t\r\n')

    def test_newline_tag_to_tsv(self):
        self.tag_diff.add("album", ["Artist\n1"])
        self.tag_diff.add("genre", ["Genre\r\n1"])
        self.tag_diff.update_tag_names()
        tags = self.tag_diff.to_tsv()
        self.assertEqual(tags, 'album\t"Artist\n1"\t\r\ngenre\t"Genre\r\n1"\t\r\n')

    def test_quoted_tag_to_tsv(self):
        self.tag_diff.add("trackname", ['This "track" is cool'])
        self.tag_diff.update_tag_names()
        tags = self.tag_diff.to_tsv()
        self.assertEqual(tags, 'trackname\t"This ""track"" is cool"\t\r\n')

    def test_new_tag_to_tsv(self):
        self.tag_diff.add("artist", new=["Artist 1"])
        self.tag_diff.update_tag_names()
        tags = self.tag_diff.to_tsv()
        self.assertEqual(tags, 'artist\t\tArtist 1\r\n')

    def test_modified_tag_to_tsv(self):
        self.tag_diff.add("artist", ["Artist 1"], ["Artist 2"])
        self.tag_diff.update_tag_names()
        tags = self.tag_diff.to_tsv()
        self.assertEqual(tags, 'artist\tArtist 1\tArtist 2\r\n')

    def test_multiple_tags_to_tsv(self):
        self.tag_diff.add("artist", ["Artist 1"], ["Artist 2"])
        self.tag_diff.add("album", ["Album 1"], ["Album 2"])
        self.tag_diff.update_tag_names()
        tags = self.tag_diff.to_tsv()
        self.assertEqual(tags, 'album\tAlbum 1\tAlbum 2\r\nartist\tArtist 1\tArtist 2\r\n')

    def test_old_length_tag_to_tsv(self):
        self.tag_diff.add("~length", "10000")
        self.tag_diff.update_tag_names()
        tags = self.tag_diff.to_tsv()
        self.assertEqual(tags, '~length\t0:10\t\r\n')

    def test_new_length_tag_to_tsv(self):
        self.tag_diff.add("~length", new="10000")
        self.tag_diff.update_tag_names()
        tags = self.tag_diff.to_tsv()
        self.assertEqual(tags, '~length\t\t0:10\r\n')

    def test_length_tag_to_pretty_tsv(self):
        self.tag_diff.add("~length", "10000", "20000")
        self.tag_diff.update_tag_names()
        tags = self.tag_diff.to_tsv(prettify_times=False)
        self.assertEqual(tags, '~length\t10000\t20000\r\n')

    def test_removed_tag_to_json(self):
        self.tag_diff.add("artist", old=["Artist 1"], removed=True)
        self.tag_diff.update_tag_names()
        tags = self.tag_diff.to_json()
        self.assertEqual(tags, '{"artist": {"old": ["Artist 1"], "removed": true}}')

    def test_removed_tag_no_values_to_json(self):
        self.tag_diff.add("artist", removed=True)
        self.tag_diff.update_tag_names()
        tags = self.tag_diff.to_json()
        self.assertEqual(tags, '{"artist": {"removed": true}}')

    def test_removed_tag_to_tsv(self):
        self.tag_diff.add("artist", old=["Artist 1"], removed=True)
        self.tag_diff.update_tag_names()
        tags = self.tag_diff.to_tsv()
        self.assertEqual(tags, 'artist\tArtist 1\t\r\n')

    def test_removed_tag_no_values_to_tsv(self):
        self.tag_diff.add("artist", removed=True)
        self.tag_diff.update_tag_names()
        tags = self.tag_diff.to_tsv()
        self.assertEqual(tags, 'artist\t\t\r\n')

    def test_removed_tag_included_in_tag_names(self):
        self.tag_diff.add("artist", removed=True)
        self.tag_diff.update_tag_names()
        self.assertIn("artist", self.tag_diff.tag_names)

    def test_removed_tags_tracked(self):
        self.tag_diff.add("artist", old=["Artist 1"], removed=True)
        self.assertIn("artist", self.tag_diff.removed_tags)

    def test_non_removed_tag_not_in_removed_tags(self):
        self.tag_diff.add("artist", old=["Artist 1"])
        self.assertNotIn("artist", self.tag_diff.removed_tags)

    def test_removed_tag_discarded_on_subsequent_non_removed_add(self):
        self.tag_diff.add("artist", old=["Artist 1"], removed=True)
        self.assertIn("artist", self.tag_diff.removed_tags)
        self.tag_diff.add("artist", old=["Artist 1"], new=["Artist 1"])
        self.assertNotIn("artist", self.tag_diff.removed_tags)


def _metadata(length=200000, **tags):
    metadata = Metadata()
    for tag, value in tags.items():
        metadata[tag] = value
    metadata.length = length
    return metadata


def _file(name='/music/song.flac', orig=None, new=None, supports=lambda tag: True):
    """A file loaded with the tags ``orig``, that would be saved with ``new``."""
    file = Mock()
    file.filename = name
    file.orig_metadata = _metadata(**(orig or {}))
    file.metadata = _metadata(**{**(orig or {}), **(new or {})})
    file.supports_tag = supports
    file.format_specific_metadata = lambda metadata, tag, settings: metadata.getall(tag)
    file.make_filename = lambda filename, metadata: '/new/' + metadata['title'] + '.flac'
    return file


def _track(title, linked_files=0, length=180000):
    track = Mock()
    track.num_linked_files = linked_files
    track.metadata = _metadata(length=length, title=title)
    track.orig_metadata = _metadata(length=length, title=title)
    return track


_SETTINGS = {
    'clear_existing_tags': False,
    'rename_files': False,
    'move_files': False,
    'ignore_track_duration_difference_under': 2,
    'metadatabox_top_tags': ['title', 'artist'],
}


class TestBuildTagDiff(PicardTestCase):
    """What the metadata box shows for a selection, without any widget."""

    def _build(self, files=(), tracks=(), changes_first=False, **settings):
        return build_tag_diff(set(files), list(tracks), {**_SETTINGS, **settings}, changes_first=changes_first)

    def test_tags_of_a_file_with_the_top_tags_first_and_the_length(self):
        file = _file(orig={'zebra': 'z', 'artist': 'Band', 'title': 'Song', 'album': 'LP'})
        diff = self._build([file])
        self.assertEqual(
            ['title', 'artist', 'album', '~length', 'zebra'], [t for t in diff.tag_names if t != '~filepath']
        )

    def test_changed_added_and_removed_tags(self):
        file = _file(orig={'title': 'Old', 'genre': 'Rock', 'date': '1999'}, new={'title': 'New', 'album': 'LP'})
        file.metadata.delete('genre')
        diff = self._build([file])
        self.assertEqual(TagStatus.CHANGED, diff.tag_status('title'))
        self.assertEqual(TagStatus.ADDED, diff.tag_status('album'))
        self.assertEqual(TagStatus.REMOVED, diff.tag_status('genre'))
        self.assertEqual(TagStatus.UNCHANGED, diff.tag_status('date'))
        self.assertEqual(['Old'], diff.old['title'])
        self.assertEqual(['New'], diff.new['title'])

    def test_changes_first(self):
        file = _file(orig={'album': 'LP', 'genre': 'Rock', 'title': 'Song'}, new={'genre': 'Jazz'})
        diff = self._build([file], changes_first=True)
        self.assertEqual('genre', diff.tag_names[0])

    def test_a_tag_a_format_cannot_save_is_not_shown(self):
        file = _file(orig={'title': 'Song', 'genre': 'Rock'}, supports=lambda tag: tag != 'genre')
        self.assertNotIn('genre', self._build([file]).tag_names)

    def test_hidden_tags_are_not_shown_except_the_length_and_the_filepath(self):
        file = _file(orig={'title': 'Song', '~bitrate': '320'})
        diff = self._build([file])
        self.assertIn('~length', diff.tag_names)
        self.assertIn('~filepath', diff.tag_names)
        self.assertNotIn('~bitrate', diff.tag_names)

    def test_the_filepath_is_only_shown_for_a_single_file(self):
        files = [_file('/music/a.flac', orig={'title': 'A'}), _file('/music/b.flac', orig={'title': 'B'})]
        self.assertNotIn('~filepath', self._build(files).tag_names)

    def test_the_filepath_preview_follows_the_naming_script_when_files_are_renamed(self):
        file = _file(orig={'title': 'Song'})
        diff = self._build([file], rename_files=True)
        self.assertEqual(['/new/Song.flac'], diff.new['~filepath'])
        self.assertEqual(['/music/song.flac'], diff.old['~filepath'])
        self.assertEqual(['/music/song.flac'], self._build([file]).new['~filepath'])

    def test_a_tag_emptied_in_the_new_metadata_keeps_the_old_value_unless_existing_tags_are_cleared(self):
        file = _file(orig={'genre': 'Rock'})
        file.metadata['genre'] = ''
        file.format_specific_metadata = lambda metadata, tag, settings: [v for v in metadata.getall(tag) if v]
        self.assertEqual(['Rock'], self._build([file]).new['genre'])
        self.assertEqual(TagStatus.REMOVED, self._build([file], clear_existing_tags=True).tag_status('genre'))

    def test_a_track_without_a_file_shows_its_own_tags(self):
        diff = self._build(tracks=[_track('Track')])
        self.assertEqual(['Track'], diff.new['title'])
        self.assertEqual(1, diff.objects)

    def test_a_track_with_a_linked_file_is_left_to_its_file(self):
        diff = self._build(tracks=[_track('Track', linked_files=1)])
        self.assertEqual([], diff.tag_names)

    def test_the_length_tolerance_comes_from_the_settings(self):
        file = _file(orig={'title': 'Song'})
        file.metadata.length = 201500
        self.assertEqual(TagStatus.UNCHANGED, self._build([file]).tag_status('~length'))
        self.assertEqual(
            TagStatus.CHANGED, self._build([file], ignore_track_duration_difference_under=1).tag_status('~length')
        )

    def test_the_number_of_objects_is_the_number_of_files_plus_the_tracks_shown(self):
        diff = self._build([_file(orig={'title': 'A'})], tracks=[_track('T1'), _track('T2', linked_files=2)])
        self.assertEqual(2, diff.objects)
