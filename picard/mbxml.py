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

from picard.util import format_time


_artist_rel_types = {
    "Composer": "composer",
    "Conductor": "conductor", 
    "PerformingOrchestra": "ensemble",
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


def _relations_to_metadata(relation_lists, m):
    for relation_list in relation_lists:
        if relation_list.target_type == 'Artist':
            for relation in relation_list.relation:
                try:
                    m.add(_artist_rel_types[relation.type], relation.artist[0].name[0].text)
                except (KeyError, IndexError):
                    pass
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


def track_to_metadata(node, m):
    m['musicbrainz_trackid'] = node.attribs['id']
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
            _relations_to_metadata(nodes, m)
        elif name == 'release_list':
            release_to_metadata(nodes[0].release[0], m)
    if '~#length' not in m:
        m['~#length'] = 0
    m['~length'] = format_time(m['~#length'])


def release_to_metadata(node, m):
    """Make metadata dict from a XML 'release' node."""
    m['musicbrainz_albumid'] = node.attribs['id']
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
            _relations_to_metadata(nodes, m)
        elif name == 'release_event_list':
            # TODO: make prefered country configurable
            m['date'] = nodes[0].event[0].date
            try:
                m['country'] = nodes[0].event[0].country
            except (AttributeError, IndexError):
                pass
        elif name == 'track_list':
            if 'track' in nodes[0].children:
                m['totaltracks'] = str(len(nodes[0].track))
            if 'offset' in nodes[0].attribs:
                m['tracknumber'] = str(int(nodes[0].attribs['offset']) + 1)
            if 'count' in nodes[0].attribs:
                m['totaltracks'] = nodes[0].attribs['count']
