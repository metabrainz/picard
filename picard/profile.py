# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Bob Swift
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

from collections import OrderedDict

# Imported to trigger inclusion of N_() in builtins
from picard import i18n  # noqa: F401,E402 # pylint: disable=unused-import


class UserProfileGroups():
    """Provides information about the profile groups available for selecting in a user profile,
    and the title and settings that apply to each profile group.
    """
    SETTINGS_GROUPS = OrderedDict()  # Add groups in the order they should be displayed

    # Each item in "settings" is a tuple of the setting key and the display title
    SETTINGS_GROUPS["metadata"] = {
        "title": N_("Metadata"),
        "settings": [
            ("va_name", N_("Various Artists name")),
            ("nat_name", N_("Non-album tracks name")),
            ("translate_artist_names", N_("Translate artist names")),
            ("artist_locale", N_("Translation locale")),
            ("release_ars", N_("Use release relationships")),
            ("track_ars", N_("Use track relationships")),
            ("convert_punctuation", N_("Convert Unicode to ASCII")),
            ("standardize_artists", N_("Standardize artist names")),
            ("standardize_instruments", N_("Standardize instrument names")),
            ("guess_tracknumber_and_title", N_("Guess track number and title")),
        ],
    }

    SETTINGS_GROUPS["tags"] = {
        "title": N_("Tags"),
        "settings": [
            ("dont_write_tags", N_("Don't write tags")),
            ("preserve_timestamps", N_("Preserve timestamps")),
            ("clear_existing_tags", N_("Clear existing tags")),
            ("preserve_images", N_("Preserve images")),
            ("remove_id3_from_flac", N_("Remove ID3 from FLAC")),
            ("remove_ape_from_mp3", N_("Remove APE from MP3")),
            ("preserved_tags", N_("Preserved tags list")),
            ("aac_save_ape", N_("Save APEv2 to AAC")),
            ("remove_ape_from_aac", N_("Remove APE from AAC")),
            ("ac3_save_ape", N_("Save APEv2 to AC3")),
            ("remove_ape_from_ac3", N_("Remove APE from AC3")),
            ("write_id3v1", N_("Write ID3v1 tags")),
            ("write_id3v23", N_("Write ID3v2.3 tags")),
            ("id3v2_encoding", N_("ID3v2.3 Text Encoding")),
            ("id3v23_join_with", N_("ID3v2.3 join character")),
            ("itunes_compatible_grouping", N_("iTunes compatible grouping")),
            ("write_wave_riff_info", N_("Write WAVE RIFF info")),
            ("remove_wave_riff_info", N_("Remove WAVE RIFF info")),
            ("wave_riff_info_encoding", N_("RIFF text encoding")),
        ],
    }

    SETTINGS_GROUPS["coverart"] = {
        "title": N_("Cover Art"),
        "settings": [
            ("save_images_to_tags", N_("Save images to tags")),
            ("embed_only_one_front_image", N_("Embed only one front image")),
            ("save_images_to_files", N_("Save images to files")),
            ("cover_image_filename", N_("File name for images")),
            ("save_images_overwrite", N_("Overwrite existing image files")),
            ("save_only_one_front_image", N_("Save only one front image")),
            ("image_type_as_filename", N_("Image type as file name")),
            ("ca_providers", N_("Cover art providers")),
        ],
    }

    SETTINGS_GROUPS["filenaming"] = {
        "title": N_("File Naming"),
        "settings": [
            ("windows_compatibility", N_("Windows compatibility")),
            ("ascii_filenames", N_("Replace non-ASCII characters")),
            ("rename_files", N_("Rename files")),
            ("move_files", N_("Move files")),
            ("move_files_to", N_("Destination directory")),
            ("move_additional_files", N_("Move additional files")),
            ("move_additional_files_pattern", N_("Additional file patterns")),
            ("delete_empty_dirs", N_("Delete empty directories")),
            ("selected_file_naming_script_id", N_("Selected file naming script")),
        ],
    }

    SETTINGS_GROUPS["scripting"] = {
        "title": N_("Scripting"),
        "settings": [
            ("enable_tagger_scripts", N_("Enable tagger scripts")),
            ("list_of_scripts", N_("Tagger scripts")),
        ],
    }

    @classmethod
    def get_all_settings_list(cls):
        """Iterable of all settings names in all setting groups.

        Yields:
            str: Setting name
        """
        settings = set()
        for settings_group in cls.SETTINGS_GROUPS.values():
            settings |= set(x[0] for x in settings_group["settings"])
        return settings

    @classmethod
    def get_setting_groups_list(cls):
        """Iterable of all setting groups keys.

        Yields:
            str: Key
        """
        yield from cls.SETTINGS_GROUPS
