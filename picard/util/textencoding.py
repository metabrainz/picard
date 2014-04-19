# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006 Lukáš Lalinský
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

import re
import unicodedata
import codecs
from functools import partial

#########################  LATIN SIMPLIFICATION ###########################
# The translation tables for punctuation and latin combined-characters are taken from
# http://unicode.org/repos/cldr/trunk/common/transforms/Latin-ASCII.xml
# Various bugs and mistakes in this have been ironed out during testing.


def _re_any(iterable):
    return re.compile('([' + ''.join(iterable) + '])', re.UNICODE)

_additional_compatibility = {
    u"\u0276": u"Œ",  # LATIN LETTER SMALL CAPITAL OE
    u"\u1D00": u"A",  # LATIN LETTER SMALL CAPITAL A
    u"\u1D01": u"Æ",  # LATIN LETTER SMALL CAPITAL AE
    u"\u1D04": u"C",  # LATIN LETTER SMALL CAPITAL C
    u"\u1D05": u"D",  # LATIN LETTER SMALL CAPITAL D
    u"\u1D07": u"E",  # LATIN LETTER SMALL CAPITAL E
    u"\u1D0A": u"J",  # LATIN LETTER SMALL CAPITAL J
    u"\u1D0B": u"K",  # LATIN LETTER SMALL CAPITAL K
    u"\u1D0D": u"M",  # LATIN LETTER SMALL CAPITAL M
    u"\u1D0F": u"O",  # LATIN LETTER SMALL CAPITAL O
    u"\u1D18": u"P",  # LATIN LETTER SMALL CAPITAL P
    u"\u1D1B": u"T",  # LATIN LETTER SMALL CAPITAL T
    u"\u1D1C": u"U",  # LATIN LETTER SMALL CAPITAL U
    u"\u1D20": u"V",  # LATIN LETTER SMALL CAPITAL V
    u"\u1D21": u"W",  # LATIN LETTER SMALL CAPITAL W
    u"\u1D22": u"Z",  # LATIN LETTER SMALL CAPITAL Z
    u"\u3007": u"0",  # IDEOGRAPHIC NUMBER ZERO
    u"\u00A0": u" ",  # NO-BREAK SPACE
    u"\u3000": u" ",  # IDEOGRAPHIC SPACE (from ‹character-fallback›)
    u"\u2033": u"”",  # DOUBLE PRIME
}
_re_additional_compatibility = _re_any(_additional_compatibility.keys())


def unicode_simplify_compatibility(string):
    interim = _re_additional_compatibility.sub(lambda m: _additional_compatibility[m.group(0)], string)
    return unicodedata.normalize("NFKC", interim)


_simplify_punctuation = {
    u"\u013F": u"L",  # LATIN CAPITAL LETTER L WITH MIDDLE DOT (compat)
    u"\u0140": u"l",  # LATIN SMALL LETTER L WITH MIDDLE DOT (compat)
    u"\u2018": u"'",  # LEFT SINGLE QUOTATION MARK (from ‹character-fallback›)
    u"\u2019": u"'",  # RIGHT SINGLE QUOTATION MARK (from ‹character-fallback›)
    u"\u201A": u"'",  # SINGLE LOW-9 QUOTATION MARK (from ‹character-fallback›)
    u"\u201B": u"'",  # SINGLE HIGH-REVERSED-9 QUOTATION MARK (from ‹character-fallback›)
    u"\u201C": u"\"",  # LEFT DOUBLE QUOTATION MARK (from ‹character-fallback›)
    u"\u201D": u"\"",  # RIGHT DOUBLE QUOTATION MARK (from ‹character-fallback›)
    u"\u201E": u"\"",  # DOUBLE LOW-9 QUOTATION MARK (from ‹character-fallback›)
    u"\u201F": u"\"",  # DOUBLE HIGH-REVERSED-9 QUOTATION MARK (from ‹character-fallback›)
    u"\u2032": u"'",  # PRIME
    u"\u2033": u"\"",  # DOUBLE PRIME
    u"\u301D": u"\"",  # REVERSED DOUBLE PRIME QUOTATION MARK
    u"\u301E": u"\"",  # DOUBLE PRIME QUOTATION MARK
    u"\u00AB": u"<<",  # LEFT-POINTING DOUBLE ANGLE QUOTATION MARK (from ‹character-fallback›)
    u"\u00BB": u">>",  # RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK (from ‹character-fallback›)
    u"\u2039": u"<",  # SINGLE LEFT-POINTING ANGLE QUOTATION MARK
    u"\u203A": u">",  # SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
    u"\u00AD": u"",  # SOFT HYPHEN (from ‹character-fallback›)
    u"\u2010": u"-",  # HYPHEN (from ‹character-fallback›)
    u"\u2011": u"-",  # NON-BREAKING HYPHEN (from ‹character-fallback›)
    u"\u2012": u"-",  # FIGURE DASH (from ‹character-fallback›)
    u"\u2013": u"-",  # EN DASH (from ‹character-fallback›)
    u"\u2014": u"-",  # EM DASH (from ‹character-fallback›)
    u"\u2015": u"-",  # HORIZONTAL BAR (from ‹character-fallback›)
    u"\uFE31": u"|",  # PRESENTATION FORM FOR VERTICAL EM DASH (compat)
    u"\uFE32": u"|",  # PRESENTATION FORM FOR VERTICAL EN DASH (compat)
    u"\uFE58": u"-",  # SMALL EM DASH (compat)
    u"\u2016": u"||",  # DOUBLE VERTICAL LINE
    u"\u2044": u"/",  # FRACTION SLASH (from ‹character-fallback›)
    u"\u2045": u"[",  # LEFT SQUARE BRACKET WITH QUILL
    u"\u2046": u"]",  # RIGHT SQUARE BRACKET WITH QUILL
    u"\u204E": u"*",  # LOW ASTERISK
    u"\u3008": u"<",  # LEFT ANGLE BRACKET
    u"\u3009": u">",  # RIGHT ANGLE BRACKET
    u"\u300A": u"<<",  # LEFT DOUBLE ANGLE BRACKET
    u"\u300B": u">>",  # RIGHT DOUBLE ANGLE BRACKET
    u"\u3014": u"[",  # LEFT TORTOISE SHELL BRACKET
    u"\u3015": u"]",  # RIGHT TORTOISE SHELL BRACKET
    u"\u3018": u"[",  # LEFT WHITE TORTOISE SHELL BRACKET
    u"\u3019": u"]",  # RIGHT WHITE TORTOISE SHELL BRACKET
    u"\u301A": u"[",  # LEFT WHITE SQUARE BRACKET
    u"\u301B": u"]",  # RIGHT WHITE SQUARE BRACKET
    u"\uFE11": u",",  # PRESENTATION FORM FOR VERTICAL IDEOGRAPHIC COMMA (compat)
    u"\uFE12": u".",  # PRESENTATION FORM FOR VERTICAL IDEOGRAPHIC FULL STOP (compat)
    u"\uFE39": u"[",  # PRESENTATION FORM FOR VERTICAL LEFT TORTOISE SHELL BRACKET (compat)
    u"\uFE3A": u"]",  # PRESENTATION FORM FOR VERTICAL RIGHT TORTOISE SHELL BRACKET (compat)
    u"\uFE3D": u"<<",  # PRESENTATION FORM FOR VERTICAL LEFT DOUBLE ANGLE BRACKET (compat)
    u"\uFE3E": u">>",  # PRESENTATION FORM FOR VERTICAL RIGHT DOUBLE ANGLE BRACKET (compat)
    u"\uFE3F": u"<",  # PRESENTATION FORM FOR VERTICAL LEFT ANGLE BRACKET (compat)
    u"\uFE40": u">",  # PRESENTATION FORM FOR VERTICAL RIGHT ANGLE BRACKET (compat)
    u"\uFE51": u",",  # SMALL IDEOGRAPHIC COMMA (compat)
    u"\uFE5D": u"[",  # SMALL LEFT TORTOISE SHELL BRACKET (compat)
    u"\uFE5E": u"]",  # SMALL RIGHT TORTOISE SHELL BRACKET (compat)
    u"\uFF5F": u"((",  # FULLWIDTH LEFT WHITE PARENTHESIS (compat)(from ‹character-fallback›)
    u"\uFF60": u"))",  # FULLWIDTH RIGHT WHITE PARENTHESIS (compat)(from ‹character-fallback›)
    u"\uFF61": u".",  # HALFWIDTH IDEOGRAPHIC FULL STOP (compat)
    u"\uFF64": u",",  # HALFWIDTH IDEOGRAPHIC COMMA (compat)
    u"\u2212": u"-",  # MINUS SIGN (from ‹character-fallback›)
    u"\u2215": u"/",  # DIVISION SLASH (from ‹character-fallback›)
    u"\u2216": u"\\",  # SET MINUS (from ‹character-fallback›)
    u"\u2223": u"|",  # DIVIDES (from ‹character-fallback›)
    u"\u2225": u"||",  # PARALLEL TO (from ‹character-fallback›)
    u"\u226A": u"<<",  # MUCH LESS-THAN
    u"\u226B": u">>",  # MUCH GREATER-THAN
    u"\u2985": u"((",  # LEFT WHITE PARENTHESIS
    u"\u2986": u"))",  # RIGHT WHITE PARENTHESIS
    u"\u200B": u"",  # Zero Width Space
}
_re_simplify_punctuation = _re_any(_simplify_punctuation.keys())


def unicode_simplify_punctuation(string):
    return _re_simplify_punctuation.sub(lambda m: _simplify_punctuation[m.group(0)], string)


_simplify_combinations = {
    u"\u00C6": u"AE",  # LATIN CAPITAL LETTER AE (from ‹character-fallback›)
    u"\u00D0": u"D",  # LATIN CAPITAL LETTER ETH
    u"\u00D8": u"OE",  # LATIN CAPITAL LETTER O WITH STROKE (see https://en.wikipedia.org/wiki/%C3%98)
    u"\u00DE": u"TH",  # LATIN CAPITAL LETTER THORN
    u"\u00DF": u"ss",  # LATIN SMALL LETTER SHARP S (from ‹character-fallback›)
    u"\u00E6": u"ae",  # LATIN SMALL LETTER AE (from ‹character-fallback›)
    u"\u00F0": u"d",  # LATIN SMALL LETTER ETH
    u"\u00F8": u"oe",  # LATIN SMALL LETTER O WITH STROKE (see https://en.wikipedia.org/wiki/%C3%98)
    u"\u00FE": u"th",  # LATIN SMALL LETTER THORN
    u"\u0110": u"D",  # LATIN CAPITAL LETTER D WITH STROKE
    u"\u0111": u"d",  # LATIN SMALL LETTER D WITH STROKE
    u"\u0126": u"H",  # LATIN CAPITAL LETTER H WITH STROKE
    u"\u0127": u"h",  # LATIN CAPITAL LETTER H WITH STROKE
    u"\u0131": u"i",  # LATIN SMALL LETTER DOTLESS I
    u"\u0138": u"q",  # LATIN SMALL LETTER KRA (collates with q in DUCET)
    u"\u0141": u"L",  # LATIN CAPITAL LETTER L WITH STROKE
    u"\u0142": u"l",  # LATIN SMALL LETTER L WITH STROKE
    u"\u0149": u"'n",  # LATIN SMALL LETTER N PRECEDED BY APOSTROPHE (from ‹character-fallback›)
    u"\u014A": u"N",  # LATIN CAPITAL LETTER ENG
    u"\u014B": u"n",  # LATIN SMALL LETTER ENG
    u"\u0152": u"OE",  # LATIN CAPITAL LIGATURE OE (from ‹character-fallback›)
    u"\u0153": u"oe",  # LATIN SMALL LIGATURE OE (from ‹character-fallback›)
    u"\u0166": u"T",  # LATIN CAPITAL LETTER T WITH STROKE
    u"\u0167": u"t",  # LATIN SMALL LETTER T WITH STROKE
    u"\u0180": u"b",  # LATIN SMALL LETTER B WITH STROKE
    u"\u0181": u"B",  # LATIN CAPITAL LETTER B WITH HOOK
    u"\u0182": u"B",  # LATIN CAPITAL LETTER B WITH TOPBAR
    u"\u0183": u"b",  # LATIN SMALL LETTER B WITH TOPBAR
    u"\u0187": u"C",  # LATIN CAPITAL LETTER C WITH HOOK
    u"\u0188": u"c",  # LATIN SMALL LETTER C WITH HOOK
    u"\u0189": u"D",  # LATIN CAPITAL LETTER AFRICAN D
    u"\u018A": u"D",  # LATIN CAPITAL LETTER D WITH HOOK
    u"\u018B": u"D",  # LATIN CAPITAL LETTER D WITH TOPBAR
    u"\u018C": u"d",  # LATIN SMALL LETTER D WITH TOPBAR
    u"\u0190": u"E",  # LATIN CAPITAL LETTER OPEN E
    u"\u0191": u"F",  # LATIN CAPITAL LETTER F WITH HOOK
    u"\u0192": u"f",  # LATIN SMALL LETTER F WITH HOOK
    u"\u0193": u"G",  # LATIN CAPITAL LETTER G WITH HOOK
    u"\u0195": u"hv",  # LATIN SMALL LETTER HV
    u"\u0196": u"I",  # LATIN CAPITAL LETTER IOTA
    u"\u0197": u"I",  # LATIN CAPITAL LETTER I WITH STROKE
    u"\u0198": u"K",  # LATIN CAPITAL LETTER K WITH HOOK
    u"\u0199": u"k",  # LATIN SMALL LETTER K WITH HOOK
    u"\u019A": u"l",  # LATIN SMALL LETTER L WITH BAR
    u"\u019D": u"N",  # LATIN CAPITAL LETTER N WITH LEFT HOOK
    u"\u019E": u"n",  # LATIN SMALL LETTER N WITH LONG RIGHT LEG
    u"\u01A2": u"GH",  # LATIN CAPITAL LETTER GHA (see http://unicode.org/notes/tn27/)
    u"\u01A3": u"gh",  # LATIN SMALL LETTER GHA (see http://unicode.org/notes/tn27/)
    u"\u01A4": u"P",  # LATIN CAPITAL LETTER P WITH HOOK
    u"\u01A5": u"p",  # LATIN SMALL LETTER P WITH HOOK
    u"\u01AB": u"t",  # LATIN SMALL LETTER T WITH PALATAL HOOK
    u"\u01AC": u"T",  # LATIN CAPITAL LETTER T WITH HOOK
    u"\u01AD": u"t",  # LATIN SMALL LETTER T WITH HOOK
    u"\u01AE": u"T",  # LATIN CAPITAL LETTER T WITH RETROFLEX HOOK
    u"\u01B2": u"V",  # LATIN CAPITAL LETTER V WITH HOOK
    u"\u01B3": u"Y",  # LATIN CAPITAL LETTER Y WITH HOOK
    u"\u01B4": u"y",  # LATIN SMALL LETTER Y WITH HOOK
    u"\u01B5": u"Z",  # LATIN CAPITAL LETTER Z WITH STROKE
    u"\u01B6": u"z",  # LATIN SMALL LETTER Z WITH STROKE
    u"\u01C4": u"DZ",  # LATIN CAPITAL LETTER DZ WITH CARON (compat)
    u"\u01C5": u"Dz",  # LATIN CAPITAL LETTER D WITH SMALL LETTER Z WITH CARON (compat)
    u"\u01C6": u"dz",  # LATIN SMALL LETTER DZ WITH CARON (compat)
    u"\u01E4": u"G",  # LATIN CAPITAL LETTER G WITH STROKE
    u"\u01E5": u"g",  # LATIN SMALL LETTER G WITH STROKE
    u"\u0221": u"d",  # LATIN SMALL LETTER D WITH CURL
    u"\u0224": u"Z",  # LATIN CAPITAL LETTER Z WITH HOOK
    u"\u0225": u"z",  # LATIN SMALL LETTER Z WITH HOOK
    u"\u0234": u"l",  # LATIN SMALL LETTER L WITH CURL
    u"\u0235": u"n",  # LATIN SMALL LETTER N WITH CURL
    u"\u0236": u"t",  # LATIN SMALL LETTER T WITH CURL
    u"\u0237": u"j",  # LATIN SMALL LETTER DOTLESS J
    u"\u0238": u"db",  # LATIN SMALL LETTER DB DIGRAPH
    u"\u0239": u"qp",  # LATIN SMALL LETTER QP DIGRAPH
    u"\u023A": u"A",  # LATIN CAPITAL LETTER A WITH STROKE
    u"\u023B": u"C",  # LATIN CAPITAL LETTER C WITH STROKE
    u"\u023C": u"c",  # LATIN SMALL LETTER C WITH STROKE
    u"\u023D": u"L",  # LATIN CAPITAL LETTER L WITH BAR
    u"\u023E": u"T",  # LATIN CAPITAL LETTER T WITH DIAGONAL STROKE
    u"\u023F": u"s",  # LATIN SMALL LETTER S WITH SWASH TAIL
    u"\u0240": u"z",  # LATIN SMALL LETTER Z WITH SWASH TAIL
    u"\u0243": u"B",  # LATIN CAPITAL LETTER B WITH STROKE
    u"\u0244": u"U",  # LATIN CAPITAL LETTER U BAR
    u"\u0246": u"E",  # LATIN CAPITAL LETTER E WITH STROKE
    u"\u0247": u"e",  # LATIN SMALL LETTER E WITH STROKE
    u"\u0248": u"J",  # LATIN CAPITAL LETTER J WITH STROKE
    u"\u0249": u"j",  # LATIN SMALL LETTER J WITH STROKE
    u"\u024C": u"R",  # LATIN CAPITAL LETTER R WITH STROKE
    u"\u024D": u"r",  # LATIN SMALL LETTER R WITH STROKE
    u"\u024E": u"Y",  # LATIN CAPITAL LETTER Y WITH STROKE
    u"\u024F": u"y",  # LATIN SMALL LETTER Y WITH STROKE
    u"\u0253": u"b",  # LATIN SMALL LETTER B WITH HOOK
    u"\u0255": u"c",  # LATIN SMALL LETTER C WITH CURL
    u"\u0256": u"d",  # LATIN SMALL LETTER D WITH TAIL
    u"\u0257": u"d",  # LATIN SMALL LETTER D WITH HOOK
    u"\u025B": u"e",  # LATIN SMALL LETTER OPEN E
    u"\u025F": u"j",  # LATIN SMALL LETTER DOTLESS J WITH STROKE
    u"\u0260": u"g",  # LATIN SMALL LETTER G WITH HOOK
    u"\u0261": u"g",  # LATIN SMALL LETTER SCRIPT G
    u"\u0262": u"G",  # LATIN LETTER SMALL CAPITAL G
    u"\u0266": u"h",  # LATIN SMALL LETTER H WITH HOOK
    u"\u0267": u"h",  # LATIN SMALL LETTER HENG WITH HOOK
    u"\u0268": u"i",  # LATIN SMALL LETTER I WITH STROKE
    u"\u026A": u"I",  # LATIN LETTER SMALL CAPITAL I
    u"\u026B": u"l",  # LATIN SMALL LETTER L WITH MIDDLE TILDE
    u"\u026C": u"l",  # LATIN SMALL LETTER L WITH BELT
    u"\u026D": u"l",  # LATIN SMALL LETTER L WITH RETROFLEX HOOK
    u"\u0271": u"m",  # LATIN SMALL LETTER M WITH HOOK
    u"\u0272": u"n",  # LATIN SMALL LETTER N WITH LEFT HOOK
    u"\u0273": u"n",  # LATIN SMALL LETTER N WITH RETROFLEX HOOK
    u"\u0274": u"N",  # LATIN LETTER SMALL CAPITAL N
    u"\u0276": u"OE",  # LATIN LETTER SMALL CAPITAL OE
    u"\u027C": u"r",  # LATIN SMALL LETTER R WITH LONG LEG
    u"\u027D": u"r",  # LATIN SMALL LETTER R WITH TAIL
    u"\u027E": u"r",  # LATIN SMALL LETTER R WITH FISHHOOK
    u"\u0280": u"R",  # LATIN LETTER SMALL CAPITAL R
    u"\u0282": u"s",  # LATIN SMALL LETTER S WITH HOOK
    u"\u0288": u"t",  # LATIN SMALL LETTER T WITH RETROFLEX HOOK
    u"\u0289": u"u",  # LATIN SMALL LETTER U BAR
    u"\u028B": u"v",  # LATIN SMALL LETTER V WITH HOOK
    u"\u028F": u"Y",  # LATIN LETTER SMALL CAPITAL Y
    u"\u0290": u"z",  # LATIN SMALL LETTER Z WITH RETROFLEX HOOK
    u"\u0291": u"z",  # LATIN SMALL LETTER Z WITH CURL
    u"\u0299": u"B",  # LATIN LETTER SMALL CAPITAL B
    u"\u029B": u"G",  # LATIN LETTER SMALL CAPITAL G WITH HOOK
    u"\u029C": u"H",  # LATIN LETTER SMALL CAPITAL H
    u"\u029D": u"j",  # LATIN SMALL LETTER J WITH CROSSED-TAIL
    u"\u029F": u"L",  # LATIN LETTER SMALL CAPITAL L
    u"\u02A0": u"q",  # LATIN SMALL LETTER Q WITH HOOK
    u"\u02A3": u"dz",  # LATIN SMALL LETTER DZ DIGRAPH
    u"\u02A5": u"dz",  # LATIN SMALL LETTER DZ DIGRAPH WITH CURL
    u"\u02A6": u"ts",  # LATIN SMALL LETTER TS DIGRAPH
    u"\u02AA": u"ls",  # LATIN SMALL LETTER LS DIGRAPH
    u"\u02AB": u"lz",  # LATIN SMALL LETTER LZ DIGRAPH
    u"\u1D01": u"AE",  # LATIN LETTER SMALL CAPITAL AE
    u"\u1D03": u"B",  # LATIN LETTER SMALL CAPITAL BARRED B
    u"\u1D06": u"D",  # LATIN LETTER SMALL CAPITAL ETH
    u"\u1D0C": u"L",  # LATIN LETTER SMALL CAPITAL L WITH STROKE
    u"\u1D6B": u"ue",  # LATIN SMALL LETTER UE
    u"\u1D6C": u"b",  # LATIN SMALL LETTER B WITH MIDDLE TILDE
    u"\u1D6D": u"d",  # LATIN SMALL LETTER D WITH MIDDLE TILDE
    u"\u1D6E": u"f",  # LATIN SMALL LETTER F WITH MIDDLE TILDE
    u"\u1D6F": u"m",  # LATIN SMALL LETTER M WITH MIDDLE TILDE
    u"\u1D70": u"n",  # LATIN SMALL LETTER N WITH MIDDLE TILDE
    u"\u1D71": u"p",  # LATIN SMALL LETTER P WITH MIDDLE TILDE
    u"\u1D72": u"r",  # LATIN SMALL LETTER R WITH MIDDLE TILDE
    u"\u1D73": u"r",  # LATIN SMALL LETTER R WITH FISHHOOK AND MIDDLE TILDE
    u"\u1D74": u"s",  # LATIN SMALL LETTER S WITH MIDDLE TILDE
    u"\u1D75": u"t",  # LATIN SMALL LETTER T WITH MIDDLE TILDE
    u"\u1D76": u"z",  # LATIN SMALL LETTER Z WITH MIDDLE TILDE
    u"\u1D7A": u"th",  # LATIN SMALL LETTER TH WITH STRIKETHROUGH
    u"\u1D7B": u"I",  # LATIN SMALL CAPITAL LETTER I WITH STROKE
    u"\u1D7D": u"p",  # LATIN SMALL LETTER P WITH STROKE
    u"\u1D7E": u"U",  # LATIN SMALL CAPITAL LETTER U WITH STROKE
    u"\u1D80": u"b",  # LATIN SMALL LETTER B WITH PALATAL HOOK
    u"\u1D81": u"d",  # LATIN SMALL LETTER D WITH PALATAL HOOK
    u"\u1D82": u"f",  # LATIN SMALL LETTER F WITH PALATAL HOOK
    u"\u1D83": u"g",  # LATIN SMALL LETTER G WITH PALATAL HOOK
    u"\u1D84": u"k",  # LATIN SMALL LETTER K WITH PALATAL HOOK
    u"\u1D85": u"l",  # LATIN SMALL LETTER L WITH PALATAL HOOK
    u"\u1D86": u"m",  # LATIN SMALL LETTER M WITH PALATAL HOOK
    u"\u1D87": u"n",  # LATIN SMALL LETTER N WITH PALATAL HOOK
    u"\u1D88": u"p",  # LATIN SMALL LETTER P WITH PALATAL HOOK
    u"\u1D89": u"r",  # LATIN SMALL LETTER R WITH PALATAL HOOK
    u"\u1D8A": u"s",  # LATIN SMALL LETTER S WITH PALATAL HOOK
    u"\u1D8C": u"v",  # LATIN SMALL LETTER V WITH PALATAL HOOK
    u"\u1D8D": u"x",  # LATIN SMALL LETTER X WITH PALATAL HOOK
    u"\u1D8E": u"z",  # LATIN SMALL LETTER Z WITH PALATAL HOOK
    u"\u1D8F": u"a",  # LATIN SMALL LETTER A WITH RETROFLEX HOOK
    u"\u1D91": u"d",  # LATIN SMALL LETTER D WITH HOOK AND TAIL
    u"\u1D92": u"e",  # LATIN SMALL LETTER E WITH RETROFLEX HOOK
    u"\u1D93": u"e",  # LATIN SMALL LETTER OPEN E WITH RETROFLEX HOOK
    u"\u1D96": u"i",  # LATIN SMALL LETTER I WITH RETROFLEX HOOK
    u"\u1D99": u"u",  # LATIN SMALL LETTER U WITH RETROFLEX HOOK
    u"\u1E9A": u"a",  # LATIN SMALL LETTER A WITH RIGHT HALF RING
    u"\u1E9C": u"s",  # LATIN SMALL LETTER LONG S WITH DIAGONAL STROKE
    u"\u1E9D": u"s",  # LATIN SMALL LETTER LONG S WITH HIGH STROKE
    u"\u1E9E": u"SS",  # LATIN CAPITAL LETTER SHARP S
    u"\u1EFA": u"LL",  # LATIN CAPITAL LETTER MIDDLE-WELSH LL
    u"\u1EFB": u"ll",  # LATIN SMALL LETTER MIDDLE-WELSH LL
    u"\u1EFC": u"V",  # LATIN CAPITAL LETTER MIDDLE-WELSH V
    u"\u1EFD": u"v",  # LATIN SMALL LETTER MIDDLE-WELSH V
    u"\u1EFE": u"Y",  # LATIN CAPITAL LETTER Y WITH LOOP
    u"\u1EFF": u"y",  # LATIN SMALL LETTER Y WITH LOOP
    u"\u00A9": u"(C)",  # COPYRIGHT SIGN (from ‹character-fallback›)
    u"\u00AE": u"(R)",  # REGISTERED SIGN (from ‹character-fallback›)
    u"\u20A0": u"CE",  # EURO-CURRENCY SIGN (from ‹character-fallback›)
    u"\u20A2": u"Cr",  # CRUZEIRO SIGN (from ‹character-fallback›)
    u"\u20A3": u"Fr.",  # FRENCH FRANC SIGN (from ‹character-fallback›)
    u"\u20A4": u"L.",  # LIRA SIGN (from ‹character-fallback›)
    u"\u20A7": u"Pts",  # PESETA SIGN (from ‹character-fallback›)
    u"\u20BA": u"TL",  # TURKISH LIRA SIGN (from ‹character-fallback›)
    u"\u20B9": u"Rs",  # INDIAN RUPEE SIGN (from ‹character-fallback›)
    u"\u211E": u"Rx",  # PRESCRIPTION TAKE (from ‹character-fallback›)
    u"\u33A7": u"m/s",  # SQUARE M OVER S (compat) (from ‹character-fallback›)
    u"\u33AE": u"rad/s",  # SQUARE RAD OVER S (compat) (from ‹character-fallback›)
    u"\u33C6": u"C/kg",  # SQUARE C OVER KG (compat) (from ‹character-fallback›)
    u"\u33DE": u"V/m",  # SQUARE V OVER M (compat) (from ‹character-fallback›)
    u"\u33DF": u"A/m",  # SQUARE A OVER M (compat) (from ‹character-fallback›)
    u"\u00BC": u" 1/4",  # VULGAR FRACTION ONE QUARTER (from ‹character-fallback›)
    u"\u00BD": u" 1/2",  # VULGAR FRACTION ONE HALF (from ‹character-fallback›)
    u"\u00BE": u" 3/4",  # VULGAR FRACTION THREE QUARTERS (from ‹character-fallback›)
    u"\u2153": u" 1/3",  # VULGAR FRACTION ONE THIRD (from ‹character-fallback›)
    u"\u2154": u" 2/3",  # VULGAR FRACTION TWO THIRDS (from ‹character-fallback›)
    u"\u2155": u" 1/5",  # VULGAR FRACTION ONE FIFTH (from ‹character-fallback›)
    u"\u2156": u" 2/5",  # VULGAR FRACTION TWO FIFTHS (from ‹character-fallback›)
    u"\u2157": u" 3/5",  # VULGAR FRACTION THREE FIFTHS (from ‹character-fallback›)
    u"\u2158": u" 4/5",  # VULGAR FRACTION FOUR FIFTHS (from ‹character-fallback›)
    u"\u2159": u" 1/6",  # VULGAR FRACTION ONE SIXTH (from ‹character-fallback›)
    u"\u215A": u" 5/6",  # VULGAR FRACTION FIVE SIXTHS (from ‹character-fallback›)
    u"\u215B": u" 1/8",  # VULGAR FRACTION ONE EIGHTH (from ‹character-fallback›)
    u"\u215C": u" 3/8",  # VULGAR FRACTION THREE EIGHTHS (from ‹character-fallback›)
    u"\u215D": u" 5/8",  # VULGAR FRACTION FIVE EIGHTHS (from ‹character-fallback›)
    u"\u215E": u" 7/8",  # VULGAR FRACTION SEVEN EIGHTHS (from ‹character-fallback›)
    u"\u215F": u" 1/",  # FRACTION NUMERATOR ONE (from ‹character-fallback›)
    u"\u3001": u",",  # IDEOGRAPHIC COMMA
    u"\u3002": u".",  # IDEOGRAPHIC FULL STOP
    u"\u00D7": u"x",  # MULTIPLICATION SIGN
    u"\u00F7": u"/",  # DIVISION SIGN
    u"\u00B7": u".",  # MIDDLE DOT
    u"\u1E9F": u"dd",  # LATIN SMALL LETTER DELTA
    u"\u0184": u"H",  # LATIN CAPITAL LETTER TONE SIX
    u"\u0185": u"h",  # LATIN SMALL LETTER TONE SIX
    u"\u01BE": u"ts",  # LATIN LETTER TS LIGATION (see http://unicode.org/notes/tn27/)
}
_re_simplify_combinations = _re_any(_simplify_combinations)


def unicode_simplify_combinations(string):
    return _re_simplify_combinations.sub(lambda m: _simplify_combinations[m.group(0)], string)


def unicode_simplify_accents(string):
    result = ''.join(c for c in unicodedata.normalize('NFKD', string) if not unicodedata.combining(c))
    return result


def asciipunct(string):
    interim = unicode_simplify_compatibility(string)
    return unicode_simplify_punctuation(interim)


def unaccent(string):
    """Remove accents ``string``."""
    return unicode_simplify_accents(string)


def replace_non_ascii(string, repl="_"):
    """Replace non-ASCII characters from ``string`` by ``repl``."""
    interim = unicode_simplify_combinations(string)
    interim = unicode_simplify_accents(interim)
    interim = unicode_simplify_punctuation(interim)
    interim = unicode_simplify_compatibility(interim)

    def error_repl(e, repl=u"_"):
        return(repl, e.start + 1)
    codecs.register_error('repl', partial(error_repl, repl=unicode(repl)))

    return interim.encode('ascii', 'repl')
