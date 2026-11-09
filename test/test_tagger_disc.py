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

from unittest.mock import (
    MagicMock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.metadata import Metadata
from picard.tagger import Tagger


class TaggerLookupCdTest(PicardTestCase):
    """Tagger.lookup_cd: which drive is read."""

    def _lookup(self, setting, device=None):
        self.set_config_values({'cd_lookup_device': setting})
        tagger = MagicMock(spec=Tagger)
        Tagger.lookup_cd(tagger, device)
        tagger.run_lookup_cd.assert_called_once()
        return tagger.run_lookup_cd.call_args.args[0]

    def test_chosen_drive_is_used(self):
        self.assertEqual(self._lookup('/dev/sr0,/dev/sr1', device='/dev/sr1'), '/dev/sr1')

    def test_first_configured_drive_by_default(self):
        self.assertEqual(self._lookup('/dev/sr0,/dev/sr1'), '/dev/sr0')

    def test_spaces_around_the_configured_drive_are_dropped(self):
        self.assertEqual(self._lookup(' /dev/sr0 , /dev/sr1'), '/dev/sr0')

    def test_empty_items_are_skipped(self):
        self.assertEqual(self._lookup(', /dev/sr1'), '/dev/sr1')

    def test_no_configured_drive_lets_discid_detect_one(self):
        self.assertIsNone(self._lookup(''))


class TaggerLookupDiscidFromTagsTest(PicardTestCase):
    """Tagger.lookup_discid_from_tags: what the user sees and what is looked up."""

    TAG = '5023F08C+100000+4+150+30000+50000+90000'

    def setUp(self):
        super().setUp()
        self.tagger = MagicMock(spec=Tagger)
        self.tagger.window = MagicMock()
        for name in ('Disc', 'busy_cursor_start', 'QtWidgets'):
            patcher = patch(f'picard.tagger.{name}')
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)

    @staticmethod
    def _files(*tags):
        files = []
        for tag in tags:
            metadata = Metadata()
            if tag:
                metadata['itunes_cddb_1'] = tag
            files.append(MagicMock(metadata=metadata))
        return files

    def _lookup(self, files):
        Tagger.lookup_discid_from_tags(self.tagger, files)

    def _assert_warned(self, message):
        self.tagger.window.set_statusbar_message.assert_called_once_with(message)
        self.QtWidgets.QMessageBox.warning.assert_called_once()
        self.assertEqual(self.QtWidgets.QMessageBox.warning.call_args.args[2], message)
        self.Disc.assert_not_called()

    def test_looks_up_the_toc_built_from_the_tags(self):
        files = self._files(*[self.TAG] * 4)
        self._lookup(files)
        self.busy_cursor_start.assert_called_once_with()
        self.Disc.return_value.lookup_by_toc.assert_called_once_with(
            '1+4+100000+150+30000+50000+90000', skip_dialog=True, files_to_match=files
        )

    def test_files_without_the_tag_are_ignored_for_the_tag_but_count_as_tracks(self):
        files = self._files(self.TAG, self.TAG, None, self.TAG)
        self._lookup(files)
        self.Disc.return_value.lookup_by_toc.assert_called_once()

    def test_no_tag_warns(self):
        self._lookup(self._files(None, None))
        self._assert_warned('Disc information could not be found')

    def test_conflicting_tags_warn(self):
        other = '5023F08C+100000+4+150+30000+50000+90001'
        self._lookup(self._files(self.TAG, other, self.TAG, self.TAG))
        self._assert_warned('Selected files contain tags with conflicting disc information')

    def test_unparsable_tag_is_only_reported_in_the_status_bar(self):
        self._lookup(self._files('garbage', 'garbage'))
        self.tagger.window.set_statusbar_message.assert_called_once()
        self.assertIn(
            'Failed to parse disc information from tags', self.tagger.window.set_statusbar_message.call_args.args[0]
        )
        self.QtWidgets.QMessageBox.warning.assert_not_called()
        self.Disc.assert_not_called()

    def test_track_count_not_matching_the_files_is_only_reported_in_the_status_bar(self):
        self._lookup(self._files(self.TAG, self.TAG))
        message = self.tagger.window.set_statusbar_message.call_args.args[0]
        self.assertIn('Number of tracks (4) does not match number of selected files (2)', message)
        self.QtWidgets.QMessageBox.warning.assert_not_called()
        self.Disc.assert_not_called()


class TaggerRunLookupTest(PicardTestCase):
    """Reading a disc and looking it up: the busy cursor and the error dialog."""

    def setUp(self):
        super().setUp()
        self.tagger = MagicMock(spec=Tagger)
        self.tagger.window = MagicMock()
        for name in ('Disc', 'busy_cursor_start', 'busy_cursor_stop', 'QtWidgets'):
            patcher = patch(f'picard.tagger.{name}')
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)
        self.disc = self.Disc.return_value

    def test_cd_is_read_from_the_drive_then_looked_up(self):
        Tagger.run_lookup_cd(self.tagger, '/dev/sr0')
        self.busy_cursor_start.assert_called_once_with()
        self.disc.read_and_lookup.assert_called_once()
        (read,) = self.disc.read_and_lookup.call_args.args
        read()
        self.disc.read.assert_called_once_with('/dev/sr0')

    def test_ripper_log_is_read_then_looked_up(self):
        Tagger.run_lookup_discid_from_logfile(self.tagger, '/rips/album.log')
        self.busy_cursor_start.assert_called_once_with()
        (read,) = self.disc.read_and_lookup.call_args.args
        read()
        self.disc.read_log.assert_called_once_with('/rips/album.log')

    def test_read_error_is_reported_with_the_cursor_restored(self):
        Tagger.run_lookup_cd(self.tagger, None)
        on_error = self.disc.read_and_lookup.call_args.kwargs['on_error']
        self.assertEqual(on_error, self.tagger._disc_read_failed)
        Tagger._disc_read_failed(self.tagger, OSError('no disc'))
        self.busy_cursor_stop.assert_called_once_with()
        self.QtWidgets.QMessageBox.critical.assert_called_once()
        self.assertIn('no disc', self.QtWidgets.QMessageBox.critical.call_args.args[2])
