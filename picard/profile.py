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


SettingDesc = namedtuple('SettingDesc', ('name', 'title', 'fields'))


class UserProfileGroups():
    """Provides information about the profile groups available for selecting in a user profile,
    and the title and settings that apply to each profile group.
    """
    SETTINGS_GROUPS = OrderedDict()  # Add groups in the order they should be displayed

    # Each item in "settings" is a tuple of the setting key, the display title, and a list of the names of the widgets to highlight
    SETTINGS_GROUPS["metadata"] = {
        "title": N_("Metadata"),
        "settings": [
            SettingDesc("va_name", N_("Various Artists name"), ["va_name"]),
            SettingDesc("nat_name", N_("Non-album tracks name"), ["nat_name"]),
            SettingDesc("translate_artist_names", N_("Translate artist names"), ["translate_artist_names"]),
            SettingDesc("artist_locales", N_("Translation locales"), ["selected_locales"]),
            SettingDesc("translate_artist_names_script_exception", N_("Translate artist names exception"), ["translate_artist_names_script_exception"]),
            SettingDesc("script_exceptions", N_("Translation script exceptions"), ["selected_scripts"]),
            SettingDesc("release_ars", N_("Use release relationships"), ["release_ars"]),
            SettingDesc("track_ars", N_("Use track relationships"), ["track_ars"]),
            SettingDesc("convert_punctuation", N_("Convert Unicode punctuation characters to ASCII"), ["convert_punctuation"]),
            SettingDesc("standardize_artists", N_("Use standardized artist names"), ["standardize_artists"]),
            SettingDesc("standardize_instruments", N_("Use standardized instrument and vocal credits"), ["standardize_instruments"]),
            SettingDesc("guess_tracknumber_and_title", N_("Guess track number and title from filename if empty"), ["guess_tracknumber_and_title"]),
        ],
    }

    SETTINGS_GROUPS["tags"] = {
        "title": N_("Tags"),
        "settings": [
            SettingDesc("dont_write_tags", N_("Don't write tags"), ["write_tags"]),
            SettingDesc("preserve_timestamps", N_("Preserve timestamps of tagged files"), ["preserve_timestamps"]),
            SettingDesc("clear_existing_tags", N_("Clear existing tags"), ["clear_existing_tags"]),
            SettingDesc("preserve_images", N_("Keep embedded images when clearing tags"), ["preserve_images"]),
            SettingDesc("remove_id3_from_flac", N_("Remove ID3 tags from FLAC files"), ["remove_id3_from_flac"]),
            SettingDesc("remove_ape_from_mp3", N_("Remove APEv2 tags from MP3 files"), ["remove_ape_from_mp3"]),
            SettingDesc("preserved_tags", N_("Preserved tags list"), ["preserved_tags"]),
            SettingDesc("aac_save_ape", N_("Save APEv2 tags to AAC"), ["aac_save_ape", "aac_no_tags"]),
            SettingDesc("remove_ape_from_aac", N_("Remove APEv2 tags from AAC files"), ["remove_ape_from_aac"]),
            SettingDesc("ac3_save_ape", N_("Save APEv2 tags to AC3"), ["ac3_save_ape", "ac3_no_tags"]),
            SettingDesc("remove_ape_from_ac3", N_("Remove APEv2 tags from AC3 files"), ["remove_ape_from_ac3"]),
            SettingDesc("write_id3v1", N_("Write ID3v1 tags"), ["write_id3v1"]),
            SettingDesc("write_id3v23", N_("Write ID3v2.3 tags"), ["write_id3v23", "write_id3v24"]),
            SettingDesc("id3v2_encoding", N_("ID3v2 text encoding"), ["enc_utf8", "enc_utf16", "enc_iso88591"]),
            SettingDesc("id3v23_join_with", N_("ID3v2.3 join character"), ["id3v23_join_with"]),
            SettingDesc("itunes_compatible_grouping", N_("Save iTunes compatible grouping and work"), ["itunes_compatible_grouping"]),
            SettingDesc("write_wave_riff_info", N_("Write RIFF INFO tags to WAVE files"), ["write_wave_riff_info"]),
            SettingDesc("remove_wave_riff_info", N_("Remove existing RIFF INFO tags from WAVE files"), ["remove_wave_riff_info"]),
            SettingDesc("wave_riff_info_encoding", N_("RIFF INFO text encoding"), ["wave_riff_info_enc_cp1252", "wave_riff_info_enc_utf8"]),
        ],
    }

    SETTINGS_GROUPS["cover"] = {
        "title": N_("Cover Art"),
        "settings": [
            SettingDesc("save_images_to_tags", N_("Embed cover images into tags"), ["save_images_to_tags"]),
            SettingDesc("embed_only_one_front_image", N_("Embed only a single front image"), ["cb_embed_front_only"]),
            SettingDesc("save_images_to_files", N_("Save cover images as separate files"), ["save_images_to_files"]),
            SettingDesc("cover_image_filename", N_("File name for images"), ["cover_image_filename"]),
            SettingDesc("save_images_overwrite", N_("Overwrite existing image files"), ["save_images_overwrite"]),
            SettingDesc("save_only_one_front_image", N_("Save only a single front image as separate file"), ["save_only_one_front_image"]),
            SettingDesc("image_type_as_filename", N_("Always use the primary image type as the file name for non-front images"), ["image_type_as_filename"]),
            SettingDesc("ca_providers", N_("Cover art providers"), ["ca_providers_list"]),
        ],
    }

    SETTINGS_GROUPS["filerenaming"] = {
        "title": N_("File Naming"),
        "settings": [
            SettingDesc("windows_compatibility", N_("Windows compatibility"), ["windows_compatibility"]),
            SettingDesc("ascii_filenames", N_("Replace non-ASCII characters"), ["ascii_filenames"]),
            SettingDesc("rename_files", N_("Rename files"), ["rename_files"]),
            SettingDesc("move_files", N_("Move files"), ["move_files"]),
            SettingDesc("move_files_to", N_("Destination directory"), ["move_files_to"]),
            SettingDesc("move_additional_files", N_("Move additional files"), ["move_additional_files"]),
            SettingDesc("move_additional_files_pattern", N_("Additional file patterns"), ["move_additional_files_pattern"]),
            SettingDesc("delete_empty_dirs", N_("Delete empty directories"), ["delete_empty_dirs"]),
            SettingDesc("selected_file_naming_script_id", N_("Selected file naming script"), ["naming_script_selector"]),
        ],
    }

    SETTINGS_GROUPS["scripting"] = {
        "title": N_("Scripting"),
        "settings": [
            SettingDesc("enable_tagger_scripts", N_("Enable tagger scripts"), ["enable_tagger_scripts"]),
            SettingDesc("list_of_scripts", N_("Tagger scripts"), ["script_list"]),
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
