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
from PyQt4 import QtCore
from PyQt4.QtCore import QUrl, QObject


class CoverArtDownloader(QtCore.QObject):
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
    AMAZON_IMAGE_URL = 'http://%(host)s/images/P/%(asin)s.%(servid)s.%(size)sZZZZZZZ.jpg'

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

    AMAZON_ASIN_URL_REGEX = re.compile(r'^http://(?:www.)?(.*?)(?:\:[0-9]+)?/.*/([0-9B][0-9A-Z]{9})(?:[^0-9A-Z]|$)')

    _CAA_THUMBNAIL_SIZE_MAP = {
        0: "small",
        1: "large",
    }

    def __init__(self, album, metadata, release):
        QtCore.QObject.__init__(self)
        self.try_list = []
        self.settings = QObject.config.setting
        self.album = album
        self.metadata = metadata
        self.release = release

    def run(self):
        """ Gets all cover art URLs from the metadata and then attempts to
        download the album art. """
        album = self.album
        if self.settings['ca_provider_use_caa']:
            url = ("http://coverartarchive.org/release/%s/" %
                    self.metadata["musicbrainz_albumid"])
            self._download(url, partial(self._caa_json_downloaded))
        else:
            self._fill_try_list()
            self._walk_try_list()

    def _extract_host_port_path(self, url):
        parsedUrl = QUrl(url)
        path = str(parsedUrl.encodedPath())
        if parsedUrl.hasQuery():
            path += '?' + parsedUrl.encodedQuery()
        host = str(parsedUrl.host())
        port = parsedUrl.port(80)
        return (host, port, path)


    def _try_list_append_image(self, url, caa_image_data = None):
        self.log.debug("Adding image %s", url)
        self.try_list.append({
            'url': url,
            'caa_image_data': caa_image_data
        })

    def _process_asin_relation(self, url):
        match = self.AMAZON_ASIN_URL_REGEX.match(url)
        if match is not None:
            asinHost = match.group(1)
            asin = match.group(2)
            if asinHost not in self.AMAZON_SERVER:
                asinHost = 'amazon.com'
            serverInfo = self.AMAZON_SERVER[asinHost]
            parms = {
                'host': serverInfo['server'],
                'asin': asin,
                'servid': serverInfo['id'],
            }
            parms['size'] = 'L' # larger must be first
            self._try_list_append_image(self.AMAZON_IMAGE_URL % parms)
            parms['size'] = 'M'
            self._try_list_append_image(self.AMAZON_IMAGE_URL % parms)

    def _process_url_relation(self, url):
        # Search for cover art on special sites
        for site in self.COVERART_SITES:
            # this loop transliterated from the perl stuff used to find cover art for the
            # musicbrainz server.
            # See mb_server/cgi-bin/MusicBrainz/Server/CoverArt.pm
            # hartzell --- Tue Apr 15 15:25:58 PDT 2008
            if not self.settings['ca_provider_use_%s' % site['name']]:
                continue
            match = re.match(site['regexp'], url)
            if match is not None:
                imgURI = site['imguri']
                for i in range(1, len(match.groups())+1):
                    if match.group(i) is not None:
                        imgURI = imgURI.replace('$' + str(i), match.group(i))
                self._try_list_append_image(imgURI)
                return True
        return False

    def _caa_append_image_to_trylist(self, caa_image_data):
        """Adds URLs to `try_list` depending on the users CAA image size settings."""
        imagesize = self.settings["caa_image_size"]
        thumbsize = self._CAA_THUMBNAIL_SIZE_MAP.get(imagesize, None)
        if thumbsize is None:
            url = caa_image_data["image"]
        else:
            url = caa_image_data["thumbnails"][thumbsize]
        self._try_list_append_image(url, caa_image_data)

    def _walk_try_list(self):
        """Downloads each item in ``try_list``. If there are none left, loading of
        ``album`` will be finalized."""
        album = self.album
        if not self.try_list:
            album._finalize_loading(None)
        elif album.id not in album.tagger.albums:
            return
        else:
            # We still have some items to try!
            imagedata = self.try_list.pop(0)
            self._download(imagedata['url'], partial(self._coverart_downloaded,
                                                     imagedata))

    def _coverart_downloaded(self, imagedata, data, http, error):
        self.album._requests -= 1
        if imagedata['caa_image_data']:
            # CAA image
            main_type = imagedata['caa_image_data']['types'][0] #FIXME: multitypes!
            comment = imagedata['caa_image_data']['comment']
        else:
            # other providers
            main_type = 'front'
            comment = ''

        if error or len(data) < 1000:
            if error:
                self.album.log.error(str(http.errorString()))
        else:
            self.tagger.window.set_statusbar_message(N_("Coverart %s downloaded"),
                    http.url().toString())
            mime = mimetype.get_from_data(data, default="image/jpeg")
            filename = None
            if main_type != 'front' and self.settings["caa_image_type_as_filename"]:
                    filename = main_type
            self.metadata.add_image(mime, data, filename, comment, main_type)
            for track in self.album._new_tracks:
                track.metadata.add_image(mime, data, filename, comment, main_type)

        # If the image already was a front image, remove any image
        # from hosts other than CAA as they provide only front images
        if main_type == 'front':
            for item in self.try_list[:]:
                if not item['caa_image_data']:
                    self.try_list.remove(item)
        self._walk_try_list()

    def _fill_try_list(self):
        """Fills ``try_list`` by looking at the relationships in ``release``."""
        try:
            release = self.release
            if 'relation_list' in release.children:
                for relation_list in release.relation_list:
                    if relation_list.target_type == 'url':
                        for relation in relation_list.relation:
                            url = relation.target[0].text
                            #process special sites first (ie. cdbaby)
                            if self._process_url_relation(url):
                                continue
                            # Use the URL of a cover art link directly
                            if self.settings['ca_provider_use_whitelist']\
                                and (relation.type == 'cover art link' or
                                        relation.type == 'has_cover_art_at'):
                                self._try_list_append_image(url)
                                continue
                            # find image from amazon url and its ASIN
                            if self.settings['ca_provider_use_amazon']\
                                and (relation.type == 'amazon asin' or
                                        relation.type == 'has_Amazon_ASIN'):
                                self._process_asin_relation(url)
        except AttributeError, e:
            self.album.log.error(traceback.format_exc())

    def _caa_json_downloaded(self, data, http, error):
        self.album._requests -= 1
        caa_front_found = False
        if error:
            self.album.log.error(str(http.errorString()))
        else:
            try:
                caa_data = json.loads(data)
            except ValueError:
                self.log.debug("Invalid JSON: %s", http.url().toString())
            else:
                caa_types = self.settings["caa_image_types"].split()
                caa_types = map(unicode.lower, caa_types)
                for caa_image_data in caa_data["images"]:
                    if self.settings["caa_approved_only"] and not caa_image_data["approved"]:
                        continue
                    if not caa_image_data["types"] and 'unknown' in caa_types:
                        self._caa_append_image_to_trylist(caa_image_data)
                    imagetypes = map(unicode.lower, caa_image_data["types"])
                    for imagetype in imagetypes:
                        if imagetype == "front":
                            caa_front_found = True
                        if imagetype in caa_types:
                            self._caa_append_image_to_trylist(caa_image_data)
                            break

        if error or not caa_front_found:
            self._fill_try_list()
        self._walk_try_list()

    def _download(self, url, handler, priority=True, important=True):
        album = self.album
        album._requests += 1
        host, port, path = self._extract_host_port_path(url)
        fmturl = "http://%s:%i%s" % (host, port, path) # FIXME: proto ?!
        self.tagger.window.set_statusbar_message(N_("Downloading %s"), fmturl)
        album.tagger.xmlws.download(host, port, path, handler,
                                    priority, important)
