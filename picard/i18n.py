# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2012 Frederik “Freso” S. Olesen
# Copyright (C) 2013-2014, 2018-2022 Laurent Monin
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2017-2022 Philipp Wolfer
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


import builtins
import gettext
import locale
import os.path

from PyQt5.QtCore import QLocale

from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)


builtins.__dict__['N_'] = lambda a: a


_logger = None


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

    def _init_default_locale():
        try:
            current_locale = locale.windows_locale[windll.kernel32.GetUserDefaultUILanguage()]
            return locale.setlocale(locale.LC_ALL, current_locale)
        except KeyError:
            return set_locale_from_env()

elif IS_MACOS:
    import Foundation

    def _init_default_locale():
        defaults = Foundation.NSUserDefaults.standardUserDefaults()
        current_locale = defaults.objectForKey_('AppleLanguages')[0]
        current_locale = current_locale.replace('-', '_')
        try:
            return locale.setlocale(locale.LC_ALL, current_locale)
        except locale.Error:
            _logger("Failed to set locale: %r", current_locale)
            return set_locale_from_env()

else:
    def _init_default_locale():
        return set_locale_from_env()


def _try_set_locale(language):
    # Try setting the locale with different or no encoding
    for encoding in (locale.getpreferredencoding(), 'UTF-8', None):
        if encoding:
            current_locale = locale.normalize(language + '.' + encoding)
        else:
            current_locale = language
        try:
            return locale.setlocale(locale.LC_ALL, current_locale)
        except locale.Error:
            _logger("Failed to set locale: %r", current_locale)
            continue
    set_locale_from_env()  # Ensure some locale settings are defined
    return language  # Just return the language, so at least UI translation works


def _load_translation(domain, localedir):
    try:
        _logger("Loading gettext translation for %s, localedir=%r", domain, localedir)
        return gettext.translation(domain, localedir)
    except OSError as e:
        _logger(e)
        return gettext.NullTranslations()


def setup_gettext(localedir, ui_language=None, logger=None):
    """Setup locales, load translations, install gettext functions."""
    global _logger
    if not logger:
        _logger = lambda *a, **b: None  # noqa: E731
    else:
        _logger = logger
    current_locale = None
    if ui_language:
        _logger("UI language: %r", ui_language)
        current_locale = _try_set_locale(ui_language)
        _logger("Using locale (UI): %r", current_locale)
    if current_locale is None:
        current_locale = _init_default_locale()
        _logger("Using locale (init): %r", current_locale)
    os.environ['LANGUAGE'] = os.environ['LANG'] = current_locale
    QLocale.setDefault(QLocale(current_locale))

    trans = _load_translation('picard', localedir)
    trans_countries = _load_translation('picard-countries', localedir)
    trans_attributes = _load_translation('picard-attributes', localedir)

    trans.install(['ngettext'])
    builtins.__dict__['gettext_countries'] = trans_countries.gettext
    builtins.__dict__['gettext_attributes'] = trans_attributes.gettext

    if hasattr(trans_attributes, 'pgettext'):
        builtins.__dict__['pgettext_attributes'] = trans_attributes.pgettext
    else:
        def pgettext(context, message):
            return gettext_ctxt(trans_attributes.gettext, message, context)
        builtins.__dict__['pgettext_attributes'] = pgettext

    _logger("_ = %r", _)
    _logger("N_ = %r", N_)
    _logger("ngettext = %r", ngettext)
    _logger("gettext_countries = %r", gettext_countries)
    _logger("gettext_attributes = %r", gettext_attributes)
    _logger("pgettext_attributes = %r", pgettext_attributes)


# Workaround for po files with msgctxt which isn't supported by Python < 3.8
# gettext
# msgctxt are used within attributes.po, and gettext is failing to translate
# strings due to that
# This workaround is a hack until we get proper msgctxt support
_CONTEXT_SEPARATOR = "\x04"


def gettext_ctxt(gettext_, message, context=None):
    if context is None:
        return gettext_(message)

    msg_with_ctxt = "%s%s%s" % (context, _CONTEXT_SEPARATOR, message)
    translated = gettext_(msg_with_ctxt)
    if _CONTEXT_SEPARATOR in translated:
        # no translation found, return original message
        return message
    return translated
