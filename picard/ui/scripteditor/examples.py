# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021-2023 Bob Swift
# Copyright (C) 2021-2025 Laurent Monin
# Copyright (C) 2021-2024 Philipp Wolfer
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

import os.path
import random

from picard.config import get_config
from picard.file import File
from picard.i18n import gettext as _
from picard.metadata import Metadata
from picard.script import (
    ScriptError,
    ScriptParser,
    get_file_naming_script,
    iter_tagging_scripts_from_tuples,
)
from picard.util import iter_files_from_objects
from picard.util.filenaming import WinPathTooLong
from picard.util.settingsoverride import SettingsOverride


class ScriptEditorExamples:
    """File naming script examples."""

    max_samples = 10  # pick up to 10 samples

    def __init__(self, tagger):
        """File naming script examples.

        Args:
            tagger (object): The main window tagger object.
        """
        self.tagger = tagger
        self._sampled_example_files = []
        config = get_config()
        self.settings = config.setting
        self.example_list = []
        self.script_text = get_file_naming_script(self.settings)

    def _get_samples(self, candidates):
        candidates = tuple(candidates)
        length = min(self.max_samples, len(candidates))
        return random.sample(candidates, k=length)

    def update_sample_example_files(self):
        """Get a new sample of randomly selected / loaded files to use as renaming examples."""
        if self.tagger.window.selected_objects:
            # If files/albums/tracks are selected, sample example files from them
            candidates = iter_files_from_objects(self.tagger.window.selected_objects)
        else:
            # If files/albums/tracks are not selected, sample example files from the pool of loaded files
            candidates = self.tagger.files.values()

        files = self._get_samples(candidates)
        self._sampled_example_files = files or list(self.default_examples())
        self.update_examples()

    def update_examples(self, override=None, script_text=None):
        """Update the before and after file naming examples list.

        Args:
            override (dict, optional): Dictionary of settings overrides to apply. Defaults to None.
            script_text (str, optional): Text of the file naming script to use. Defaults to None.
        """
        if override and isinstance(override, dict):
            config = get_config()
            self.settings = SettingsOverride(config.setting, override)
        if script_text and isinstance(script_text, str):
            self.script_text = script_text

        if self.settings['move_files'] or self.settings['rename_files']:
            if not self._sampled_example_files:
                self.update_sample_example_files()
            self.example_list = [self._example_to_filename(example) for example in self._sampled_example_files]
        else:
            err_text = _("Renaming options are disabled")
            self.example_list = [[err_text, err_text]]

    def _example_to_filename(self, file):
        """Produce the before and after file naming example tuple for the specified file.

        Args:
            file (File): File to produce example before and after names

        Returns:
            tuple: Example before and after names for the specified file
        """
        # Operate on a copy of the file object metadata to avoid multiple changes to file metadata.  See PICARD-2508.
        c_metadata = Metadata()
        c_metadata.copy(file.metadata)
        try:
            # Only apply scripts if the original file metadata has not been changed.
            if self.settings['enable_tagger_scripts'] and not c_metadata.diff(file.orig_metadata):
                for s in iter_tagging_scripts_from_tuples(self.settings['list_of_scripts']):
                    if s.enabled and s.content:
                        parser = ScriptParser()
                        parser.eval(s.content, c_metadata)
            filename_before = file.filename
            filename_after = file.make_filename(filename_before, c_metadata, self.settings, self.script_text)
            if not self.settings['move_files']:
                return os.path.basename(filename_before), os.path.basename(filename_after)
            return filename_before, filename_after
        except (FileNotFoundError, PermissionError, ScriptError, TypeError, WinPathTooLong):
            return "", ""

    def update_example_listboxes(self, before_listbox, after_listbox):
        """Update the contents of the file naming examples before and after listboxes.

        Args:
            before_listbox (QListBox): The before listbox
            after_listbox (QListBox): The after listbox
        """
        before_listbox.clear()
        after_listbox.clear()
        for before, after in sorted(self.get_examples(), key=lambda x: x[1]):
            before_listbox.addItem(before)
            after_listbox.addItem(after)

    def get_examples(self):
        """Get the list of examples.

        Returns:
            [list]: List of the before and after file name example tuples
        """
        return self.example_list

    @staticmethod
    def synchronize_selected_example_lines(current_row, source, target):
        """Sets the current row in the target to match the current row in the source.

        Args:
            current_row (int): Currently selected row
            source (QListView): Source list
            target (QListView): Target list
        """
        if source.currentRow() != current_row:
            current_row = source.currentRow()
            target.blockSignals(True)
            target.setCurrentRow(current_row)
            target.blockSignals(False)

    @classmethod
    def get_notes_text(cls):
        """Provides usage notes text suitable for display on the dialog.

        Returns:
            str: Notes text
        """
        return (
            _(
                "If you select files from the Cluster pane or Album pane prior to opening the Options screen, "
                "up to %u files will be randomly chosen from your selection as file naming examples.  If you "
                "have not selected any files, then some default examples will be provided."
            )
            % cls.max_samples
        )

    @classmethod
    def get_tooltip_text(cls):
        """Provides tooltip text suitable for display on the dialog.

        Returns:
            str: Tooltip text
        """
        return _("Reload up to %u items chosen at random from files selected in the main window") % cls.max_samples

    @staticmethod
    def default_examples():
        """Generator for default example files.

        Yields:
            File: the next example File object
        """
        # example 1
        efile = File("ticket_to_ride.mp3")
        efile.state = File.State.NORMAL
        efile.metadata.update(
            {
                'album': 'Help!',
                'title': 'Ticket to Ride',
                '~releasecomment': '2014 mono remaster',
                'artist': 'The Beatles',
                'artistsort': 'Beatles, The',
                'albumartist': 'The Beatles',
                'albumartistsort': 'Beatles, The',
                'tracknumber': '7',
                'totaltracks': '14',
                'discnumber': '1',
                'totaldiscs': '1',
                'originaldate': '1965-08-06',
                'originalyear': '1965',
                'date': '2014-09-08',
                'releasetype': ['album', 'soundtrack'],
                '~primaryreleasetype': ['album'],
                '~secondaryreleasetype': ['soundtrack'],
                'releasestatus': 'official',
                'releasecountry': 'US',
                'barcode': '602537825745',
                'catalognumber': 'PMC 1255',
                'genre': 'Rock',
                'isrc': 'GBAYE0900666',
                'label': 'Parlophone',
                'language': 'eng',
                'media': '12″ Vinyl',
                'script': 'Latn',
                'engineer': ['Ken Scott', 'Norman Smith'],
                'producer': 'George Martin',
                'writer': ['John Lennon', 'Paul McCartney'],
                '~bitrate': '192.0',
                '~channels': '2',
                '~extension': 'mp3',
                '~filename': 'ticket_to_ride',
                '~filesize': '3563068',
                '~format': 'MPEG-1 Layer 3 - ID3v2.4',
                '~length': '3:13',
                '~sample_rate': '44100',
                'musicbrainz_albumid': 'd7fbbb0a-1348-40ad-8eef-cd438d4cd203',
                'musicbrainz_albumartistid': 'b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d',
                'musicbrainz_artistid': 'b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d',
                'musicbrainz_recordingid': 'ed052ae1-c950-47f2-8d2b-46e1b58ab76c',
                'musicbrainz_trackid': '392639f5-5629-477e-b04b-93bffa703405',
                'musicbrainz_releasegroupid': '0d44e1cb-c6e0-3453-8b68-4d2082f05421',
            }
        )
        yield efile

        # example 2
        config = get_config()
        efile = File("track05.flac")
        efile.state = File.State.NORMAL
        efile.metadata.update(
            {
                'album': "Coup d'État, Volume 1: Ku De Ta / Prologue",
                'title': "I've Got to Learn the Mambo",
                'artist': "Snowboy feat. James Hunter",
                'artistsort': "Snowboy feat. Hunter, James",
                'albumartist': config.setting['va_name'],
                'albumartistsort': config.setting['va_name'],
                'tracknumber': '5',
                'totaltracks': '13',
                'discnumber': '2',
                'totaldiscs': '2',
                'discsubtitle': "Beat Up",
                'originaldate': '2005-07-04',
                'originalyear': '2005',
                'date': '2005-07-04',
                'releasetype': ['album', 'compilation'],
                '~primaryreleasetype': 'album',
                '~secondaryreleasetype': 'compilation',
                'releasestatus': 'official',
                'releasecountry': 'AU',
                'barcode': '5021456128754',
                'catalognumber': 'FM001',
                'label': 'Filter Music',
                'media': 'CD',
                'script': 'Latn',
                'compilation': '1',
                '~multiartist': '1',
                '~bitrate': '1609.038',
                '~channels': '2',
                '~extension': 'flac',
                '~filename': 'track05',
                '~filesize': '9237672',
                '~format': 'FLAC',
                '~sample_rate': '44100',
                'musicbrainz_albumid': '4b50c71e-0a07-46ac-82e4-cb85dc0c9bdd',
                'musicbrainz_recordingid': 'b3c487cb-0e55-477d-8df3-01ec6590f099',
                'musicbrainz_trackid': 'f8649a05-da39-39ba-957c-7abf8f9012be',
                'musicbrainz_albumartistid': '89ad4ac3-39f7-470e-963a-56509c546377',
                'musicbrainz_artistid': [
                    '7b593455-d207-482c-8c6f-19ce22c94679',
                    '9e082466-2390-40d1-891e-4803531f43fd',
                ],
                'musicbrainz_releasegroupid': 'fa90225d-1810-347c-ae5f-f051a760b623',
            }
        )
        yield efile
