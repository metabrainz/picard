# -*- coding: utf-8 -*-

PLUGIN_NAME = _(u'Musicians Sorted')
PLUGIN_AUTHOR = u'Sophist'
PLUGIN_DESCRIPTION = u'''Changes musicians tags (e.g. Performer, Composer, Lyricist etc.)
from unsorted names (forename surname) to sorted names (surname, forename).
<br/><br/>
Sort Multi-Value Tags plugin can be used with or without this plugin.
If used without this plugin, then musicians tags are sorted by forename.
If used with this plugin, then musicians tags are sorted by surname.'''
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ["1.3.0"]

from picard.metadata import register_track_metadata_processor

def use_musicians_sorted(self, album, metadata, *args):

    for key in metadata.keys():
        if key.startswith('~') or key.endswith('sort'):
            continue
        if ':' in key:
            mainkey, subkey = key.split(':', 1)
        else:
            mainkey = key
            subkey = None
        sortedkey = '~%ssort%s' % (
            mainkey,
            (':' + subkey) if subkey else '',
            )
        unsortedkey = '~%s%s' % (
            mainkey,
            (':' + subkey) if subkey else '',
            )
        if not sortedkey in metadata:
            continue
        metadata[unsortedkey] = dict.get(metadata,key)
        metadata[key] = dict.get(metadata,sortedkey)

register_track_metadata_processor(use_musicians_sorted)
