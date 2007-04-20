PLUGIN_NAME = 'Amazon Cover Art Downloader'
PLUGIN_AUTHOR = 'Lukas Lalinsky'
PLUGIN_DESCRIPTION = '''Downloads cover art from Amazon.'''

from picard.metadata import register_album_metadata_processor
from picard.util import partial

_AMAZON_IMAGE_HOST = 'images.amazon.com'
_AMAZON_IMAGE_PATH = '/images/P/%s.01.LZZZZZZZ.jpg'
_AMAZON_IMAGE_PATH_SMALL = '/images/P/%s.01.MZZZZZZZ.jpg'

def _coverart_downloaded(album, metadata, path, data, http, error):
    try:
        if error:
            album.log.error(str(http.errorString()))
        else:
            if len(data) > 1000:
                image = ("image/jpeg", data)
                metadata.add("~artwork", image)
                for track in album._new_tracks:
                    track.metadata.add("~artwork", image)
            elif path.endswith('LZZZZZZZ.jpg'):
                amazon_coverart(album, metadata, None, _AMAZON_IMAGE_PATH_SMALL)
    finally:
        album._requests -= 1
        album._finalize_loading(None)

def amazon_coverart(album, metadata, release, path=_AMAZON_IMAGE_PATH):
    asin = metadata['asin']
    if asin:
        album._requests += 1
        album.tagger.xmlws.download(
            _AMAZON_IMAGE_HOST, 80, path % asin,
            partial(_coverart_downloaded, album, metadata, path),
            position=1)

register_album_metadata_processor(amazon_coverart)
