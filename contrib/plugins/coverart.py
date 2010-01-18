""" 
A small plugin to download cover art for any releseas that have a
CoverArtLink or ASIN relation.


Changelog:

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
PLUGIN_AUTHOR = 'Oliver Charles, Philipp Wolfer'
PLUGIN_DESCRIPTION = '''Downloads cover artwork for releases that have a
CoverArtLink or ASIN.'''
PLUGIN_VERSION = "0.6.1"
PLUGIN_API_VERSIONS = ["0.12"]

from picard.metadata import register_album_metadata_processor
from picard.util import partial, mimetype
from PyQt4.QtCore import QUrl
import re

# data transliterated from the perl stuff used to find cover art for the
# musicbrainz server.
# See mb_server/cgi-bin/MusicBrainz/Server/CoverArt.pm
# hartzell --- Tue Apr 15 15:25:58 PDT 2008
COVERART_SITES = (
    # CD-Baby
    # tested with http://musicbrainz.org/release/1243cc17-b9f7-48bd-a536-b10d2013c938.html
    {
    'regexp': 'http://(www\.)?cdbaby.com/cd/(\w)(\w)(\w*)',
    'imguri': 'http://cdbaby.name/$2/$3/$2$3$4.jpg',
    },
    # Jamendo
    # tested with http://musicbrainz.org/release/2fe63977-bda9-45da-8184-25a4e7af8da7.html
    {
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
    try:
        if error or len(data) < 1000:
            if error:
                album.log.error(str(http.errorString()))
            coverart(album, metadata, release, try_list)
        else:
            mime = mimetype.get_from_data(data, "image/jpeg")
            metadata.add_image(mime, data)
            for track in album._new_tracks:
                track.metadata.add_image(mime, data)
    finally:
        album._requests -= 1
        album._finalize_loading(None)


def coverart(album, metadata, release, try_list=None):
    """ Gets all cover art URLs from the metadata and then attempts to
    download the album art. """

    # try_list will be None for the first call
    if try_list is None:
        try_list = []

        try:
            for relation_list in release.relation_list:
                if relation_list.target_type == 'Url':
                    for relation in relation_list.relation:
                        _process_url_relation(try_list, relation)

                        # Use the URL of a cover art link directly
                        if relation.type == 'CoverArtLink':
                            _try_list_append_image_url(try_list, QUrl(relation.target))
                        elif relation.type == 'AmazonAsin':
                            _process_asin_relation(try_list, relation)
        except AttributeError, e:
            album.log.error(e)

    if len(try_list) > 0:
        # We still have some items to try!
        album._requests += 1
        album.tagger.xmlws.download(
                try_list[0]['host'], try_list[0]['port'], try_list[0]['path'],
                partial(_coverart_downloaded, album, metadata, release, try_list[1:]),
                position=1)


def _process_url_relation(try_list, relation):
    # Search for cover art on special sites
    for site in COVERART_SITES:
        # this loop transliterated from the perl stuff used to find cover art for the
        # musicbrainz server.
        # See mb_server/cgi-bin/MusicBrainz/Server/CoverArt.pm
        # hartzell --- Tue Apr 15 15:25:58 PDT 2008
        match = re.match(site['regexp'], relation.target)
        if match != None:
            imgURI = site['imguri']
            for i in range(1, len(match.groups())+1 ):
                if match.group(i) != None:
                    imgURI = imgURI.replace('$' + str(i), match.group(i))
            _try_list_append_image_url(try_list, QUrl(imgURI))


def _process_asin_relation(try_list, relation):
    match = AMAZON_ASIN_URL_REGEX.match(relation.target)
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
    path = parsedUrl.path()
    if parsedUrl.hasQuery():
        path += '?'+'&'.join(["%s=%s" % (k,v) for k,v in parsedUrl.queryItems()])
    try_list.append({
        'host': str(parsedUrl.host()),
        'port': parsedUrl.port(80),
        'path': str(path)
    })

register_album_metadata_processor(coverart)
