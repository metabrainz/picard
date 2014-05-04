# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Oliver Charles
# Copyright (C) 2007-2011 Philipp Wolfer
# Copyright (C) 2007, 2010, 2011 Lukáš Lalinský
# Copyright (C) 2011 Michael Wiencek
# Copyright (C) 2011-2012 Wieland Hoffmann
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
from picard.metadata import Image, is_front_image
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

AMAZON_IMAGE_PATH = '/images/P/%s.%s.%sZZZZZZZ.jpg'


def _coverart_http_error(album, http):
    album.error_append(u'Coverart error: %s' % (unicode(http.errorString())))



_CAA_THUMBNAIL_SIZE_MAP = {
    0: "small",
    1: "large",
}




class CoverArt:

    def __init__(self, album, metadata, release):
        self.try_list = []
        self.album = album
        self.metadata = metadata

        # MB web service indicates if CAA has artwork
        # http://tickets.musicbrainz.org/browse/MBS-4536
        has_caa_artwork = False
        caa_types = map(unicode.lower, config.setting["caa_image_types"])

        if 'cover_art_archive' in release.children:
            caa_node = release.children['cover_art_archive'][0]
            has_caa_artwork = (caa_node.artwork[0].text == 'true')
            has_front = 'front' in caa_types
            has_back = 'back' in caa_types

            if len(caa_types) == 2 and (has_front or has_back):
                # The OR cases are there to still download and process the CAA
                # JSON file if front or back is enabled but not in the CAA and
                # another type (that's neither front nor back) is enabled.
                # For example, if both front and booklet are enabled and the
                # CAA only has booklet images, the front element in the XML
                # from the webservice will be false (thus front_in_caa is False
                # as well) but it's still necessary to download the booklet
                # images by using the fact that back is enabled but there are
                # no back images in the CAA.
                front_in_caa = caa_node.front[0].text == 'true' or not has_front
                back_in_caa = caa_node.back[0].text == 'true' or not has_back
                has_caa_artwork = has_caa_artwork and (front_in_caa or back_in_caa)

            elif len(caa_types) == 1 and (has_front or has_back):
                front_in_caa = caa_node.front[0].text == 'true' and has_front
                back_in_caa = caa_node.back[0].text == 'true' and has_back
                has_caa_artwork = has_caa_artwork and (front_in_caa or back_in_caa)

        if config.setting['ca_provider_use_caa'] and has_caa_artwork\
            and len(caa_types) > 0:
            log.debug("There are suitable images in the cover art archive for %s"
                        % release.id)
            self.album._requests += 1
            self.album.tagger.xmlws.download(
                CAA_HOST, CAA_PORT, "/release/%s/" %
                self.metadata["musicbrainz_albumid"],
                partial(self._caa_json_downloaded, release),
                priority=True, important=False)
        else:
            log.debug("There are no suitable images in the cover art archive for %s"
                        % release.id)
            self._fill_try_list(release)
            self._walk_try_list(release)

    def _coverart_downloaded(self, release, coverinfos, data, http, error):
        self.album._requests -= 1

        if error or len(data) < 1000:
            if error:
                _coverart_http_error(self.album, http)
        else:
            QObject.tagger.window.set_statusbar_message(
                N_("Cover art of type '%(type)s' downloaded for %(albumid)s from %(host)s"),
                {
                    'type': coverinfos['type'].title(),
                    'albumid': self.album.id,
                    'host': coverinfos['host']
                }
            )
            mime = mimetype.get_from_data(data, default="image/jpeg")

            try:
                self.metadata.make_and_add_image(mime, data,
                                            imagetype=coverinfos['type'],
                                            comment=coverinfos['desc'])
                for track in self.album._new_tracks:
                    track.metadata.make_and_add_image(mime, data,
                                                    imagetype=coverinfos['type'],
                                                    comment=coverinfos['desc'])
            except (IOError, OSError) as e:
                self.album.error_append(e.message)
                self.album._finalize_loading(error=True)
                # It doesn't make sense to store/download more images if we can't
                # save them in the temporary folder, abort.
                return

        # If the image already was a front image, there might still be some
        # other front images in the try_list - remove them.
        if is_front_image(coverinfos):
            for item in self.try_list[:]:
                if is_front_image(item) and 'archive.org' not in item['host']:
                    # Hosts other than archive.org only provide front images
                    self.try_list.remove(item)
        self._walk_try_list(release)


    def _caa_json_downloaded(self, release, data, http, error):
        self.album._requests -= 1
        caa_front_found = False
        if error:
            _coverart_http_error(self.album, http)
        else:
            try:
                caa_data = json.loads(data)
            except ValueError:
                log.debug("Invalid JSON: %s", http.url().toString())
            else:
                caa_types = config.setting["caa_image_types"]
                caa_types = map(unicode.lower, caa_types)
                for image in caa_data["images"]:
                    if config.setting["caa_approved_only"] and not image["approved"]:
                        continue
                    if not image["types"] and "unknown" in caa_types:
                        image["types"] = [u"Unknown"]
                    imagetypes = map(unicode.lower, image["types"])
                    for imagetype in imagetypes:
                        if imagetype == "front":
                            caa_front_found = True
                        if imagetype in caa_types:
                            self._caa_append_image_to_trylist(image)
                            break

        if error or not caa_front_found:
            self._fill_try_list(release)
        self._walk_try_list(release)


    def _caa_append_image_to_trylist(self, imagedata):
        """Adds URLs to `try_list` depending on the users CAA image size settings."""
        imagesize = config.setting["caa_image_size"]
        thumbsize = _CAA_THUMBNAIL_SIZE_MAP.get(imagesize, None)
        if thumbsize is None:
            url = QUrl(imagedata["image"])
        else:
            url = QUrl(imagedata["thumbnails"][thumbsize])
        extras = {
            'type': imagedata["types"][0].lower(),  # FIXME: we pass only 1 type
            'desc': imagedata["comment"],
            'front': imagedata['front'],  # front image indicator from CAA
        }
        self._try_list_append_image_url(url, extras)


    def _fill_try_list(self, release):
        """Fills ``try_list`` by looking at the relationships in ``release``."""
        use_whitelist = config.setting['ca_provider_use_whitelist']
        use_amazon = config.setting['ca_provider_use_amazon']
        if not (use_whitelist or use_amazon):
            return
        try:
            if 'relation_list' in release.children:
                for relation_list in release.relation_list:
                    if relation_list.target_type == 'url':
                        for relation in relation_list.relation:
                            # Use the URL of a cover art link directly
                            if use_whitelist \
                            and (relation.type == 'cover art link' or
                                    relation.type == 'has_cover_art_at'):
                                url = QUrl(relation.target[0].text)
                                self._try_list_append_image_url(url)
                            elif use_amazon \
                                and (relation.type == 'amazon asin' or
                                    relation.type == 'has_Amazon_ASIN'):
                                self._process_asin_relation(relation)
        except AttributeError:
            self.album.error_append(traceback.format_exc())


    def _walk_try_list(self, release):
        """Downloads each item in ``try_list``. If there are none left, loading of
        ``album`` will be finalized."""
        if len(self.try_list) == 0:
            self.album._finalize_loading(None)
        elif self.album.id not in self.album.tagger.albums:
            return
        else:
            # We still have some items to try!
            self.album._requests += 1
            coverinfos = self.try_list.pop(0)
            QObject.tagger.window.set_statusbar_message(
                N_("Downloading cover art of type '%(type)s' for %(albumid)s from %(host)s ..."),
                {
                    'type': coverinfos['type'],
                    'albumid': self.album.id,
                    'host': coverinfos['host']
                }
            )
            self.album.tagger.xmlws.download(
                coverinfos['host'], coverinfos['port'], coverinfos['path'],
                partial(self._coverart_downloaded, release, coverinfos),
                priority=True, important=False)


    def _process_asin_relation(self, relation):
        amz = parse_amazon_url(relation.target[0].text)
        if amz is not None:
            if amz['host'] in AMAZON_SERVER:
                serverInfo = AMAZON_SERVER[amz['host']]
            else:
                serverInfo = AMAZON_SERVER['amazon.com']
            host = serverInfo['server']
            path_l = AMAZON_IMAGE_PATH % (amz['asin'], serverInfo['id'], 'L')
            path_m = AMAZON_IMAGE_PATH % (amz['asin'], serverInfo['id'], 'M')
            self._try_list_append_image_url(QUrl("http://%s:%s" % (host, path_l)))
            self._try_list_append_image_url(QUrl("http://%s:%s" % (host, path_m)))


    def _try_list_append_image_url(self, parsedUrl, extras=None):
        path = str(parsedUrl.encodedPath())
        if parsedUrl.hasQuery():
            path += '?' + parsedUrl.encodedQuery()
        coverinfos = {
            'host': str(parsedUrl.host()),
            'port': parsedUrl.port(80),
            'path': str(path),
            'type': 'front',
            'desc': ''
        }
        if extras is not None:
            coverinfos.update(extras)
        log.debug("Adding %s image %s", coverinfos['type'], parsedUrl.toString())
        self.try_list.append(coverinfos)


def coverart(album, metadata, release, coverartobj=None):
    """ Gets all cover art URLs from the metadata and then attempts to
    download the album art. """

    # try_list will be None for the first call
    if coverartobj is not None:
        return

    coverartobj = CoverArt(album, metadata, release)
