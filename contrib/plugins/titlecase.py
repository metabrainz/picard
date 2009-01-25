# Copyright 2007 Javier Kohen
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

import unicodedata

def iswbound(char):
    """Returns whether the given character is a word boundary."""
    category = unicodedata.category(char)
    # If it's a space separator or punctuation
    return 'Zs' == category or 'Sk' == category or 'P' == category[0]

def utitle(string):
    """Title-case a string using a less destructive method than str.title."""
    new_string = string[0].capitalize()
    cap = False
    for i in xrange(1, len(string)):
        s = string[i]
        # Special case apostrophe in the middle of a word.
        if u"'" == s and string[i-1].isalpha(): cap = False
        elif iswbound(s): cap = True
        elif cap and s.isalpha():
            cap = False
            s = s.capitalize()
        else: cap = False
        new_string += s
    return new_string

def title(string, locale="utf-8"):
    """Title-case a string using a less destructive method than str.title."""
    if not string: return u""
    # if the string is all uppercase, lowercase it - Erich/Javier
    #   Lots of Japanese songs use entirely upper-case English titles,
    #   so I don't like this change... - JoeW
    #if string == string.upper(): string = string.lower()
    if not isinstance(string, unicode):
        string = string.decode(locale)
    return utitle(string)


PLUGIN_NAME = "Title Case"
PLUGIN_API_VERSIONS = ["0.9", "0.10", "0.11"]
PLUGIN_DESCRIPTION = "Capitalize First Character In Every Word Of A Title"
from picard.metadata import (
    register_track_metadata_processor,
    register_album_metadata_processor,
    )

def title_case(tagger, metadata, release, track=None):
    for name, value in metadata.rawitems():
        if name in ["title", "album", "artist"]:
            metadata[name] = [title(x) for x in value]

register_track_metadata_processor(title_case)
register_album_metadata_processor(title_case)
