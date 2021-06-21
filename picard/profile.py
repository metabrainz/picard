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

    SETTINGS_GROUPS["metadata"] = {
        "title": N_("Metadata"),
        "settings": [
            "va_name",
            "nat_name",
            "artist_locale",
            "translate_artist_names",
            "release_ars",
            "track_ars",
            "convert_punctuation",
            "standardize_artists",
            "standardize_instruments",
            "guess_tracknumber_and_title",
        ],
    }

    SETTINGS_GROUPS["tags"] = {
        "title": N_("Tags"),
        "settings": [
            "dont_write_tags",
            "preserve_timestamps",
            "clear_existing_tags",
            "preserve_images",
            "remove_id3_from_flac",
            "remove_ape_from_mp3",
            "preserved_tags",
            "aac_save_ape",
            "remove_ape_from_aac",
            "ac3_save_ape",
            "remove_ape_from_ac3",
            "write_id3v1",
            "write_id3v23",
            "id3v2_encoding",
            "id3v23_join_with",
            "itunes_compatible_grouping",
            "write_wave_riff_info",
            "remove_wave_riff_info",
            "wave_riff_info_encoding",
        ],
    }

    SETTINGS_GROUPS["coverart"] = {
        "title": N_("Cover Art"),
        "settings": [
            "save_images_to_tags",
            "embed_only_one_front_image",
            "save_images_to_files",
            "cover_image_filename",
            "save_images_overwrite",
            "save_only_one_front_image",
            "image_type_as_filename",
            "ca_providers",
        ],
    }

    SETTINGS_GROUPS["filenaming"] = {
        "title": N_("File Naming"),
        "settings": [
            "windows_compatibility",
            "ascii_filenames",
            "rename_files",
            "move_files",
            "move_files_to",
            "move_additional_files",
            "move_additional_files_pattern",
            "delete_empty_dirs",
        ],
    }

    SETTINGS_GROUPS["scripting"] = {
        "title": N_("Scripting"),
        "settings": [
            "enable_tagger_scripts",
            "list_of_scripts",
            "last_selected_script_position",
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
            settings |= set(settings_group["settings"])
        return settings

    @classmethod
    def get_setting_groups_list(cls):
        """Iterable of all setting groups keys.

        Yields:
            str: Key
        """
        yield from cls.SETTINGS_GROUPS
