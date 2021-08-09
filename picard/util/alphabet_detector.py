# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2015 Eli Finkelshteyn
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import unicodedata as ud
from collections import defaultdict


class AlphabetDetector:
    def __init__(self, no_memory=False):
        self.alphabet_letters = defaultdict(dict)
        self.no_memory = no_memory

    def is_in_alphabet(self, uchr, alphabet):
        if self.no_memory:
            return alphabet in ud.name(uchr)
        try:
            return self.alphabet_letters[alphabet][uchr]
        except KeyError:
            return self.alphabet_letters[alphabet].setdefault(
                uchr, alphabet in ud.name(uchr))

    def only_alphabet_chars(self, unistr, alphabet):
        return all(self.is_in_alphabet(uchr, alphabet)
                   for uchr in unistr if uchr.isalpha())

    def detect_alphabet(self, unistr):
        return set(ud.name(char).split(' ')[0]
                   for char in unistr if char.isalpha())

    def is_greek(self, unistr):
        return self.only_alphabet_chars(unistr, 'GREEK')

    def is_cyrillic(self, unistr):
        return self.only_alphabet_chars(unistr, 'CYRILLIC')

    def is_latin(self, unistr):
        return self.only_alphabet_chars(unistr, 'LATIN')

    def is_arabic(self, unistr):
        return True if self.only_alphabet_chars(unistr, 'ARABIC') else False

    def is_hebrew(self, unistr):
        return self.only_alphabet_chars(unistr, 'HEBREW')

    # NOTE: this only detects Chinese script characters (Hanzi/Kanji/Hanja).
    # it does not detect other CJK script characters like Hangul or Katakana
    def is_cjk(self, unistr):
        return True if self.only_alphabet_chars(unistr, 'CJK') else False

    def is_hangul(self, unistr):
        return True if self.only_alphabet_chars(unistr, 'HANGUL') else False

    def is_hiragana(self, unistr):
        return self.only_alphabet_chars(unistr, 'HIRAGANA')

    def is_katakana(self, unistr):
        return self.only_alphabet_chars(unistr, 'KATAKANA')

    def is_thai(self, unistr):
        return True if self.only_alphabet_chars(unistr, 'THAI') else False
