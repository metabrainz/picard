""" 
A small plugin to download cover art for any releseas that have a
CoverArtLink relation.


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
CoverArtLink.'''
PLUGIN_VERSION = "0.4"
PLUGIN_API_VERSIONS = ["0.9.0", "0.10"]

from picard.metadata import register_album_metadata_processor
from picard.util import partial
from PyQt4.QtCore import QUrl
import re

#
# data transliterated from the perl stuff used to find cover art for the
# musicbrainz server.
# See mb_server/cgi-bin/MusicBrainz/Server/CoverArt.pm
# hartzell --- Tue Apr 15 15:25:58 PDT 2008
coverArtSites = [
    # CD-Baby
    # tested with http://musicbrainz.org/release/1243cc17-b9f7-48bd-a536-b10d2013c938.html
    {
    'regexp': 'http://cdbaby.com/cd/(\w)(\w)(\w*)',
    'imguri': 'http://cdbaby.name/$1/$2/$1$2$3.jpg',
    },
    # Jamendo
    # tested with http://musicbrainz.org/release/2fe63977-bda9-45da-8184-25a4e7af8da7.html
    {
    'regexp': 'http:\/\/(?:www.)?jamendo.com\/(?:[a-z]+\/)?album\/([0-9]+)',
    'imguri': 'http://www.jamendo.com/get/album/id/album/artworkurl/redirect/$1/?artwork_size=0',
    },
    ]

_AMAZON_IMAGE_HOST = 'images.amazon.com'
_AMAZON_IMAGE_PATH = '/images/P/%s.01.LZZZZZZZ.jpg'
_AMAZON_IMAGE_PATH_SMALL = '/images/P/%s.01.MZZZZZZZ.jpg'
_AMAZON_IMAGE_PATH2 = '/images/P/%s.02.LZZZZZZZ.jpg'
_AMAZON_IMAGE_PATH2_SMALL = '/images/P/%s.02.MZZZZZZZ.jpg'

def _coverart_downloaded(album, metadata, release, try_list, data, http, error):
    try:
        if error or len(data) < 1000:
            if error:
                album.log.error(str(http.errorString()))
            coverart(album, metadata, release, try_list)
        else:
            metadata.add_image("image/jpeg", data)
            for track in album._new_tracks:
                track.metadata.add_image("image/jpeg", data)
    finally:
        album._requests -= 1
        album._finalize_loading(None)


def coverart(album, metadata, release, try_list=None):
    """ Gets the CDBaby URL from the metadata, and the attempts to
    download the album art. """

    # try_list will be None for the first call
    if try_list is None:
        try_list = []

        try:
            for relation_list in release.relation_list:
                if relation_list.target_type == 'Url':
                    for relation in relation_list.relation:
                        # Search for cover art on special sites
                        for site in coverArtSites:
                            #
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

                        # Use the URL of a cover art link directly
                        if relation.type == 'CoverArtLink':
                            _try_list_append_image_url(try_list, QUrl(relation.target))
        except AttributeError:
            pass

        if metadata['asin']:
            try_list.append({'host': _AMAZON_IMAGE_HOST, 'port': 80,
                'path': _AMAZON_IMAGE_PATH % metadata['asin']
            })
            try_list.append({'host': _AMAZON_IMAGE_HOST, 'port': 80,
                'path': _AMAZON_IMAGE_PATH_SMALL % metadata['asin']
            })
            try_list.append({'host': _AMAZON_IMAGE_HOST, 'port': 80,
                'path': _AMAZON_IMAGE_PATH2 % metadata['asin']
            })
            try_list.append({'host': _AMAZON_IMAGE_HOST, 'port': 80,
                'path': _AMAZON_IMAGE_PATH2_SMALL % metadata['asin']
            })

    if len(try_list) > 0:
        # We still have some items to try!
        album._requests += 1
        album.tagger.xmlws.download(
                try_list[0]['host'], try_list[0]['port'], try_list[0]['path'],
                partial(_coverart_downloaded, album, metadata, release, try_list[1:]),
                position=1)

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
