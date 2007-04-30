# -*- coding: utf-8 -*-

PLUGIN_NAME = u'Last.fm'
PLUGIN_AUTHOR = u'Lukáš Lalinský'
PLUGIN_DESCRIPTION = u'Use tags from Last.fm as genre.'

from PyQt4 import QtGui, QtCore
from picard.metadata import register_album_metadata_processor, register_track_metadata_processor
from picard.ui.options import register_options_page, OptionsPage
from picard.config import BoolOption, IntOption, TextOption
from picard.plugins.lastfm.ui_options_lastfm import Ui_LastfmOptionsPage
from picard.util import partial

# TODO: move this to an options page
_cache = {}
JOIN_TAGS = None # use e.g. "/" to produce only one "genre" tag with "Tag1/Tag2"
TRANSLATE_TAGS = {
    "hip hop": u"Hip-Hop",
    "synth-pop": u"Synthpop",
    "electronica": u"Electronic",
}
TITLE_CASE = True


def _tags_finalize(album, metadata, tags, next):
    if next:
        album._requests += 1
        next(tags)
    else:
        tags = list(set(tags))
        if tags:
            if JOIN_TAGS:
                tags = JOIN_TAGS.join(tags)
            metadata["genre"] = tags


def _tags_downloaded(album, metadata, min_usage, ignore, next, current, data, http, error):
    try:
        try: intags = data.toptags[0].tag
        except AttributeError: intags = []
        tags = []
        for tag in intags:
            name = tag.name[0].text.strip()
            try: count = int(tag.count[0].text.strip(), 10)
            except ValueError: count = 0
            if count < min_usage:
                break
            try: name = TRANSLATE_TAGS[name]
            except KeyError: pass
            if name.lower() not in ignore:
                tags.append(name.title())
        _cache[str(http.currentRequest().path())] = tags
        _tags_finalize(album, metadata, current + tags, next)
    finally:
        album._requests -= 1
        album._finalize_loading(None)


def get_tags(album, metadata, path, min_usage, ignore, next, current):
    """Get tags from an URL."""
    try:
        if path in _cache:
            _tags_finalize(album, metadata, _cache[path], next)
        else:
            album._requests += 1
            album.tagger.xmlws.get("ws.audioscrobbler.com", 80, path,
                partial(_tags_downloaded, album, metadata, min_usage, ignore, next, current),
                position=1)
    finally:
        album._requests -= 1
        album._finalize_loading(None)
    return False


def get_track_tags(album, metadata, artist, track, min_usage, ignore, next, current):
    """Get track top tags."""
    path = "/1.0/track/%s/%s/toptags.xml" % (
        QtCore.QUrl.toPercentEncoding(artist),
        QtCore.QUrl.toPercentEncoding(track))
    return get_tags(album, metadata, path, min_usage, ignore, next, current)


def get_artist_tags(album, metadata, artist, min_usage, ignore, next, current):
    """Get artist top tags."""
    path = "/1.0/artist/%s/toptags.xml" % (
        QtCore.QUrl.toPercentEncoding(artist),)
    return get_tags(album, metadata, path, min_usage, ignore, next, current)


def process_track(album, metadata, release, track):
    tagger = album.tagger
    use_track_tags = tagger.config.setting["lastfm_use_track_tags"]
    use_artist_tags = tagger.config.setting["lastfm_use_artist_tags"]
    min_tag_usage = tagger.config.setting["lastfm_min_tag_usage"]
    ignore_tags = tagger.config.setting["lastfm_ignore_tags"].lower().split(",")
    if use_track_tags or use_artist_tags:
        artist = metadata["artist"].encode("utf-8")
        title = metadata["title"].encode("utf-8")
        if artist:
            if use_artist_tags:
                get_artist_tags_func = partial(get_artist_tags, album, metadata, artist, min_tag_usage, ignore_tags, None)
            else:
                get_artist_tags_func = None
            if title and use_track_tags:
                func = partial(get_track_tags, album, metadata, artist, title, min_tag_usage, ignore_tags, get_artist_tags_func, [])
            elif get_artist_tags_func:
                func = partial(get_artist_tags_func, [])
            if func:
                album._requests += 1
                tagger.xmlws.add_task(func, position=1)


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
#register_album_metadata_processor(process_album)
register_options_page(LastfmOptionsPage)
