"""
A small plugin to download cover art for any releseas that have a
CoverArtLink or ASIN relation or a cover on coverartarchive.org


Changelog:

    [2012-08-23] Added an options page (mineo)
    [2012-03-23] Added support for coverartarchive.org (mineo)
    [2008-04-15] Refactored the code to be similar to the server code (hartzell, phw)

    [2008-03-10] Added CDBaby support (phw)

    [2007-09-06] Added Jamendo support (phw)

    [2007-04-24] Moved parsing code into here
                 Swapped to QUrl
                 Moved to a list of urls

    [2007-04-23] Moved it to use the bzr picard
                 Took the hack out
                 Added Amazon ASIN support

    [2007-04-23] Initial plugin, uses a hack that relies on Python being
                 installed and musicbrainz2 for the query.

"""

PLUGIN_NAME = 'Cover Art Downloader'
PLUGIN_AUTHOR = 'Oliver Charles, Philipp Wolfer, Wieland Hoffmann'
PLUGIN_DESCRIPTION = '''Downloads cover artwork for releases that have a
CoverArtLink or ASIN. Unlike the rest of Picard, this plugin requires at least
Python 2.6'''
PLUGIN_VERSION = "0.7.0"
PLUGIN_API_VERSIONS = ["0.15"]

import json
import re
import traceback
import picard.webservice

from picard.config import BoolOption, IntOption, TextOption
from picard.metadata import register_album_metadata_processor
from picard.ui.options import register_options_page, OptionsPage
from picard.util import partial, mimetype
from PyQt4.QtCore import QUrl, QObject
from picard.plugins.coverart.ui_options_coverart import Ui_CoverartOptionsPage

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

def _coverart_downloaded(album, metadata, release, try_list, data, http, error):
    album._requests -= 1
    if error or len(data) < 1000:
        if error:
            album.log.error(str(http.errorString()))
        coverart(album, metadata, release, try_list)
    else:
        mime = mimetype.get_from_data(data, default="image/jpeg")
        metadata.add_image(mime, data)
        for track in album._new_tracks:
            track.metadata.add_image(mime, data)

    if len(try_list) == 0:
        album._finalize_loading(None)
    else:
        # If the image already was a front image, there might still be some
        # other front images in the try_list - remove them.
        for item in try_list[:]:
            if not "archive.org" in item["host"]:
                # Hosts other than archive.org only provide front images
                # For still remaining front images from archive.org, refer to
                # the comment in _caa_json_downloaded (~line 156).
                try_list.remove(item)
        coverart(album, metadata, release, try_list)

def _caa_json_downloaded(album, metadata, release, try_list, data, http, error):
    album._requests -= 1
    # If there's already an image, it can only be a front one. There *should*
    # be at most one front image that was downloaded from non-CAA sites.
    assert len(metadata.images) <= 1
    if error:
        album.log.error(str(http.errorString()))
        coverart(album, metadata, release, try_list)
    else:
        caa_data = json.loads(data)
        caa_types = QObject.config.setting["caa_image_types"].split()
        caa_types = map(unicode.lower, caa_types)
        for image in caa_data["images"]:
            imagetypes = map(unicode.lower, image["types"])
            for imagetype in imagetypes:
                if imagetype in caa_types:
                    if QObject.config.setting["caa_approved_only"]:
                        if image["approved"]:
                            _caa_append_image_to_trylist(try_list, image)
                    else:
                        _caa_append_image_to_trylist(try_list, image)
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
    _try_list_append_image_url(try_list, url)

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
        url = try_list.pop()
        album.tagger.xmlws.download(
                url['host'], url['port'], url['path'],
                partial(_coverart_downloaded, album, metadata, release, try_list),
                priority=True, important=True)
    else:
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
            'path': AMAZON_IMAGE_PATH % (asin, serverInfo['id'], 'L')
        })
        try_list.append({'host': serverInfo['server'], 'port': 80,
            'path': AMAZON_IMAGE_PATH % (asin, serverInfo['id'], 'M')
        })


def _try_list_append_image_url(try_list, parsedUrl):
    path = str(parsedUrl.encodedPath())
    if parsedUrl.hasQuery():
        path += '?' + parsedUrl.encodedQuery()
    try_list.append({
        'host': str(parsedUrl.host()),
        'port': parsedUrl.port(80),
        'path': str(path)
    })

class CoverArtOptionsPage(OptionsPage):
    NAME = "coverartproviders"
    TITLE = "Providers"
    PARENT = "cover"

    options = [
            BoolOption("setting", "ca_provider_use_amazon", True),
            BoolOption("setting", "ca_provider_use_cdbaby", True),
            BoolOption("setting", "ca_provider_use_caa", True),
            BoolOption("setting", "ca_provider_use_jamendo", True),
            BoolOption("setting", "ca_provider_use_whitelist", True),
            BoolOption("setting", "caa_approved_only", False),
            IntOption("setting", "caa_image_size", 2),
            TextOption("setting", "caa_image_types", "front"),
            ]

    def __init__(self, parent=None):
        super(CoverArtOptionsPage, self).__init__(parent)
        self.ui = Ui_CoverartOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.caprovider_amazon.setChecked(self.config.setting["ca_provider_use_amazon"])
        self.ui.caprovider_cdbaby.setChecked(self.config.setting["ca_provider_use_cdbaby"])
        self.ui.caprovider_caa.setChecked(self.config.setting["ca_provider_use_caa"])
        self.ui.caprovider_jamendo.setChecked(self.config.setting["ca_provider_use_jamendo"])
        self.ui.caprovider_whitelist.setChecked(self.config.setting["ca_provider_use_whitelist"])
        self.ui.gb_caa.setEnabled(self.config.setting["ca_provider_use_caa"])

        self.ui.cb_image_size.setCurrentIndex(self.config.setting["caa_image_size"])
        self.ui.le_image_types.setText(self.config.setting["caa_image_types"])
        self.ui.cb_approved_only.setChecked(self.config.setting["caa_approved_only"])

    def save(self):
        self.config.setting["ca_provider_use_amazon"] =\
            self.ui.caprovider_amazon.isChecked()
        self.config.setting["ca_provider_use_cdbaby"] =\
            self.ui.caprovider_cdbaby.isChecked()
        self.config.setting["ca_provider_use_caa"] =\
            self.ui.caprovider_caa.isChecked()
        self.config.setting["ca_provider_use_jamendo"] =\
            self.ui.caprovider_jamendo.isChecked()
        self.config.setting["ca_provider_use_whitelist"] =\
            self.ui.caprovider_whitelist.isChecked()
        self.config.setting["caa_image_size"] =\
            self.ui.cb_image_size.currentIndex()
        self.config.setting["caa_image_types"] = self.ui.le_image_types.text()
        self.config.setting["caa_approved_only"] =\
            self.ui.cb_approved_only.isChecked()

picard.webservice.REQUEST_DELAY[("coverartarchive.org", 80)] = 0
register_album_metadata_processor(coverart)
register_options_page(CoverArtOptionsPage)
