# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2009, 2012 Lukáš Lalinský
# Copyright (C) 2007 Javier Kohen
# Copyright (C) 2008-2011, 2014-2015, 2018-2021, 2023 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2011-2012 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2012 stephen
# Copyright (C) 2012, 2014, 2017 Wieland Hoffmann
# Copyright (C) 2013-2014, 2017-2021 Laurent Monin
# Copyright (C) 2014, 2017 Sophist-UK
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2016-2017 Ville Skyttä
# Copyright (C) 2017-2018 Antonio Larrosa
# Copyright (C) 2018 Calvin Walton
# Copyright (C) 2018 virusMac
# Copyright (C) 2020-2021, 2023 Bob Swift
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


from picard import log
from picard.config import get_config
from picard.const import (
    DEFAULT_FILE_NAMING_FORMAT,
    DEFAULT_NAMING_PRESET_ID,
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
from picard.script.serializer import FileNamingScript


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
    if not config.setting['enable_tagger_scripts']:
        return []
    return [(s_name, s_text) for _s_pos, s_name, s_enabled, s_text in config.setting['list_of_scripts'] if s_enabled and s_text]


def get_file_naming_script(settings):
    """Retrieve the file naming script.

    Args:
        settings (ConfigSection): Object containing the user settings

    Returns:
        str: The text of the file naming script if available, otherwise None
    """
    from picard.script import get_file_naming_script_presets
    scripts = settings['file_renaming_scripts']
    selected_id = settings['selected_file_naming_script_id']
    if selected_id:
        if scripts and selected_id in scripts:
            return scripts[selected_id]['script']
        for item in get_file_naming_script_presets():
            if item['id'] == selected_id:
                return str(item['script'])
    log.error("Unable to retrieve the file naming script '%s'", selected_id)
    return None


def get_file_naming_script_presets():
    """Generator of preset example file naming script objects.

    Yields:
        FileNamingScript: the next example FileNamingScript object
    """
    AUTHOR = "MusicBrainz Picard Development Team"
    DESCRIPTION = _("This preset example file naming script does not require any special settings, tagging scripts or plugins.")
    LICENSE = "GNU Public License version 2"

    def preset_title(number, title):
        return _("Preset %(number)d: %(title)s") % {
            'number': number,
            'title': _(title),
        }

    yield FileNamingScript(
        id=DEFAULT_NAMING_PRESET_ID,
        title=preset_title(1, N_("Default file naming script")),
        script=DEFAULT_FILE_NAMING_FORMAT,
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
        author=AUTHOR,
        description=DESCRIPTION,
        version="1.0",
        license=LICENSE,
        last_updated="2021-04-12 21:30:00 UTC",
        script_language_version="1.0",
    )
