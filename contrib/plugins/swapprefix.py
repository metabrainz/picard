# -*- coding: utf-8 -*-
#
# Picard plugin swapprefix
# Adds the swapprefix tagger script function.
# This function offers the same functionality as the one in Foobar2000.
# See http://wiki.hydrogenaudio.org/index.php?title=Foobar2000:Title_Formatting_Reference
#
# Copyright (C) 2010 Philipp Wolfer
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

PLUGIN_NAME = 'swapprefix function'
PLUGIN_AUTHOR = 'Philipp Wolfer'
PLUGIN_DESCRIPTION = 'Moves the specified prefixes to the end of a string.'
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.9.0", "0.10", "0.11", "0.12", "0.15"]

from picard.script import register_script_function
import re

def swapprefix(parser, text, *prefixes):
    """
    Moves the specified prefixes to the end of text.
    If no prefix is specified 'A' and 'The' are taken
    as default.
    """
    if not prefixes:
        prefixes = ('A', 'The')
    for prefix in prefixes:
        pattern = re.compile('^' + re.escape(prefix) + '\s')
        match = pattern.match(text)
        if match:
            rest = pattern.split(text)[1].strip()
            if rest:
                return ", ".join((rest, match.group(0).rstrip()))
    return text

register_script_function(swapprefix)


