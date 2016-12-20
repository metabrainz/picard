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
from picard import config
from picard.util import (format_time, translate_from_sortname, parse_amazon_url,
                         linear_combination_of_weights)
from picard.const import RELEASE_FORMATS


_artist_rel_types = {
    "composer": "composer",
    "writer": "writer",
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
_BLANK_SPECIAL_RELTYPES = {'vocal': 'vocals'}


def _parse_attributes(attrs, reltype):
    attrs = [_decamelcase(_REPLACE_MAP.get(a, a)) for a in attrs]
    prefix = ' '.join([a for a in attrs if a in _EXTRA_ATTRS])
    attrs = [a for a in attrs if a not in _EXTRA_ATTRS]
    if len(attrs) > 1:
        attrs = '%s and %s' % (', '.join(attrs[:-1]), attrs[-1:][0])
    elif len(attrs) == 1:
        attrs = attrs[0]
    else:
        attrs = _BLANK_SPECIAL_RELTYPES.get(reltype, '')
    return ' '.join([prefix, attrs]).strip().lower()


def _relations_to_metadata(relation_lists, m):
    use_credited_as = not config.setting["standardize_artists"]
    for relation_list in relation_lists:
        if relation_list.target_type == 'artist':
            for relation in relation_list.relation:
                artist = relation.artist[0]
                value, valuesort = _translate_artist_node(artist)
                has_translation = (value != artist.name[0].text)
                if not has_translation and use_credited_as and 'target_credit' in relation.children:
                    credited_as = relation.target_credit[0].text
                    if credited_as:
                        value, valuesort = credited_as, credited_as
                reltype = relation.type
                attribs = []
                if 'attribute_list' in relation.children:
                    attribs = [a.text for a in relation.attribute_list[0].attribute]
                if reltype in ('vocal', 'instrument', 'performer'):
                    name = 'performer:' + _parse_attributes(attribs, reltype)
                elif reltype == 'mix-DJ' and len(attribs) > 0:
                    if not hasattr(m, "_djmix_ars"):
                        m._djmix_ars = {}
                    for attr in attribs:
                        m._djmix_ars.setdefault(attr.split()[1], []).append(value)
                    continue
                else:
                    try:
                        name = _artist_rel_types[reltype]
                    except KeyError:
                        continue
                if value not in m[name]:
                    m.add(name, value)
                if name == 'composer' and valuesort not in m['composersort']:
                    m.add('composersort', valuesort)
        elif relation_list.target_type == 'work':
            for relation in relation_list.relation:
                if relation.type == 'performance':
                    performance_to_metadata(relation, m)
                    work_to_metadata(relation.work[0], m)
        elif relation_list.target_type == 'url':
            for relation in relation_list.relation:
                if relation.type == 'amazon asin' and 'asin' not in m:
                    amz = parse_amazon_url(relation.target[0].text)
                    if amz is not None:
                        m['asin'] = amz['asin']
                elif relation.type == 'license':
                    url = relation.target[0].text
                    m.add('license', url)


def _translate_artist_node(node):
    transl, translsort = None, None
    if config.setting['translate_artist_names']:
        locale = config.setting["artist_locale"]
        lang = locale.split("_")[0]
        if "alias_list" in node.children:
            result = (-1, (None, None))
            for alias in node.alias_list[0].alias:
                if alias.attribs.get("primary") != "primary":
                    continue
                if "locale" not in alias.attribs:
                    continue
                parts = []
                if alias.locale == locale:
                    score = 0.8
                elif alias.locale == lang:
                    score = 0.6
                elif alias.locale.split("_")[0] == lang:
                    score = 0.4
                else:
                    continue
                parts.append((score, 5))
                if alias.attribs.get("type") == u"Artist name":
                    score = 0.8
                elif alias.attribs.get("type") == u"Legal Name":
                    score = 0.5
                else:
                    # as 2014/09/19, only Artist or Legal names should have the
                    # Primary flag
                    score = 0.0
                parts.append((score, 5))
                comb = linear_combination_of_weights(parts)
                if comb > result[0]:
                    result = (comb, (alias.text, alias.attribs["sort_name"]))
            transl, translsort = result[1]
        if not transl:
            translsort = node.sort_name[0].text
            transl = translate_from_sortname(node.name[0].text, translsort)
    else:
        transl, translsort = node.name[0].text, node.sort_name[0].text
    return (transl, translsort)


def artist_credit_from_node(node):
    artist = ""
    artistsort = ""
    artists = []
    artistssort = []
    use_credited_as = not config.setting["standardize_artists"]
    for credit in node.name_credit:
        a = credit.artist[0]
        translated, translated_sort = _translate_artist_node(a)
        has_translation = (translated != a.name[0].text)
        if has_translation:
            name = translated
        elif use_credited_as and 'name' in credit.children:
            name = credit.name[0].text
        else:
            name = a.name[0].text
        artist += name
        artistsort += translated_sort
        artists.append(name)
        artistssort.append(translated_sort)
        if 'joinphrase' in credit.attribs:
            artist += credit.joinphrase
            artistsort += credit.joinphrase
    return (artist, artistsort, artists, artistssort)


def artist_credit_to_metadata(node, m, release=False):
    ids = [n.artist[0].id for n in node.name_credit]
    artist, artistsort, artists, artistssort = artist_credit_from_node(node)
    if release:
        m["musicbrainz_albumartistid"] = ids
        m["albumartist"] = artist
        m["albumartistsort"] = artistsort
        m["~albumartists"] = artists
        m["~albumartists_sort"] = artistssort
    else:
        m["musicbrainz_artistid"] = ids
        m["artist"] = artist
        m["artistsort"] = artistsort
        m["artists"] = artists
        m["~artists_sort"] = artistsort


def country_list_from_node(node):
    """Extract list of country codes from `release_event_list` node.
    This is in contrast with `country` element, which has single release
    event information.
    """
    if "release_event_list" in node.children:
        country = []
        for release_event in node.release_event_list[0].release_event:
            try:
                country.append(
                    release_event.area[0].iso_3166_1_code_list[0].iso_3166_1_code[0].text)
            except AttributeError:
                pass
        return country


def label_info_from_node(node):
    labels = []
    catalog_numbers = []
    if node.children:
        for label_info in node.label_info:
            if 'label' in label_info.children and label_info.label[0].children:
                label = label_info.label[0].name[0].text
                if label not in labels:
                    labels.append(label)
            if 'catalog_number' in label_info.children:
                cat_num = label_info.catalog_number[0].text
                if cat_num not in catalog_numbers:
                    catalog_numbers.append(cat_num)
    return (labels, catalog_numbers)


def media_formats_from_node(node):
    formats_count = {}
    formats_order = []
    for medium in node.medium:
        if "format" in medium.children:
            text = medium.format[0].text
        else:
            text = "(unknown)"
        if text in formats_count:
            formats_count[text] += 1
        else:
            formats_count[text] = 1
            formats_order.append(text)
    formats = []
    for format in formats_order:
        count = formats_count[format]
        format = RELEASE_FORMATS.get(format, format)
        if count > 1:
            format = str(count) + u"×" + format
        formats.append(format)
    return " + ".join(formats)


def track_to_metadata(node, track):
    m = track.metadata
    recording_to_metadata(node.recording[0], m, track)
    m.add_unique('musicbrainz_trackid', node.id)
    # overwrite with data we have on the track
    for name, nodes in node.children.iteritems():
        if not nodes:
            continue
        if name == 'title':
            m['title'] = nodes[0].text
        elif name == 'position':
            m['tracknumber'] = nodes[0].text
        elif name == 'number':
            m['~musicbrainz_tracknumber'] = nodes[0].text
        elif name == 'length' and nodes[0].text:
            m.length = int(nodes[0].text)
        elif name == 'artist_credit':
            artist_credit_to_metadata(nodes[0], m)
    m['~length'] = format_time(m.length)


def recording_to_metadata(node, m, track=None):
    m.length = 0
    m.add_unique('musicbrainz_recordingid', node.id)
    for name, nodes in node.children.iteritems():
        if not nodes:
            continue
        if name == 'title':
            m['title'] = nodes[0].text
            m['~recordingtitle'] = nodes[0].text
        elif name == 'length' and nodes[0].text:
            m.length = int(nodes[0].text)
        elif name == 'disambiguation':
            m['~recordingcomment'] = nodes[0].text
        elif name == 'artist_credit':
            artist_credit_to_metadata(nodes[0], m)
            if 'name_credit' in nodes[0].children and track:
                for name_credit in nodes[0].name_credit:
                    if 'artist' in name_credit.children:
                        for artist in name_credit.artist:
                            trackartist = track.append_track_artist(artist.id)
                            if 'tag_list' in artist.children:
                                add_folksonomy_tags(artist.tag_list[0],
                                                    trackartist)
                            if 'user_tag_list' in artist.children:
                                add_user_folksonomy_tags(artist.user_tag_list[0],
                                                         trackartist)
        elif name == 'relation_list':
            _relations_to_metadata(nodes, m)
        elif name == 'tag_list':
            add_folksonomy_tags(nodes[0], track)
        elif name == 'user_tag_list':
            add_user_folksonomy_tags(nodes[0], track)
        elif name == 'isrc_list':
            add_isrcs_to_metadata(nodes[0], m)
        elif name == 'user_rating':
            m['~rating'] = nodes[0].text
        elif name == 'video' and nodes[0].text == 'true':
            m['~video'] = '1'
    m['~length'] = format_time(m.length)


def performance_to_metadata(relation, m):
    if 'attribute_list' in relation.children:
        if 'attribute' in relation.attribute_list[0].children:
            for attribute in relation.attribute_list[0].attribute:
                m.add_unique("~performance_attributes", attribute.text)


def work_to_metadata(work, m):
    m.add_unique("musicbrainz_workid", work.id)
    if 'language' in work.children:
        m.add_unique("language", work.language[0].text)
    if 'title' in work.children:
        m.add_unique("work", work.title[0].text)
    if 'relation_list' in work.children:
        _relations_to_metadata(work.relation_list, m)


def medium_to_metadata(node, m):
    for name, nodes in node.children.iteritems():
        if not nodes:
            continue
        if name == 'position':
            m['discnumber'] = nodes[0].text
        elif name == 'track_list':
            m['totaltracks'] = nodes[0].count
        elif name == 'title':
            m['discsubtitle'] = nodes[0].text
        elif name == 'format':
            m['media'] = nodes[0].text


def artist_to_metadata(node, m):
    """Make meatadata dict from a XML 'artist' node."""
    m.add_unique("musicbrainz_artistid", node.id)
    for name, nodes in node.children.iteritems():
        if not nodes:
            continue
        if name == "name":
            m["name"] = nodes[0].text
        elif name == "area":
            m["area"] = nodes[0].name[0].text
        elif name == "gender":
            m["gender"] = nodes[0].text
        elif name == "life_span":
            if "begin" in nodes[0].children:
                m["begindate"] = nodes[0].begin[0].text
            if "ended" in nodes[0].children:
                ended = nodes[0].ended[0].text
                if ended == "true" and "end" in nodes[0].children:
                    m["enddate"] = nodes[0].end[0].text
        elif name == "begin_area":
            m["beginarea"] = nodes[0].name[0].text
        elif name == "end_area":
            m["endarea"] = nodes[0].name[0].text

    try:
        m["type"] = node.type
    except AttributeError:
        pass


def release_to_metadata(node, m, album=None):
    """Make metadata dict from a XML 'release' node."""
    m.add_unique('musicbrainz_albumid', node.id)
    for name, nodes in node.children.iteritems():
        if not nodes:
            continue
        if name == 'status':
            m['releasestatus'] = nodes[0].text.lower()
        elif name == 'title':
            m['album'] = nodes[0].text
        elif name == 'disambiguation':
            m['~releasecomment'] = nodes[0].text
        elif name == 'asin':
            m['asin'] = nodes[0].text
        elif name == 'artist_credit':
            artist_credit_to_metadata(nodes[0], m, release=True)
            # set tags from artists
            if album is not None:
                if 'name_credit' in nodes[0].children:
                    for name_credit in nodes[0].name_credit:
                        if 'artist' in name_credit.children:
                            for artist in name_credit.artist:
                                albumartist = album.append_album_artist(artist.id)
                                if 'tag_list' in artist.children:
                                    add_folksonomy_tags(artist.tag_list[0],
                                                        albumartist)
                                if 'user_tag_list' in artist.children:
                                    add_user_folksonomy_tags(artist.user_tag_list[0],
                                                             albumartist)
        elif name == 'date':
            m['date'] = nodes[0].text
        elif name == 'country':
            m['releasecountry'] = nodes[0].text
        elif name == 'barcode':
            m['barcode'] = nodes[0].text
        elif name == 'relation_list':
            _relations_to_metadata(nodes, m)
        elif name == 'label_info_list' and nodes[0].children:
            m['label'], m['catalognumber'] = label_info_from_node(nodes[0])
        elif name == 'text_representation':
            if 'language' in nodes[0].children:
                m['~releaselanguage'] = nodes[0].language[0].text
            if 'script' in nodes[0].children:
                m['script'] = nodes[0].script[0].text
        elif name == 'tag_list':
            add_folksonomy_tags(nodes[0], album)
        elif name == 'user_tag_list':
            add_user_folksonomy_tags(nodes[0], album)


def release_group_to_metadata(node, m, release_group=None):
    """Make metadata dict from a XML 'release-group' node taken from inside a 'release' node."""
    m.add_unique('musicbrainz_releasegroupid', node.id)
    for name, nodes in node.children.iteritems():
        if not nodes:
            continue
        if name == 'title':
            m['~releasegroup'] = nodes[0].text
        elif name == 'disambiguation':
            m['~releasegroupcomment'] = nodes[0].text
        elif name == 'first_release_date':
            m['originaldate'] = nodes[0].text
            if m['originaldate']:
                m['originalyear'] = m['originaldate'][:4]
        elif name == 'tag_list':
            add_folksonomy_tags(nodes[0], release_group)
        elif name == 'user_tag_list':
            add_user_folksonomy_tags(nodes[0], release_group)
        elif name == 'primary_type':
            m['~primaryreleasetype'] = nodes[0].text.lower()
        elif name == 'secondary_type_list':
            add_secondary_release_types(nodes[0], m)
    m['releasetype'] = m.getall('~primaryreleasetype') + m.getall('~secondaryreleasetype')


def add_secondary_release_types(node, m):
    if 'secondary_type' in node.children:
        for secondary_type in node.secondary_type:
            m.add_unique('~secondaryreleasetype', secondary_type.text.lower())


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
