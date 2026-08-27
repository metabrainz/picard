# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2012 Frederik “Freso” S. Olesen
# Copyright (C) 2013-2014, 2018-2024, 2026 Laurent Monin
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
import gettext as module_gettext
import locale
import os

from PyQt6.QtCore import QLocale

from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)


_logger = lambda *a, **b: None  # noqa: E731
_null_translations = module_gettext.NullTranslations()
_translation = {
    'main': _null_translations,
    'attributes': _null_translations,
    'constants': _null_translations,
    'countries': _null_translations,
}


def get_current_locale():
    lang, encoding = locale.getlocale()
    if lang is None:
        lang = 'C'
    if encoding is None:
        return f"{lang}"
    return f"{lang}.{encoding}"


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
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error as e:
        _logger("Failed to set locale: %s", e)
        try:
            # default to 'C' locale if it couldn't be set from env
            locale.setlocale(locale.LC_ALL, 'C')
        except locale.Error as e:
            _logger("Failed to set locale to C: %s", e)
    current_locale = get_current_locale()
    _logger("Setting locale from env: %r", current_locale)
    return current_locale


def _bcp47_to_locale(tag: str) -> str:
    """Convert a BCP 47 language tag to a POSIX locale identifier.

    Extracts the language and region components, skipping script subtags.
    If no region is found, uses locale.normalize() to infer a default region
    for the language.

    Examples:
        'en-US' -> 'en_US'
        'zh-Hans-CN' -> 'zh_CN'
        'en' -> 'en_US' (via locale.normalize)
        'fr' -> 'fr_FR' (via locale.normalize)
    """
    parts = tag.split('-')
    language = parts[0]
    for part in parts[1:]:
        # Region designator: 2 uppercase ASCII letters or 3 digits
        if (len(part) == 2 and part.isascii() and part.isupper()) or (len(part) == 3 and part.isdigit()):
            return f'{language}_{part}'
    # No region found — use locale.normalize to infer a default region
    normalized = locale.normalize(language)
    if normalized != language:
        # Strip encoding suffix (e.g. 'en_US.ISO8859-1' -> 'en_US')
        return normalized.split('.')[0]
    return language


if IS_WIN:
    from ctypes import windll  # type: ignore[attr-defined]

    def _get_default_locale_win():
        try:
            return locale.windows_locale[windll.kernel32.GetUserDefaultUILanguage()]
        except KeyError:
            return None

    _get_default_locale = _get_default_locale_win

elif IS_MACOS:
    import Foundation

    def _get_default_locale_mac() -> str | None:
        """Read the user's locale from macOS user defaults.

        Prefers AppleLocale (full locale with region, e.g. 'en_US') and falls
        back to AppleLanguages (BCP 47 language tags, e.g. 'en-US').

        Handles known quirks:
        - AppleLocale may contain ICU keyword suffixes (e.g. '@currency=GBP')
          when the user has customized regional settings; these are stripped.
        - AppleLocale may be absent on some macOS 10.13/10.14 configurations.
        - AppleLanguages on newer macOS may contain script subtags
          (e.g. 'zh-Hans-CN') or lack region entirely (e.g. 'en').
        """
        try:
            defaults = Foundation.NSUserDefaults.standardUserDefaults()
            if 'AppleLocale' in defaults:
                locale_str = defaults['AppleLocale']
                # Strip ICU keyword suffixes like @currency=USD or @calendar=gregorian
                return locale_str.split('@')[0] if locale_str else None
            elif 'AppleLanguages' in defaults:
                # Note: In newer macOS versions AppleLanguages no longer contains the full
                # locale name with region, so this might return only a language code.
                return _bcp47_to_locale(defaults['AppleLanguages'][0])
        except Exception as e:
            _logger("Failed to read macOS locale defaults: %s", e)
        return None

    _get_default_locale = _get_default_locale_mac
else:

    def _get_default_locale_none():
        return None

    _get_default_locale = _get_default_locale_none


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


def setup_gettext(localedir: str | None, ui_language: str | None, logger: Callable):
    """Setup locales, load translations, install gettext functions."""
    global _logger
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
            locale.setlocale(locale.LC_ALL, loc)
            current_locale = get_current_locale()
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


def gettext(message: str) -> str:
    """Translate the messsage using the current translator."""
    # Calling gettext("") by default returns the header of the PO file for the
    # current locale. This is unexpected. Return an empty string instead.
    if message == "":
        return message
    return _translation['main'].gettext(message)


def _(message: str) -> str:
    """Alias for gettext"""
    return gettext(message)


def N_(message: str) -> str:
    """No-op marker for translatable strings"""
    return message


def ngettext(singular: str, plural: str, n: int) -> str:
    return _translation['main'].ngettext(singular, plural, n)


def pgettext_attributes(context: str, message: str) -> str:
    return _translation['attributes'].pgettext(context, message)


def gettext_attributes(message: str) -> str:
    return _translation['attributes'].gettext(message)


def gettext_countries(message: str) -> str:
    return _translation['countries'].gettext(message)


def gettext_constants(message: str) -> str:
    return _translation['constants'].gettext(message)


# Dev utility: trace all gettext calls to a file with caller location.
# Purpose: detect strings that are translated at startup but NOT re-translated
# after a language switch (i.e., missing dynamic retranslation code).
#
# Usage: PICARD_I18N_TRACE=/path/to/trace.log picard
#
# Log format: PREFIX CALLER_FILE:LINE SOURCE_STRING
#   - "n:" prefix means N_() was called (string marked for extraction only)
#   - "LANG:" prefix means _() was called (actual translation lookup)
#
# On exit, a report is appended listing strings that were translated in one
# locale phase but not in the subsequent phase (missing retranslation).
# Strings without an available translation (untranslated) are excluded from
# the report since those are a Weblate issue, not a code issue.
#
# Zero overhead when not enabled (functions remain unwrapped).

_trace_file = None
_trace_phases = []  # list of (locale, set_of_strings)
_trace_current_locale = None
_trace_current_strings = None
_trace_has_translation = set()  # strings that have a known translation (source != result)


def _trace_switch_phase(locale):
    """Track locale phases for the exit report."""
    global _trace_current_locale, _trace_current_strings
    if locale != _trace_current_locale:
        if _trace_current_locale is not None and _trace_current_strings:
            _trace_phases.append((_trace_current_locale, _trace_current_strings))
        _trace_current_locale = locale
        _trace_current_strings = set()


def _make_traced(fn, domain, prefix_fn):
    """Wrap a gettext function to log every call with caller location."""
    import traceback

    def traced(*args, **kwargs):
        result = fn(*args, **kwargs)
        source = args[0] if args else ''
        if source:
            locale = QLocale().name()
            prefix = prefix_fn()
            stack = traceback.extract_stack(limit=3)
            if stack:
                frame = stack[0]
                caller = f"{frame.filename}:{frame.lineno}"
            else:
                caller = "??:0"
            _trace_file.write(f"{prefix} {caller} {source!r}\n")
            _trace_file.flush()
            # Track for exit report
            _trace_switch_phase(locale)
            if _trace_current_strings is not None:
                _trace_current_strings.add(source)
            # Track if this string actually has a translation
            if source != result:
                _trace_has_translation.add(source)
        return result

    traced.__wrapped__ = fn
    return traced


def _make_traced_n(fn):
    """Wrap N_() to log with 'n:' prefix."""
    import traceback

    def traced(message):
        result = fn(message)
        if message:
            stack = traceback.extract_stack(limit=3)
            if stack:
                frame = stack[0]
                caller = f"{frame.filename}:{frame.lineno}"
            else:
                caller = "??:0"
            _trace_file.write(f"n: {caller} {message!r}\n")
            _trace_file.flush()
        return result

    traced.__wrapped__ = fn
    return traced


def _trace_exit_report():
    """Write exit report: strings missing retranslation after locale switch."""
    global _trace_current_locale, _trace_current_strings
    if not _trace_file:
        return
    # Flush the last phase
    if _trace_current_locale and _trace_current_strings:
        _trace_phases.append((_trace_current_locale, _trace_current_strings))

    if len(_trace_phases) < 2:
        _trace_file.write("\n=== NO LANGUAGE SWITCH DETECTED ===\n")
        _trace_file.flush()
        return

    _trace_file.write("\n=== EXIT REPORT: MISSING RETRANSLATION ===\n")
    _trace_file.write("(Only strings with known translations are shown.\n")
    _trace_file.write(" Untranslated strings are a Weblate issue, not a code issue.)\n\n")

    for i in range(len(_trace_phases) - 1):
        prev_locale, prev_strings = _trace_phases[i]
        next_locale, next_strings = _trace_phases[i + 1]
        # Strings in prev phase but not in next phase
        missing = prev_strings - next_strings
        # Only report strings that have a known translation (source != result at some point)
        missing_with_translation = missing & _trace_has_translation
        if missing_with_translation:
            _trace_file.write(
                f"--- Strings translated in {prev_locale} but NOT re-translated in {next_locale} "
                f"({len(missing_with_translation)} strings) ---\n"
            )
            for s in sorted(missing_with_translation):
                _trace_file.write(f"  {s!r}\n")
            _trace_file.write("\n")

    _trace_file.flush()


def enable_trace(path):
    """Enable tracing of all gettext calls to a file.

    Patches the module-level gettext functions to log every call with
    the caller's file and line number. N_() calls are prefixed with "n:",
    _() calls with the current locale (e.g. "fr_FR:").

    On exit, appends a report of strings missing retranslation.
    """
    global _trace_file, gettext, ngettext, gettext_attributes, pgettext_attributes
    global gettext_countries, gettext_constants, _, N_

    import atexit

    _trace_file = open(path, 'w', encoding='utf-8')
    atexit.register(_trace_exit_report)

    def _locale_prefix():
        return QLocale().name() + ':'

    gettext = _make_traced(gettext, 'main', _locale_prefix)
    _ = gettext
    ngettext = _make_traced(ngettext, 'main', _locale_prefix)
    gettext_attributes = _make_traced(gettext_attributes, 'attributes', _locale_prefix)
    pgettext_attributes = _make_traced(pgettext_attributes, 'attributes', _locale_prefix)
    gettext_countries = _make_traced(gettext_countries, 'countries', _locale_prefix)
    gettext_constants = _make_traced(gettext_constants, 'constants', _locale_prefix)
    N_ = _make_traced_n(N_)


def disable_trace():
    """Disable tracing and restore original functions."""
    global _trace_file, gettext, ngettext, gettext_attributes, pgettext_attributes
    global gettext_countries, gettext_constants, _, N_
    if _trace_file:
        _trace_exit_report()
        _trace_file.close()
        _trace_file = None
    for name in (
        'gettext',
        'ngettext',
        'gettext_attributes',
        'pgettext_attributes',
        'gettext_countries',
        'gettext_constants',
        'N_',
    ):
        fn = globals()[name]
        if hasattr(fn, '__wrapped__'):
            globals()[name] = fn.__wrapped__
    _ = gettext


# Enable trace via env var: PICARD_I18N_TRACE=/path/to/trace.log
_trace_path = os.environ.get('PICARD_I18N_TRACE')
if _trace_path:
    enable_trace(_trace_path)
