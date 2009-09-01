PLUGIN_NAME = 'First alphabetic character function'
PLUGIN_AUTHOR = 'Philipp Wolfer'
PLUGIN_DESCRIPTION = 'Provides the tagger script function $firstalphachar(text, nonalpha=#).'
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.9.0", "0.10", "0.11", "0.12"]

from picard.script import register_script_function

def firstalphachar(parser, text, nonalpha="#"):
    if len(text) == 0:
        return nonalpha
    firstchar = text[0]
    if firstchar.isalpha():
        return firstchar.upper()
    else:
        return nonalpha

register_script_function(firstalphachar)
