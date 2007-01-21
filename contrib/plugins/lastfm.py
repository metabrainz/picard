# -*- coding: utf-8 -*-

PLUGIN_NAME = u'Last.fm'
PLUGIN_AUTHOR = u'Lukáš Lalinsky'
PLUGIN_DESCRIPTION = u''

from musicbrainz2.model import VARIOUS_ARTISTS_ID
from picard.metadata import register_album_metadata_processor, register_track_metadata_processor
from xml.dom.minidom import parse
import re
import urllib

# TODO: move this to an options page
MIN_TAG_COUNT = 15
JOIN_TAGS = None # use e.g. "/" to produce only one "genre" tag with "Tag1/Tag2"
IGNORE_TAGS = ["seen live"]
USE_TRACK_TAGS = True
USE_ARTIST_TAGS = True
USE_ARTIST_IMAGES = True

def get_text(root):
    text = []
    for node in root.childNodes:
        if node.nodeType == node.TEXT_NODE:
            text.append(node.data)
    return "".join(text)

def get_tags(ws, url):
    """Get tags from an URL."""
    try:
        stream = ws.get_from_url(url)
    except IOError:
        return []
    dom = parse(stream)
    tags = []
    for tag in dom.getElementsByTagName("toptags")[0].getElementsByTagName("tag"):
        name = get_text(tag.getElementsByTagName("name")[0]).strip()
        count = int(get_text(tag.getElementsByTagName("count")[0]).strip())
        if count < MIN_TAG_COUNT:
            break
        tags.append(name)
    stream.close()
    return filter(lambda t: t not in IGNORE_TAGS, tags)

def get_track_tags(ws, artist, track):
    """Get track top tags."""
    url = "http://ws.audioscrobbler.com/1.0/track/%s/%s/toptags.xml" % (urllib.quote(artist, ""), urllib.quote(track, ""))
    return get_tags(ws, url)

def get_artist_tags(ws, artist):
    """Get artist top tags."""
    url = "http://ws.audioscrobbler.com/1.0/artist/%s/toptags.xml" % (urllib.quote(artist, ""))
    return get_tags(ws, url)

def get_artist_image(ws, artist):
    """Get the main artist image."""
    url = "http://ws.audioscrobbler.com/ass/artistmetadata.php?%s" % (urllib.urlencode({"artist": artist}))
    try:
        stream = ws.get_from_url(url)
    except IOError:
        return None
    res = stream.read()
    stream.close()
    res = res.split("\t")
    if len(res) != 4:
        return None
    image_url = res[3][1:-1]
    if not image_url.startswith("http://static.last.fm"):
        return None
    stream = ws.get_from_url(image_url)
    data = stream.read()
    stream.close()
    return data

def process_album(tagger, metadata, release):
    if USE_ARTIST_IMAGES and release.artist.id != VARIOUS_ARTISTS_ID:
        artist = metadata["artist"].encode("utf-8")
        if artist:
            ws = tagger.get_web_service()
            data = get_artist_image(ws, artist)
            if data:
                metadata.add("~artwork", ["image/jpeg", data])

def process_track(tagger, metadata, release, track):
    if USE_TRACK_TAGS or USE_ARTIST_TAGS:
        ws = tagger.get_web_service()
        artist = metadata["artist"].encode("utf-8")
        title = metadata["title"].encode("utf-8")
        tags = []
        if artist:
            if USE_TRACK_TAGS:
                tags = get_artist_tags(ws, artist)
                # No tags for artist? Why trying track tags...
                if not tags:
                    return
            if title and USE_ARTIST_TAGS:
                tags.extend(get_track_tags(ws, artist, title))
        tags = list(set(tags))
        if tags:
            if JOIN_TAGS:
                tags = JOIN_TAGS.join(tags)
            metadata["genre"] = tags

register_track_metadata_processor(process_track)
register_album_metadata_processor(process_album)
