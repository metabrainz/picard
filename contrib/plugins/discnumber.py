PLUGIN_NAME = 'Disc Numbers'
PLUGIN_AUTHOR = 'Lukas Lalinsky'
PLUGIN_DESCRIPTION = '''Moves disc numbers and subtitles from album titles to separate tags. For example:<br/>
<em>"Aerial (disc 1: A Sea of Honey)"</em>
<ul>
    <li>album = <em>"Aerial"</em></li>
    <li>discnumber = <em>"1"</em></li>
    <li>discsubtitle = <em>"A Sea of Honey"</em></li>
</ul>'''
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.9.0", "0.10", "0.15"]

from picard.metadata import register_album_metadata_processor
import re

_discnumber_re = re.compile(r"\s+\(disc (\d+)(?::\s+([^)]+))?\)")


def remove_discnumbers(tagger, metadata, release):
    matches = _discnumber_re.search(metadata["album"])
    if matches:
        metadata["discnumber"] = matches.group(1)
        if matches.group(2):
            metadata["discsubtitle"] = matches.group(2)
        metadata["album"] = _discnumber_re.sub('', metadata["album"])

register_album_metadata_processor(remove_discnumbers)
