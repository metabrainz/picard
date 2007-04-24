# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

import re
import unicodedata
from picard.util import format_time, translate_artist


_artist_rel_types = {
    "Composer": "composer",
    "Conductor": "conductor",
    "PerformingOrchestra": "performer:orchestra",
    "Arranger": "arranger",
    "Orchestrator": "arranger",
    "Instrumentator": "arranger",
    "Lyricist": "lyricist",
    "Remixer": "remixer",
    "Producer": "producer",
    "Engineer": "engineer",
    "Audio": "engineer",
    #"Mastering": "engineer",
    "Sound": "engineer",
    "LiveSound": "engineer",
    #"Mix": "engineer",
    #"Recording": "engineer",
}


def _decamelcase(text):
    return re.sub(r'([A-Z])', r' \1', text).strip()


_EXTRA_ATTRS = ['Guest', 'Additional', 'Minor']
def _parse_attributes(attrs):
    attrs = map(_decamelcase, attrs)
    prefix = ' '.join([a for a in attrs if a in _EXTRA_ATTRS])
    attrs = [a for a in attrs if a not in _EXTRA_ATTRS]
    if len(attrs) > 1:
        attrs = '%s and %s' % (', '.join(attrs[:-1]), attrs[-1:][0])
    elif len(attrs) == 1:
        attrs = attrs[0]
    else:
        attrs = ''
    return ' '.join([prefix, attrs]).strip().lower()


def _relations_to_metadata(relation_lists, m, config):
    for relation_list in relation_lists:
        if relation_list.target_type == 'Artist':
            for relation in relation_list.relation:
                value = relation.artist[0].name[0].text
                if config and config.setting['translate_artist_names']:
                    value = translate_artist(value, relation.artist[0].sort_name[0].text)
                reltype = relation.type
                attribs = relation.attribs.get('attributes', '').split()
                if reltype == 'Vocal':
                    name = 'performer:' + ' '.join([_parse_attributes(attribs), 'vocal']).strip()
                elif reltype == 'Instrument':
                    name = 'performer:' + _parse_attributes(attribs)
                elif reltype == 'Performer':
                    name = 'performer:'
                else:
                    try:
                        name = _artist_rel_types[relation.type]
                    except KeyError:
                        continue
                m.add(name, value)
        # TODO: Release, Track, URL relations          


def _set_artist_item(m, release, albumname, name, value):
    if release:
        m[albumname] = value
        if name not in m:
            m[name] = value
    else:
        m[name] = value


def artist_to_metadata(node, m, release=False):
    _set_artist_item(m, release, 'musicbrainz_albumartistid', 'musicbrainz_artistid', node.id)
    for name, nodes in node.children.iteritems():
        if not nodes:
            continue
        if name == 'name':
            _set_artist_item(m, release, 'albumartist', 'artist', nodes[0].text)
        elif name == 'sort_name':
            _set_artist_item(m, release, 'albumartistsort', 'artistsort', nodes[0].text)


def track_to_metadata(node, m, config=None):
    m['musicbrainz_trackid'] = node.attribs['id']
    m['~#length'] = 0
    for name, nodes in node.children.iteritems():
        if not nodes:
            continue
        if name == 'title':
            m['title'] = nodes[0].text
        elif name == 'duration':
            m['~#length'] = int(nodes[0].text)
        elif name == 'artist':
            artist_to_metadata(nodes[0], m)
        elif name == 'relation_list':
            _relations_to_metadata(nodes, m, config)
        elif name == 'release_list':
            release_to_metadata(nodes[0].release[0], m)
    m['~length'] = format_time(m['~#length'])


def release_to_metadata(node, m, config=None, catalognumber=None):
    """Make metadata dict from a XML 'release' node."""
    m['musicbrainz_albumid'] = node.attribs['id']

    # Parse release type and status
    if 'type' in node.attribs:
        types = node.attribs['type'].split()
        for t in types:
            if t in ('Official', 'Promotion', 'Bootleg', 'Pseudo-Release'):
                m['releasestatus'] = t.lower()
            else:
                m['releasetype'] = t.lower()

    for name, nodes in node.children.iteritems():
        if not nodes:
            continue
        if name == 'title':
            m['album'] = nodes[0].text
        elif name == 'asin':
            m['asin'] = nodes[0].text
        elif name == 'artist':
            artist_to_metadata(nodes[0], m, True)
        elif name == 'relation_list':
            _relations_to_metadata(nodes, m, config)
        elif name == 'release_event_list':
            # TODO: make prefered country configurable
            relevent = nodes[0].event[0]
            if catalognumber:
                for event in nodes[0].event:
                    try:
                        if event.catalog_number == catalognumber:
                            relevent = event
                            break
                    except AttributeError:
                        pass
            m['date'] = relevent.date
            try:m['releasecountry'] = relevent.country
            except (AttributeError, IndexError): pass
            try: m['catalognumber'] = relevent.catalog_number
            except (AttributeError, IndexError): pass
            try: m['barcode'] = relevent.barcode
            except (AttributeError, IndexError): pass
            try: m['label'] = relevent.label[0].name[0].text
            except (AttributeError, IndexError): pass
        elif name == 'track_list':
            if 'track' in nodes[0].children:
                m['totaltracks'] = str(len(nodes[0].track))
            if 'offset' in nodes[0].attribs:
                m['tracknumber'] = str(int(nodes[0].attribs['offset']) + 1)
            if 'count' in nodes[0].attribs:
                m['totaltracks'] = nodes[0].attribs['count']
