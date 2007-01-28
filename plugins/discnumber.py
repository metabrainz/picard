PLUGIN_NAME = 'Disc Numbers'
PLUGIN_AUTHOR = 'Lukas Lalinsky'
PLUGIN_DESCRIPTION = 'Moves disc numbers from album titles to tags.'

from picard.metadata import register_album_metadata_processor
import re

def remove_discnumbers(tagger, metadata, release):
    matches = re.search(r"\(disc (\d+)\)", metadata["album"])
    if matches:
        metadata["discnumber"] = matches.group(1)
        metadata["album"] = re.sub(r"\(disc \d+\)", "", metadata["album"])

register_album_metadata_processor(remove_discnumbers)
