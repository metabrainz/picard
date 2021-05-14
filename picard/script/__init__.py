# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2009, 2012 Lukáš Lalinský
# Copyright (C) 2007 Javier Kohen
# Copyright (C) 2008-2011, 2014-2015, 2018-2021 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2011-2012 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2012 stephen
# Copyright (C) 2012, 2014, 2017 Wieland Hoffmann
# Copyright (C) 2013-2014, 2017-2020 Laurent Monin
# Copyright (C) 2014, 2017 Sophist-UK
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2016-2017 Ville Skyttä
# Copyright (C) 2017-2018 Antonio Larrosa
# Copyright (C) 2018 Calvin Walton
# Copyright (C) 2018 virusMac
# Copyright (C) 2020-2021 Bob Swift
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
import datetime
from enum import (
    IntEnum,
    unique,
)
import json
import uuid

import yaml

from picard.config import get_config
from picard.const import (
    DEFAULT_FILE_NAMING_FORMAT,
    DEFAULT_SCRIPT_NAME,
    SCRIPT_LANGUAGE_VERSION,
)
from picard.script.functions import (  # noqa: F401 # pylint: disable=unused-import
    register_script_function,
    script_function,
)
from picard.script.parser import (  # noqa: F401 # pylint: disable=unused-import
    MultiValue,
    ScriptEndOfFile,
    ScriptError,
    ScriptExpression,
    ScriptFunction,
    ScriptParseError,
    ScriptParser,
    ScriptRuntimeError,
    ScriptSyntaxError,
    ScriptText,
    ScriptUnicodeError,
    ScriptUnknownFunction,
    ScriptVariable,
)


class ScriptFunctionDocError(Exception):
    pass


def script_function_documentation(name, fmt, functions=None, postprocessor=None):
    if functions is None:
        functions = dict(ScriptParser._function_registry)
    if name not in functions:
        raise ScriptFunctionDocError("no such function: %s (known functions: %r)" % (name, [name for name in functions]))

    if fmt == 'html':
        return functions[name].htmldoc(postprocessor)
    elif fmt == 'markdown':
        return functions[name].markdowndoc(postprocessor)
    else:
        raise ScriptFunctionDocError("no such documentation format: %s (known formats: html, markdown)" % fmt)


def script_function_names(functions=None):
    if functions is None:
        functions = dict(ScriptParser._function_registry)
    yield from sorted(functions)


def script_function_documentation_all(fmt='markdown', pre='',
                                      post='', postprocessor=None):
    functions = dict(ScriptParser._function_registry)
    doc_elements = []
    for name in script_function_names(functions):
        doc_element = script_function_documentation(name, fmt,
                                                    functions=functions,
                                                    postprocessor=postprocessor)
        if doc_element:
            doc_elements.append(pre + doc_element + post)
    return "\n".join(doc_elements)


def enabled_tagger_scripts_texts():
    """Returns an iterator over the enabled tagger scripts.
    For each script, you'll get a tuple consisting of the script name and text"""
    config = get_config()
    if not config.setting["enable_tagger_scripts"]:
        return []
    return [(s_name, s_text) for _s_pos, s_name, s_enabled, s_text in config.setting["list_of_scripts"] if s_enabled and s_text]


@unique
class PicardScriptType(IntEnum):
    """Picard Script object types
    """
    BASE = 0
    TAGGER = 1
    FILENAMING = 2


class ScriptImportError(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class ScriptLiteral(str):
    @staticmethod
    def yaml_presenter(dumper, data):
        if data:
            data = data.rstrip() + '\n'
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")


yaml.add_representer(ScriptLiteral, ScriptLiteral.yaml_presenter)


class PicardScript():
    """Base class for Picard script objects.
    """
    # Base class developed to support future tagging script class as possible replacement for currently used tuples in config.setting["list_of_scripts"].

    TYPE = PicardScriptType.BASE
    OUTPUT_FIELDS = {'title', 'script', 'script_language_version', 'id'}

    # Don't automatically trigger changing the `script_last_updated` property when updating these properties.
    _last_updated_ignore_list = {'last_updated', 'readonly', 'deletable', 'id'}

    def __init__(self, script='', title='', id=None, last_updated=None, script_language_version=None):
        """Base class for Picard script objects

        Args:
            script (str): Text of the script.
            title (str): Title of the script.
            id (str): ID code for the script. Defaults to a system generated uuid.
            last_updated (str): The UTC date and time when the script was last updated. Defaults to current date/time.
        """
        self.title = title if title else DEFAULT_SCRIPT_NAME
        self.script = script
        if not id:
            self._set_new_id()
        else:
            self.id = id
        if last_updated is None:
            self.update_last_updated()
        else:
            self.last_updated = last_updated
        if script_language_version is None or not script_language_version:
            self.script_language_version = SCRIPT_LANGUAGE_VERSION
        else:
            self.script_language_version = script_language_version

    def _set_new_id(self):
        """Sets the ID of the script to a new system generated uuid.
        """
        self.id = str(uuid.uuid4())

    def __getitem__(self, setting):
        """A safe way of getting the value of the specified property setting, because
        it handles missing properties by returning None rather than raising an exception.

        Args:
            setting (str): The setting whose value to return.

        Returns:
            any: The value of the specified setting, or None if the setting was not found.
        """
        if hasattr(self, setting):
            value = getattr(self, setting)
            if isinstance(value, str):
                value = value.strip()
            return value
        return None

    @property
    def script(self):
        return self._script

    @script.setter
    def script(self, value):
        self._script = ScriptLiteral(value)

    @staticmethod
    def make_last_updated():
        """Provide consistently formatted last updated string.

        Returns:
            str: Last updated string from current date and time
        """
        return datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

    def update_last_updated(self):
        """Update the last updated attribute to the current UTC date and time.
        """
        self.last_updated = self.make_last_updated()

    def update_script_setting(self, **kwargs):
        """Updates the value of the specified properties.

        Args:
            **kwargs: Properties to update in the form `property=value`.
        """
        self._update_from_dict(kwargs)

    def _update_from_dict(self, settings):
        """Updates the values of the properties based on the contents of the dictionary provided.
        Properties in the `settings` dictionary that are not found in the script object are ignored.

        Args:
            settings (dict): The settings to update.
        """
        updated = False
        for key, value in settings.items():
            if value is not None and hasattr(self, key):
                if isinstance(value, str):
                    value = value.strip()
                setattr(self, key, value)
                if key not in self._last_updated_ignore_list:
                    updated = True
        # Don't overwrite `last_updated` with a generated value if a last_updated value has been provided.
        if updated and 'last_updated' not in settings:
            self.update_last_updated()

    def copy(self):
        """Create a copy of the current script object with updated title and last updated attributes.
        """
        new_object = deepcopy(self)
        new_object.update_script_setting(
            title=_("%s (Copy)") % self.title,
            script_language_version=SCRIPT_LANGUAGE_VERSION,
            readonly=False,
            deletable=True
        )
        new_object._set_new_id()
        return new_object

    def to_yaml(self):
        """Converts the properties of the script object to a YAML formatted string.  Note that only property
        names listed in `OUTPUT_FIELDS` will be included in the output.

        Returns:
            str: The properties of the script object formatted as a YAML string.
        """
        items = {key: getattr(self, key) for key in dir(self) if key in self.OUTPUT_FIELDS}
        return yaml.dump(items)

    def to_json(self, indent=None):
        """Converts the properties of the script object to a JSON formatted string.  Note that only property
        names listed in `OUTPUT_FIELDS` will be included in the output.

        Args:
            indent (int): Amount to indent the output. Defaults to None.

        Returns:
            str: The properties of the script object formatted as a JSON string.
        """
        items = {key: getattr(self, key) for key in dir(self) if key in self.OUTPUT_FIELDS}
        return json.dumps(items, indent=indent, sort_keys=True)

    @classmethod
    def create_from_yaml(cls, yaml_string, create_new_id=True):
        """Creates an instance based on the contents of the YAML string provided.
        Properties in the YAML string that are not found in the script object are ignored.

        Args:
            yaml_string (str): YAML string containing the property settings.

        Returns:
            object: An instance of the class, populated from the property settings in the YAML string.
        """
        new_object = cls()
        yaml_dict = yaml.safe_load(yaml_string)
        if not isinstance(yaml_dict, dict):
            raise ScriptImportError(N_("File content not a dictionary"))
        if 'title' not in yaml_dict or 'script' not in yaml_dict:
            raise ScriptImportError(N_('Invalid script package'))
        new_object._update_from_dict(yaml_dict)
        if create_new_id or not new_object['id']:
            new_object._set_new_id()
        return new_object

    @classmethod
    def create_from_json(cls, json_string, create_new_id=True):
        """Creates an instance based on the contents of the JSON string provided.
        Properties in the JSON string that are not found in the script object are ignored.

        Args:
            json_string (str): JSON string containing the property settings.
            create_new_id (bool): Do not use the existing id.  Defaults to True.

        Returns:
            object: An instance of the class, populated from the property settings in the JSON string.
        """
        new_object = cls()
        new_object.title = ''
        new_object.update_from_json(json_string)
        if not (new_object['title'] and new_object['script']):
            raise ScriptImportError(N_('Invalid script package'))
        if create_new_id or not new_object['id']:
            new_object._set_new_id()
        return new_object

    def update_from_json(self, json_string):
        """Updates the values of the properties based on the contents of the JSON string provided.
        Properties in the JSON string that are not found in the script object are ignored.

        Args:
            json_string (str): JSON string containing the property settings.
        """
        try:
            decoded_string = json.loads(json_string)
        except json.decoder.JSONDecodeError:
            raise ScriptImportError(N_("Unable to decode JSON string"))
        self._update_from_dict(decoded_string)


class FileNamingScript(PicardScript):
    """Picard file naming script class
    """
    TYPE = PicardScriptType.FILENAMING
    OUTPUT_FIELDS = {'title', 'script', 'author', 'description', 'license', 'version', 'last_updated', 'script_language_version', 'id'}

    def __init__(
        self,
        script='',
        title='',
        id=None,
        readonly=False,
        deletable=True,
        author='',
        description='',
        license='',
        version='',
        last_updated=None,
        script_language_version=None
    ):
        """Creates a Picard file naming script object.

        Args:
            script (str): Text of the script.
            title (str): Title of the script.
            id (str): ID code for the script. Defaults to a system generated uuid.
            readonly (bool): Identifies if the script is readonly. Defaults to False.
            deletable (bool): Identifies if the script can be deleted from the selection list. Defaults to True.
            author (str): The author of the script. Defaults to ''.
            description (str): A description of the script, typically including type of output and any required plugins or settings. Defaults to ''.
            license (str): The license under which the script is being distributed. Defaults to ''.
            version (str): Identifies the version of the script. Defaults to ''.
            last_updated (str): The UTC date and time when the script was last updated. Defaults to current date/time.
            script_language_version (str): The version of the script language supported by the script.
        """
        super().__init__(script=script, title=title, id=id, last_updated=last_updated, script_language_version=script_language_version)
        self.readonly = readonly    # for presets
        self.deletable = deletable  # Allow removal from list of scripts
        self.author = author
        self.description = description
        self.license = license
        self.version = version


def get_file_naming_script_presets():
    """Generator of preset example file naming script objects.

    Yields:
        FileNamingScript: the next example FileNamingScript object
    """
    AUTHOR = "MusicBrainz Picard Development Team"
    DESCRIPTION = _("This preset example file naming script does not require any special settings, tagging scripts or plugins.")
    LICENSE = "GNU Public License version 2"

    def preset_title(number, title):
        return _("Preset %d: %s") % (number, _(title))

    yield FileNamingScript(
        id="Preset 1",
        title=preset_title(1, N_("Default file naming script")),
        script=DEFAULT_FILE_NAMING_FORMAT,
        readonly=True,
        deletable=False,
        author=AUTHOR,
        description=DESCRIPTION,
        version="1.0",
        license=LICENSE,
        last_updated="2019-08-05 13:40:00 UTC",
        script_language_version="1.0",
    )

    yield FileNamingScript(
        id="Preset 2",
        title=preset_title(2, N_("[album artist]/[album]/[track #]. [title]")),
        script="%albumartist%/\n"
               "%album%/\n"
               "%tracknumber%. %title%",
        readonly=True,
        deletable=False,
        author=AUTHOR,
        description=DESCRIPTION,
        version="1.0",
        license=LICENSE,
        last_updated="2021-04-12 21:30:00 UTC",
        script_language_version="1.0",
    )

    yield FileNamingScript(
        id="Preset 3",
        title=preset_title(3, N_("[album artist]/[album]/[disc and track #] [artist] - [title]")),
        script="$if2(%albumartist%,%artist%)/\n"
               "$if(%albumartist%,%album%/,)\n"
               "$if($gt(%totaldiscs%,1),%discnumber%-,)\n"
               "$if($and(%albumartist%,%tracknumber%),$num(%tracknumber%,2) ,)\n"
               "$if(%_multiartist%,%artist% - ,)\n"
               "%title%",
        readonly=True,
        deletable=False,
        author=AUTHOR,
        description=DESCRIPTION,
        version="1.0",
        license=LICENSE,
        last_updated="2021-04-12 21:30:00 UTC",
        script_language_version="1.0",
    )
