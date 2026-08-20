# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Philipp Wolfer
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

from enum import Enum

from PyQt6.QtCore import QTranslator


class PluginTranslator(QTranslator):
    """QTranslator for plugin UI files (.ui) translations."""

    def __init__(self, translations: dict, source_locale: str = 'en', plugin_id: str = '', parent=None) -> None:
        super().__init__(parent=parent)
        self._translations = translations
        self._source_locale = source_locale
        self._current_locale = 'en'
        self.plugin_id = plugin_id

    def isEmpty(self) -> bool:
        """Return False to indicate this translator has translations."""
        return not self._translations

    def translate(  # type: ignore[override]
        self, context: str | None, source_text: str | None, disambiguation: str | None = None, n: int = -1
    ) -> str | None:
        """Translate text from Qt UI files.

        Args:
            context: Qt context (usually class name)
            source_text: Text to translate
            disambiguation: Optional disambiguation string
            n: Optional plural number

        Returns:
            Translated text or source_text if not found
        """
        if not context or not source_text:
            return None

        # Generate key: qt.context.source_text
        key = f'qt.{context}.{source_text}'

        # Try to get translation
        for locale in (self._current_locale, self._source_locale):
            if locale in self._translations and key in self._translations[locale]:
                return self._translations[locale][key]

            # Try language without region
            lang = locale.split('_')[0]
            if lang in self._translations and key in self._translations[lang]:
                return self._translations[lang][key]

        # Not found, pass on to next translator
        return None


class Plural(Enum):
    ZERO = 'zero'
    ONE = 'one'
    TWO = 'two'
    FEW = 'few'
    MANY = 'many'
    OTHER = 'other'


def _plural_english(n: int) -> Plural:
    return Plural.ONE if n == 1 else Plural.OTHER


def _plural_french(n: int) -> Plural:
    return Plural.ONE if n in {0, 1} else Plural.OTHER


def _plural_polish(n: int) -> Plural:
    if n == 1:
        return Plural.ONE
    if n % 10 in {2, 3, 4} and n % 100 not in {12, 13, 14}:
        return Plural.FEW
    return Plural.MANY


def _plural_russian(n: int) -> Plural:
    if n % 10 == 1 and n % 100 != 11:
        return Plural.ONE
    if n % 10 in {2, 3, 4} and n % 100 not in {12, 13, 14}:
        return Plural.FEW
    return Plural.MANY


def _plural_arabic(n: int) -> Plural:
    if n == 0:
        return Plural.ZERO
    if n == 1:
        return Plural.ONE
    if n == 2:
        return Plural.TWO
    if 3 <= n % 100 <= 10:
        return Plural.FEW
    if 11 <= n % 100 <= 99:
        return Plural.MANY
    return Plural.OTHER


def _plural_hebrew(n: int) -> Plural:
    if n == 1:
        return Plural.ONE
    if n == 2:
        return Plural.TWO
    return Plural.OTHER


def _plural_czech(n: int) -> Plural:
    if n == 1:
        return Plural.ONE
    if 2 <= n <= 4:
        return Plural.FEW
    return Plural.OTHER


def _plural_romanian(n: int) -> Plural:
    if n == 1:
        return Plural.ONE
    if n == 0 or (n != 1 and 1 <= n % 100 <= 19):
        return Plural.FEW
    return Plural.OTHER


def _plural_croatian(n: int) -> Plural:
    if n % 10 == 1 and n % 100 != 11:
        return Plural.ONE
    if n % 10 in {2, 3, 4} and n % 100 not in {12, 13, 14}:
        return Plural.FEW
    return Plural.OTHER


def _plural_catalan(n: int) -> Plural:
    if n == 1:
        return Plural.ONE
    if n != 0 and n % 1_000_000 == 0:
        return Plural.MANY
    return Plural.OTHER


def _plural_lithuanian(n: int) -> Plural:
    if n % 10 == 1 and not 11 <= n % 100 <= 19:
        return Plural.ONE
    if 2 <= n % 10 <= 9 and not 11 <= n % 100 <= 19:
        return Plural.FEW
    return Plural.OTHER


def _plural_other(n: int) -> Plural:
    return Plural.OTHER


def _plural_icelandic(n: int) -> Plural:
    if n % 10 == 1 and n % 100 != 11:
        return Plural.ONE
    return Plural.OTHER


def _plural_irish(n: int) -> Plural:
    if n == 1:
        return Plural.ONE
    if n == 2:
        return Plural.TWO
    if n in {3, 4, 5, 6}:
        return Plural.FEW
    if n in {7, 8, 9, 10}:
        return Plural.MANY
    return Plural.OTHER


def _plural_welsh(n: int) -> Plural:
    if n == 0:
        return Plural.ZERO
    if n == 1:
        return Plural.ONE
    if n == 2:
        return Plural.TWO
    if n == 3:
        return Plural.FEW
    if n == 6:
        return Plural.MANY
    return Plural.OTHER


_PLURAL_RULES = {
    # English, German, Spanish, Italian, Portuguese, etc.
    'en': _plural_english,
    'de': _plural_english,
    'es': _plural_english,
    'it': _plural_english,
    'pt': _plural_english,
    'nl': _plural_english,
    'sv': _plural_english,
    'da': _plural_english,
    'no': _plural_english,
    'fi': _plural_english,
    # French, Punjabi (0 and 1 are singular)
    'fr': _plural_french,
    'pa': _plural_french,
    # Polish
    'pl': _plural_polish,
    # Russian, Ukrainian
    'ru': _plural_russian,
    'uk': _plural_russian,
    # Arabic
    'ar': _plural_arabic,
    # Hebrew
    'he': _plural_hebrew,
    # Czech, Slovak
    'cs': _plural_czech,
    'sk': _plural_czech,
    # Romanian
    'ro': _plural_romanian,
    # Croatian, Bosnian, Serbian
    'hr': _plural_croatian,
    'bs': _plural_croatian,
    'sr': _plural_croatian,
    # Catalan
    'ca': _plural_catalan,
    # Lithuanian
    'lt': _plural_lithuanian,
    # Japanese, Korean, Malay, Vietnamese, Chinese
    'ja': _plural_other,
    'ko': _plural_other,
    'ms': _plural_other,
    'vi': _plural_other,
    'zh': _plural_other,
    # Icelandic
    'is': _plural_icelandic,
    # Irish
    'ga': _plural_irish,
    # Welsh
    'cy': _plural_welsh,
}


def get_plural_form(locale: str, n: int) -> Plural:
    """Get CLDR plural form for a number in a given locale.

    Args:
        locale: Locale code (e.g., 'en', 'de', 'pl', 'ru', 'ar')
        n: Number to get plural form for

    Returns:
        Plural enum value
    """
    lang = locale.split('_')[0]
    return _PLURAL_RULES.get(lang, _plural_english)(n)
