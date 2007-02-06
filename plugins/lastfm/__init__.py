# -*- coding: utf-8 -*-

PLUGIN_NAME = u'Last.fm'
PLUGIN_AUTHOR = u'Lukáš Lalinsky'
PLUGIN_DESCRIPTION = u''

import re
import urllib
from PyQt4 import QtGui
from musicbrainz2.model import VARIOUS_ARTISTS_ID
from picard.metadata import register_album_metadata_processor, register_track_metadata_processor
from picard.ui.options import register_options_page, OptionsPage
from xml.dom.minidom import parse
from picard.config import BoolOption, IntOption, TextOption
from picard.plugins.lastfm.ui_options_lastfm import Ui_LastfmOptionsPage

# TODO: move this to an options page
JOIN_TAGS = None # use e.g. "/" to produce only one "genre" tag with "Tag1/Tag2"
TRANSLATE_TAGS = {
    "hip hop": "hip-hop",
    "synth-pop": "synthpop",
    "electronica": "electronic",
}
TITLE_CASE = True


def get_text(root):
    text = []
    for node in root.childNodes:
        if node.nodeType == node.TEXT_NODE:
            text.append(node.data)
    return "".join(text)


def get_tags(ws, url, min_usage, ignore):
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
        if count < min_usage:
            break
        try: name = TRANSLATE_TAGS[name]
        except KeyError: pass
        tags.append(name.title())
    stream.close()
    return filter(lambda t: t.lower() not in ignore, tags)


def get_track_tags(ws, artist, track, min_usage, ignore):
    """Get track top tags."""
    url = "http://ws.audioscrobbler.com/1.0/track/%s/%s/toptags.xml" % (urllib.quote(artist, ""), urllib.quote(track, ""))
    return get_tags(ws, url, min_usage, ignore)


def get_artist_tags(ws, artist, min_usage, ignore):
    """Get artist top tags."""
    url = "http://ws.audioscrobbler.com/1.0/artist/%s/toptags.xml" % (urllib.quote(artist, ""))
    return get_tags(ws, url, min_usage, ignore)


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
    if tagger.config.setting["lastfm_use_artist_images"] and release.artist.id != VARIOUS_ARTISTS_ID:
        artist = metadata["artist"].encode("utf-8")
        if artist:
            ws = tagger.get_web_service()
            data = get_artist_image(ws, artist)
            if data:
                metadata.add("~artwork", ["image/jpeg", data])


def process_track(tagger, metadata, release, track):
    use_track_tags = tagger.config.setting["lastfm_use_track_tags"]
    use_artist_tags = tagger.config.setting["lastfm_use_artist_tags"]
    min_tag_usage = tagger.config.setting["lastfm_min_tag_usage"]
    ignore_tags = tagger.config.setting["lastfm_ignore_tags"].lower().split(",")
    if use_track_tags or use_artist_tags:
        ws = tagger.get_web_service()
        artist = metadata["artist"].encode("utf-8")
        title = metadata["title"].encode("utf-8")
        tags = []
        if artist:
            if use_artist_tags:
                tags = get_artist_tags(ws, artist, min_tag_usage, ignore_tags)
                # No tags for artist? Why trying track tags...
                if not tags:
                    return
            if title and use_track_tags:
                tags.extend(get_track_tags(ws, artist, title, min_tag_usage, ignore_tags))
        tags = list(set(tags))
        if tags:
            if JOIN_TAGS:
                tags = JOIN_TAGS.join(tags)
            metadata["genre"] = tags


class LastfmOptionsPage(OptionsPage):

    NAME = "lastfm"
    TITLE = "Last.fm"
    PARENT = "plugins"

    options = [
        BoolOption("setting", "lastfm_use_track_tags", False),
        BoolOption("setting", "lastfm_use_artist_tags", False),
        BoolOption("setting", "lastfm_use_artist_images", False),
        IntOption("setting", "lastfm_min_tag_usage", 15),
        TextOption("setting", "lastfm_ignore_tags", "seen live,favorites"),
    ]

    def __init__(self, parent=None):
        super(LastfmOptionsPage, self).__init__(parent)
        self.ui = Ui_LastfmOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.use_track_tags.setChecked(self.config.setting["lastfm_use_track_tags"])
        self.ui.use_artist_tags.setChecked(self.config.setting["lastfm_use_artist_tags"])
        self.ui.use_artist_images.setChecked(self.config.setting["lastfm_use_artist_images"])
        self.ui.min_tag_usage.setValue(self.config.setting["lastfm_min_tag_usage"])
        self.ui.ignore_tags.setText(self.config.setting["lastfm_ignore_tags"])

    def save(self):
        self.config.setting["lastfm_use_track_tags"] = self.ui.use_track_tags.isChecked()
        self.config.setting["lastfm_use_artist_tags"] = self.ui.use_artist_tags.isChecked()
        self.config.setting["lastfm_use_artist_images"] = self.ui.use_artist_images.isChecked()
        self.config.setting["lastfm_min_tag_usage"] = self.ui.min_tag_usage.value()
        self.config.setting["lastfm_ignore_tags"] = unicode(self.ui.ignore_tags.text())


register_track_metadata_processor(process_track)
register_album_metadata_processor(process_album)
register_options_page(LastfmOptionsPage)
