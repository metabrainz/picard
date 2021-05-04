# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2012 Frederik “Freso” S. Olesen
# Copyright (C) 2013-2014, 2018-2020 Laurent Monin
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2017-2020 Philipp Wolfer
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


def setup_gettext(localedir, ui_language=None, logger=None):
    """Setup locales, load translations, install gettext functions."""
    if not logger:
        logger = lambda *a, **b: None  # noqa: E731
    current_locale = ''
    if ui_language:
        try:
            current_locale = locale.normalize(ui_language + '.' + locale.getpreferredencoding())
            locale.setlocale(locale.LC_ALL, current_locale)
        except Exception as e:
            logger(e)
    else:
        if IS_WIN:
            from ctypes import windll
            try:
                current_locale = locale.windows_locale[windll.kernel32.GetUserDefaultUILanguage()]
                current_locale += '.' + locale.getpreferredencoding()
                locale.setlocale(locale.LC_ALL, current_locale)
            except KeyError:
                try:
                    current_locale = locale.setlocale(locale.LC_ALL, '')
                except Exception as e:
                    logger(e)
            except Exception as e:
                logger(e)
        elif IS_MACOS:
            try:
                import Foundation
                defaults = Foundation.NSUserDefaults.standardUserDefaults()
                current_locale = defaults.objectForKey_('AppleLanguages')[0]
                current_locale = current_locale.replace('-', '_')
                locale.setlocale(locale.LC_ALL, current_locale)
            except Exception as e:
                logger(e)
        else:
            try:
                locale.setlocale(locale.LC_ALL, '')
                current_locale = '.'.join(locale.getlocale(locale.LC_MESSAGES))
            except Exception as e:
                logger(e)
    os.environ['LANGUAGE'] = os.environ['LANG'] = current_locale
    QLocale.setDefault(QLocale(current_locale))
    logger("Using locale %r", current_locale)
    try:
        logger("Loading gettext translation, localedir=%r", localedir)
        trans = gettext.translation("picard", localedir)
        logger("Loading gettext translation (picard-countries), localedir=%r", localedir)
        trans_countries = gettext.translation("picard-countries", localedir)
        logger("Loading gettext translation (picard-attributes), localedir=%r", localedir)
        trans_attributes = gettext.translation("picard-attributes", localedir)
    except OSError as e:
        logger(e)
        trans = gettext.NullTranslations()
        trans_countries = gettext.NullTranslations()
        trans_attributes = gettext.NullTranslations()

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
