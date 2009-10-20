# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2009 Carlin Mangar
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
#
# THIS FILE MAKES USE OF:
# titlecase.py v0.2
# Original Perl version by: John Gruber http://daringfireball.net/ 10 May 2008
# Python version by Stuart Colville http://muffinresearch.co.uk
# License: http://www.opensource.org/licenses/mit-license.php
#
# The MIT License
#
# Copyright (c) 2008 John Gruber, Stuart Colville

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
#
# Source Code: https://launchpad.net/titlecase.py/trunk/0.2

PLUGIN_NAME = "Advanced Title Case for Picard"
PLUGIN_AUTHOR = "Carlin Mangar, John Gruber, Stuart Colville"
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.9", "0.10", "0.11", "0.12"]
PLUGIN_DESCRIPTION = "This plugin changes all words in title, album and artist to Title Case according \
                        to the New York Times Manual of Style. Read Source code"

import sys
import re
import unicodedata
from picard.metadata import (
    register_track_metadata_processor,
    register_album_metadata_processor,
    )

SMALL = 'a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?'
PUNCT = "[!\"#$%&'â€˜()*+,-./:;?@[\\\\\\]_`{|}~]"

SMALL_WORDS = re.compile(r'^(%s)$' % SMALL, re.I)
INLINE_PERIOD = re.compile(r'[a-zA-Z][.][a-zA-Z]')
UC_ELSEWHERE = re.compile(r'%s*?[a-zA-Z]+[A-Z]+?' % PUNCT)
CAPFIRST = re.compile(r"^%s*?([A-Za-z])" % PUNCT)
SMALL_FIRST = re.compile(r'^(%s*)(%s)\b' % (PUNCT, SMALL), re.I)
SMALL_LAST = re.compile(r'\b(%s)%s?$' % (SMALL, PUNCT), re.I)
SUBPHRASE = re.compile(r'([:.;?!][ ])(%s)' % SMALL)

def titlecase(text):

    """
    Titlecases input text

    This filter changes all words to Title Caps, and attempts to be clever
    about *un*capitalizing SMALL words like a/an/the in the input.

    The list of "SMALL words" which are not capped comes from
    the New York Times Manual of Style, plus 'vs' and 'v'.

    """

    words = re.split('\s', text)
    line = []
    for word in words:
        if INLINE_PERIOD.search(word) or UC_ELSEWHERE.match(word):
            line.append(word)
            continue
        if SMALL_WORDS.match(word):
            line.append(word.lower())
            continue
        line.append(CAPFIRST.sub(lambda m: m.group(0).upper(), word))

    line = " ".join(line)

    line = SMALL_FIRST.sub(lambda m: '%s%s' % (
        m.group(1),
        m.group(2).capitalize()
    ), line)

    line = SMALL_LAST.sub(lambda m: m.group(0).capitalize(), line)

    line = SUBPHRASE.sub(lambda m: '%s%s' % (
        m.group(1),
        m.group(2).capitalize()
    ), line)

    return line


def nx_title_case(tagger, metadata, release, track=None):
    for name, value in metadata.rawitems():
        if name in ["title", "album", "artist"]:
            metadata[name] = [titlecase(x) for x in value]

register_track_metadata_processor(nx_title_case)
register_album_metadata_processor(nx_title_case)
