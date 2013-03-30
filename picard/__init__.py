# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
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

version_info = (1, 2, 0, 'final', 0)

if version_info[3] == 'final':
    if version_info[2] == 0:
        version_string = '%d.%d' % version_info[:2]
    else:
        version_string = '%d.%d.%d' % version_info[:3]
else:
    version_string = '%d.%d.%d%s%d' % version_info
__version__ = version_string

api_versions = ["0.15.0", "0.15.1", "0.16.0", "1.0.0", "1.1.0", "1.2.0"]

