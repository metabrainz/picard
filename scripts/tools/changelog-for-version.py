#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020 Philipp Wolfer
# Copyright (C) 2020-2021 Laurent Monin
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


import re
import sys


if len(sys.argv) == 1:
    print("Call with changelog-for-version.py [version]", file=sys.stderr)
    sys.exit(1)

version = sys.argv[1]
re_changes = re.compile(r'^# Version ' + re.escape(version) + '.*?\n(.*?)# Version',
    re.DOTALL | re.MULTILINE)

with open('NEWS.md', 'r') as newsfile:
    news = newsfile.read()
    result = re_changes.search(news)
    if not result:
        print("No changelog found for version %s" % version, file=sys.stderr)
        sys.exit(1)
    print(result[1].strip())
