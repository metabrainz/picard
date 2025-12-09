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

from PyQt6.QtCore import QTranslator


class PluginTranslator(QTranslator):
    """QTranslator for plugin UI files (.ui) translations."""

    def __init__(self, translations: dict, source_locale: str = 'en') -> None:
        super().__init__()
        self._translations = translations
        self._source_locale = source_locale
        self._current_locale = 'en'

    def isEmpty(self) -> bool:
        """Return False to indicate this translator has translations."""
        return not self._translations

    def translate(
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
            return source_text or ''

        # Generate key: qt.context.source_text
        key = f'qt.{context}.{source_text}'

        # Try to get translation
        for locale in {self._current_locale, self._source_locale}:
            if locale in self._translations and key in self._translations[locale]:
                return self._translations[locale][key]

            # Try language without region
            lang = locale.split('_')[0]
            if lang in self._translations and key in self._translations[lang]:
                return self._translations[lang][key]

        # Not found, pass on to next translator
        return None


def get_plural_form(locale: str, n: int) -> str:
    """Get CLDR plural form for a number in a given locale.

    Args:
        locale: Locale code (e.g., 'en', 'de', 'pl', 'ru', 'ar')
        n: Number to get plural form for

    Returns:
        One of: 'zero', 'one', 'two', 'few', 'many', 'other'
    """
    lang = locale.split('_')[0]

    # English, German, Spanish, Italian, Portuguese, etc.
    if lang in ('en', 'de', 'es', 'it', 'pt', 'nl', 'sv', 'da', 'no', 'fi'):
        return 'one' if n == 1 else 'other'

    # French (0 and 1 are singular)
    if lang == 'fr':
        return 'one' if n in (0, 1) else 'other'

    # Polish
    if lang == 'pl':
        if n == 1:
            return 'one'
        if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
            return 'few'
        return 'many'

    # Russian, Ukrainian
    if lang in ('ru', 'uk'):
        if n % 10 == 1 and n % 100 != 11:
            return 'one'
        if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
            return 'few'
        return 'many'

    # Arabic
    if lang == 'ar':
        if n == 0:
            return 'zero'
        if n == 1:
            return 'one'
        if n == 2:
            return 'two'
        if 3 <= n % 100 <= 10:
            return 'few'
        if 11 <= n % 100 <= 99:
            return 'many'
        return 'other'

    # Czech, Slovak
    if lang in ('cs', 'sk'):
        if n == 1:
            return 'one'
        if 2 <= n <= 4:
            return 'few'
        return 'other'

    # Default to English rules
    return 'one' if n == 1 else 'other'
