#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020-2021 Philipp Wolfer
# Copyright (C) 2024 Laurent Monin
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


# See list of available NSIS languages at
# https://sourceforge.net/p/nsis/code/HEAD/tree/NSIS/trunk/Contrib/Language%20files/
LANGUAGES = {
    'Afrikaans': 'af',
    'Albanian': 'sq',
    'Arabic': 'ar',
    'Asturian': 'ast',
    'Basque': 'eu',
    'Belarusian': 'be',
    'Bosnian': 'bs',
    'Breton': 'br',
    'Bulgarian': 'bg',
    'Catalan': 'ca',
    'Cibemba': 'bem',
    'Corsican': 'co',
    'Croation': 'hr',
    'Czech': 'cs',
    'Danish': 'da',
    'Dutch': 'nl',
    'English': 'en',
    'Esperanto': 'eo',
    'Estonian': 'et',
    'Farsi': 'fa',
    'Finnish': 'fi',
    'French': 'fr',
    'Galician': 'gl',
    'Georgian': 'ka',
    'German': 'de',
    'Greek': 'el',
    'Hebrew': 'he',
    'Hindi': 'hi',
    'Hungarian': 'hu',
    'Icelandic': 'is',
    'Igbo': 'ig',
    'Indonesian': 'id',
    'Irish': 'ga',
    'Italian': 'it',
    'Japanese': 'ja',
    'Khmer': 'km',
    'Korean': 'ko',
    'Kurdish': 'ku',
    'Latvian': 'lv',
    'Lithuanian': 'lt',
    'Luxembourgish': 'lb',
    'Macedonian': 'mk',
    'Malagasy': 'mg',
    'Malay': 'ms_MY',
    'Mongolian': 'mn',
    'Norwegian': 'nb',
    'NorwegianNynorsk': 'nn',
    'Polish': 'pl',
    'Portuguese': 'pt',
    'PortugueseBR': 'pt_BR',
    'Romanian': 'ro',
    'Russian': 'ru',
    'ScotsGaelic': 'sco',
    'Serbian': 'sr',
    # 'SimpChinese': 'zh-Hans',
    'SimpChinese': 'zh_CN',
    'Slovak': 'sk',
    'Slovenian': 'sl',
    'Spanish': 'es',
    'Swahili': 'sw',
    'Swedish': 'sv',
    'Tatar': 'tt',
    'Thai': 'th',
    # 'TradChinese': 'zh-Hant',
    'TradChinese': 'zh_TW',
    'Turkish': 'tr',
    'Ukrainian': 'uk',
    'Uzbek': 'uz',
    'Vietnamese': 'vi',
    'Welsh': 'cy',
    'Yoruba': 'yo',
}

_R_LANGUAGES = {code: name for name, code in LANGUAGES.items()}

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
        if char not in {"'", "`"}:  # No need to escape quotes other than ""
            text = text.replace(char, escape)
    return text


def unescape_string(text):
    for escape, char in ESCAPE_CHARS.items():
        text = text.replace(escape, char)
    return text


def parse_langstring(line):
    match_ = RE_LANGSTRING_LINE.match(line)
    if match_:
        return (
            match_.group('identifier'),
            unescape_string(match_.group('text'))
        )
    else:
        return None


def make_langstring(language, identifier, text):
    language = language.upper()
    text = escape_string(text)
    return f'LangString {identifier} ${{LANG_{language}}} "{text}"\n'
