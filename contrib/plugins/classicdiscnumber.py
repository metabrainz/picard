PLUGIN_NAME = 'Classic Disc Numbers'
PLUGIN_AUTHOR = 'Lukas Lalinsky'
PLUGIN_DESCRIPTION = '''Moves disc numbers and subtitles from the separate tags to album titles.'''
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.15"]

from picard.metadata import register_track_metadata_processor
import re

def add_discnumbers(tagger, metadata, release, track):
    if int(metadata["totaldiscs"] or "0") > 1:
        if "discsubtitle" in metadata:
            metadata["album"] = "%s (disc %s: %s)" % (
                metadata["album"], metadata["discnumber"],
                metadata["discsubtitle"])
        else:
            metadata["album"] = "%s (disc %s)" % (
                metadata["album"], metadata["discnumber"])

register_track_metadata_processor(add_discnumbers)

