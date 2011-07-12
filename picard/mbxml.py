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
    "composer": "composer",
    "conductor": "conductor",
    "chorus master": "conductor",
    "performing orchestra": "performer:orchestra",
    "arranger": "arranger",
    "orchestrator": "arranger",
    "instrumentator": "arranger",
    "lyricist": "lyricist",
    "librettist": "lyricist",
    "remixer": "remixer",
    "producer": "producer",
    "engineer": "engineer",
    "audio": "engineer",
    #"Mastering": "engineer",
    "sound": "engineer",
    "live sound": "engineer",
    "mix": "mixer",
    #"Recording": "engineer",
    "mix-DJ": "djmixer",
}


def _decamelcase(text):
    return re.sub(r'([A-Z])', r' \1', text).strip()


_REPLACE_MAP = {}
_EXTRA_ATTRS = ['guest', 'additional', 'minor']
def _parse_attributes(attrs):
    attrs = [_decamelcase(_REPLACE_MAP.get(a, a)) for a in attrs]
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
        if relation_list.target_type == 'artist':
            for relation in relation_list.relation:
                value = relation.artist[0].name[0].text
                if config and config.setting['translate_artist_names']:
                    value = translate_artist(value, relation.artist[0].sort_name[0].text)
                reltype = relation.type
                attribs = []
                if 'attribute_list' in relation.children:
                    attribs = [a.text for a in relation.attribute_list[0].attribute]
                if reltype == 'vocal':
                    name = 'performer:' + ' '.join([_parse_attributes(attribs), 'vocal']).strip()
                elif reltype == 'instrument':
                    name = 'performer:' + _parse_attributes(attribs)
                elif reltype == 'performer':
                    name = 'performer:' + _parse_attributes(attribs)
                else:
                    try:
                        name = _artist_rel_types[reltype]
                    except KeyError:
                        continue
                m.add(name, value)
        elif relation_list.target_type == 'work':
            for relation in relation_list.relation:
                if relation.type == 'performance':
                    work = relation.work[0]
                    if 'relation_list' in work.children:
                        _relations_to_metadata(work.relation_list, m, config)
        # TODO: Release, Track, URL relations


def _set_artist_item(m, release, albumname, name, value):
    if release:
        m[albumname] = value
        if name not in m:
            m[name] = value
    else:
        m[name] = value


def artist_credit_from_node(node, config=None):
    artist = ""
    artistsort = ""
    standardize_name = config and config.setting["standardize_artists"]
    for credit in node.name_credit:
        a = credit.artist[0]
        artistsort += a.sort_name[0].text
        if 'name' in credit.children and not standardize_name:
            artist += credit.name[0].text
        else:
            artist += a.name[0].text
        if 'joinphrase' in credit.attribs:
            artist += credit.joinphrase
            artistsort += credit.joinphrase
    return (artist, artistsort)


def artist_credit_to_metadata(node, m=None, release=None, config=None):
    ids = [n.artist[0].id for n in node.name_credit]
    _set_artist_item(m, release, 'musicbrainz_albumartistid', 'musicbrainz_artistid', ids)
    artist, artistsort = artist_credit_from_node(node, config)
    _set_artist_item(m, release, 'albumartist', 'artist', artist)
    _set_artist_item(m, release, 'albumartistsort', 'artistsort', artistsort)


def label_info_from_node(node):
    labels = []
    catalog_numbers = []
    if node.count != "0":
        for label_info in node.label_info:
            if 'label' in label_info.children:
                labels.append(label_info.label[0].name[0].text)
            if 'catalog_number' in label_info.children:
                catalog_numbers.append(label_info.catalog_number[0].text)
    return (labels, catalog_numbers)


def track_to_metadata(node, track, config=None):
    m = track.metadata
    recording_to_metadata(node.recording[0], track, config)
    # overwrite with data we have on the track
    standardize_title = config and config.setting["standardize_tracks"]
    standardize_artist = config and config.setting["standardize_artists"]
    for name, nodes in node.children.iteritems():
        if not nodes:
            continue
        if name == 'title' and not standardize_title:
            m['title'] = nodes[0].text
        if name == 'position':
            m['tracknumber'] = nodes[0].text
        elif name == 'length' and nodes[0].text:
            m.length = int(nodes[0].text)
        elif name == 'artist_credit' and not standardize_artist:
            artist_credit_to_metadata(nodes[0], m, config=config)


def recording_to_metadata(node, track, config=None):
    m = track.metadata
    m.length = 0
    m['musicbrainz_trackid'] = node.attribs['id']
    for name, nodes in node.children.iteritems():
        if not nodes:
            continue
        if name == 'title':
            m['title'] = nodes[0].text
        elif name == 'length' and nodes[0].text:
            m.length = int(nodes[0].text)
        elif name == 'disambiguation':
            m['~recordingcomment'] = nodes[0].text
        elif name == 'artist_credit':
            artist_credit_to_metadata(nodes[0], m, config=config)
        if name == 'relation_list':
            _relations_to_metadata(nodes, m, config)
        elif name == 'release_list' and nodes[0].count != '0':
            release_to_metadata(nodes[0].release[0], m)
        elif name == 'tag_list':
            add_folksonomy_tags(nodes[0], track)
        elif name == 'user_tag_list':
            add_user_folksonomy_tags(nodes[0], track)
        elif name == 'isrc_list':
            add_isrcs_to_metadata(nodes[0], m)
        elif name == 'user_rating':
            m['~rating'] = nodes[0].text


def release_to_metadata(node, m, config=None, album=None):
    """Make metadata dict from a XML 'release' node."""
    m['musicbrainz_albumid'] = node.attribs['id']
    standardize_title = config and config.setting["standardize_releases"]

    for name, nodes in node.children.iteritems():
        if not nodes:
            continue
        if name == 'release_group':
            if 'type' in nodes[0].attribs:
                m['releasetype'] = nodes[0].type.lower()
            if standardize_title:
                m['album'] = nodes[0].title[0].text
        elif name == 'status':
            m['releasestatus'] = nodes[0].text.lower()
        elif name == 'title' and not standardize_title:
            m['album'] = nodes[0].text
        elif name == 'disambiguation':
            m['~releasecomment'] = nodes[0].text
        elif name == 'asin':
            m['asin'] = nodes[0].text
        elif name == 'artist_credit':
            artist_credit_to_metadata(nodes[0], m, True, config=config)
        elif name == 'date':
            m['date'] = nodes[0].text
        elif name == 'country':
            m['releasecountry'] = nodes[0].text
        elif name == 'barcode':
            m['barcode'] = nodes[0].text
        elif name == 'relation_list':
            _relations_to_metadata(nodes, m, config)
        elif name == 'label_info_list' and nodes[0].count != '0':
            m['label'], m['catalognumber'] = label_info_from_node(nodes[0])
        elif name == 'text_representation':
            if 'language' in nodes[0].children:
                m['language'] = nodes[0].language[0].text
            if 'script' in nodes[0].children:
                m['script'] = nodes[0].script[0].text
        elif name == 'tag_list':
            add_folksonomy_tags(nodes[0], album)
        elif name == 'user_tag_list':
            add_user_folksonomy_tags(nodes[0], album)


def add_folksonomy_tags(node, obj):
    if obj and 'tag' in node.children:
        for tag in node.tag:
            name = tag.name[0].text
            count = int(tag.attribs['count'])
            obj.add_folksonomy_tag(name, count)


def add_user_folksonomy_tags(node, obj):
    if obj and 'user_tag' in node.children:
        for tag in node.user_tag:
            name = tag.name[0].text
            obj.add_folksonomy_tag(name, 1)


def add_isrcs_to_metadata(node, metadata):
    if 'isrc' in node.children:
        for isrc in node.isrc:
            metadata.add('isrc', isrc.id)
