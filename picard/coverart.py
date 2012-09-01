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
import picard.webservice

from picard.metadata import register_album_metadata_processor
from picard.util import partial, mimetype
from PyQt4.QtCore import QUrl, QObject

# data transliterated from the perl stuff used to find cover art for the
# musicbrainz server.
# See mb_server/cgi-bin/MusicBrainz/Server/CoverArt.pm
# hartzell --- Tue Apr 15 15:25:58 PDT 2008
COVERART_SITES = (
    # CD-Baby
    # tested with http://musicbrainz.org/release/1243cc17-b9f7-48bd-a536-b10d2013c938.html
    {
    'name': 'cdbaby',
    'regexp': 'http://(www\.)?cdbaby.com/cd/(\w)(\w)(\w*)',
    'imguri': 'http://cdbaby.name/$2/$3/$2$3$4.jpg',
    },
    # Jamendo
    # tested with http://musicbrainz.org/release/2fe63977-bda9-45da-8184-25a4e7af8da7.html
    {
    'name': 'jamendo',
    'regexp': 'http:\/\/(?:www.)?jamendo.com\/(?:[a-z]+\/)?album\/([0-9]+)',
    'imguri': 'http://www.jamendo.com/get/album/id/album/artworkurl/redirect/$1/?artwork_size=0',
    },
    )

# amazon image file names are unique on all servers and constructed like
# <ASIN>.<ServerNumber>.[SML]ZZZZZZZ.jpg
# A release sold on amazon.de has always <ServerNumber> = 03, for example.
# Releases not sold on amazon.com, don't have a "01"-version of the image,
# so we need to make sure we grab an existing image.
AMAZON_SERVER = {
    "amazon.jp": {
		"server": "ec1.images-amazon.com",
		"id"    : "09",
	},
    "amazon.co.jp": {
		"server": "ec1.images-amazon.com",
		"id"    : "09",
	},
    "amazon.co.uk": {
		"server": "ec1.images-amazon.com",
		"id"    : "02",
	},
    "amazon.de": {
		"server": "ec2.images-amazon.com",
		"id"    : "03",
	},
    "amazon.com": {
		"server": "ec1.images-amazon.com",
		"id"    : "01",
	},
    "amazon.ca": {
		"server": "ec1.images-amazon.com",
		"id"    : "01",                   # .com and .ca are identical
	},
    "amazon.fr": {
		"server": "ec1.images-amazon.com",
		"id"    : "08"
	},
}

AMAZON_IMAGE_PATH = '/images/P/%s.%s.%sZZZZZZZ.jpg'
AMAZON_ASIN_URL_REGEX = re.compile(r'^http://(?:www.)?(.*?)(?:\:[0-9]+)?/.*/([0-9B][0-9A-Z]{9})(?:[^0-9A-Z]|$)')

def _coverart_downloaded(album, metadata, release, try_list, imagetype, data, http, error):
    album._requests -= 1
    if error or len(data) < 1000:
        if error:
            album.log.error(str(http.errorString()))
        coverart(album, metadata, release, try_list)
    else:
        QObject.tagger.window.set_statusbar_message(N_("Coverart %s downloaded"),
                http.url().toString())
        mime = mimetype.get_from_data(data, default="image/jpeg")
        filename = None
        if imagetype != 'front' and QObject.config.setting["caa_image_type_as_filename"]:
                filename = imagetype
        metadata.add_image(mime, data, filename)
        for track in album._new_tracks:
            track.metadata.add_image(mime, data, filename)

    # If the image already was a front image, there might still be some
    # other front images in the try_list - remove them.
    for item in try_list[:]:
        if item['type'] == 'front' and 'archive.org' not in item['host']:
            # Hosts other than archive.org only provide front images
            # For still remaining front images from archive.org, refer to
            # the comment in _caa_json_downloaded (~line 156).
            try_list.remove(item)
    if len(try_list) == 0:
        album._finalize_loading(None)
    coverart(album, metadata, release, try_list)

def _caa_json_downloaded(album, metadata, release, try_list, data, http, error):
    album._requests -= 1
    # If there's already an image, it can only be a front one. There *should*
    # be at most one front image that was downloaded from non-CAA sites.
    assert len(metadata.images) <= 1
    if error:
        album.log.error(str(http.errorString()))
    else:
        caa_data = json.loads(data)
        caa_types = QObject.config.setting["caa_image_types"].split()
        caa_types = map(unicode.lower, caa_types)
        for image in caa_data["images"]:
            imagetypes = map(unicode.lower, image["types"])
            for imagetype in imagetypes:
                if imagetype == "front":
                    # There's a front image in the CAA, delete all previously
                    # found front images under the assumption that people do
                    # not upload images to the CAA that are worse than what's
                    # found on the other sites supported by this plugin.
                    QObject.log.debug(
                    "Front image found in the CAA, discarding (possibly) existing one")
                    try:
                        metadata.remove_image(0)
                    except IndexError:
                        pass
                if imagetype in caa_types:
                    if QObject.config.setting["caa_approved_only"]:
                        if image["approved"]:
                            _caa_append_image_to_trylist(try_list, image)
                    else:
                        _caa_append_image_to_trylist(try_list, image)
                    break

    if len(try_list) == 0:
        album._finalize_loading(None)
    else:
        coverart(album, metadata, release, try_list)

_CAA_THUMBNAIL_SIZE_MAP = {
        0: "small",
        1: "large",
        }

def _caa_append_image_to_trylist(try_list, imagedata):
    """Adds URLs to `try_list` depending on the users CAA image size settings."""
    imagesize = QObject.config.setting["caa_image_size"]
    thumbsize = _CAA_THUMBNAIL_SIZE_MAP.get(imagesize, None)
    if thumbsize is None:
        url = QUrl(imagedata["image"])
    else:
        url = QUrl(imagedata["thumbnails"][thumbsize])
    _try_list_append_image_url(try_list, url, imagedata["types"][0])

def coverart(album, metadata, release, try_list=None):
    """ Gets all cover art URLs from the metadata and then attempts to
    download the album art. """

    # try_list will be None for the first call
    if try_list is None:
        try_list = []

        try:
            if release.children.has_key('relation_list'):
                for relation_list in release.relation_list:
                    if relation_list.target_type == 'url':
                        for relation in relation_list.relation:
                            _process_url_relation(try_list, relation)

                            # Use the URL of a cover art link directly
                            if QObject.config.setting['ca_provider_use_whitelist']\
                                and (relation.type == 'cover art link' or
                                     relation.type == 'has_cover_art_at'):
                                _try_list_append_image_url(try_list, QUrl(relation.target[0].text))
                            elif QObject.config.setting['ca_provider_use_amazon']\
                                and (relation.type == 'amazon asin' or
                                     relation.type == 'has_Amazon_ASIN'):
                                _process_asin_relation(try_list, relation)
        except AttributeError, e:
            album.log.error(traceback.format_exc())

    if len(try_list) > 0:
        # We still have some items to try!
        album._requests += 1
        url = try_list.pop(0)
        QObject.tagger.window.set_statusbar_message(N_("Downloading http://%s:%i%s"),
                url['host'], url['port'], url['path'])
        album.tagger.xmlws.download(
                url['host'], url['port'], url['path'],
                partial(_coverart_downloaded, album, metadata, release,
                        try_list, url['type']),
                priority=True, important=True)
    else:
        if QObject.config.setting['ca_provider_use_caa']:
            album._requests += 1
            album.tagger.xmlws.download(
                    "coverartarchive.org", 80, "/release/%s/" %
                    metadata["musicbrainz_albumid"],
                    partial(_caa_json_downloaded, album, metadata, release, try_list),
                    priority=True, important=True)

def _process_url_relation(try_list, relation):
    # Search for cover art on special sites
    for site in COVERART_SITES:
        # this loop transliterated from the perl stuff used to find cover art for the
        # musicbrainz server.
        # See mb_server/cgi-bin/MusicBrainz/Server/CoverArt.pm
        # hartzell --- Tue Apr 15 15:25:58 PDT 2008
        if not QObject.config.setting['ca_provider_use_%s' % site['name']]:
            continue
        match = re.match(site['regexp'], relation.target[0].text)
        if match != None:
            imgURI = site['imguri']
            for i in range(1, len(match.groups())+1 ):
                if match.group(i) != None:
                    imgURI = imgURI.replace('$' + str(i), match.group(i))
            _try_list_append_image_url(try_list, QUrl(imgURI))


def _process_asin_relation(try_list, relation):
    match = AMAZON_ASIN_URL_REGEX.match(relation.target[0].text)
    if match != None:
        asinHost = match.group(1)
        asin = match.group(2);
        if AMAZON_SERVER.has_key(asinHost):
            serverInfo = AMAZON_SERVER[asinHost]
        else:
            serverInfo = AMAZON_SERVER['amazon.com']
        try_list.append({'host': serverInfo['server'], 'port': 80,
            'path': AMAZON_IMAGE_PATH % (asin, serverInfo['id'], 'L'),
            'type': 'front'
        })
        try_list.append({'host': serverInfo['server'], 'port': 80,
            'path': AMAZON_IMAGE_PATH % (asin, serverInfo['id'], 'M'),
            'type': 'front'
        })


def _try_list_append_image_url(try_list, parsedUrl, imagetype="front"):
    QObject.log.debug("Adding %s image %s", imagetype, parsedUrl)
    path = str(parsedUrl.encodedPath())
    if parsedUrl.hasQuery():
        path += '?' + parsedUrl.encodedQuery()
    try_list.append({
        'host': str(parsedUrl.host()),
        'port': parsedUrl.port(80),
        'path': str(path),
        'type': imagetype.lower()
    })

