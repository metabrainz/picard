# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2012 Frederik “Freso” S. Olesen
# Copyright (C) 2013-2014, 2018-2024 Laurent Monin
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2017-2023 Philipp Wolfer
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

import gettext as module_gettext
import locale
import os

from PyQt6.QtCore import QLocale

from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)


_logger = None
_translation = dict()


def set_locale_from_env():
    """
    Depending on environment, locale.setlocale(locale.LC_ALL, '') can fail.

    Returns a string LANG[.ENCODING]

    >>> import locale
    >>> import os
    >>> os.environ['LANG'] = 'buggy'
    >>> locale.setlocale(locale.LC_ALL, '')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/usr/lib/python3.10/locale.py", line 620, in setlocale
        return _setlocale(category, locale)
    locale.Error: unsupported locale setting
    >>> locale.setlocale(locale.LC_ALL, 'C')
    'C'
    >>> locale.getlocale(locale.LC_ALL)
    (None, None)
    >>> os.environ['LANG'] = 'en_US.UTF-8'
    >>> locale.setlocale(locale.LC_ALL, '')
    'en_US.UTF-8'
    >>> locale.getlocale(locale.LC_ALL)
    ('en_US', 'UTF-8')
    """
    try:
        current_locale = locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        # default to 'C' locale if it couldn't be set from env
        current_locale = locale.setlocale(locale.LC_ALL, 'C')
    _logger("Setting locale from env: %r", current_locale)
    return current_locale


if IS_WIN:
    from ctypes import windll

    def _get_default_locale():
        try:
            return locale.windows_locale[windll.kernel32.GetUserDefaultUILanguage()]
        except KeyError:
            return None

elif IS_MACOS:
    import Foundation

    def _get_default_locale():
        defaults = Foundation.NSUserDefaults.standardUserDefaults()
        return defaults.objectForKey_('AppleLanguages')[0].replace('-', '_')

else:
    def _get_default_locale():
        return None


def _try_encodings():
    """Generate encodings to try, starting with preferred encoding if possible"""
    preferred_encoding = locale.getpreferredencoding()
    if preferred_encoding != 'UTF-8':
        yield preferred_encoding
    yield from ('UTF-8', None)


def _try_locales(language):
    """Try setting the locale from language with preferred/UTF-8/no encoding"""
    for encoding in _try_encodings():
        if encoding:
            yield locale.normalize(language + '.' + encoding)
        else:
            yield language


def _load_translation(domain, localedir, language):
    try:
        _logger("Loading gettext translation for %s, localedir=%r, language=%r", domain, localedir, language)
        return module_gettext.translation(domain, localedir, languages=[language])
    except OSError as e:
        _logger(e)
        return module_gettext.NullTranslations()


def _log_lang_env_vars():
    env_vars = []
    lc_keys = sorted(k for k in os.environ.keys() if k.startswith('LC_'))
    for k in ('LANG', 'LANGUAGE') + tuple(lc_keys):
        if k in os.environ:
            env_vars.append(k + '=' + os.environ[k])
    _logger("Env vars: %s", ' '.join(env_vars))


def setup_gettext(localedir, ui_language=None, logger=None):
    """Setup locales, load translations, install gettext functions."""
    global _logger
    if not logger:
        _logger = lambda *a, **b: None  # noqa: E731
    else:
        _logger = logger

    if ui_language:
        _logger("UI language: %r", ui_language)
        try_locales = list(_try_locales(ui_language))
    else:
        _logger("UI language: system")
        _log_lang_env_vars()
        try_locales = []

    default_locale = _get_default_locale()
    if default_locale:
        try_locales.append(default_locale)

    _logger("Trying locales: %r", try_locales)

    current_locale = None
    for loc in try_locales:
        try:
            current_locale = locale.setlocale(locale.LC_ALL, loc)
            _logger("Set locale to: %r", current_locale)
            break
        except locale.Error:
            _logger("Failed to set locale: %r", loc)

    if ui_language:
        # UI locale may differ from env, those have to match files in po/
        current_locale = ui_language
    if current_locale is None:
        current_locale = set_locale_from_env()

    _logger("Using locale: %r", current_locale)
    QLocale.setDefault(QLocale(current_locale))

    global _translation
    _translation = {
        'main': _load_translation('picard', localedir, language=current_locale),
        'attributes': _load_translation('picard-attributes', localedir, language=current_locale),
        'constants': _load_translation('picard-constants', localedir, language=current_locale),
        'countries': _load_translation('picard-countries', localedir, language=current_locale),
    }
    _logger(_translation)


def _get_translation(key: str) -> module_gettext.NullTranslations:
    try:
        return _translation[key]
    except KeyError:
        return module_gettext.NullTranslations()


def gettext(message: str) -> str:
    """Translate the messsage using the current translator."""
    return _get_translation('main').gettext(message)


def _(message: str) -> str:
    """Alias for gettext"""
    return gettext(message)


def N_(message: str) -> str:
    """No-op marker for translatable strings"""
    return message


def ngettext(singular: str, plural: str, n: int) -> str:
    return _get_translation('main').ngettext(singular, plural, n)


def pgettext_attributes(context: str, message: str) -> str:
    return _get_translation('attributes').pgettext(context, message)


def gettext_attributes(message: str) -> str:
    return _get_translation('attributes').gettext(message)


def gettext_countries(message: str) -> str:
    return _get_translation('countries').gettext(message)


def gettext_constants(message: str) -> str:
    return _get_translation('constants').gettext(message)
