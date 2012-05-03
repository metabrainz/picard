PLUGIN_NAME = 'Feat. Artists in Titles'
PLUGIN_AUTHOR = 'Lukas Lalinsky, Michael Wiencek, Bryan Toth'
PLUGIN_DESCRIPTION = 'Move "feat." from artist names to album and track titles. Match is case insensitive.'
PLUGIN_VERSION = "0.2"
PLUGIN_API_VERSIONS = ["0.9.0", "0.10", "0.15", "0.16"]

from picard.metadata import register_album_metadata_processor, register_track_metadata_processor
import re

def move_album_featartists(tagger, metadata, release):
    match = re.match(r"([\s\S]+) feat.([\s\S]+)", metadata["albumartist"], re.IGNORECASE)
    if match:
        metadata["albumartist"] = match.group(1)
        metadata["album"] += " (feat.%s)" % match.group(2)

def move_track_featartists(tagger, metadata, release, track):
    match = re.match(r"([\s\S]+) feat.([\s\S]+)", metadata["artist"], re.IGNORECASE)
    if match:
        metadata["artist"] = match.group(1)
        metadata["title"] += " (feat.%s)" % match.group(2)

register_album_metadata_processor(move_album_featartists)
register_track_metadata_processor(move_track_featartists)
