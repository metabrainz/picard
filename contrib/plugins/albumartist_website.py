# -*- coding: utf-8 -*-

PLUGIN_NAME = _(u'Album Artist Website')
PLUGIN_AUTHOR = u'Sophist'
PLUGIN_DESCRIPTION = u'''Add's the album artist(s) Official Homepage(s)
(if they are defined in the MusicBrainz database).'''
PLUGIN_VERSION = '0.3'
PLUGIN_API_VERSIONS = ["0.15.0", "0.15.1", "0.16.0", "1.0.0", "1.1.0", "1.2.0", "1.3.0"]

from picard import config, log
from picard.util import LockableObject
from picard.metadata import register_track_metadata_processor
from functools import partial

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
                    track_metadata['website'] = self.website_cache[artistId]
            else:
                # Jump through hoops to get track object!!
                self.website_add_track(album, album._new_tracks[-1], artistId)


    def website_add_track(self, album, track, artistId):
        self.album_add_request(album)
        if self.website_queue.append(artistId, (track, album)):
            host = config.setting["server_host"]
            port = config.setting["server_port"]
            path = "/ws/2/%s/%s?inc=%s" % ('artist', artistId, 'url-rels')
            return album.tagger.xmlws.get(host, port, path,
                        partial(self.website_process, artistId),
                        xml=True, priority=True, important=False)

    def website_process(self, artistId, response, reply, error):
        if error:
            log.error("%s: %r: Network error retrieving artist record", PLUGIN_NAME, artistId)
            tuples = self.website_queue.remove(artistId)
            for track, album in tuples:
                self.album_remove_request(album)
            return
        urls = self.artist_process_metadata(artistId, response)
        self.website_cache[artistId] = urls
        tuples = self.website_queue.remove(artistId)
        log.debug("%s: %r: Artist Official Homepages = %s", PLUGIN_NAME, artistId, url)
        for track, album in tuples:
            self.album_remove_request(album)
            if urls:
                tm = track.metadata
                tm['website'] = urls
                for file in track.iterfiles(True):
                    fm = file.metadata
                    fm['website'] = urls


    def album_add_request(self, album):
        album._requests += 1

    def album_remove_request(self, album):
        album._requests -= 1
        if album._requests == 0:
            album._finalize_loading(None)


    def artist_process_metadata(self, artistId, response):
        if 'metadata' in response.children:
            if 'artist' in response.metadata[0].children:
                if 'relation_list' in response.metadata[0].artist[0].children:
                    if 'relation' in response.metadata[0].artist[0].relation_list[0].children:
                        return self.artist_process_relations(response.metadata[0].artist[0].relation_list[0].relation)
        log.error("%s: %r: MusicBrainz artist xml result not in correct format - %s", PLUGIN_NAME, artistId, response)
        return None

    def artist_process_relations(self, relations):
        urls = []
        for relation in relations:
            if relation.type == 'official homepage' \
                and 'target' in relation.children:
                urls.append(relation.target[0].text)
        return urls


register_track_metadata_processor(AlbumArtistWebsite().add_artist_website)
