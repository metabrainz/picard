PLUGIN_NAME = 'Feat. Artists'
PLUGIN_AUTHOR = 'Lukas Lalinsky'
PLUGIN_DESCRIPTION = 'Removes feat. artists from track titles.'
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.9.0", "0.10"]

from picard.metadata import register_track_metadata_processor
import re

def remove_featartists(tagger, metadata, release, track):
    metadata["title"] = re.sub(r"\s+\(feat. [^)]*\)", "", metadata["title"])

register_track_metadata_processor(remove_featartists)
