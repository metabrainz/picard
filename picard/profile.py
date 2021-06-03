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


from copy import deepcopy
import uuid

from picard.config import get_config


class ProfileImportError(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class UserProfile():
    """Base class for Picard user profile objects.
    """

    OUTPUT_FIELDS = ('title', 'description', 'id', 'settings')
    DEFAULT_TITLE = N_("User Profile")

    def __init__(
        self,
        title='',
        description='',
        id=None,
        settings_dict=None
    ):
        """Base class for Picard user profile objects

        Args:
            title (str): Title of the profile.
            description (str): Description of the profile.
            id (str): ID code for the script. Defaults to a system generated uuid.
            settings_dict (dict): Dictionary of settings as produced using config.setting.as_dict()
        """
        self.title = title if title else _(self.DEFAULT_TITLE)
        self.description = description
        if not id:
            self._set_new_id()
        else:
            self.id = id
        self.settings = None
        self.load_settings(settings_dict)

    def _set_new_id(self):
        """Sets the ID of the script to a new system generated uuid.
        """
        self.id = str(uuid.uuid4())

    def __getitem__(self, setting):
        if hasattr(self, setting):
            value = getattr(self, setting)
            if isinstance(value, str):
                value = value.strip()
            return value
        return None

    def __setitem__(self, setting, value):
        if hasattr(self, setting):
            if isinstance(value, str):
                value = value.strip()
            setattr(self, setting, value)

    def load_settings(self, settings):
        """Load settings from a dictionary.  If the dictionary provided is None or empty, uses the current config.setting.as_dict().

        Args:
            settings (dict): Dictionary of settings as produced using config.setting.as_dict()
        """
        if settings and isinstance(settings, dict):
            self.settings = settings
        else:
            config = get_config()
            self.settings = config.setting.as_dict()

    def settings_to_config(self):
        """Updates the current config.setting with the profile object's stored settings.
        """
        config = get_config()
        for key, value in self.settings.items():
            if key in config.setting:
                config.setting[key] = value

    def copy(self):
        """Create a copy of the current profile object with updated title.
        """
        new_object = deepcopy(self)
        new_object.title = _("%s (Copy)") % self.title
        new_object._set_new_id()
        return new_object

    def to_dict(self):
        """Create a dictionary from the class instance.

        Returns:
            dict: Dictionary of the instance attributes listed in OUTPUT_FIELDS
        """
        return {key: getattr(self, key) for key in self.OUTPUT_FIELDS}

    @classmethod
    def create_from_dict(cls, profile_dict, create_new_id=False):
        """Creates an instance based on the contents of the dictionary provided.

        Args:
            profile_dict (dict): Dictionary containing the property settings
            create_new_id (bool, optional): Determines whether a new ID is assigned. Defaults to False.

        Returns:
            object: An instance of the class.
        """
        new_object = cls()
        if not isinstance(profile_dict, dict):
            raise ProfileImportError(N_('Argument is not a dictionary'))
        if 'title' not in profile_dict or 'settings' not in profile_dict:
            raise ProfileImportError(N_('Invalid profile dictionary'))
        for key in set(cls.OUTPUT_FIELDS).intersection(profile_dict):
            new_object[key] = profile_dict[key]
        if not new_object['title']:
            new_object['title'] = _(cls.DEFAULT_TITLE)
        if create_new_id or not new_object['id']:
            new_object._set_new_id()
        return new_object
