# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2014 Sophist-UK
# Copyright (C) 2014, 2018, 2020-2021, 2024 Laurent Monin
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018-2019, 2021 Philipp Wolfer
# Copyright (C) 2020 Gabriel Ferreira
# Copyright (C) 2020 Undearius
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


# This modules provides functionality for simplifying unicode strings.

# The unicode character set (of over 1m codepoints and 24,000 characters) includes:
#   Normal ascii (latin) non-accented characters
#   Combined latin characters e.g. ae in normal usage
#   Compatibility combined latin characters (retained for compatibility with other character sets)
#     These can look very similar to normal characters and can be confusing for searches, sort orders etc.
#   Non-latin (e.g. japanese, greek, hebrew etc.) characters
# Both latin and non-latin characters can be accented. Accents can be either:
#   Provided by separate nonspacing_mark characters which are visually overlaid (visually 1 character is actually 2); or
#   Integrated accented characters (i.e. non-accented characters combined with a nonspace_mark into a single character)
# Again these can be confusing for searches, sort orders etc.
# Punctuation can also be confusing in unicode e.g. several types of single or double quote mark.

# For latin script:
#   Combined characters, accents and punctuation can be visually similar but look different to search engines,
#   sort orders etc. and the number of ways to use similar looking characters can (does) result in inconsistent
#   usage inside Music metadata.
#
#   Simplifying # the unicode character sets by many-to-one mappings can improve consistency and reduce confusion,
#   however sometimes the choice of specific characters can be a deliberate part of an album, song title or artist name
#   (and should not therefore be changed without careful thought) and occasionally the choice of characters can be
#   malicious (i.e. to defeat firewalls or spam filters or to appear to be something else).
#
#   Finally, given the size of the unicode character set, fonts are unlikely to display all characters,
#   making simplification a necessity.
#
#   Simplification may also be needed to make tags conform to ISO-8859-1 (extended ascii) or to make tags or filenames
#   into ascii, perhaps because the file system or player cannot support unicode.
#
# Non-latin scripts may also need to be converted to latin scripts through:
#   Translation (e.g. hebrew word for mother is translated to "mother"); or
#   Transliteration (e.g. the SOUND of the hebrew letter or word is spelt out in latin)
# These are non-trivial, and the software to do these is far from comprehensive.

# This module provides utility functions to enable simplification of latin and punctuation unicode:
#   1. simplify compatibility characters;
#   2. split combined characters;
#   3. remove accents (entirely or if not in ISO-8859-1 as applicable);
#   4. replace remaining non-ascii or non-ISO-8859-1 characters with a default character
# This module also provides an extension infrastructure to allow translation and / or transliteration plugins to be added.

import codecs
from functools import partial
import unicodedata

from picard.util import sanitize_filename


# LATIN SIMPLIFICATION
# The translation tables for punctuation and latin combined-characters are taken from
# http://unicode.org/repos/cldr/trunk/common/transforms/Latin-ASCII.xml
# Various bugs and mistakes in this have been ironed out during testing.


_ADDITIONAL_COMPATIBILITY = {
    "\u0276": "Œ",  # LATIN LETTER SMALL CAPITAL OE
    "\u1d00": "A",  # LATIN LETTER SMALL CAPITAL A
    "\u1d01": "Æ",  # LATIN LETTER SMALL CAPITAL AE
    "\u1d04": "C",  # LATIN LETTER SMALL CAPITAL C
    "\u1d05": "D",  # LATIN LETTER SMALL CAPITAL D
    "\u1d07": "E",  # LATIN LETTER SMALL CAPITAL E
    "\u1d0a": "J",  # LATIN LETTER SMALL CAPITAL J
    "\u1d0b": "K",  # LATIN LETTER SMALL CAPITAL K
    "\u1d0d": "M",  # LATIN LETTER SMALL CAPITAL M
    "\u1d0f": "O",  # LATIN LETTER SMALL CAPITAL O
    "\u1d18": "P",  # LATIN LETTER SMALL CAPITAL P
    "\u1d1b": "T",  # LATIN LETTER SMALL CAPITAL T
    "\u1d1c": "U",  # LATIN LETTER SMALL CAPITAL U
    "\u1d20": "V",  # LATIN LETTER SMALL CAPITAL V
    "\u1d21": "W",  # LATIN LETTER SMALL CAPITAL W
    "\u1d22": "Z",  # LATIN LETTER SMALL CAPITAL Z
    "\u3007": "0",  # IDEOGRAPHIC NUMBER ZERO
    "\u00a0": " ",  # NO-BREAK SPACE
    "\u3000": " ",  # IDEOGRAPHIC SPACE (from ‹character-fallback›)
    "\u2033": "”",  # DOUBLE PRIME
    "\uff0f": "/",  # FULLWIDTH SOLIDUS
}


def unicode_simplify_compatibility(string, pathsave=False, win_compat=False):
    interim = ''.join(_replace_char(_ADDITIONAL_COMPATIBILITY, ch, pathsave, win_compat) for ch in string)
    return unicodedata.normalize("NFKC", interim)


_SIMPLIFY_PUNCTUATION = {
    "\u013f": "L",  # LATIN CAPITAL LETTER L WITH MIDDLE DOT (compat)
    "\u0140": "l",  # LATIN SMALL LETTER L WITH MIDDLE DOT (compat)
    "\u2018": "'",  # LEFT SINGLE QUOTATION MARK (from ‹character-fallback›)
    "\u2019": "'",  # RIGHT SINGLE QUOTATION MARK (from ‹character-fallback›)
    "\u201a": "'",  # SINGLE LOW-9 QUOTATION MARK (from ‹character-fallback›)
    "\u201b": "'",  # SINGLE HIGH-REVERSED-9 QUOTATION MARK (from ‹character-fallback›)
    "\u201c": "\"",  # LEFT DOUBLE QUOTATION MARK (from ‹character-fallback›)
    "\u201d": "\"",  # RIGHT DOUBLE QUOTATION MARK (from ‹character-fallback›)
    "\u201e": "\"",  # DOUBLE LOW-9 QUOTATION MARK (from ‹character-fallback›)
    "\u201f": "\"",  # DOUBLE HIGH-REVERSED-9 QUOTATION MARK (from ‹character-fallback›)
    "\u2032": "'",  # PRIME
    "\u2033": "\"",  # DOUBLE PRIME
    "\u301d": "\"",  # REVERSED DOUBLE PRIME QUOTATION MARK
    "\u301e": "\"",  # DOUBLE PRIME QUOTATION MARK
    "\u00ab": "<<",  # LEFT-POINTING DOUBLE ANGLE QUOTATION MARK (from ‹character-fallback›)
    "\u00bb": ">>",  # RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK (from ‹character-fallback›)
    "\u2039": "<",  # SINGLE LEFT-POINTING ANGLE QUOTATION MARK
    "\u203a": ">",  # SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
    "\u00ad": "",  # SOFT HYPHEN (from ‹character-fallback›)
    "\u2010": "-",  # HYPHEN (from ‹character-fallback›)
    "\u2011": "-",  # NON-BREAKING HYPHEN (from ‹character-fallback›)
    "\u2012": "-",  # FIGURE DASH (from ‹character-fallback›)
    "\u2013": "-",  # EN DASH (from ‹character-fallback›)
    "\u2014": "-",  # EM DASH (from ‹character-fallback›)
    "\u2015": "-",  # HORIZONTAL BAR (from ‹character-fallback›)
    "\ufe31": "|",  # PRESENTATION FORM FOR VERTICAL EM DASH (compat)
    "\ufe32": "|",  # PRESENTATION FORM FOR VERTICAL EN DASH (compat)
    "\ufe58": "-",  # SMALL EM DASH (compat)
    "\u2016": "||",  # DOUBLE VERTICAL LINE
    "\u2044": "/",  # FRACTION SLASH (from ‹character-fallback›)
    "\u2045": "[",  # LEFT SQUARE BRACKET WITH QUILL
    "\u2046": "]",  # RIGHT SQUARE BRACKET WITH QUILL
    "\u204e": "*",  # LOW ASTERISK
    "\u3008": "<",  # LEFT ANGLE BRACKET
    "\u3009": ">",  # RIGHT ANGLE BRACKET
    "\u300a": "<<",  # LEFT DOUBLE ANGLE BRACKET
    "\u300b": ">>",  # RIGHT DOUBLE ANGLE BRACKET
    "\u3014": "[",  # LEFT TORTOISE SHELL BRACKET
    "\u3015": "]",  # RIGHT TORTOISE SHELL BRACKET
    "\u3018": "[",  # LEFT WHITE TORTOISE SHELL BRACKET
    "\u3019": "]",  # RIGHT WHITE TORTOISE SHELL BRACKET
    "\u301a": "[",  # LEFT WHITE SQUARE BRACKET
    "\u301b": "]",  # RIGHT WHITE SQUARE BRACKET
    "\ufe11": ",",  # PRESENTATION FORM FOR VERTICAL IDEOGRAPHIC COMMA (compat)
    "\ufe12": ".",  # PRESENTATION FORM FOR VERTICAL IDEOGRAPHIC FULL STOP (compat)
    "\ufe39": "[",  # PRESENTATION FORM FOR VERTICAL LEFT TORTOISE SHELL BRACKET (compat)
    "\ufe3a": "]",  # PRESENTATION FORM FOR VERTICAL RIGHT TORTOISE SHELL BRACKET (compat)
    "\ufe3d": "<<",  # PRESENTATION FORM FOR VERTICAL LEFT DOUBLE ANGLE BRACKET (compat)
    "\ufe3e": ">>",  # PRESENTATION FORM FOR VERTICAL RIGHT DOUBLE ANGLE BRACKET (compat)
    "\ufe3f": "<",  # PRESENTATION FORM FOR VERTICAL LEFT ANGLE BRACKET (compat)
    "\ufe40": ">",  # PRESENTATION FORM FOR VERTICAL RIGHT ANGLE BRACKET (compat)
    "\ufe51": ",",  # SMALL IDEOGRAPHIC COMMA (compat)
    "\ufe5d": "[",  # SMALL LEFT TORTOISE SHELL BRACKET (compat)
    "\ufe5e": "]",  # SMALL RIGHT TORTOISE SHELL BRACKET (compat)
    "\uff5f": "((",  # FULLWIDTH LEFT WHITE PARENTHESIS (compat)(from ‹character-fallback›)
    "\uff60": "))",  # FULLWIDTH RIGHT WHITE PARENTHESIS (compat)(from ‹character-fallback›)
    "\uff61": ".",  # HALFWIDTH IDEOGRAPHIC FULL STOP (compat)
    "\uff64": ",",  # HALFWIDTH IDEOGRAPHIC COMMA (compat)
    "\u2212": "-",  # MINUS SIGN (from ‹character-fallback›)
    "\u2215": "/",  # DIVISION SLASH (from ‹character-fallback›)
    "\u2216": "\\",  # SET MINUS (from ‹character-fallback›)
    "\u2223": "|",  # DIVIDES (from ‹character-fallback›)
    "\u2225": "||",  # PARALLEL TO (from ‹character-fallback›)
    "\u226a": "<<",  # MUCH LESS-THAN
    "\u226b": ">>",  # MUCH GREATER-THAN
    "\u2985": "((",  # LEFT WHITE PARENTHESIS
    "\u2986": "))",  # RIGHT WHITE PARENTHESIS
    "\u2022": "-",  # BULLET
    "\u200b": "",  # Zero Width Space
}


def unicode_simplify_punctuation(string, pathsave=False, win_compat=False):
    return ''.join(_replace_char(_SIMPLIFY_PUNCTUATION, ch, pathsave, win_compat) for ch in string)


_SIMPLIFY_COMBINATIONS = {
    "\u00c6": "AE",  # LATIN CAPITAL LETTER AE (from ‹character-fallback›)
    "\u00d0": "D",  # LATIN CAPITAL LETTER ETH
    "\u00d8": "OE",  # LATIN CAPITAL LETTER O WITH STROKE (see https://en.wikipedia.org/wiki/%C3%98)
    "\u00de": "TH",  # LATIN CAPITAL LETTER THORN
    "\u00df": "ss",  # LATIN SMALL LETTER SHARP S (from ‹character-fallback›)
    "\u00e6": "ae",  # LATIN SMALL LETTER AE (from ‹character-fallback›)
    "\u00f0": "d",  # LATIN SMALL LETTER ETH
    "\u00f8": "oe",  # LATIN SMALL LETTER O WITH STROKE (see https://en.wikipedia.org/wiki/%C3%98)
    "\u00fe": "th",  # LATIN SMALL LETTER THORN
    "\u0110": "D",  # LATIN CAPITAL LETTER D WITH STROKE
    "\u0111": "d",  # LATIN SMALL LETTER D WITH STROKE
    "\u0126": "H",  # LATIN CAPITAL LETTER H WITH STROKE
    "\u0127": "h",  # LATIN CAPITAL LETTER H WITH STROKE
    "\u0131": "i",  # LATIN SMALL LETTER DOTLESS I
    "\u0138": "q",  # LATIN SMALL LETTER KRA (collates with q in DUCET)
    "\u0141": "L",  # LATIN CAPITAL LETTER L WITH STROKE
    "\u0142": "l",  # LATIN SMALL LETTER L WITH STROKE
    "\u0149": "'n",  # LATIN SMALL LETTER N PRECEDED BY APOSTROPHE (from ‹character-fallback›)
    "\u014a": "N",  # LATIN CAPITAL LETTER ENG
    "\u014b": "n",  # LATIN SMALL LETTER ENG
    "\u0152": "OE",  # LATIN CAPITAL LIGATURE OE (from ‹character-fallback›)
    "\u0153": "oe",  # LATIN SMALL LIGATURE OE (from ‹character-fallback›)
    "\u0166": "T",  # LATIN CAPITAL LETTER T WITH STROKE
    "\u0167": "t",  # LATIN SMALL LETTER T WITH STROKE
    "\u0180": "b",  # LATIN SMALL LETTER B WITH STROKE
    "\u0181": "B",  # LATIN CAPITAL LETTER B WITH HOOK
    "\u0182": "B",  # LATIN CAPITAL LETTER B WITH TOPBAR
    "\u0183": "b",  # LATIN SMALL LETTER B WITH TOPBAR
    "\u0187": "C",  # LATIN CAPITAL LETTER C WITH HOOK
    "\u0188": "c",  # LATIN SMALL LETTER C WITH HOOK
    "\u0189": "D",  # LATIN CAPITAL LETTER AFRICAN D
    "\u018a": "D",  # LATIN CAPITAL LETTER D WITH HOOK
    "\u018b": "D",  # LATIN CAPITAL LETTER D WITH TOPBAR
    "\u018c": "d",  # LATIN SMALL LETTER D WITH TOPBAR
    "\u0190": "E",  # LATIN CAPITAL LETTER OPEN E
    "\u0191": "F",  # LATIN CAPITAL LETTER F WITH HOOK
    "\u0192": "f",  # LATIN SMALL LETTER F WITH HOOK
    "\u0193": "G",  # LATIN CAPITAL LETTER G WITH HOOK
    "\u0195": "hv",  # LATIN SMALL LETTER HV
    "\u0196": "I",  # LATIN CAPITAL LETTER IOTA
    "\u0197": "I",  # LATIN CAPITAL LETTER I WITH STROKE
    "\u0198": "K",  # LATIN CAPITAL LETTER K WITH HOOK
    "\u0199": "k",  # LATIN SMALL LETTER K WITH HOOK
    "\u019a": "l",  # LATIN SMALL LETTER L WITH BAR
    "\u019d": "N",  # LATIN CAPITAL LETTER N WITH LEFT HOOK
    "\u019e": "n",  # LATIN SMALL LETTER N WITH LONG RIGHT LEG
    "\u01a2": "GH",  # LATIN CAPITAL LETTER GHA (see http://unicode.org/notes/tn27/)
    "\u01a3": "gh",  # LATIN SMALL LETTER GHA (see http://unicode.org/notes/tn27/)
    "\u01a4": "P",  # LATIN CAPITAL LETTER P WITH HOOK
    "\u01a5": "p",  # LATIN SMALL LETTER P WITH HOOK
    "\u01ab": "t",  # LATIN SMALL LETTER T WITH PALATAL HOOK
    "\u01ac": "T",  # LATIN CAPITAL LETTER T WITH HOOK
    "\u01ad": "t",  # LATIN SMALL LETTER T WITH HOOK
    "\u01ae": "T",  # LATIN CAPITAL LETTER T WITH RETROFLEX HOOK
    "\u01b2": "V",  # LATIN CAPITAL LETTER V WITH HOOK
    "\u01b3": "Y",  # LATIN CAPITAL LETTER Y WITH HOOK
    "\u01b4": "y",  # LATIN SMALL LETTER Y WITH HOOK
    "\u01b5": "Z",  # LATIN CAPITAL LETTER Z WITH STROKE
    "\u01b6": "z",  # LATIN SMALL LETTER Z WITH STROKE
    "\u01c4": "DZ",  # LATIN CAPITAL LETTER DZ WITH CARON (compat)
    "\u01c5": "Dz",  # LATIN CAPITAL LETTER D WITH SMALL LETTER Z WITH CARON (compat)
    "\u01c6": "dz",  # LATIN SMALL LETTER DZ WITH CARON (compat)
    "\u01e4": "G",  # LATIN CAPITAL LETTER G WITH STROKE
    "\u01e5": "g",  # LATIN SMALL LETTER G WITH STROKE
    "\u0221": "d",  # LATIN SMALL LETTER D WITH CURL
    "\u0224": "Z",  # LATIN CAPITAL LETTER Z WITH HOOK
    "\u0225": "z",  # LATIN SMALL LETTER Z WITH HOOK
    "\u0234": "l",  # LATIN SMALL LETTER L WITH CURL
    "\u0235": "n",  # LATIN SMALL LETTER N WITH CURL
    "\u0236": "t",  # LATIN SMALL LETTER T WITH CURL
    "\u0237": "j",  # LATIN SMALL LETTER DOTLESS J
    "\u0238": "db",  # LATIN SMALL LETTER DB DIGRAPH
    "\u0239": "qp",  # LATIN SMALL LETTER QP DIGRAPH
    "\u023a": "A",  # LATIN CAPITAL LETTER A WITH STROKE
    "\u023b": "C",  # LATIN CAPITAL LETTER C WITH STROKE
    "\u023c": "c",  # LATIN SMALL LETTER C WITH STROKE
    "\u023d": "L",  # LATIN CAPITAL LETTER L WITH BAR
    "\u023e": "T",  # LATIN CAPITAL LETTER T WITH DIAGONAL STROKE
    "\u023f": "s",  # LATIN SMALL LETTER S WITH SWASH TAIL
    "\u0240": "z",  # LATIN SMALL LETTER Z WITH SWASH TAIL
    "\u0243": "B",  # LATIN CAPITAL LETTER B WITH STROKE
    "\u0244": "U",  # LATIN CAPITAL LETTER U BAR
    "\u0246": "E",  # LATIN CAPITAL LETTER E WITH STROKE
    "\u0247": "e",  # LATIN SMALL LETTER E WITH STROKE
    "\u0248": "J",  # LATIN CAPITAL LETTER J WITH STROKE
    "\u0249": "j",  # LATIN SMALL LETTER J WITH STROKE
    "\u024c": "R",  # LATIN CAPITAL LETTER R WITH STROKE
    "\u024d": "r",  # LATIN SMALL LETTER R WITH STROKE
    "\u024e": "Y",  # LATIN CAPITAL LETTER Y WITH STROKE
    "\u024f": "y",  # LATIN SMALL LETTER Y WITH STROKE
    "\u0253": "b",  # LATIN SMALL LETTER B WITH HOOK
    "\u0255": "c",  # LATIN SMALL LETTER C WITH CURL
    "\u0256": "d",  # LATIN SMALL LETTER D WITH TAIL
    "\u0257": "d",  # LATIN SMALL LETTER D WITH HOOK
    "\u025b": "e",  # LATIN SMALL LETTER OPEN E
    "\u025f": "j",  # LATIN SMALL LETTER DOTLESS J WITH STROKE
    "\u0260": "g",  # LATIN SMALL LETTER G WITH HOOK
    "\u0261": "g",  # LATIN SMALL LETTER SCRIPT G
    "\u0262": "G",  # LATIN LETTER SMALL CAPITAL G
    "\u0266": "h",  # LATIN SMALL LETTER H WITH HOOK
    "\u0267": "h",  # LATIN SMALL LETTER HENG WITH HOOK
    "\u0268": "i",  # LATIN SMALL LETTER I WITH STROKE
    "\u026a": "I",  # LATIN LETTER SMALL CAPITAL I
    "\u026b": "l",  # LATIN SMALL LETTER L WITH MIDDLE TILDE
    "\u026c": "l",  # LATIN SMALL LETTER L WITH BELT
    "\u026d": "l",  # LATIN SMALL LETTER L WITH RETROFLEX HOOK
    "\u0271": "m",  # LATIN SMALL LETTER M WITH HOOK
    "\u0272": "n",  # LATIN SMALL LETTER N WITH LEFT HOOK
    "\u0273": "n",  # LATIN SMALL LETTER N WITH RETROFLEX HOOK
    "\u0274": "N",  # LATIN LETTER SMALL CAPITAL N
    "\u0276": "OE",  # LATIN LETTER SMALL CAPITAL OE
    "\u027c": "r",  # LATIN SMALL LETTER R WITH LONG LEG
    "\u027d": "r",  # LATIN SMALL LETTER R WITH TAIL
    "\u027e": "r",  # LATIN SMALL LETTER R WITH FISHHOOK
    "\u0280": "R",  # LATIN LETTER SMALL CAPITAL R
    "\u0282": "s",  # LATIN SMALL LETTER S WITH HOOK
    "\u0288": "t",  # LATIN SMALL LETTER T WITH RETROFLEX HOOK
    "\u0289": "u",  # LATIN SMALL LETTER U BAR
    "\u028b": "v",  # LATIN SMALL LETTER V WITH HOOK
    "\u028f": "Y",  # LATIN LETTER SMALL CAPITAL Y
    "\u0290": "z",  # LATIN SMALL LETTER Z WITH RETROFLEX HOOK
    "\u0291": "z",  # LATIN SMALL LETTER Z WITH CURL
    "\u0299": "B",  # LATIN LETTER SMALL CAPITAL B
    "\u029b": "G",  # LATIN LETTER SMALL CAPITAL G WITH HOOK
    "\u029c": "H",  # LATIN LETTER SMALL CAPITAL H
    "\u029d": "j",  # LATIN SMALL LETTER J WITH CROSSED-TAIL
    "\u029f": "L",  # LATIN LETTER SMALL CAPITAL L
    "\u02a0": "q",  # LATIN SMALL LETTER Q WITH HOOK
    "\u02a3": "dz",  # LATIN SMALL LETTER DZ DIGRAPH
    "\u02a5": "dz",  # LATIN SMALL LETTER DZ DIGRAPH WITH CURL
    "\u02a6": "ts",  # LATIN SMALL LETTER TS DIGRAPH
    "\u02aa": "ls",  # LATIN SMALL LETTER LS DIGRAPH
    "\u02ab": "lz",  # LATIN SMALL LETTER LZ DIGRAPH
    "\u1d01": "AE",  # LATIN LETTER SMALL CAPITAL AE
    "\u1d03": "B",  # LATIN LETTER SMALL CAPITAL BARRED B
    "\u1d06": "D",  # LATIN LETTER SMALL CAPITAL ETH
    "\u1d0c": "L",  # LATIN LETTER SMALL CAPITAL L WITH STROKE
    "\u1d6b": "ue",  # LATIN SMALL LETTER UE
    "\u1d6c": "b",  # LATIN SMALL LETTER B WITH MIDDLE TILDE
    "\u1d6d": "d",  # LATIN SMALL LETTER D WITH MIDDLE TILDE
    "\u1d6e": "f",  # LATIN SMALL LETTER F WITH MIDDLE TILDE
    "\u1d6f": "m",  # LATIN SMALL LETTER M WITH MIDDLE TILDE
    "\u1d70": "n",  # LATIN SMALL LETTER N WITH MIDDLE TILDE
    "\u1d71": "p",  # LATIN SMALL LETTER P WITH MIDDLE TILDE
    "\u1d72": "r",  # LATIN SMALL LETTER R WITH MIDDLE TILDE
    "\u1d73": "r",  # LATIN SMALL LETTER R WITH FISHHOOK AND MIDDLE TILDE
    "\u1d74": "s",  # LATIN SMALL LETTER S WITH MIDDLE TILDE
    "\u1d75": "t",  # LATIN SMALL LETTER T WITH MIDDLE TILDE
    "\u1d76": "z",  # LATIN SMALL LETTER Z WITH MIDDLE TILDE
    "\u1d7a": "th",  # LATIN SMALL LETTER TH WITH STRIKETHROUGH
    "\u1d7b": "I",  # LATIN SMALL CAPITAL LETTER I WITH STROKE
    "\u1d7d": "p",  # LATIN SMALL LETTER P WITH STROKE
    "\u1d7e": "U",  # LATIN SMALL CAPITAL LETTER U WITH STROKE
    "\u1d80": "b",  # LATIN SMALL LETTER B WITH PALATAL HOOK
    "\u1d81": "d",  # LATIN SMALL LETTER D WITH PALATAL HOOK
    "\u1d82": "f",  # LATIN SMALL LETTER F WITH PALATAL HOOK
    "\u1d83": "g",  # LATIN SMALL LETTER G WITH PALATAL HOOK
    "\u1d84": "k",  # LATIN SMALL LETTER K WITH PALATAL HOOK
    "\u1d85": "l",  # LATIN SMALL LETTER L WITH PALATAL HOOK
    "\u1d86": "m",  # LATIN SMALL LETTER M WITH PALATAL HOOK
    "\u1d87": "n",  # LATIN SMALL LETTER N WITH PALATAL HOOK
    "\u1d88": "p",  # LATIN SMALL LETTER P WITH PALATAL HOOK
    "\u1d89": "r",  # LATIN SMALL LETTER R WITH PALATAL HOOK
    "\u1d8a": "s",  # LATIN SMALL LETTER S WITH PALATAL HOOK
    "\u1d8c": "v",  # LATIN SMALL LETTER V WITH PALATAL HOOK
    "\u1d8d": "x",  # LATIN SMALL LETTER X WITH PALATAL HOOK
    "\u1d8e": "z",  # LATIN SMALL LETTER Z WITH PALATAL HOOK
    "\u1d8f": "a",  # LATIN SMALL LETTER A WITH RETROFLEX HOOK
    "\u1d91": "d",  # LATIN SMALL LETTER D WITH HOOK AND TAIL
    "\u1d92": "e",  # LATIN SMALL LETTER E WITH RETROFLEX HOOK
    "\u1d93": "e",  # LATIN SMALL LETTER OPEN E WITH RETROFLEX HOOK
    "\u1d96": "i",  # LATIN SMALL LETTER I WITH RETROFLEX HOOK
    "\u1d99": "u",  # LATIN SMALL LETTER U WITH RETROFLEX HOOK
    "\u1e9a": "a",  # LATIN SMALL LETTER A WITH RIGHT HALF RING
    "\u1e9c": "s",  # LATIN SMALL LETTER LONG S WITH DIAGONAL STROKE
    "\u1e9d": "s",  # LATIN SMALL LETTER LONG S WITH HIGH STROKE
    "\u1e9e": "SS",  # LATIN CAPITAL LETTER SHARP S
    "\u1efa": "LL",  # LATIN CAPITAL LETTER MIDDLE-WELSH LL
    "\u1efb": "ll",  # LATIN SMALL LETTER MIDDLE-WELSH LL
    "\u1efc": "V",  # LATIN CAPITAL LETTER MIDDLE-WELSH V
    "\u1efd": "v",  # LATIN SMALL LETTER MIDDLE-WELSH V
    "\u1efe": "Y",  # LATIN CAPITAL LETTER Y WITH LOOP
    "\u1eff": "y",  # LATIN SMALL LETTER Y WITH LOOP
    "\u00a9": "(C)",  # COPYRIGHT SIGN (from ‹character-fallback›)
    "\u00ae": "(R)",  # REGISTERED SIGN (from ‹character-fallback›)
    "\u20a0": "CE",  # EURO-CURRENCY SIGN (from ‹character-fallback›)
    "\u20a2": "Cr",  # CRUZEIRO SIGN (from ‹character-fallback›)
    "\u20a3": "Fr.",  # FRENCH FRANC SIGN (from ‹character-fallback›)
    "\u20a4": "L.",  # LIRA SIGN (from ‹character-fallback›)
    "\u20a7": "Pts",  # PESETA SIGN (from ‹character-fallback›)
    "\u20ba": "TL",  # TURKISH LIRA SIGN (from ‹character-fallback›)
    "\u20b9": "Rs",  # INDIAN RUPEE SIGN (from ‹character-fallback›)
    "\u211e": "Rx",  # PRESCRIPTION TAKE (from ‹character-fallback›)
    "\u33a7": "m/s",  # SQUARE M OVER S (compat) (from ‹character-fallback›)
    "\u33ae": "rad/s",  # SQUARE RAD OVER S (compat) (from ‹character-fallback›)
    "\u33c6": "C/kg",  # SQUARE C OVER KG (compat) (from ‹character-fallback›)
    "\u33de": "V/m",  # SQUARE V OVER M (compat) (from ‹character-fallback›)
    "\u33df": "A/m",  # SQUARE A OVER M (compat) (from ‹character-fallback›)
    "\u00bc": " 1/4",  # VULGAR FRACTION ONE QUARTER (from ‹character-fallback›)
    "\u00bd": " 1/2",  # VULGAR FRACTION ONE HALF (from ‹character-fallback›)
    "\u00be": " 3/4",  # VULGAR FRACTION THREE QUARTERS (from ‹character-fallback›)
    "\u2153": " 1/3",  # VULGAR FRACTION ONE THIRD (from ‹character-fallback›)
    "\u2154": " 2/3",  # VULGAR FRACTION TWO THIRDS (from ‹character-fallback›)
    "\u2155": " 1/5",  # VULGAR FRACTION ONE FIFTH (from ‹character-fallback›)
    "\u2156": " 2/5",  # VULGAR FRACTION TWO FIFTHS (from ‹character-fallback›)
    "\u2157": " 3/5",  # VULGAR FRACTION THREE FIFTHS (from ‹character-fallback›)
    "\u2158": " 4/5",  # VULGAR FRACTION FOUR FIFTHS (from ‹character-fallback›)
    "\u2159": " 1/6",  # VULGAR FRACTION ONE SIXTH (from ‹character-fallback›)
    "\u215a": " 5/6",  # VULGAR FRACTION FIVE SIXTHS (from ‹character-fallback›)
    "\u215b": " 1/8",  # VULGAR FRACTION ONE EIGHTH (from ‹character-fallback›)
    "\u215c": " 3/8",  # VULGAR FRACTION THREE EIGHTHS (from ‹character-fallback›)
    "\u215d": " 5/8",  # VULGAR FRACTION FIVE EIGHTHS (from ‹character-fallback›)
    "\u215e": " 7/8",  # VULGAR FRACTION SEVEN EIGHTHS (from ‹character-fallback›)
    "\u215f": " 1/",  # FRACTION NUMERATOR ONE (from ‹character-fallback›)
    "\u3001": ",",  # IDEOGRAPHIC COMMA
    "\u3002": ".",  # IDEOGRAPHIC FULL STOP
    "\u00d7": "x",  # MULTIPLICATION SIGN
    "\u00f7": "/",  # DIVISION SIGN
    "\u00b7": ".",  # MIDDLE DOT
    "\u1e9f": "dd",  # LATIN SMALL LETTER DELTA
    "\u0184": "H",  # LATIN CAPITAL LETTER TONE SIX
    "\u0185": "h",  # LATIN SMALL LETTER TONE SIX
    "\u01be": "ts",  # LATIN LETTER TS LIGATION (see http://unicode.org/notes/tn27/)
}


def _replace_unicode_simplify_combinations(char, pathsave, win_compat):
    result = _SIMPLIFY_COMBINATIONS.get(char)
    if result is None:
        return char
    elif not pathsave:
        return result
    else:
        return sanitize_filename(result, win_compat=win_compat)


def unicode_simplify_combinations(string, pathsave=False, win_compat=False):
    return ''.join(_replace_unicode_simplify_combinations(c, pathsave, win_compat) for c in string)


def unicode_simplify_accents(string):
    return ''.join(c for c in unicodedata.normalize('NFKD', string) if not unicodedata.combining(c))


def asciipunct(string):
    interim = unicode_simplify_compatibility(string)
    return unicode_simplify_punctuation(interim)


def unaccent(string):
    """Remove accents ``string``."""
    return unicode_simplify_accents(string)


def replace_non_ascii(string, repl="_", pathsave=False, win_compat=False):
    """Replace non-ASCII characters from ``string`` by ``repl``."""
    interim = unicode_simplify_combinations(string, pathsave, win_compat)
    interim = unicode_simplify_punctuation(interim, pathsave, win_compat)
    interim = unicode_simplify_compatibility(interim, pathsave, win_compat)
    interim = unicode_simplify_accents(interim)

    def error_repl(e, repl="_"):
        return (repl, e.start + 1)

    codecs.register_error('repl', partial(error_repl, repl=repl))
    # Decoding and encoding to allow replacements
    return interim.encode('ascii', 'repl').decode('ascii')


def _replace_char(mapping, ch, pathsave=False, win_compat=False):
    try:
        result = mapping[ch]
        if ch != result and pathsave:
            result = sanitize_filename(result, win_compat=win_compat)
        return result
    except KeyError:
        return ch
