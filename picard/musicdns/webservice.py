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

import musicbrainz2.webservice
import urllib
from musicbrainz2.webservice import ResponseError
from musicbrainz2.wsxml import MbXmlParser, ParseError


class TrackFilter(musicbrainz2.webservice.IFilter):

	def __init__(self, clientId=None, clientVersion=None, fingerprint=None,
                 puid=None, fileSha1=None, acousticSha1=None, metadata=None,
                 bitrate=None, format=None, length=None, artist=None,
                 title=None, album=None, trackNum=None, genre=None, year=None,
                 composer=None, conductor=None, orchestra=None, encoding=None,
                 lookupType=None):
		self._params = [
            ('lkt', lookupType),
            ('cid', clientId),
            ('cvr', clientVersion),
            ('fpt', fingerprint),
            ('uid', puid),
            ('s1f', fileSha1),
            ('s1a', acousticSha1),
            ('rmd', metadata),
            ('brt', bitrate),
            ('fmt', format),
            ('dur', length),
            ('art', artist),
            ('ttl', title),
            ('alb', album),
            ('tnm', trackNum),
            ('gnr', genre),
            ('yrr', year),
            ('cmp', composer),
            ('cnd', conductor),
            ('orc', orchestra),
            ('enc', encoding),
        ]

	def createParameters(self):
		return musicbrainz2.webservice._createParameters(self._params)


class Query(musicbrainz2.webservice.Query):

    def getTrack(self, filter):
        params = filter.createParameters()
        stream = self._ws.post("track", "", urllib.urlencode(params, True))
        try:
            parser = MbXmlParser()
            return parser.parse(stream).getTrack()
        except ParseError, e:
            raise ResponseError(str(e), e)

