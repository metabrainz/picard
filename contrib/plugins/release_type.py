PLUGIN_NAME = 'Release Type'
PLUGIN_AUTHOR = 'Elliot Chance'
PLUGIN_DESCRIPTION = 'Appends information to EPs and Singles'
PLUGIN_VERSION = '1.0'
PLUGIN_API_VERSIONS = ["0.9.0"]

from picard.metadata import register_album_metadata_processor
import re

#==================
# options
#==================
_SINGLE = " (single)"
_EP = " EP"

def add_release_type(tagger, metadata, release):

  # make sure "EP" isn't already at the end
  if metadata["album"].lower().endswith(" ep"):
    return
  elif metadata["album"].lower().endswith(" single"):
    return

  # check release type
  if metadata["releasetype"] == "ep":
    rs = _EP;
  elif metadata["releasetype"] == "single":
    rs = _SINGLE;
  else:
    rs = ""

  # append title
  metadata["album"] = metadata["album"] + rs

register_album_metadata_processor(add_release_type)

