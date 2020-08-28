#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020 Philipp Wolfer
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

import re


LANGUAGES = {
    'Arabic': 'ar',
    'Catalan': 'ca',
    'Czech': 'cs',
    'Danish': 'da',
    'Dutch': 'nl',
    'English': 'en',
    'Estonian': 'et',
    'Finnish': 'fi',
    'French': 'fr',
    'German': 'de',
    'Greek': 'el',
    'Hebrew': 'he',
    'Italian': 'it',
    'Japanese': 'ja',
    'Korean': 'ko',
    'Norwegian': 'nb',
    'Polish': 'pl',
    'Portuguese': 'pt',
    'PortugueseBR': 'pt_BR',
    'Russian': 'ru',
    'SimpChinese': 'zh-Hans',
    'Slovak': 'sk',
    'Slovenian': 'sl',
    'Spanish': 'es',
    'Swedish': 'sv',
    'TradChinese': 'zh-Hant',
    'Turkish': 'tr',
    'Ukrainian': 'uk',
}

_R_LANGUAGES = dict([(code, name) for name, code in LANGUAGES.items()])

# See https://nsis.sourceforge.io/Docs/Chapter4.html#varstrings
ESCAPE_CHARS = {
    r'$\r': '\r',
    r'$\n': '\n',
    r'$\t': '\t',
    r'$\"': '"',
    r'$\'': "'",
    r'$\`': '`',
}

RE_LANGSTRING_LINE = re.compile(r'LangString\s+(?P<identifier>[A-Za-z0-9_]+)\s+\${LANG_[A-Z]+}\s+["\'`](?P<text>.*)["\'`]$')


def language_to_code(language):
    return LANGUAGES.get(language)


def code_to_language(language_code):
    return _R_LANGUAGES.get(language_code)


def escape_string(text):
    for escape, char in ESCAPE_CHARS.items():
        if char in ("'", "`"):  # No need to escape quotes other than ""
            continue
        text = text.replace(char, escape)
    return text


def unescape_string(text):
    for escape, char in ESCAPE_CHARS.items():
        text = text.replace(escape, char)
    return text


def parse_langstring(line):
    match = RE_LANGSTRING_LINE.match(line)
    if match:
        return (
            match.group('identifier'),
            unescape_string(match.group('text'))
        )
    else:
        return None


def make_langstring(language, identifier, text):
    language = language.upper()
    text = escape_string(text)
    return f'LangString {identifier} ${{LANG_{language}}} "{text}"\n'
