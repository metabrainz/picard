PLUGIN_NAME = 'Initials'
PLUGIN_AUTHOR = 'Lukas Lalinsky'
PLUGIN_DESCRIPTION = 'Provides tagger script function $initials(text).'

from picard.script import register_script_function

def initials(parser, text):
    return "".join(a[:1] for a in text.split(" ") if a[:1].isalpha())

register_script_function(initials)
