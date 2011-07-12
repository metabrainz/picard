PLUGIN_NAME = 'Release Type'
PLUGIN_AUTHOR = 'Elliot Chance'
PLUGIN_DESCRIPTION = 'Appends information to EPs and Singles'
PLUGIN_VERSION = '1.2'
PLUGIN_API_VERSIONS = ["0.9.0", "0.10", "0.15"]

from picard.metadata import register_album_metadata_processor
import re

#==================
# options
#==================
_SINGLE = " (single)"
_EP = " EP"

def add_release_type(tagger, metadata, release):

  # make sure "EP" (or "single", ...) is not already a word in the name
  words = metadata["album"].lower().split(" ")
  for word in ["ep", "e.p.", "single", "(single)"]:
    if word in words:
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

