PLUGIN_NAME = 'Number of matched tracks'
PLUGIN_AUTHOR = 'Nikolai Prokoschenko'
PLUGIN_DESCRIPTION = '''Provides a scripting function called $matchedtracks, which returns the number of tracks matched in an album. Useful for distinguishing complete and incomplete releases'''
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.9.0", "0.10"]


from picard.script import register_script_function

def matchedtracks(parser, arg):
    # FIXME arg is actually not needed, why is it used by eval?
    if parser.file:
        if parser.file.parent:
            return str(parser.file.parent.album.get_num_matched_tracks())
    return "0"

register_script_function(matchedtracks)
