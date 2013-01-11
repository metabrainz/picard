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

def _mk_image_filename(image):
    settings = QObject.config.setting
    filename = settings["cover_image_filename"]
    if not image.is_main_cover and settings["caa_image_type_as_filename"]:
        filename = "-".join(image.types)
    return filename

def _coverart_downloaded(album, metadata, release, try_list, imagedata, data, http, error):
    album._requests -= 1
    imagetypes = imagedata["types"]
    is_front = False

    if error or len(data) < 1000:
        if error:
            album.log.error(str(http.errorString()))
    else:
        QObject.tagger.window.set_statusbar_message(N_("Coverart %s downloaded"),
                http.url().toString())
        mime = mimetype.get_from_data(data, default="image/jpeg")
        imagetypes = imagedata["types"]
        img = metadata.add_image(mime, data, _mk_image_filename, None, imagedata["description"],
                           imagetypes)
        is_front = img.is_front
        for track in album._new_tracks:
            track.metadata.add_image(mime, data, _mk_image_filename, None,
                                     imagedata["description"], imagetypes)

    # If the image already was a front image, there might still be some
    # other front images in the try_list - remove them.
    if is_front:
        for item in try_list[:]:
            if 'front' in item['types'] and 'archive.org' not in item['host']:
                # Hosts other than archive.org only provide front images
                try_list.remove(item)
    _walk_try_list(album, metadata, release, try_list)


def _caa_json_downloaded(album, metadata, release, try_list, data, http, error):
    album._requests -= 1
    caa_front_found = False
    if error:
        album.log.error(str(http.errorString()))
    else:
        try:
            caa_data = json.loads(data)
        except ValueError:
            QObject.log.debug("Invalid JSON: %s", http.url().toString())
        else:
            caa_types = QObject.config.setting["caa_image_types"].split()
            caa_types = map(unicode.lower, caa_types)
            for image in caa_data["images"]:
                if QObject.config.setting["caa_approved_only"] and not image["approved"]:
                    continue
                if not image["types"] and 'unknown' in caa_types:
                    _caa_append_image_to_trylist(try_list, image)
                imagetypes = map(unicode.lower, image["types"])
                for imagetype in imagetypes:
                    if imagetype in caa_types:
                        _caa_append_image_to_trylist(try_list, image)
                        caa_front_found = "front" in imagetypes
                        break

    if error or not caa_front_found:
        _fill_try_list(album, release, try_list)
    _walk_try_list(album, metadata, release, try_list)

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
    _try_list_append_image_url(try_list, url, imagedata["types"], imagedata["comment"])


def coverart(album, metadata, release, try_list=None):
    """ Gets all cover art URLs from the metadata and then attempts to
    download the album art. """

    # try_list will be None for the first call
    if try_list is None:
        try_list = []
        if QObject.config.setting['ca_provider_use_caa']:
            album._requests += 1
            album.tagger.xmlws.download(
                    "coverartarchive.org", 80, "/release/%s/" %
                    metadata["musicbrainz_albumid"],
                    partial(_caa_json_downloaded, album, metadata, release, try_list),
                    priority=True, important=True)
        else:
            _fill_try_list(album, release, try_list)
            _walk_try_list(album, metadata, release, try_list)


def _fill_try_list(album, release, try_list):
    """Fills ``try_list`` by looking at the relationships in ``release``."""
    try:
        if 'relation_list' in release.children:
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


def _walk_try_list(album, metadata, release, try_list):
    """Downloads each item in ``try_list``. If there are none left, loading of
    ``album`` will be finalized."""
    if len(try_list) == 0:
        album._finalize_loading(None)
    elif album.id not in album.tagger.albums:
        return
    else:
        # We still have some items to try!
        album._requests += 1
        url = try_list.pop(0)
        QObject.tagger.window.set_statusbar_message(N_("Downloading http://%s:%i%s"),
                url['host'], url['port'], url['path'])
        album.tagger.xmlws.download(
                url['host'], url['port'], url['path'],
                partial(_coverart_downloaded, album, metadata, release,
                        try_list, url),
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
        if match is not None:
            imgURI = site['imguri']
            for i in range(1, len(match.groups())+1):
                if match.group(i) is not None:
                    imgURI = imgURI.replace('$' + str(i), match.group(i))
            _try_list_append_image_url(try_list, QUrl(imgURI))


def _process_asin_relation(try_list, relation):
    match = AMAZON_ASIN_URL_REGEX.match(relation.target[0].text)
    if match is not None:
        asinHost = match.group(1)
        asin = match.group(2)
        if asinHost in AMAZON_SERVER:
            serverInfo = AMAZON_SERVER[asinHost]
        else:
            serverInfo = AMAZON_SERVER['amazon.com']
        host = serverInfo['server']
        path_l = AMAZON_IMAGE_PATH % (asin, serverInfo['id'], 'L')
        path_m = AMAZON_IMAGE_PATH % (asin, serverInfo['id'], 'M')
        _try_list_append_image_url(try_list, QUrl("http://%s:%s" % (host, path_l)))
        _try_list_append_image_url(try_list, QUrl("http://%s:%s" % (host, path_m)))


def _try_list_append_image_url(try_list, parsedUrl, imagetypes=[u"front"], description=""):
    QObject.log.debug("Adding %s image %s", ",".join(imagetypes), parsedUrl)
    path = str(parsedUrl.encodedPath())
    if parsedUrl.hasQuery():
        path += '?' + parsedUrl.encodedQuery()
    try_list.append({
        'host': str(parsedUrl.host()),
        'port': parsedUrl.port(80),
        'path': str(path),
        'types': map(unicode.lower, imagetypes),
        'description': description,
    })
