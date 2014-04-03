# -*- coding: utf-8 -*-

PLUGIN_NAME = _(u'Album Artist Website')
PLUGIN_AUTHOR = u'Sophist'
PLUGIN_DESCRIPTION = u'''Add's the album artist(s) Official Homepage(s)
(if they are defined in the MusicBrainz database).'''
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ["0.15.0", "0.15.1", "0.16.0", "1.0.0", "1.1.0", "1.2.0", "1.3.0"]

from picard import config, log
from picard.album import Album
from picard.util import LockableObject
from picard.metadata import register_track_metadata_processor
from PyQt4 import QtCore, QtGui
from functools import partial
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

class AlbumArtistWebsite:

    class ArtistWebsiteQueue(LockableObject):

        def __init__(self):
            LockableObject.__init__(self)
            self.queue = {}

        def __contains__(self, name):
            return name in self.queue

        def __iter__(self):
            return self.queue.__iter__()

        def __getitem__(self, name):
            self.lock_for_read()
            value = self.queue[name] if name in self.queue else None
            self.unlock()
            return value

        def __setitem__(self, name, value):
            self.lock_for_write()
            self.queue[name] = value
            self.unlock()

        def append(self, name, value):
            self.lock_for_write()
            if name in self.queue:
                self.queue[name].append(value)
                value = False
            else:
                self.queue[name] = [value]
                value = True
            self.unlock()
            return value

        def remove(self, name):
            self.lock_for_write()
            value = None
            if name in self.queue:
                value = self.queue[name]
                del self.queue[name]
            self.unlock()
            return value

    def __init__(self):
        self.website_cache = {}
        self.website_queue = self.ArtistWebsiteQueue()

    def add_artist_website(self, album, track_metadata, trackXmlNode, releaseXmlNode):
        albumArtistIds = dict.get(track_metadata,'musicbrainz_albumartistid', [])
        for artistId in albumArtistIds:
            if artistId in self.website_cache:
                if self.website_cache[artistId]:
                    track_metadata.add('website', self.website_cache[artistId])
            else:
                # Jump through hoops to get track object!!
                self.website_add_track(album, album._new_tracks[-1], artistId)


    def website_add_track(self, album, track, artistId):
        if self.website_queue.append(artistId, track):
            host = config.setting["server_host"]
            port = config.setting["server_port"]
            path = "/ws/2/%s/%s?inc=%s" % ('artist', artistId, 'url-rels')
            return album.tagger.xmlws.get(host, port, path,
                        partial(self.website_process, artistId),
                        xml=False, priority=True, important=False)

    def website_process(self, artistId, response, reply, error):
        if error:
            log.error("%s: %r: Network error retrieving artist record", PLUGIN_NAME, artistId)
            self.website_queue.remove(artistId)
            return
        url = self.artist_process_metadata(artistId, response)
        self.website_cache[artistId] = url
        tracks = self.website_queue.remove(artistId)
        log.debug("%s: %r: Artist Official Homepages = %s", PLUGIN_NAME, artistId, url)
        if url:
            for track in tracks:
                tm = track.metadata
                tm.add('website', url)
                track.update()
                for file in track.iterfiles(True):
                    fm = file.metadata
                    fm.add('website', url)
                    file.update()


    def artist_process_metadata(self, artistId, response):
        xml = ET.fromstring(response)
        xmlroot = xml.tag
        if not xmlroot.endswith('metadata'):
            log.error("%s: %r: MusicBrainz artist xml result not in correct format - %s", PLUGIN_NAME, artistId, xml.tag)
            return
        xmlns = xmlroot[0:].split("}")[0] + '}' if xmlroot.startswith('{') else ''
        relationships = xml.findall('.' + ('/' + xmlns).join(['', 'artist', 'relation-list', 'relation']))
        for relationship in relationships:
            if 'type' in relationship.attrib and relationship.attrib['type'] =='official homepage':
                return relationship.findtext(xmlns + 'target')
        return None

register_track_metadata_processor(AlbumArtistWebsite().add_artist_website)
