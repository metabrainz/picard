# -*- coding: utf-8 -*-

PLUGIN_NAME = _(u'Standardise Performers')
PLUGIN_AUTHOR = u'Sophist'
PLUGIN_DESCRIPTION = u'''Splits multi-instrument performer tags into single
instruments and combines names so e.g. (from 10cc by 10cc track 1):
<pre>
Performer [acoustic guitar, bass, dobro, electric guitar and tambourine]: Graham Gouldman
Performer [acoustic guitar, electric guitar, grand piano and synthesizer]: Lol Creme
Performer [electric guitar, moog and slide guitar]: Eric Stewart
</pre>
becomes:
<pre>
Performer [acoustic guitar]: Graham Gouldman; Lol Creme
Performer [bass]: Graham Gouldman
Performer [dobro]: Graham Gouldman
Performer [electric guitar]: Eric Stewart; Graham Gouldman; Lol Creme
Performer [grand piano]: Lol Creme
Performer [moog]: Eric Stewart
Performer [slide guitar]: Eric Stewart
Performer [synthesizer]: Lol Creme
Performer [tambourine]: Graham Gouldman
</pre>
'''
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ["1.3.0"]

import re
from picard import log
from picard.metadata import register_track_metadata_processor

standardise_performers_split = re.compile(r", | and ").split

def standardise_performers(album, metadata, *args):
    for key, values in metadata.rawitems():
        if not key.startswith('performer:') \
        and not key.startswith('~performersort:'):
            continue
        mainkey, subkey = key.split(':', 1)
        if not subkey:
            continue
        instruments = standardise_performers_split(subkey)
        if len(instruments) == 1:
            continue
        log.debug("%s: Splitting Performer [%s] into separate performers",
            PLUGIN_NAME,
            subkey,
            )
        for instrument in instruments:
            newkey = '%s:%s' % (mainkey, instrument)
            for value in values:
                metadata.add_unique(newkey, value)
        del metadata[key]

register_track_metadata_processor(standardise_performers, priority = True)
