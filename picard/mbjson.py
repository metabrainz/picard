# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2017 Sambhav Kothari
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

_TRACK_TO_METADATA = {
    'title': 'title',
    'position': 'tracknumber',
    'number': '~musicbrainz_tracknumber',
}

_MEDIUM_TO_METADATA = {
    'title': 'discsubtitle',
    'position': 'discnumber',
    'track-count': 'totaltracks',
    'format': 'media',
}

_RECORDING_TO_METADATA = {
    'title': 'title',
    'disambiguation': '~recordingcomment',
}

_RELEASE_TO_METADATA = {
    'title': 'album',
    'disambiguation': '~releasecomment',
    'asin': 'asin',
    'date': 'date',
    'country': 'releasecountry',
    'barcode': 'barcode'
}

_ARTIST_TO_METADATA = {
    'name': 'name',
    'gender': 'gender',
    'type': 'type',
}

_RELEASE_GROUP_TO_METADATA = {
    'title': '~releasegroup',
    'disambiguation': '~releasegroupcomment',
    'first-release-date': 'originaldate',
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
    len_attrs = len(attrs)
    if len_attrs > 1:
        attrs = '%s and %s' % (', '.join(attrs[:-1]), attrs[-1:][0])
    elif len_attrs == 1:
        attrs = attrs[0]
    else:
        attrs = _BLANK_SPECIAL_RELTYPES.get(reltype, '')
    return ' '.join([prefix, attrs]).strip().lower()


def _relations_to_metadata(relations, m):
    use_credited_as = not config.setting["standardize_artists"]
    for relation in relations:
        if relation['target-type'] == 'artist':
            artist = relation['artist']
            value, valuesort = _translate_artist_node(artist)
            has_translation = (value != artist['name'])
            if not has_translation and use_credited_as and 'target-credit' in relation:
                credited_as = relation['target-credit']
                if credited_as:
                    value, valuesort = credited_as, credited_as
            reltype = relation['type']
            attribs = []
            if 'attributes' in relation:
                attribs = [a for a in relation['attributes']]
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
        elif relation['target-type'] == 'work':
            if relation['type'] == 'performance':
                performance_to_metadata(relation, m)
                work_to_metadata(relation['work'], m)
        elif relation['target-type'] == 'url':
            if relation['type'] == 'amazon asin' and 'asin' not in m:
                amz = parse_amazon_url(relation['url']['resource'])
                if amz is not None:
                    m['asin'] = amz['asin']
            elif relation['type'] == 'license':
                url = relation['url']['resource']
                m.add('license', url)


def _translate_artist_node(node):
    transl, translsort = None, None
    if config.setting['translate_artist_names']:
        locale = config.setting["artist_locale"]
        lang = locale.split("_")[0]
        if "aliases" in node:
            result = (-1, (None, None))
            for alias in node['aliases']:
                if not alias["primary"]:
                    continue
                if "locale" not in alias:
                    continue
                parts = []
                if alias['locale'] == locale:
                    score = 0.8
                elif alias['locale'] == lang:
                    score = 0.6
                elif alias['locale'].split("_")[0] == lang:
                    score = 0.4
                else:
                    continue
                parts.append((score, 5))
                if alias["type"] == "Artist name":
                    score = 0.8
                elif alias["type"] == "Legal Name":
                    score = 0.5
                else:
                    # as 2014/09/19, only Artist or Legal names should have the
                    # Primary flag
                    score = 0.0
                parts.append((score, 5))
                comb = linear_combination_of_weights(parts)
                if comb > result[0]:
                    result = (comb, (alias['name'], alias["sort-name"]))
            transl, translsort = result[1]
        if not transl:
            translsort = node['sort-name']
            transl = translate_from_sortname(node['name'] or "", translsort)
    else:
        transl, translsort = node['name'], node['sort-name']
    return (transl, translsort)


def artist_credit_from_node(node):
    artist = ""
    artistsort = ""
    artists = []
    artistssort = []
    use_credited_as = not config.setting["standardize_artists"]
    for artist_info in node:
        a = artist_info['artist']
        translated, translated_sort = _translate_artist_node(a)
        has_translation = (translated != a['name'])
        if has_translation:
            name = translated
        elif use_credited_as and 'name' in artist_info:
            name = artist_info['name']
        else:
            name = a['name']
        artist += name
        artistsort += translated_sort or ""
        artists.append(name)
        artistssort.append(translated_sort)
        if 'joinphrase' in artist_info:
            artist += artist_info['joinphrase'] or ""
            artistsort += artist_info['joinphrase'] or ""
    return (artist, artistsort, artists, artistssort)


def artist_credit_to_metadata(node, m, release=False):
    ids = [n['artist']['id'] for n in node]
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
        m["~artists_sort"] = artistssort


def country_list_from_node(node):
    if "release-events" in node:
        country = []
        for release_event in node['release-events']:
            try:
                country_code = release_event['area']['iso-3166-1-codes'][0]
            # TypeError in case object is None
            except (KeyError, IndexError, TypeError):
                pass
            else:
                if country_code:
                    country.append(country_code)
        return country


def release_dates_and_countries_from_node(node):
    dates = []
    countries = []
    if "release-events" in node:
        for release_event in node['release-events']:
            dates.append(release_event['date'] or '')
            country_code = ''
            try:
                country_code = release_event['area']['iso-3166-1-codes'][0]
            # TypeError in case object is None
            except (KeyError, IndexError, TypeError):
                pass
            countries.append(country_code)
    return dates, countries


def label_info_from_node(node):
    labels = []
    catalog_numbers = []
    for label_info in node:
        if 'label' in label_info and label_info['label'] and 'name' in label_info['label']:
            label = label_info['label']['name']
            if label and label not in labels:
                labels.append(label)
        if 'catalog-number' in label_info:
            cat_num = label_info['catalog-number']
            if cat_num and cat_num not in catalog_numbers:
                catalog_numbers.append(cat_num)
    return (labels, catalog_numbers)


def media_formats_from_node(node):
    formats_count = {}
    formats_order = []
    for medium in node:
        text = medium.get('format', "(unknown)") or "(unknown)"
        if text in formats_count:
            formats_count[text] += 1
        else:
            formats_count[text] = 1
            formats_order.append(text)
    formats = []
    for medium_format in formats_order:
        count = formats_count[medium_format]
        medium_format = RELEASE_FORMATS.get(medium_format, medium_format)
        if count > 1:
            medium_format = string_(count) + "×" + medium_format
        formats.append(medium_format)
    return " + ".join(formats)


def track_to_metadata(node, track):
    m = track.metadata
    recording_to_metadata(node['recording'], m, track)
    m.add_unique('musicbrainz_trackid', node['id'])
    # overwrite with data we have on the track
    for key, value in node.items():
        if not value:
            continue
        if key in _TRACK_TO_METADATA:
            m[_TRACK_TO_METADATA[key]] = value
        elif key == 'length' and value:
            m.length = value
        elif key == 'artist-credit':
            artist_credit_to_metadata(value, m)
    if m.length:
        m['~length'] = format_time(m.length)


def recording_to_metadata(node, m, track=None):
    m.length = 0
    m.add_unique('musicbrainz_recordingid', node['id'])
    for key, value in node.items():
        if not value:
            continue
        if key in _RECORDING_TO_METADATA:
            m[_RECORDING_TO_METADATA[key]] = value
        elif key == 'user-rating':
            m['~rating'] = value['value']
        elif key == 'length':
            m.length = value
        elif key == 'artist-credit':
            artist_credit_to_metadata(value, m)
            # set tags from artists
            if track:
                for artist in value:
                    track.append_track_artist(artist['artist']['id'])
        elif key == 'relations':
            _relations_to_metadata(value, m)
        elif key == 'tags' and track:
            add_folksonomy_tags(value, track)
        elif key == 'user-tags' and track:
            add_user_folksonomy_tags(value, track)
        elif key == 'isrcs':
            add_isrcs_to_metadata(value, m)
        elif key == 'video' and value:
            m['~video'] = '1'
    if m['title']:
        m['~recordingtitle'] = m['title']
    if m.length:
        m['~length'] = format_time(m.length)


def performance_to_metadata(relation, m):
    if 'attributes' in relation:
        for attribute in relation['attributes']:
            m.add_unique("~performance_attributes", attribute)


def work_to_metadata(work, m):
    m.add_unique("musicbrainz_workid", work['id'])
    if 'languages' in work:
        for language in work['languages']:
            m.add_unique("language", language)
    elif 'language' in work:
        m.add_unique("language", work['language'])
    if 'title' in work:
        m.add_unique("work", work['title'])
    if 'relations' in work:
        _relations_to_metadata(work['relations'], m)


def medium_to_metadata(node, m):
    for key, value in node.items():
        if not value:
            continue
        if key in _MEDIUM_TO_METADATA:
            m[_MEDIUM_TO_METADATA[key]] = value


def artist_to_metadata(node, m):
    """Make meatadata dict from a JSON 'artist' node."""
    m.add_unique("musicbrainz_artistid", node['id'])
    for key, value in node.items():
        if not value:
            continue
        if key in _ARTIST_TO_METADATA:
            m[_ARTIST_TO_METADATA[key]] = value
        elif key == "area":
            m["area"] = value['name']
        elif key == "life-span":
            if "begin" in value:
                m["begindate"] = value['begin']
            if "ended" in value:
                ended = value['ended']
                if ended and "end" in value:
                    m["enddate"] = value['end']
        elif key == "begin_area":
            m["beginarea"] = value['name']
        elif key == "end_area":
            m["endarea"] = value['name']


def release_to_metadata(node, m, album=None):
    """Make metadata dict from a JSON 'release' node."""
    m.add_unique('musicbrainz_albumid', node['id'])
    for key, value in node.items():
        if not value:
            continue
        if key in _RELEASE_TO_METADATA:
            m[_RELEASE_TO_METADATA[key]] = value
        elif key == 'status':
            m['releasestatus'] = value.lower()
        elif key == 'artist-credit':
            artist_credit_to_metadata(value, m, release=True)
            # set tags from artists
            if album is not None:
                for artist in value:
                    album.append_album_artist(artist['artist']['id'])
        elif key == 'relations':
            _relations_to_metadata(value, m)
        elif key == 'label-info':
            m['label'], m['catalognumber'] = label_info_from_node(value)
        elif key == 'text-representation':
            if 'language' in value:
                m['~releaselanguage'] = value['language']
            if 'script' in value:
                m['script'] = value['script']
        elif key == 'tags':
            add_folksonomy_tags(value, album)
        elif key == 'user-tags':
            add_user_folksonomy_tags(value, album)


def release_group_to_metadata(node, m, release_group=None):
    """Make metadata dict from a JSON 'release-group' node taken from inside a 'release' node."""
    m.add_unique('musicbrainz_releasegroupid', node['id'])
    for key, value in node.items():
        if not value:
            continue
        if key in _RELEASE_GROUP_TO_METADATA:
            m[_RELEASE_GROUP_TO_METADATA[key]] = value
        elif key == 'tags':
            add_folksonomy_tags(value, release_group)
        elif key == 'user-tags':
            add_user_folksonomy_tags(value, release_group)
        elif key == 'primary-type':
            m['~primaryreleasetype'] = value.lower()
        elif key == 'secondary-types':
            add_secondary_release_types(value, m)
    if m['originaldate']:
        m['originalyear'] = m['originaldate'][:4]
    m['releasetype'] = m.getall('~primaryreleasetype') + m.getall('~secondaryreleasetype')


def add_secondary_release_types(node, m):
    for secondary_type in node:
        m.add_unique('~secondaryreleasetype', secondary_type.lower())


def add_folksonomy_tags(node, obj):
    if obj is not None:
        for tag in node:
            key = tag['name']
            count = tag['count']
            if key:
                obj.add_folksonomy_tag(key, count)


def add_user_folksonomy_tags(node, obj):
    if obj is not None:
        for tag in node:
            key = tag['name']
            if key:
                obj.add_folksonomy_tag(key, 1)


def add_isrcs_to_metadata(node, metadata):
    for isrc in node:
        metadata.add('isrc', isrc)
