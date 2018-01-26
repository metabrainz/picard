# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Oliver Charles
# Copyright (C) 2007-2011 Philipp Wolfer
# Copyright (C) 2007, 2010, 2011 Lukáš Lalinský
# Copyright (C) 2011 Michael Wiencek
# Copyright (C) 2011-2012 Wieland Hoffmann
# Copyright (C) 2013-2014 Laurent Monin
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


from picard import log
from picard.util import parse_amazon_url
from picard.coverart.providers import CoverArtProvider
from picard.coverart.image import CoverArtImage


# amazon image file names are unique on all servers and constructed like
# <ASIN>.<ServerNumber>.[SML]ZZZZZZZ.jpg
# A release sold on amazon.de has always <ServerNumber> = 03, for example.
# Releases not sold on amazon.com, don't have a "01"-version of the image,
# so we need to make sure we grab an existing image.
AMAZON_SERVER = {
    "amazon.jp": {
        "server": "ec1.images-amazon.com",
        "id": "09",
    },
    "amazon.co.jp": {
        "server": "ec1.images-amazon.com",
        "id": "09",
    },
    "amazon.co.uk": {
        "server": "ec1.images-amazon.com",
        "id": "02",
    },
    "amazon.de": {
        "server": "ec2.images-amazon.com",
        "id": "03",
    },
    "amazon.com": {
        "server": "ec1.images-amazon.com",
        "id": "01",
    },
    "amazon.ca": {
        "server": "ec1.images-amazon.com",
        "id": "01",  # .com and .ca are identical
    },
    "amazon.fr": {
        "server": "ec1.images-amazon.com",
        "id": "08"
    },
}

AMAZON_IMAGE_PATH = '/images/P/%(asin)s.%(serverid)s.%(size)s.jpg'

# First item in the list will be tried first
AMAZON_SIZES = (
    # huge size option is only available for items
    # that have a ZOOMing picture on its amazon web page
    # and it doesn't work for all of the domain names
    #'_SCRM_',        # huge size
    'LZZZZZZZ',      # large size, option format 1
    #'_SCLZZZZZZZ_',  # large size, option format 3
    'MZZZZZZZ',      # default image size, format 1
    #'_SCMZZZZZZZ_',  # medium size, option format 3
    #'TZZZZZZZ',      # medium image size, option format 1
    #'_SCTZZZZZZZ_',  # small size, option format 3
    #'THUMBZZZ',      # small size, option format 1
)


class CoverArtProviderAmazon(CoverArtProvider):

    """Use Amazon ASIN Musicbrainz relationships to get cover art"""

    NAME = "Amazon"
    TITLE = N_('Amazon')

    def enabled(self):
        return (super().enabled()
                and not self.coverart.front_image_found)

    def queue_images(self):
        self.match_url_relations(('amazon asin', 'has_Amazon_ASIN'),
                                 self._queue_from_asin_relation)
        return CoverArtProvider.FINISHED

    def _queue_from_asin_relation(self, url):
        """Queue cover art images from Amazon"""
        amz = parse_amazon_url(url)
        if amz is None:
            return
        log.debug("Found ASIN relation : %s %s", amz['host'], amz['asin'])
        if amz['host'] in AMAZON_SERVER:
            serverInfo = AMAZON_SERVER[amz['host']]
        else:
            serverInfo = AMAZON_SERVER['amazon.com']
        host = serverInfo['server']
        for size in AMAZON_SIZES:
            path = AMAZON_IMAGE_PATH % {
                'asin': amz['asin'],
                'serverid': serverInfo['id'],
                'size': size
            }
            self.queue_put(CoverArtImage("http://%s%s" % (host, path)))
