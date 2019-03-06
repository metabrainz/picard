# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2013 Laurent Monin
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
        logger = lambda *a, **b: None  # noop
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
                locale.setlocale(locale.LC_ALL, current_locale)
            except Exception as e:
                logger(e)
        else:
            try:
                current_locale = locale.setlocale(locale.LC_ALL, '')
            except Exception as e:
                logger(e)
    os.environ['LANGUAGE'] = os.environ['LANG'] = current_locale
    QLocale.setDefault(QLocale(current_locale))
    logger("Using locale %r", current_locale)
    try:
        logger("Loading gettext translation, localedir=%r", localedir)
        trans = gettext.translation("picard", localedir)
        trans.install(True)
        _ngettext = trans.ngettext
        logger("Loading gettext translation (picard-countries), localedir=%r", localedir)
        trans_countries = gettext.translation("picard-countries", localedir)
        _gettext_countries = trans_countries.gettext
        logger("Loading gettext translation (picard-attributes), localedir=%r", localedir)
        trans_attributes = gettext.translation("picard-attributes", localedir)
        _gettext_attributes = trans_attributes.gettext
    except IOError as e:
        logger(e)
        builtins.__dict__['_'] = lambda a: a

        def _ngettext(a, b, c):
            if c == 1:
                return a
            else:
                return b

        def _gettext_countries(msg):
            return msg

        def _gettext_attributes(msg):
            return msg

    builtins.__dict__['ngettext'] = _ngettext
    builtins.__dict__['gettext_countries'] = _gettext_countries
    builtins.__dict__['gettext_attributes'] = _gettext_attributes

    logger("_ = %r", _)
    logger("N_ = %r", N_)
    logger("ngettext = %r", ngettext)
    logger("gettext_countries = %r", gettext_countries)
    logger("gettext_attributes = %r", gettext_attributes)


# Workaround for po files with msgctxt which isn't supported by current python
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


def gettext_attr(message, context=None):
    """Translate MB attributes, depending on context"""
    return gettext_ctxt(gettext_attributes, message, context)
