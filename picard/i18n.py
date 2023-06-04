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


if IS_WIN:
    from ctypes import windll

    def _init_default_locale():
        try:
            current_locale = locale.windows_locale[windll.kernel32.GetUserDefaultUILanguage()]
            return locale.setlocale(locale.LC_ALL, current_locale)
        except KeyError:
            return locale.setlocale(locale.LC_ALL, '')

elif IS_MACOS:
    import Foundation

    def _init_default_locale():
        defaults = Foundation.NSUserDefaults.standardUserDefaults()
        current_locale = defaults.objectForKey_('AppleLanguages')[0]
        current_locale = current_locale.replace('-', '_')
        locale.setlocale(locale.LC_ALL, current_locale)
        return current_locale

else:
    def _init_default_locale():
        locale.setlocale(locale.LC_ALL, '')
        return '.'.join(locale.getlocale(locale.LC_MESSAGES))


def _try_set_locale(language):
    # Try setting the locale with different or no encoding
    for encoding in (locale.getpreferredencoding(), 'UTF-8', None):
        if encoding:
            current_locale = locale.normalize(language + '.' + encoding)
        else:
            current_locale = language
        try:
            locale.setlocale(locale.LC_ALL, current_locale)
            return current_locale
        except locale.Error:
            continue
    locale.setlocale(locale.LC_ALL, '')  # Ensure some locale settings are defined
    return language  # Just return the language, so at least UI translation works


def _load_translation(domain, localedir, logger):
    try:
        logger("Loading gettext translation for %s, localedir=%r", domain, localedir)
        return gettext.translation(domain, localedir)
    except OSError as e:
        logger(e)
        return gettext.NullTranslations()


def setup_gettext(localedir, ui_language=None, logger=None):
    """Setup locales, load translations, install gettext functions."""
    if not logger:
        logger = lambda *a, **b: None  # noqa: E731
    current_locale = ''
    try:
        if ui_language:
            current_locale = _try_set_locale(ui_language)
        else:
            current_locale = _init_default_locale()
    except Exception as e:
        logger(e)
    os.environ['LANGUAGE'] = os.environ['LANG'] = current_locale
    QLocale.setDefault(QLocale(current_locale))
    logger("Using locale %r", current_locale)

    trans = _load_translation('picard', localedir, logger)
    trans_countries = _load_translation('picard-countries', localedir, logger)
    trans_attributes = _load_translation('picard-attributes', localedir, logger)

    trans.install(['ngettext'])
    builtins.__dict__['gettext_countries'] = trans_countries.gettext
    builtins.__dict__['gettext_attributes'] = trans_attributes.gettext

    if hasattr(trans_attributes, 'pgettext'):
        builtins.__dict__['pgettext_attributes'] = trans_attributes.pgettext
    else:
        def pgettext(context, message):
            return gettext_ctxt(trans_attributes.gettext, message, context)
        builtins.__dict__['pgettext_attributes'] = pgettext

    logger("_ = %r", _)
    logger("N_ = %r", N_)
    logger("ngettext = %r", ngettext)
    logger("gettext_countries = %r", gettext_countries)
    logger("gettext_attributes = %r", gettext_attributes)
    logger("pgettext_attributes = %r", pgettext_attributes)


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
