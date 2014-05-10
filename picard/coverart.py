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

import json
import re
import traceback
from functools import partial
from picard import config, log
from picard.util import mimetype, parse_amazon_url
from picard.const import CAA_HOST, CAA_PORT
from PyQt4.QtCore import QUrl, QObject

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

_CAA_THUMBNAIL_SIZE_MAP = {
    0: "small",
    1: "large",
}


class CoverArtImage:

    support_types = False
    # consider all images as front if types aren't supported by provider
    is_front = True

    def __init__(self, url=None, types=[u'front'], comment=''):
        if url is not None:
            self.parse_url(url)
        else:
            self.url = None
        self.types = types
        self.comment = comment

    def parse_url(self, url):
        self.url = QUrl(url)
        self.host = str(self.url.host())
        self.port = self.url.port(80)
        self.path = str(self.url.encodedPath())
        if self.url.hasQuery():
            self.path += '?' + str(self.url.encodedQuery())

    def is_front_image(self):
        # CAA has a flag for "front" image, use it in priority
        if self.is_front:
            return True
        # no caa front flag, use type instead
        return u'front' in self.types

    def __repr__(self):
        p = []
        if self.url is not None:
            p.append("url=%r" % self.url.toString())
        p.append("types=%r" % self.types)
        if self.comment:
            p.append("comment=%r" % self.comment)
        return "%s(%s)" % (self.__class__.__name__, ", ".join(p))

    def __unicode__(self):
        p = [u'Image']
        if self.url is not None:
            p.append(u"from %s" % self.url.toString())
        p.append(u"of type %s" % u','.join(self.types))
        if self.comment:
            p.append(u"and comment '%s'" % self.comment)
        return u' '.join(p)

    def __str__(self):
        return unicode(self).encode('utf-8')


class CaaCoverArtImage(CoverArtImage):

    is_front = False
    support_types = True


class CoverArt:

    def __init__(self, album, metadata, release):
        self._queue_new()
        self.album = album
        self.metadata = metadata
        self.release = release
        self.caa_types = map(unicode.lower, config.setting["caa_image_types"])
        self.len_caa_types = len(self.caa_types)
        self.front_image_found = False

    def __repr__(self):
        return "CoverArt for %r" % (self.album)

    def retrieve(self):
        """Retrieve available cover art images for the release"""

        if self._caa_has_suitable_artwork():
            self._xmlws_download(
                CAA_HOST,
                CAA_PORT,
                "/release/%s/" % self.metadata["musicbrainz_albumid"],
                self._caa_json_downloaded,
                priority=True,
                important=False
            )
        else:
            self._queue_from_relationships()
            self._download_next_in_queue()

    def _caa_has_suitable_artwork(self):
        """Check if CAA artwork has to be downloaded"""
        if not config.setting['ca_provider_use_caa']:
            log.debug("Cover Art Archive disabled by user")
            return False
        if not self.len_caa_types:
            log.debug("User disabled all Cover Art Archive types")
            return False

        # MB web service indicates if CAA has artwork
        # http://tickets.musicbrainz.org/browse/MBS-4536
        if 'cover_art_archive' not in self.release.children:
            log.debug("No Cover Art Archive information for %s"
                      % self.release.id)
            return False

        caa_node = self.release.children['cover_art_archive'][0]
        caa_has_suitable_artwork = caa_node.artwork[0].text == 'true'

        if not caa_has_suitable_artwork:
            log.debug("There are no images in the Cover Art Archive for %s"
                      % self.release.id)
            return False

        want_front = 'front' in self.caa_types
        want_back = 'back' in self.caa_types
        caa_has_front = caa_node.front[0].text == 'true'
        caa_has_back = caa_node.back[0].text == 'true'

        if self.len_caa_types == 2 and (want_front or want_back):
            # The OR cases are there to still download and process the CAA
            # JSON file if front or back is enabled but not in the CAA and
            # another type (that's neither front nor back) is enabled.
            # For example, if both front and booklet are enabled and the
            # CAA only has booklet images, the front element in the XML
            # from the webservice will be false (thus front_in_caa is False
            # as well) but it's still necessary to download the booklet
            # images by using the fact that back is enabled but there are
            # no back images in the CAA.
            front_in_caa = caa_has_front or not want_front
            back_in_caa = caa_has_back or not want_back
            caa_has_suitable_artwork = front_in_caa or back_in_caa

        elif self.len_caa_types == 1 and (want_front or want_back):
            front_in_caa = caa_has_front and want_front
            back_in_caa = caa_has_back and want_back
            caa_has_suitable_artwork = front_in_caa or back_in_caa

        if not caa_has_suitable_artwork:
            log.debug("There are no suitable images in the Cover Art Archive for %s"
                      % self.release.id)
        else:
            log.debug("There are suitable images in the Cover Art Archive for %s"
                      % self.release.id)

        return caa_has_suitable_artwork

    def _coverart_http_error(self, http):
        """Append http error to album errors"""
        self.album.error_append(u'Coverart error: %s' %
                                (unicode(http.errorString())))

    def _coverart_downloaded(self, coverartimage, data, http, error):
        """Handle finished download, save it to metadata"""
        self.album._requests -= 1

        if error:
            self._coverart_http_error(http)
        elif len(data) < 1000:
            log.warning("Not enough data, skipping %s" % coverartimage)
        else:
            self._message(
                N_("Cover art of type '%(type)s' downloaded for %(albumid)s from %(host)s"),
                {
                    'type': ','.join(coverartimage.types),
                    'albumid': self.album.id,
                    'host': coverartimage.host
                }
            )
            mime = mimetype.get_from_data(data, default="image/jpeg")

            try:
                self.metadata.make_and_add_image(
                    mime,
                    data,
                    types=coverartimage.types,
                    comment=coverartimage.comment,
                    is_front=coverartimage.is_front
                )
                for track in self.album._new_tracks:
                    track.metadata.make_and_add_image(
                        mime,
                        data,
                        types=coverartimage.types,
                        comment=coverartimage.comment,
                        is_front=coverartimage.is_front
                    )
                # If the image already was a front image,
                # there might still be some other non-CAA front
                # images in the queue - ignore them.
                if not self.front_image_found:
                    self.front_image_found = coverartimage.is_front_image()

            except (IOError, OSError) as e:
                self.album.error_append(e.message)
                self.album._finalize_loading(error=True)
                # It doesn't make sense to store/download more images if we can't
                # save them in the temporary folder, abort.
                return

        self._download_next_in_queue()

    def _caa_json_downloaded(self, data, http, error):
        """Parse CAA JSON file and queue CAA cover art images for download"""
        self.album._requests -= 1
        caa_front_found = False
        if error:
            self._coverart_http_error(http)
        else:
            try:
                caa_data = json.loads(data)
            except ValueError:
                self.album.error_append(
                    "Invalid JSON: %s", http.url().toString())
            else:
                for image in caa_data["images"]:
                    if config.setting["caa_approved_only"] and not image["approved"]:
                        continue
                    # if image has no type set, we still want it to match
                    # pseudo type 'unknown'
                    if not image["types"]:
                        image["types"] = [u"unknown"]
                    else:
                        image["types"] = map(unicode.lower, image["types"])
                    # only keep enabled caa types
                    types = set(image["types"]).intersection(
                        set(self.caa_types))
                    if types:
                        if not caa_front_found:
                            caa_front_found = u'front' in types
                        self._queue_from_caa(image)

        if error or not caa_front_found:
            self._queue_from_relationships()
        self._download_next_in_queue()

    def _queue_from_caa(self, image):
        """Queue images depending on the CAA image size settings."""
        imagesize = config.setting["caa_image_size"]
        thumbsize = _CAA_THUMBNAIL_SIZE_MAP.get(imagesize, None)
        if thumbsize is None:
            url = image["image"]
        else:
            url = image["thumbnails"][thumbsize]
        coverartimage = CaaCoverArtImage(
            url,
            types=image["types"],
            comment=image["comment"],
        )
        # front image indicator from CAA
        coverartimage.is_front = bool(image['front'])
        self._queue_put(coverartimage)

    def _queue_from_relationships(self):
        """Queue images by looking at the release's relationships.
        """
        use_whitelist = config.setting['ca_provider_use_whitelist']
        use_amazon = config.setting['ca_provider_use_amazon']
        if not (use_whitelist or use_amazon):
            return
        log.debug("Trying to get cover art from release relationships ...")
        try:
            if 'relation_list' in self.release.children:
                for relation_list in self.release.relation_list:
                    if relation_list.target_type == 'url':
                        for relation in relation_list.relation:
                            # Use the URL of a cover art link directly
                            if use_whitelist \
                                and (relation.type == 'cover art link' or
                                     relation.type == 'has_cover_art_at'):
                                self._queue_from_cover_art_relation(relation)
                            elif use_amazon \
                                and (relation.type == 'amazon asin' or
                                     relation.type == 'has_Amazon_ASIN'):
                                self._queue_from_asin_relation(relation)
        except AttributeError:
            self.album.error_append(traceback.format_exc())

    def _queue_from_cover_art_relation(self, relation):
        """Queue from cover art relationships"""
        log.debug("Found cover art link in whitelist")
        url = relation.target[0].text
        self._queue_put(CoverArtImage(url))

    def _queue_from_asin_relation(self, relation):
        """Queue cover art images from Amazon"""
        amz = parse_amazon_url(relation.target[0].text)
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
            url = "http://%s:%s" % (host, path)
            self._queue_put(CoverArtImage(url))

    def _download_next_in_queue(self):
        """Downloads next item in queue.
           If there are none left, loading of album will be finalized.
        """
        if self._queue_empty():
            self.album._finalize_loading(None)
            return

        if self.album.id not in self.album.tagger.albums:
            return

        # We still have some items to try!
        coverartimage = self._queue_get()
        if not coverartimage.support_types and self.front_image_found:
            # we already have one front image, no need to try other type-less
            # sources
            log.debug("Skipping %r, one front image is already available",
                      coverartimage)
            self._download_next_in_queue()
            return

        self._message(
            N_("Downloading cover art of type '%(type)s' for %(albumid)s from %(host)s ..."),
            {
                'type': ','.join(coverartimage.types),
                'albumid': self.album.id,
                'host': coverartimage.host
            }
        )
        self._xmlws_download(
            coverartimage.host,
            coverartimage.port,
            coverartimage.path,
            partial(self._coverart_downloaded, coverartimage),
            priority=True,
            important=False
        )

    def _queue_put(self, coverartimage):
        "Add an image to queue"
        log.debug("Queing %r for download", coverartimage)
        self.__queue.append(coverartimage)

    def _queue_get(self):
        "Get next image and remove it from queue"
        return self.__queue.pop(0)

    def _queue_empty(self):
        "Returns True if the queue is empty"
        return not self.__queue

    def _queue_new(self):
        "Initialize the queue"
        self.__queue = []

    def _message(self, *args, **kwargs):
        """Display message to status bar"""
        QObject.tagger.window.set_statusbar_message(*args, **kwargs)

    def _xmlws_download(self, *args, **kwargs):
        """xmlws.download wrapper"""
        self.album._requests += 1
        self.album.tagger.xmlws.download(*args, **kwargs)


def coverart(album, metadata, release):
    """Gets all cover art URLs from the metadata and then attempts to
    download the album art. """

    coverart = CoverArt(album, metadata, release)
    coverart.retrieve()
    log.debug("New %r", coverart)
