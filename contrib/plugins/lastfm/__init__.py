# -*- coding: utf-8 -*-

PLUGIN_NAME = u'Last.fm'
PLUGIN_AUTHOR = u'Lukáš Lalinský'
PLUGIN_DESCRIPTION = u'Use tags from Last.fm as genre.'
PLUGIN_VERSION = "0.4"
PLUGIN_API_VERSIONS = ["0.15"]

from PyQt4 import QtCore
from picard.metadata import register_track_metadata_processor
from picard.ui.options import register_options_page, OptionsPage
from picard.config import BoolOption, IntOption, TextOption
from picard.plugins.lastfm.ui_options_lastfm import Ui_LastfmOptionsPage
from picard.util import partial
import traceback

LASTFM_HOST = "ws.audioscrobbler.com"
LASTFM_PORT = 80

# From http://www.last.fm/api/tos, 2011-07-30
# 4.4 (...) You will not make more than 5 requests per originating IP address per second, averaged over a
# 5 minute period, without prior written consent. (...)
from picard.webservice import REQUEST_DELAY
REQUEST_DELAY[(LASTFM_HOST, LASTFM_PORT)] = 200

# Cache for Tags to avoid re-requesting tags within same Picard session
_cache = {}
# Keeps track of requests for tags made to webservice API but not yet returned (to avoid re-requesting the same URIs)
_pending_xmlws_requests = {}

# TODO: move this to an options page
TRANSLATE_TAGS = {
    "hip hop": u"Hip-Hop",
    "synth-pop": u"Synthpop",
    "electronica": u"Electronic",
}
TITLE_CASE = True


def _tags_finalize(album, metadata, tags, next):
    if next:
        next(tags)
    else:
        tags = list(set(tags))
        if tags:
            join_tags = album.tagger.config.setting["lastfm_join_tags"]
            if join_tags:
                tags = join_tags.join(tags)
            metadata["genre"] = tags


def _tags_downloaded(album, metadata, min_usage, ignore, next, current, data, reply, error):
    try:
        try: intags = data.toptags[0].tag
        except AttributeError: intags = []
        tags = []
        for tag in intags:
            name = tag.name[0].text.strip()
            try: count = int(tag.count[0].text.strip())
            except ValueError: count = 0
            if count < min_usage:
                break
            try: name = TRANSLATE_TAGS[name]
            except KeyError: pass
            if name.lower() not in ignore:
                tags.append(name.title())
        url = str(reply.url().path())
        _cache[url] = tags
        _tags_finalize(album, metadata, current + tags, next)

        # Process any pending requests for the same URL
        if url in _pending_xmlws_requests:
            pending = _pending_xmlws_requests[url]
            del _pending_xmlws_requests[url]
            for delayed_call in pending:
                delayed_call()

    except:
        album.tagger.log.error("Problem processing downloaded tags in last.fm plugin: %s", traceback.format_exc())
        raise
    finally:
        album._requests -= 1
        album._finalize_loading(None)


def get_tags(album, metadata, path, min_usage, ignore, next, current):
    """Get tags from an URL."""
    url = str(QtCore.QUrl.fromPercentEncoding(path))
    if url in _cache:
        _tags_finalize(album, metadata, current + _cache[url], next)
    else:

        # If we have already sent a request for this URL, delay this call until later
        if url in _pending_xmlws_requests:
            _pending_xmlws_requests[url].append(partial(get_tags, album, metadata, path, min_usage, ignore, next, current))
        else:
            _pending_xmlws_requests[url] = []
            album._requests += 1
            album.tagger.xmlws.get(LASTFM_HOST, LASTFM_PORT, path,
                                   partial(_tags_downloaded, album, metadata, min_usage, ignore, next, current),
                                   priority=True, important=True)


def encode_str(s):
    # Yes, that's right, Last.fm prefers double URL-encoding
    s = QtCore.QUrl.toPercentEncoding(s)
    s = QtCore.QUrl.toPercentEncoding(unicode(s))
    return s

def get_track_tags(album, metadata, artist, track, min_usage, ignore, next, current):
    """Get track top tags."""
    path = "/1.0/track/%s/%s/toptags.xml" % (encode_str(artist), encode_str(track))
    get_tags(album, metadata, path, min_usage, ignore, next, current)


def get_artist_tags(album, metadata, artist, min_usage, ignore, next, current):
    """Get artist top tags."""
    path = "/1.0/artist/%s/toptags.xml" % (encode_str(artist),)
    get_tags(album, metadata, path, min_usage, ignore, next, current)


def process_track(album, metadata, release, track):
    tagger = album.tagger
    use_track_tags = tagger.config.setting["lastfm_use_track_tags"]
    use_artist_tags = tagger.config.setting["lastfm_use_artist_tags"]
    min_tag_usage = tagger.config.setting["lastfm_min_tag_usage"]
    ignore_tags = tagger.config.setting["lastfm_ignore_tags"].lower().split(",")
    if use_track_tags or use_artist_tags:
        artist = metadata["artist"]
        title = metadata["title"]
        if artist:
            if use_artist_tags:
                get_artist_tags_func = partial(get_artist_tags, album, metadata, artist, min_tag_usage, ignore_tags, None)
            else:
                get_artist_tags_func = None
            if title and use_track_tags:
                get_track_tags(album, metadata, artist, title, min_tag_usage, ignore_tags, get_artist_tags_func, [])
            elif get_artist_tags_func:
                get_artist_tags_func([])


class LastfmOptionsPage(OptionsPage):

    NAME = "lastfm"
    TITLE = "Last.fm"
    PARENT = "plugins"

    options = [
        BoolOption("setting", "lastfm_use_track_tags", False),
        BoolOption("setting", "lastfm_use_artist_tags", False),
        IntOption("setting", "lastfm_min_tag_usage", 15),
        TextOption("setting", "lastfm_ignore_tags", "seen live,favorites"),
        TextOption("setting", "lastfm_join_tags", ""),
    ]

    def __init__(self, parent=None):
        super(LastfmOptionsPage, self).__init__(parent)
        self.ui = Ui_LastfmOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.use_track_tags.setChecked(self.config.setting["lastfm_use_track_tags"])
        self.ui.use_artist_tags.setChecked(self.config.setting["lastfm_use_artist_tags"])
        self.ui.min_tag_usage.setValue(self.config.setting["lastfm_min_tag_usage"])
        self.ui.ignore_tags.setText(self.config.setting["lastfm_ignore_tags"])
        self.ui.join_tags.setEditText(self.config.setting["lastfm_join_tags"])

    def save(self):
        self.config.setting["lastfm_use_track_tags"] = self.ui.use_track_tags.isChecked()
        self.config.setting["lastfm_use_artist_tags"] = self.ui.use_artist_tags.isChecked()
        self.config.setting["lastfm_min_tag_usage"] = self.ui.min_tag_usage.value()
        self.config.setting["lastfm_ignore_tags"] = unicode(self.ui.ignore_tags.text())
        self.config.setting["lastfm_join_tags"] = unicode(self.ui.join_tags.currentText())


register_track_metadata_processor(process_track)
register_options_page(LastfmOptionsPage)
