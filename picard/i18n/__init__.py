# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2012 Frederik “Freso” S. Olesen
# Copyright (C) 2013-2014, 2018-2024 Laurent Monin
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2017-2024, 2026 Philipp Wolfer
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from collections.abc import Callable

from PyQt6.QtCore import (
    QObject,
    pyqtSignal,
)

from picard.i18n.collate import (
    setup_collator,
    sort_key,
)
from picard.i18n.gettext import (
    N_,
    _,
    gettext,
    gettext_attributes,
    gettext_constants,
    gettext_countries,
    ngettext,
    pgettext_attributes,
    setup_gettext,
)


class _I18nSignals(QObject):
    """Signals emitted by the i18n subsystem."""

    # Emitted after the UI language has been switched at runtime.
    language_changed = pyqtSignal()


_signals = _I18nSignals()
language_changed = _signals.language_changed


# Store the localedir used at startup so switch_language() can reuse it.
_localedir: str | None = None


__all__ = [
    'N_',
    '_',
    'gettext',
    'gettext_attributes',
    'gettext_constants',
    'gettext_countries',
    'language_changed',
    'ngettext',
    'pgettext_attributes',
    'setup_i18n',
    'sort_key',
    'switch_language',
]


def setup_i18n(localedir: str | None, ui_language: str | None = None, logger: Callable | None = None):
    global _localedir
    _localedir = localedir
    logger = _init_logger(logger)

    # Setup gettext translations
    setup_gettext(localedir, ui_language, logger)

    # Setup collator
    setup_collator(logger)


def switch_language(ui_language: str | None, logger: Callable | None = None):
    """Switch the UI language at runtime.

    Reloads gettext translations, refreshes the collator, and emits
    the language_changed signal so UI components can retranslate.

    Args:
        ui_language: The new language code (e.g. 'de', 'fr', 'ja'),
                     or empty string / None for system default.
        logger: Optional logging callable.
    """
    logger = _init_logger(logger)
    logger("Switching UI language to: %r", ui_language)

    # Reload gettext translations
    setup_gettext(_localedir, ui_language or None, logger)

    # Refresh collator for new locale
    setup_collator(logger)

    # Notify all connected UI components
    language_changed.emit()


def _init_logger(logger: Callable | None) -> Callable:
    if not logger:
        logger = lambda *a, **b: None  # noqa: E731
    return logger
