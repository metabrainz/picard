# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
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

"""Variable pattern for script completion."""

import re


# Character class for variable names: Unicode letters/digits ("\w") and colon.
# Python's regex "\w" includes Unicode letters, digits, and underscores.
VAR_NAME_CLASS = r"[\w:]"
_VARIABLE_NAME_GROUP = rf"({VAR_NAME_CLASS}+)"


# Compiled patterns for variable syntaxes
PERCENT_VARIABLE_RE = re.compile(rf"%({_VARIABLE_NAME_GROUP})%")


GET_VARIABLE_RE = re.compile(rf"\$get\(\s*({_VARIABLE_NAME_GROUP})\s*\)")


SET_VARIABLE_RE = re.compile(rf"\$set\(\s*({_VARIABLE_NAME_GROUP})\s*,")


VARIABLE_NAME_FULLMATCH_RE = re.compile(rf"^(?:{_VARIABLE_NAME_GROUP})+$")
