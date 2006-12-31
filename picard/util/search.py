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

"""Lucene query builder"""

from musicbrainz2.webservice import IFilter, _createParameters
from picard.util import strip_non_alnum

class LuceneQueryFilter(IFilter):

    def __init__(self, **kwargs):
        self._params = []
        for name in ('limit',):
            if name in kwargs:
                self._params.append((name, kwargs[name]))
                del kwargs[name]
        query = []
        for name, value in kwargs.items():
            # FIXME escape special characters, not remove them
            value = strip_non_alnum(value).strip()
            if value:
                query.append('%s:(%s)' % (name, value))
        self._params.append(('query', ' '.join(query)))

    def createParameters(self):
        return _createParameters(self._params)
