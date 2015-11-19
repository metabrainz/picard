# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006-2007 Lukáš Lalinský
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

from picard import config, log
from picard.const import TIMESTAMP_FORMAT
from picard.coverart.image import TagCoverArtImage, CoverArtImageError
from picard.metadata import Metadata
from picard.file import File
from picard.util import encode_filename, sanitize_date, sanitize_int, isurl

try:
    import mutagen.aiff
except ImportError:
    mutagen.aiff = None
import mutagen.apev2
from mutagen import id3
import mutagen.mp3
import mutagen.trueaudio
from mutagen.id3 import Frames, Frames_2_2, TextFrame

from collections import defaultdict
import json
from os import path
import re
from time import strftime, gmtime


# Add support for iTunes frame types
class TCMP(TextFrame):
    pass

class TSO2(TextFrame):
    pass

class TSOC(TextFrame):
    pass

# Add support for prototype frame types (which are upgraded)
class XDOR(TextFrame):
    pass

class XSOP(TextFrame):
    pass

id3.TCMP = TCMP
id3.TSO2 = TSO2
id3.TSOC = TSOC
id3.XDOR = XDOR
id3.XSOP = XSOP

known_frames = {
    "TCMP": TCMP,
    "TSO2": TSO2,
    "TSOC": TSOC,
    "XDOR": XDOR,
    "XSOP": XSOP,
}
known_frames.update(dict(Frames))
known_frames.update(dict(Frames_2_2))

# Mutagen Monkey Patch #1
# We need to save the text in ISO-8859-1 even if it contains unsupported characters
# and this approach is better than encoding, decoding and again encoding.
def patched_EncodedTextSpec_write(self, frame, value):
    try:
        enc, term = self._encodings[frame.encoding]
    except AttributeError:
        enc, term = self.encodings[frame.encoding]
    return value.encode(enc, 'ignore') + term

id3.EncodedTextSpec.write = patched_EncodedTextSpec_write


# Mutagen Monkey Patch #2
# The ID3 spec says that multiple text values should be _separated_ by the string
# terminator, which means that e.g. 'a\x00' are two values, 'a' and ''.
# This patch removes a trailing \x00.
def patched_MultiSpec_write(self, frame, value):
    data = self._write_orig(frame, value)
    spec = self.specs[-1]
    if isinstance(spec, id3.EncodedTextSpec):
        try:
            term = spec._encodings[frame.encoding][1]
        except AttributeError:
            term = spec.encodings[frame.encoding][1]
        if data.endswith(term):
            data = data[:-len(term)]
    return data

id3.MultiSpec._write_orig = id3.MultiSpec.write
id3.MultiSpec.write = patched_MultiSpec_write


__ID3_IMAGE_TYPES = {
    "other": 0,
    "obi": 0,
    "tray": 0,
    "spine": 0,
    "sticker": 0,
    "front": 3,
    "back": 4,
    "booklet": 5,
    "medium": 6,
    "track": 6,
}

__R_ID3_IMAGE_TYPES = dict([(v, k) for k, v in __ID3_IMAGE_TYPES.iteritems()])

def image_type_from_id3_num(id3type):
    return __R_ID3_IMAGE_TYPES.get(id3type, "other")

def image_type_as_id3_num(texttype):
    return __ID3_IMAGE_TYPES.get(texttype, 0)

def types_from_id3(id3type):
    return [unicode(image_type_from_id3_num(id3type))]


EMPTY_LANG = '\x00\x00\x00'


class ID3File(File):
    """
    Generic ID3-based file.
        ID3v2.4 spec: http://id3.org/id3v2.4.0-frames
    """
    _IsMP3 = False

    __load_text_tags = {
        # In same sequence as defined at http://id3.org/id3v2.4.0-frames
        # Tags here must be text or web tags without desc
        'TIT1': 'grouping',
        'TIT2': 'title',
        'TIT3': 'subtitle',
        'TALB': 'album',
        'TOAL': 'originalalbum',
        'TSST': 'discsubtitle',
        'TSRC': 'isrc',
        'TPE1': 'artist',
        'TPE2': 'albumartist',
        'TPE3': 'conductor',
        'TPE4': 'remixer',
        'TOPE': 'originalartist',
        'TEXT': 'lyricist',
        'TOLY': 'originallyricist',
        'TCOM': 'composer',
        'TENC': 'encodedby',
        'TBPM': 'bpm',
        'TKEY': 'key',
        'TLAN': 'language',
        'TCON': 'genre',
        'TMED': 'media',
        'TMOO': 'mood',
        'TCOP': 'copyright',
        'TPRO': 'recordingcopyright',
        'TPUB': 'label',
        'TDOR': 'originaldate',
        'TDRC': 'date',
        'TDTG': '~tagtime',
        'TDEN': 'encodingtime',
        'TSSE': 'encodersettings',
        'TSOA': 'albumsort',
        'TSOP': 'artistsort',
        'TSOT': 'titlesort',
        'TDLY': 'playdelay',
        'WCOP': 'license',
        'WOAR': 'web_official_artist',
        'WPUB': 'web_official_label',

        # The following are informal iTunes extensions to id3v2:
        'TCMP': 'compilation',
        'TSOC': 'composersort',
        'TSO2': 'albumartistsort',
    }
    __save_text_tags = dict([(v, k) for k, v in __load_text_tags.iteritems()])

    __load_freetext_tags = {
        # Text tags
        'ASIN': 'asin',
        'Acoustid Fingerprint': 'acoustid_fingerprint',
        'Acoustid Id': 'acoustid_id',
        'Album Artists': 'albumartists',
        'Album Genre': 'albumgenre',
        'Album Rating': 'albumrating',
        'Artists': 'artists',
        'BARCODE': 'barcode',
        'CATALOGNUMBER': 'catalognumber',
        'Category': 'category',
        'Country': 'country',
        'fBPM': 'bpm',
        'Keywords': 'keywords',
        'LICENSE': 'license',
        'MusicBrainz Album Artist Id': 'musicbrainz_albumartistid',
        'MusicBrainz Album Id': 'musicbrainz_albumid',
        'MusicBrainz Album Status': 'releasestatus',
        'MusicBrainz Album Type': 'releasetype',
        'MusicBrainz Artist Id': 'musicbrainz_artistid',
        'MusicBrainz Disc Id': 'musicbrainz_discid',
        'MusicBrainz Label Id': 'musicbrainz_labelid',
        'MusicBrainz Original Album Id': 'musicbrainz_original_albumid',
        'MusicBrainz Original Artist Id': 'musicbrainz_original_artistid',
        'MusicBrainz Album Release Country': 'releasecountry',
        'MusicBrainz Recording Id': 'musicbrainz_recordingid',
        'MusicBrainz Release Group Id': 'musicbrainz_releasegroupid',
        'MusicBrainz Track Id': 'musicbrainz_trackid',
        'MusicBrainz Work Id': 'musicbrainz_workid',
        'MusicMagic PUID': 'musicip_puid',
        'MusicMagic Fingerprint': 'musicip_fingerprint',
        'Occasion': 'occasion',
        'Original Year': 'originalyear',
        'Recording Date': 'recordingdate',
        'Recording Location': 'recordinglocation',
        'Quality': 'quality',
        'SCRIPT': 'script',
        'Tempo': 'tempo',
        'Work': 'work',
        'Writer': 'writer',
        # Web tags
        'DISCOGS_ARTIST':       'web_discogs_artist',
        'DISCOGS_LABEL':        'web_discogs_label',
        'DISCOGS_RELEASE':      'web_discogs_release',
        'DISCOGS_MASTER':       'web_discogs_releasegroup',
        'MUSICBRAINZ_ARTIST':   'web_musicbrainz_artist',
        'MUSICBRAINZ_LABEL':    'web_musicbrainz_label',
        'MUSICBRAINZ_RECORDING': 'web_musicbrainz_recording',
        'MUSICBRAINZ_RELEASE':  'web_musicbrainz_release',
        'MUSICBRAINZ_RELEASEGROUP':  'web_musicbrainz_releasegroup',
        'MUSICBRAINZ_WORK':     'web_musicbrainz_work',
        'WIKIPEDIA_ARTIST':     'web_wikipedia_artist',
        'WIKIPEDIA_LABEL':      'web_wikipedia_label',
        'WIKIPEDIA_RELEASE':    'web_wikipedia_release',
        'WIKIPEDIA_WORK':       'web_wikipedia_work',
        'LYRICS_SITE':          'web_lyrics',
        'OFFICIAL_RELEASE':     'web_official_release',
        'COVERART':             'web_coverart',
    }
    __save_freetext_tags = dict([(v, k) for k, v in __load_freetext_tags.iteritems()])

    __load_tipl_roles = {
        'engineer': 'engineer',
        'arranger': 'arranger',
        'producer': 'producer',
        'DJ-mix': 'djmixer',
        'mix': 'mixer',
    }
    __save_tipl_roles = dict([(v, k) for k, v in __load_tipl_roles.iteritems()])

    __other_supported_tags = [
        "discnumber", "tracknumber",
        "totaldiscs", "totaltracks",
        "performer:", "comment",
        "lyrics", "~lyrics_sync",
    ]

    # Regex for parsing track/disk number/total
    __tag_re_parse = {
        'TRCK': re.compile(r'^(?P<tracknumber>\d+)(?:/(?P<totaltracks>\d+))?$'),
        'TPOS': re.compile(r'^(?P<discnumber>\d+)(?:/(?P<totaldiscs>\d+))?$'),
    }

    _supported_tags = (
        __save_text_tags.keys() +
        __save_freetext_tags.keys() +
        __save_tipl_roles.keys() +
        __other_supported_tags
    )

    __v24_to_v23_translation = {
        # Following tags are new in v2.4 will be converted to TXXX frames when
        # saving as v2.3.
        'TDEN': 'Encoding Time',
        'TDOR': 'Original Date',
        'TDTG': 'Tagging Date',
        'TMOO': 'Mood',
        'TPRO': 'Recording Copyright',
        'TSST': 'Disc Subtitle',
    }
    # Add support for id3v24 tags which are converted to TXXX if saving id3v23
    for tag in __v24_to_v23_translation:
        __load_freetext_tags[__v24_to_v23_translation[tag]] = __load_text_tags[tag]

    # Compatibility only currenty handles text tags i.. tags with text keyword
    __compatibility = {
        'TXXX:discnumber': ':discnumber',
        'TXXX:MusicBrainz Release Track Id': 'TXXX:MusicBrainz Track Id',
        'TXXX:MusicBrainz Album Artist Sortname': 'TSO2', # Picard 0.70
        'TXXX:MusicBrainz Album Artist': 'TPE2', # Picard 0.70
        'TXXX:MusicBrainz Non-Album': '', # Picard 0.70
        'TXXX:MusicBrainz Various Artists': 'TCMP', # Picard 0.70
        'TXXX:totaldiscs': ':totaldiscs',
        'TXXX:totaltracks': ':totaltracks',
        'TXXX:tracknumber': ':tracknumber',
        'TXXX:MusicBrainz TRM Id': '',
        #'TXXX:MusicMagic Fingerprint': '',
        #'TXXX:musicip_fingerprint': '',
        'TXXX:musicip_puid': 'MusicMagic PUID',
        'TXXX:TCMP': 'TCMP',
        'TXXX:DISCTOTAL': ':totaldiscs',
        'TXXX:TOTALDISCS': ':totaldiscs',
        'TXXX:TOTALTRACKS': ':totaltracks',
        'TXXX:TRACKTOTAL': ':totaltracks',
        'XDOR': 'TDOR',
        'XSOP': 'TSOP',
    }
    for text_tag, tag in __load_text_tags.iteritems():
        tag = tag[1:] if tag.startswith('~') else tag
        if tag not in __save_freetext_tags:
            __compatibility['TXXX:%s' % tag] = text_tag
            __compatibility['TXXX:%s' % tag.upper()] = text_tag
            __compatibility['TXXX:%s' % tag.title()] = text_tag
    for text_tag, tag in __load_freetext_tags.iteritems():
        tag = tag[1:] if tag.startswith('~') else tag
        from_tags, to_tag = (['TXXX', 'WXXX'], 'WXXX') if tag.startswith('web_') else (['TXXX'], 'TXXX')
        for from_tag in from_tags:
            if text_tag.upper() != text_tag:
                __compatibility['%s:%s' % (from_tag, text_tag.upper())] = '%s:%s' % (to_tag, text_tag)
            if text_tag.lower() != text_tag:
                __compatibility['%s:%s' % (from_tag, text_tag.lower())] = '%s:%s' % (to_tag, text_tag)
            if text_tag.title() != text_tag:
                __compatibility['%s:%s' % (from_tag, text_tag.title())] = '%s:%s' % (to_tag, text_tag)
            if tag != text_tag:
                __compatibility['%s:%s' % (from_tag, tag)] = '%s:%s' % (to_tag, text_tag)
            if tag.upper() != text_tag:
                __compatibility['%s:%s' % (from_tag, tag.upper())] = '%s:%s' % (to_tag, text_tag)
            if tag.title() != text_tag:
                __compatibility['%s:%s' % (from_tag, tag.title())] = '%s:%s' % (to_tag, text_tag)
    for text_tag, tag in __load_tipl_roles.iteritems():
        tag = tag[1:] if tag.startswith('~') else tag
        if text_tag.upper() != text_tag:
            __compatibility['TIPL:%s' % text_tag.upper()] = 'TIPL:%s' % text_tag
        if text_tag.lower() != text_tag:
            __compatibility['TIPL:%s' % text_tag.lower()] = 'TIPL:%s' % text_tag
        if text_tag.title() != text_tag:
            __compatibility['TIPL:%s' % text_tag.title()] = 'TIPL:%s' % text_tag
        if tag != text_tag:
            __compatibility['TIPL:%s' % tag] = 'TIPL:%s' % text_tag
        if tag.upper() != text_tag:
            __compatibility['TIPL:%s' % tag.upper()] = 'TIPL:%s' % text_tag
        if tag.lower() != text_tag:
            __compatibility['TIPL:%s' % tag.lower()] = 'TIPL:%s' % text_tag
        if tag.title() != text_tag:
            __compatibility['TIPL:%s' % tag.title()] = 'TIPL:%s' % text_tag
        __compatibility['TXXX:%s' % text_tag] = 'TIPL:%s' % text_tag
        __compatibility['TXXX:%s' % text_tag.upper()] = 'TIPL:%s' % text_tag
        __compatibility['TXXX:%s' % text_tag.lower()] = 'TIPL:%s' % text_tag
        __compatibility['TXXX:%s' % text_tag.title()] = 'TIPL:%s' % text_tag

    __load_date_tags = [
        'date',
        'encodingtime',
        'originaldate',
        'originalyear',
        'recordingdate',
        '~tagtime',
    ]

    __load_int_tags = [
        'discnumber',
        'tracknumber',
        'disctotal',
        'tracktotal',
    ]


    def _load(self, filename):
        log.debug("Loading file: %r", filename)
        file = self._get_file(encode_filename(filename))
        tags = file.tags or {}
        metadata = Metadata()
        self._info(metadata, file)

        # handle other tools / backwards compatibility
        for old, new in self.__compatibility.iteritems():
            if old not in tags:
                continue
            if new:
                tag, desc = new.split(':', 1) if ':' in new else (new, '')
                frame = tags[old]
                value = frame.url if frame.FrameID.startswith('W') else frame.text
                if not tag:
                    # e.g. old tag has no direct equivalent - store to metadata
                    if old.startswith('T'):
                        metadata[desc] = sanitize_int(value)
                        log.info('ID3: File %r: Upgrading tag: %s=>%s',
                            path.split(filename)[1], old, desc)
                    else:
                        log.warning('ID3: File %r: Cannot upgrade tag - not a text tag: %s=>%s',
                            path.split(filename)[1], old, desc)
                        continue
                elif new in tags:
                    log.warning('ID3: File %r: Cannot upgrade text tag - new tag already exists: %s=>%s',
                        path.split(filename)[1], old, new)
                    continue
                else:
                    if tag.startswith('W'):
                        tags.add(getattr(id3, tag)(encoding=frame.encoding, desc=desc, url=value))
                    else:
                        tags.add(getattr(id3, tag)(encoding=frame.encoding, desc=desc, text=value))

                    if (tag not in self.__v24_to_v23_translation
                            or frame.desc != self.__v24_to_v23_translation[tag]):
                        log.info('ID3: File %r: Upgrading tag: %s=>%s',
                            path.split(filename)[1], old, new)
            frame = tags.pop(old)

        for tag_name, frame in tags.items():
            frameid = frame.FrameID
            if frameid in self.__load_text_tags:
                name = self.__load_text_tags[frameid]
                # If id3v23, original year TORY (year only) has been upgraded to TDOR.
                # If previously saved by Picard, then we also saved full Original Date
                # as TXXX so do not overwrite that if previously loaded.
                # Ditto for TBPM which is integer and we saved a full version as TXXX.
                if name in self.__save_freetext_tags and name in metadata:
                    continue
                if frameid.startswith('T'):
                    metadata[name] = [unicode(v) for v in frame.text if unicode(v)]
                elif frameid.startswith('W'):
                    metadata[name] = unicode(frame.url)
                else:
                    log.error('ID3: File %r: Unhandled frameid %s in one-to-one tags: %s=%r',
                        path.split(filename)[1], frameid, name, frame)
            elif frameid == 'COMM':
                name = 'comment'
                if frame.desc:
                    name +=':%s' % frame.desc
                for text in frame.text:
                    if text:
                        metadata.add(name, unicode(text))
            elif frameid in ["TMCL", "TIPL"]:
                # If file is ID3v2.3, TIPL tag could contain TMCL
                # so we will test for TMCL values and add to TIPL if not TMCL
                for role, name in frame.people:
                    if role and role in self.__load_tipl_roles:
                        metadata.add(self.__load_tipl_roles[role], name)
                    else:
                        metadata.add('performer:%s' % role, name)
            elif frameid in ['TXXX', 'WXXX']:
                name = frame.desc
                values = frame.text if frameid == 'TXXX' else [frame.url]
                if name in self.__load_freetext_tags:
                    name = self.__load_freetext_tags[name]
                elif ((name in self.__save_text_tags) !=
                        (name in self.__save_freetext_tags)):
                    # If the desc of a TXXX frame conflicts with the name of a
                    # Picard tag, load it into ~id3:TXXX:desc rather than desc.
                    #
                    # This basically performs an XOR, making sure that 'name'
                    # is in __save_text_tags or __save_freetext_tags, but not
                    # both. (Being in both implies we support reading it both
                    # ways.) Currently, the only tag in both is license.

                    # TODO Switch to _supported_tags instead of _rtranslate
                    log.info('ID3: File %r: Loading ID3 specific %s metadata which conflicts with known Picard tag: %s=%r',
                        path.split(filename)[1], frameid, name, values)
                    name = '~id3:%s:%s' % (frameid, name)
                else:
                    log.info('ID3: File %r: Loading user %s metadata: %s=%r',
                        path.split(filename)[1], frameid, name, values)
                metadata[name] = [unicode(v) for v in values]
            elif frameid == 'USLT':
                name = 'lyrics'
                if frame.desc or frame.lang != EMPTY_LANG:
                    name += ':'
                    if frame.desc:
                        name += frame.desc
                    if frame.lang != EMPTY_LANG:
                        name += '(%s)' % frame.lang
                metadata[name] = frame.text.split('\n\n\n\n')
            elif frameid == 'SYLT':
                name = '~lyrics_sync:'
                if frame.desc and frame.desc != 'None':
                    name += frame.desc
                if frame.lang and frame.lang != EMPTY_LANG:
                    name += '(%s)' % frame.lang
                if name.endswith(':'):
                    name = name[:-1]
                metadata.add(name, json.dumps({
                    'timestamp_format': frame.format,
                    'content_type': frame.type,
                    'text': frame.text,
                    }, sort_keys=True)
                )
            elif (frameid == 'UFID'
                    and frame.owner == 'http://musicbrainz.org'
                    and 'musicbrainz_recordingid' not in metadata):
                metadata['musicbrainz_recordingid'] = frame.data.decode('ascii', 'ignore')
            elif frameid in self.__tag_re_parse:
                # Track/Disc Number/Total
                m = self.__tag_re_parse[frameid].search(frame.text[0])
                if m:
                    for name, value in m.groupdict().iteritems():
                        if value is not None:
                            metadata[name] = value
                else:
                    log.warning("ID3: File %r: Invalid Track/Disc Number/Total dropped: %s=%s",
                        filename, frameid, frame.text[0])
            elif frameid == 'APIC':
                try:
                    coverartimage = TagCoverArtImage(
                        file=filename,
                        tag=frameid,
                        types=types_from_id3(frame.type),
                        comment=frame.desc,
                        support_types=True,
                        data=frame.data,
                    )
                except CoverArtImageError as e:
                    log.error('ID3: File %r: Cannot load image: %s', filename, e)
                else:
                    metadata.append_image(coverartimage)
            elif frameid == 'POPM':
                # Rating in ID3 ranges from 0 to 255, normalize this to the range 0 to 5
                if frame.email == config.setting['rating_user_email']:
                    rating = unicode(int(round(frame.rating / 255.0 * (config.setting['rating_steps'] - 1))))
                    metadata.add('~rating', rating)

        for tag in self.__load_date_tags:
            if tag in metadata:
                sanitized = sanitize_date(metadata.getall(tag)[0])
                if sanitized:
                    metadata[tag] = sanitized

        for tag in self.__load_int_tags:
            if tag in metadata:
                metadata[tag] = [sanitize_int(d) for d in metadata.getall(tag)]

        return metadata

    def _save(self, filename, metadata):
        """Save metadata to the file."""
        log.debug("Saving file: %r", filename)
        tags = self._get_tags(filename)

        if config.setting['clear_existing_tags']:
            tags.clear()
        if metadata.images_to_be_saved_to_tags:
            tags.delall('APIC')

        encoding = {'iso-8859-1': 0, 'utf-8': 3, 'utf-16': 1}.get(config.setting['id3v2_encoding'], 0)

        if 'tracknumber' in metadata:
            if 'totaltracks' in metadata:
                text = '%s/%s' % (metadata['tracknumber'], metadata['totaltracks'])
            else:
                text = metadata['tracknumber']
            tags.add(id3.TRCK(encoding=encoding, text=text))

        if 'discnumber' in metadata:
            if 'totaldiscs' in metadata:
                text = '%s/%s' % (metadata['discnumber'], metadata['totaldiscs'])
            else:
                text = metadata['discnumber']
            tags.add(id3.TPOS(encoding=encoding, text=text))

        if 'musicbrainz_recordingid' in metadata:
            tags.add(id3.UFID(owner='http://musicbrainz.org', data=metadata['musicbrainz_recordingid']))

        # This is necessary because mutagens HashKey for APIC frames only
        # includes the FrameID (APIC) and description - it's basically
        # impossible to save two images, even of different types, without
        # any description.
        counters = defaultdict(lambda: 0)
        for image in metadata.images_to_be_saved_to_tags:
            desc = desctag = image.comment
            if counters[desc] > 0:
                if desc:
                    desctag = "%s (%i)" % (desc, counters[desc])
                else:
                    desctag = "(%i)" % counters[desc]
            counters[desc] += 1
            tags.add(id3.APIC(encoding=encoding,
                              mime=image.mimetype,
                              type=image_type_as_id3_num(image.maintype),
                              desc=desctag,
                              data=image.data))

        tmcl = id3.TMCL(encoding=encoding, people=[])
        tipl = id3.TIPL(encoding=encoding, people=[])

        tags.delall('TCMP')
        for name, values in metadata.rawitems():
            if name.startswith('performer:'):
                role = name.split(':', 1)[1]
                for value in values:
                    tmcl.people.append([role, value])
            elif name in self.__save_tipl_roles:
                for value in values:
                    tipl.people.append([self.__save_tipl_roles[name], value])
            elif name.startswith('comment:') or name == 'comment':
                desc = ''
                lang = EMPTY_LANG
                if ':' in name:
                    desc = name.split(':', 1)[1]
                    if desc.endswith(')') and '(' in desc:
                        desc, lang = desc[:-1].rsplit('(',1)
                if desc.lower()[:4] == "itun":
                    tags.delall('COMM:' + desc)
                    tags.add(id3.COMM(encoding=encoding, desc=desc, lang='eng', text=[v + u'\x00' for v in values]))
                else:
                    tags.add(id3.COMM(encoding=encoding, desc=desc, text=values))
            elif name.startswith('lyrics:') or name == 'lyrics':
                desc = ''
                lang = EMPTY_LANG
                if ':' in name:
                    desc = name.split(':', 1)[1]
                    if desc.endswith(')') and '(' in desc:
                        desc, lang = desc[:-1].rsplit('(',1)
                values = '\n\n\n\n'.join(values)
                tags.add(id3.USLT(encoding=encoding, desc=desc, lang=lang, text=values))
            elif name.startswith('~lyrics_sync:') or name == '~lyrics_sync':
                desc = lang = None
                if ':' in name:
                    desc = name.split(':', 1)[1]
                    if desc.endswith(')') and '(' in desc:
                        desc, lang = desc[:-1].rsplit('(',1)
                for value in values:
                    sylt = json.loads(value)
                    tags.add(id3.SYLT(
                        encoding=encoding,
                        lang=lang,
                        format=sylt['timestamp_format'],
                        type=sylt['content_type'],
                        desc=desc,
                        text=sylt['text']
                        ))
            elif name == '~rating':
                # Unclear what should happen if config.setting['enable_ratings'] == False
                # Search for an existing POPM frame to get the current playcount
                for frame in tags.values():

                    if frame.FrameID == 'POPM' and frame.email == config.setting['rating_user_email']:
                        count = getattr(frame, 'count', 0)
                        break
                else:
                    count = 0
                # Convert rating to range between 0 and 255
                rating = int(round(float(values[0]) * 255 / (config.setting['rating_steps'] - 1)))
                tags.add(id3.POPM(email=config.setting['rating_user_email'], rating=rating, count=count))
            elif name in self.__save_text_tags:
                if name in self.__save_freetext_tags:
                    # Where needed to preserve full values, also save as a text tag
                    tags.add(id3.TXXX(encoding=encoding, desc=self.__save_freetext_tags[name], text=values))
                frameid = self.__save_text_tags[name]
                if frameid == 'WCOP':
                    # Only add WCOP if there is only one license URL, otherwise use TXXX:LICENSE
                    if len(values) == 1 and isurl(values[0]):
                        tags.add(id3.WCOP(url=values[0]))
                    else:
                        tags.add(id3.TXXX(encoding=encoding, desc=self.__save_freetext_tags[name], text=values))
                elif frameid in ['WOAR', 'WPUB']:
                    for url in values:
                        if isurl(url):
                            tags.add(getattr(id3, frameid)(url=url))
                        else:
                            log.warning('ID3: File %r: Cannot save invalid URL for web tag: %s=%r',
                                path.split(filename)[1], frameid, url)
                elif frameid.startswith('T'):
                    if frameid == 'TBPM':
                        # According to spec., TBPM needs to be an integer
                        values = [str(int(float(values[0])))]
                    tags.add(getattr(id3, frameid)(encoding=encoding, text=values))
            elif name in self.__save_freetext_tags:
                desc = self.__save_freetext_tags[name]
                if len(values) == 1 and isurl(values[0]):
                    tags.add(id3.WXXX(encoding=encoding, desc=desc, url=values[0]))
                    tags.delall('TXXX:%s' % desc)
                else:
                    tags.add(id3.TXXX(encoding=encoding, desc=desc, text=values))
                    tags.delall('WXXX:%s' % desc)
            elif name.startswith('~id3:'):
                name = name[5:]
                log.info('ID3: File %r: Saving ID3 specific metadata: %s=%r',
                    path.split(filename)[1], name, values)
                if name[:5] in ['TXXX:', 'WXXX:']:
                    if name[:5] == 'TXXX' or len(values) > 1:
                        tags.add(id3.TXXX(encoding=encoding, desc=name[5:], text=values))
                    elif len(values) > 1:
                        log.warning('ID3: File %r: Saving ID3 specific multi-value WXXX metadata as TXXX: %s=%r',
                            path.split(filename)[1], name, values)
                        tags.add(id3.TXXX(encoding=encoding, desc=name[5:], text=values))
                    elif not isurl(values[0]):
                        log.warning('ID3: File %r: Saving ID3 specific non-url WXXX metadata as TXXX: %s=%r',
                            path.split(filename)[1], name, values[0])
                        tags.add(id3.TXXX(encoding=encoding, desc=name[5:], text=values))
                    else:
                        tags.add(id3.WXXX(encoding=encoding, desc=name[5:], url=values[0]))
                elif len(name) != 4 and name[4] != ':':
                    log.warning('ID3: File %r: Invalid ID3 specific tag: %s=%r',
                        path.split(filename)[1], name, values)
                else:
                    frameclass = getattr(id3, name[:4], None)
                    desc = name[5:] if len(desc) > 5 else None
                    if name[4:] and not name[4:].startswith(':'):
                        log.warning('ID3: File %r: Unable to save ID3 specific tag: %s=%r raised exception: %s',
                            path.split(filename)[1], name, values, e)
                    elif frameclass:
                            tags.add(frameclass(encoding=encoding, desc=desc, text=values))
                    else:
                        log.warning('ID3: File %r: Unable to save invalid ID3 specific tag: %s=%r',
                            path.split(filename)[1], name, values)
            elif name not in self._supported_tags and not name.startswith("~"):
                if len(values) == 1 and isurl(values[0]):
                    log.info('ID3: File %r: Saving user WXXX metadata: %s=%r',
                        path.split(filename)[1], name, values)
                    tags.add(id3.WXXX(encoding=encoding, desc=name, url=values[0]))
                else:
                    log.info('ID3: File %r: Saving user TXXX metadata: %s=%r',
                        path.split(filename)[1], name, values)
                    tags.add(id3.TXXX(encoding=encoding, desc=name, text=values))

        if tmcl.people:
            tags.add(tmcl)
        if tipl.people:
            tags.add(tipl)

        tags.delall('TDTG')
        tags.add(id3.TDTG(encoding=encoding, text=strftime(TIMESTAMP_FORMAT, gmtime())))

        self._save_tags(tags, encode_filename(filename))

        if self._IsMP3 and config.setting["remove_ape_from_mp3"]:
            try:
                mutagen.apev2.delete(encode_filename(filename))
            except:
                pass

    def _get_file(self, filename):
        raise NotImplementedError()

    def _get_tags(self, filename):
        file = self._get_file(filename)
        if file.tags is None:
            file.add_tags()
        return file.tags

    def _get_id3v1(self):
        return 2 if config.setting['write_id3v1'] else 0

    def _save_tags(self, tags, filename):
        v1 = self._get_id3v1()
        if config.setting['write_id3v23']:
            separator = config.setting['id3v23_join_with']

            # convert tags in id3v24 and not id3v23 to freetext
            encoding = {'utf-16': 1}.get(config.setting['id3v2_encoding'], 0)
            # New frames added in v2.4.
            for key in self.__v24_to_v23_translation:
                if key in tags:
                    text = tags[key].text
                    tags.add(
                        id3.TXXX(
                            encoding=encoding,
                            desc=self.__v24_to_v23_translation[key],
                            text=separator.join(map(str,text))
                        )
                    )
                    del tags[key]

            # save TSOP, TSOA and TSOT even though they are officially defined
            # only in ID3v2.4, because most applications use them also in ID3v2.3
            # See https://code.google.com/p/mutagen/issues/detail?id=85#c19 for
            # officially sanctioned approach.
            saved_tags = []
            for tag in ['TSOP', 'TSOA', 'TSOT']:
                if tag in tags:
                    saved_tags.append(tags[tag])
            tags.update_to_v23()
            for tag in saved_tags:
                tags.add(tag)
            if v1 != None:
                tags.save(filename, v2_version=3, v1=v1, v23_sep=separator)
            else:
                tags.save(filename, v2_version=3, v23_sep=separator)
        else:
            tags.update_to_v24()
            if v1 != None:
                tags.save(filename, v2_version=4, v1=v1)
            else:
                tags.save(filename, v2_version=4)

    @property
    def new_metadata(self):
        if not config.setting["write_id3v23"]:
            return self.metadata

        copy = Metadata()
        copy.copy(self.metadata)

        join_with = config.setting["id3v23_join_with"]
        copy.multi_valued_joiner = join_with

        for name, values in copy.rawitems():
            # ID3v23 can only save TDOR dates in YYYY format. Mutagen cannot
            # handle ID3v23 dates which are YYYY-MM rather than YYYY or
            # YYYY-MM-DD.

            if name == "originaldate":
                values = [v[:4] for v in values]
            elif name == "date":
                values = [v[:4] if len(v) < 10 else v for v in values]

            # If this is a multi-valued field, then it needs to be flattened,
            # unless it's:
            #   TIPL or TMCL which can still be multi-valued; or
            #   a Web URL which can only be single valued; or
            #   comments or lyrics which are often multi-line.

            if (len(values) > 1
                    # IPLS supports multi-value
                    and not name in ID3File.__save_tipl_roles
                    and not name.startswith("performer:")
                    # URLs cannot be joined
                    and not name.startswith("web_")):
                # lyrics and comments can be multi-line, so joining with
                # new lines makes more sense than joining with '/' or '; '
                if (    name.startswith("lyrics:") or name == "lyrics"
                    or  name.startswith("comment:") or name == "comment"):
                        values = ['\n----------\n'.join(values)]
                else:
                        values = [join_with.join(values)]

            copy[name] = values

        return copy


class MP3File(ID3File):

    """MP3 file."""
    EXTENSIONS = [".mp3", ".mp2", ".m2a"]
    NAME = "MPEG-1 Audio"
    _IsMP3 = True

    def _get_file(self, filename):
        return mutagen.mp3.MP3(filename, known_frames=known_frames)

    def _info(self, metadata, file):
        super(MP3File, self)._info(metadata, file)
        id3version = ''
        if file.tags is not None and file.info.layer == 3:
            id3version = ' - ID3v%d.%d' % (file.tags.version[0], file.tags.version[1])
        metadata['~format'] = 'MPEG-1 Layer %d%s' % (file.info.layer, id3version)
        if hasattr(file.info, 'encoder_info') and file.info.encoder_info:
            metadata['~codec'] = file.info.encoder_info


class TrueAudioFile(ID3File):

    """TTA file."""
    EXTENSIONS = [".tta"]
    NAME = "The True Audio (TTA)"

    def _get_file(self, filename):
        return mutagen.trueaudio.TrueAudio(filename, known_frames=known_frames)


if mutagen.aiff:
    class AiffFile(ID3File):

        """AIFF file."""
        EXTENSIONS = [".aiff", ".aif", ".aifc"]
        NAME = "Audio Interchange File Format (AIFF)"

        def _get_file(self, filename):
            return mutagen.aiff.AIFF(filename, known_frames=known_frames)

        def _get_id3v1(self):
            return None

else:
    AiffFile = None
