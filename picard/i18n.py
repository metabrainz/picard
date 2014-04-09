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

import gettext
import locale
import os.path
import sys
import __builtin__

__builtin__.__dict__['N_'] = lambda a: a


def setup_gettext(localedir, ui_language=None, logger=None):
    """Setup locales, load translations, install gettext functions."""
    if not logger:
        logger = lambda *a, **b: None  # noop
    current_locale = ''
    if ui_language:
        os.environ['LANGUAGE'] = ''
        os.environ['LANG'] = ui_language
        try:
            current_locale = locale.normalize(ui_language + '.' + locale.getpreferredencoding())
            locale.setlocale(locale.LC_ALL, current_locale)
        except:
            pass
    if sys.platform == "win32":
        try:
            locale.setlocale(locale.LC_ALL, os.environ["LANG"])
        except KeyError:
            os.environ["LANG"] = locale.getdefaultlocale()[0]
            try:
                current_locale = locale.setlocale(locale.LC_ALL, "")
            except:
                pass
        except:
            pass
    elif not ui_language:
        if sys.platform == "darwin":
            try:
                import Foundation
                defaults = Foundation.NSUserDefaults.standardUserDefaults()
                os.environ["LANG"] = \
                    defaults.objectForKey_("AppleLanguages")[0]
            except:
                pass
        try:
            current_locale = locale.setlocale(locale.LC_ALL, "")
        except:
            pass
    logger("Using locale %r", current_locale)
    try:
        logger("Loading gettext translation, localedir=%r", localedir)
        trans = gettext.translation("picard", localedir)
        trans.install(True)
        _ungettext = trans.ungettext
        logger("Loading gettext translation (picard-countries), localedir=%r", localedir)
        trans_countries = gettext.translation("picard-countries", localedir)
        _ugettext_countries = trans_countries.ugettext
        logger("Loading gettext translation (picard-attributes), localedir=%r", localedir)
        trans_attributes = gettext.translation("picard-attributes", localedir)
        _ugettext_attributes = trans_attributes.ugettext
    except IOError as e:
        logger(e)
        __builtin__.__dict__['_'] = lambda a: a

        def _ungettext(a, b, c):
            if c == 1:
                return a
            else:
                return b

        def _ugettext_countries(msg):
            return msg

        def _ugettext_attributes(msg):
            return msg

    __builtin__.__dict__['ungettext'] = _ungettext
    __builtin__.__dict__['ugettext_countries'] = _ugettext_countries
    __builtin__.__dict__['ugettext_attributes'] = _ugettext_attributes

    logger("_ = %r", _)
    logger("N_ = %r", N_)
    logger("ungettext = %r", ungettext)
    logger("ugettext_countries = %r", ugettext_countries)
    logger("ugettext_attributes = %r", ugettext_attributes)


# Workaround for po files with msgctxt which isn't supported by current python
# gettext
# msgctxt are used within attributes.po, and ugettext is failing to translate
# strings due to that
# This workaround is a hack until we get proper msgctxt support
_CONTEXT_SEPARATOR = "\x04"
def ugettext_ctxt(ugettext_, message, context=None):
    if context is None:
        return ugettext_(message)

    msg_with_ctxt = u"%s%s%s" % (context, _CONTEXT_SEPARATOR, message)
    translated = ugettext_(msg_with_ctxt)
    if _CONTEXT_SEPARATOR in translated:
        # no translation found, return original message
        return message
    return translated


def ugettext_attr(message, context=None):
    """Translate MB attributes, depending on context"""
    return ugettext_ctxt(ugettext_attributes, message, context)
