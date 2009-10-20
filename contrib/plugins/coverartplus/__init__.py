"""
A small plugin to download cover art for any releseas that have a
CoverArtLink relation.


Changelog:
    [2009-10-11] Added support for Amazon's new api and possibility for configuration
                 NXisGOD

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

PLUGIN_NAME = 'Cover Art Plus'
PLUGIN_AUTHOR = 'Carlin Mangar, Oliver Charles, Philipp Wolfer, Lukas Lalinksy'
PLUGIN_DESCRIPTION = '''Downloads cover artwork for releases that have a
CoverArtLink. Now uses the new Amazon API to get cover art.'''
PLUGIN_VERSION = "0.6"
PLUGIN_API_VERSIONS = ["0.12"]

from PyQt4.QtCore import QUrl
from picard.metadata import register_album_metadata_processor
from picard.util import partial, mimetype
from picard.webservice import *
from picard.tagger import Tagger
import re
import datetime


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

AMAZON_API_LOCATOR = 'free.apisigning.com'
AMAZON_XML="/onca/xml"
ACCESS_KEY='AKIAJU7ZJ3PGRVJG6LSA'
AMAZON_SIGNATURE=''
_re_fixdate=re.compile(":")
_re_detecturl=re.compile(r"(?<=\<LargeImage><URL>)https?://(\w*:\w*@)?[-\w.]+(:\d+)?(/([\w/_.]*(\?\S+)?)?)?(?=</URL>)")

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
                                _try_list_append_image_url(try_list, QUrl.fromEncoded(str(imgURI)))

                        # Use the URL of a cover art link directly
                        if relation.type == 'CoverArtLink':
                            _try_list_append_image_url(try_list, QUrl.fromEncoded(str(relation.target)))
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

            path = '%s?Service=AWSECommerceService&AWSAccessKeyId=%s&ItemId=%s&Operation=ItemLookup&ResponseGroup=Images&Timestamp=%s&Version=%s' \
            % ( AMAZON_XML, ACCESS_KEY, metadata['asin'], _re_fixdate.sub("%3A",datetime.datetime.now().isoformat()[:23]+"Z"),datetime.date.today().isoformat())
            album._requests += 1
            album.tagger.xmlws.get(AMAZON_API_LOCATOR, 80, path,
                partial(_url_downloaded, album, metadata, release, try_list))

    if len(try_list) > 0:
        # We still have some items to try!
        album._requests += 1
        album.tagger.xmlws.download(
                try_list[0]['host'], try_list[0]['port'], try_list[0]['path'],
                partial(_coverart_downloaded, album, metadata, release, try_list[1:]),
                position=1)


def _parse_image_url(parsed_url):
    path = parsed_url.path()
    if parsed_url.hasQuery():
        path += '?' + location.encodedQuery()
    return {
        'host': str(parsed_url.host()),
        'port': parsed_url.port(80),
        'path': str(path)
    }

def _try_list_append_image_url(try_list, parsed_url):
    try_list.append(_parse_image_url(parsed_url))

def _url_downloaded(album, metadata, release, try_list, data, http, error):
    album._requests -= 1
    if data:
        try:
            url = data.ItemLookupResponse[0].Items[0].Item[0].LargeImage[0].URL[0].text
            try_list.insert(0, _parse_image_url(QUrl.fromEncoded(str(url))))
        except AttributeError:
            try:
                url = data.ItemLookupResponse[0].Items[0].Item[0].MediumImage[0].URL[0].text
                try_list.insert(0, _parse_image_url(QUrl.fromEncoded(str(url))))
            except AttributeError:
                pass
    coverart(album, metadata, release, try_list)

register_album_metadata_processor(coverart)
