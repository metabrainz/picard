import traceback

from PyQt4 import QtCore

from picard.track import Track
from picard.metadata import Metadata, run_track_metadata_processors
from picard.mbxml import medium_to_metadata, track_to_metadata
from picard.util import partial


class Medium(QtCore.QObject):

    def __init__(self, album, release, medium):
        self.album = album
        self.metadata = Metadata()
        self.tracks = []
        self._parse_medium(release, medium)

    def __getattr__(self, name):
        return self.metadata[name]

    def _parse_medium(self, release, medium):
        album = self.album
        m = self.metadata
        am = album._new_metadata
        m.copy(am)

        medium_to_metadata(medium, m)

        for track_node in medium.track_list[0].track:
            track = Track(track_node.recording[0].id, album)
            self.tracks.append(track)

            # Get track metadata
            tm = track.metadata
            tm.copy(m)
            track_to_metadata(track_node, track, self.config)
            am.length += tm.length

            album.artists.add(tm["musicbrainz_artistid"])

            track._customize_metadata()

            # Run track metadata plugins
            try:
                run_track_metadata_processors(album, tm, release, track_node)
            except:
                self.log.error(traceback.format_exc())

        album._new_tracks.extend(self.tracks)
