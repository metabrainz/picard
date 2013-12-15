import gettext
import locale
import os.path
import sys
import __builtin__

__builtin__.__dict__['N_'] = lambda a: a


def setup_gettext(localedir, ui_language=None, logdebug=None):
    """Setup locales, load translations, install gettext functions."""
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
    if logdebug:
        logdebug("Using locale %r", current_locale)
    try:
        if logdebug:
            logdebug("Loading gettext translation, localedir=%r", localedir)
        trans = gettext.translation("picard", localedir)
        trans.install(True)
        _ungettext = trans.ungettext
    except IOError:
        __builtin__.__dict__['_'] = lambda a: a

        def _ungettext(a, b, c):
            if c == 1:
                return a
            else:
                return b
    __builtin__.__dict__['ungettext'] = _ungettext
    if logdebug:
        logdebug("_ = %r", _)
        logdebug("N_ = %r", N_)
        logdebug("ungettext = %r", ungettext)
