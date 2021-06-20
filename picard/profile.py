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
    PROFILE_GROUPS = OrderedDict()  # Add groups in the order they should be displayed

    PROFILE_GROUPS["metadata"] = {
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

    PROFILE_GROUPS["tags"] = {
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

    PROFILE_GROUPS["coverart"] = {
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

    PROFILE_GROUPS["filenaming"] = {
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

    PROFILE_GROUPS["scripting"] = {
        "title": N_("Scripting"),
        "settings": [
            "enable_tagger_scripts",
            "list_of_scripts",
            "last_selected_script_position",
        ],
    }

    @classmethod
    def get_profile_settings_list(cls):
        """Iterable of all settings names in all profile groups.

        Yields:
            str: Setting name
        """
        for key, profile_group in cls.PROFILE_GROUPS.items():
            for setting in profile_group["settings"]:
                yield setting

    @classmethod
    def get_profile_list(cls):
        for key in cls.PROFILE_GROUPS:
            yield key
