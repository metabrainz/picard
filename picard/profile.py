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

from collections import (
    OrderedDict,
    namedtuple,
)

# Imported to trigger inclusion of N_() in builtins
from picard import i18n  # noqa: F401,E402 # pylint: disable=unused-import


SettingDesc = namedtuple('SettingDesc', ('name', 'title'))


class UserProfileGroups():
    """Provides information about the profile groups available for selecting in a user profile,
    and the title and settings that apply to each profile group.
    """
    SETTINGS_GROUPS = OrderedDict()  # Add groups in the order they should be displayed

    # Each item in "settings" is a tuple of the setting key and the display title
    SETTINGS_GROUPS["metadata"] = {
        "title": N_("Metadata"),
        "settings": [
            SettingDesc("va_name", N_("Various Artists name")),
            SettingDesc("nat_name", N_("Non-album tracks name")),
            SettingDesc("translate_artist_names", N_("Translate artist names")),
            SettingDesc("artist_locale", N_("Translation locale")),
            SettingDesc("release_ars", N_("Use release relationships")),
            SettingDesc("track_ars", N_("Use track relationships")),
            SettingDesc("convert_punctuation", N_("Convert Unicode punctuation characters to ASCII")),
            SettingDesc("standardize_artists", N_("Use standardized artist names")),
            SettingDesc("standardize_instruments", N_("Use standardized instrument and vocal credits")),
            SettingDesc("guess_tracknumber_and_title", N_("Guess track number and title from filename if empty")),
        ],
    }

    SETTINGS_GROUPS["tags"] = {
        "title": N_("Tags"),
        "settings": [
            SettingDesc("dont_write_tags", N_("Don't write tags")),
            SettingDesc("preserve_timestamps", N_("Preserve timestamps of tagged files")),
            SettingDesc("clear_existing_tags", N_("Clear existing tags")),
            SettingDesc("preserve_images", N_("Keep embedded images when clearing tags")),
            SettingDesc("remove_id3_from_flac", N_("Remove ID3 tags from FLAC files")),
            SettingDesc("remove_ape_from_mp3", N_("Remove APEv2 tags from MP3 files")),
            SettingDesc("preserved_tags", N_("Preserved tags list")),
            SettingDesc("aac_save_ape", N_("Save APEv2 tags to AAC")),
            SettingDesc("remove_ape_from_aac", N_("Remove APEv2 tags from AAC files")),
            SettingDesc("ac3_save_ape", N_("Save APEv2 tags to AC3")),
            SettingDesc("remove_ape_from_ac3", N_("Remove APEv2tags from AC3 files")),
            SettingDesc("write_id3v1", N_("Write ID3v1 tags")),
            SettingDesc("write_id3v23", N_("Write ID3v2.3 tags")),
            SettingDesc("id3v2_encoding", N_("ID3v2 text encoding")),
            SettingDesc("id3v23_join_with", N_("ID3v2.3 join character")),
            SettingDesc("itunes_compatible_grouping", N_("iTunes compatible grouping and work")),
            SettingDesc("write_wave_riff_info", N_("Write RIFF INFO tags to WAVE files")),
            SettingDesc("remove_wave_riff_info", N_("Remove existing RIFF INFO tags from WAVE files")),
            SettingDesc("wave_riff_info_encoding", N_("RIFF INFO text encoding")),
        ],
    }

    SETTINGS_GROUPS["coverart"] = {
        "title": N_("Cover Art"),
        "settings": [
            SettingDesc("save_images_to_tags", N_("Embed cover images into tags")),
            SettingDesc("embed_only_one_front_image", N_("Embed only a single front image")),
            SettingDesc("save_images_to_files", N_("Save cover images as separate files")),
            SettingDesc("cover_image_filename", N_("File name for images")),
            SettingDesc("save_images_overwrite", N_("Overwrite existing image files")),
            SettingDesc("save_only_one_front_image", N_("Save only a single front image as separate file")),
            SettingDesc("image_type_as_filename", N_("Always use the primary image type as the file name for non-front images")),
            SettingDesc("ca_providers", N_("Cover art providers")),
        ],
    }

    SETTINGS_GROUPS["filenaming"] = {
        "title": N_("File Naming"),
        "settings": [
            SettingDesc("windows_compatibility", N_("Windows compatibility")),
            SettingDesc("ascii_filenames", N_("Replace non-ASCII characters")),
            SettingDesc("rename_files", N_("Rename files")),
            SettingDesc("move_files", N_("Move files")),
            SettingDesc("move_files_to", N_("Destination directory")),
            SettingDesc("move_additional_files", N_("Move additional files")),
            SettingDesc("move_additional_files_pattern", N_("Additional file patterns")),
            SettingDesc("delete_empty_dirs", N_("Delete empty directories")),
            SettingDesc("selected_file_naming_script_id", N_("Selected file naming script")),
        ],
    }

    SETTINGS_GROUPS["scripting"] = {
        "title": N_("Scripting"),
        "settings": [
            SettingDesc("enable_tagger_scripts", N_("Enable tagger scripts")),
            SettingDesc("list_of_scripts", N_("Tagger scripts")),
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
            settings |= set(x.name for x in settings_group["settings"])
        return settings

    @classmethod
    def get_setting_groups_list(cls):
        """Iterable of all setting groups keys.

        Yields:
            str: Key
        """
        yield from cls.SETTINGS_GROUPS
