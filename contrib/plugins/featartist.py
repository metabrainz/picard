PLUGIN_NAME = 'Feat. Artists Removed'
PLUGIN_AUTHOR = 'Lukas Lalinsky, Bryan Toth'
PLUGIN_DESCRIPTION = 'Removes feat. artists from track titles.  Substitution is case insensitive.'
PLUGIN_VERSION = "0.2"
PLUGIN_API_VERSIONS = ["0.9.0", "0.10", "0.15", "0.16"]

from picard.metadata import register_track_metadata_processor
import re


def remove_featartists(tagger, metadata, release, track):
    metadata["title"] = re.sub(r"\s+\(feat. [^)]*\)", "", metadata["title"], flags=re.IGNORECASE)

register_track_metadata_processor(remove_featartists)
