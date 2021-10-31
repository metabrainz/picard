# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2009, 2011-2012 Lukáš Lalinský
# Copyright (C) 2008-2011, 2014, 2018-2021 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2011-2012 Johannes Weißl
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2011-2014 Wieland Hoffmann
# Copyright (C) 2013 Calvin Walton
# Copyright (C) 2013-2014, 2017-2020 Laurent Monin
# Copyright (C) 2013-2015, 2017, 2021 Sophist-UK
# Copyright (C) 2015 Frederik “Freso” S. Olesen
# Copyright (C) 2016 Christoph Reiter
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 tungol
# Copyright (C) 2019 Zenara Daley
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


from collections import defaultdict
from enum import IntEnum
import re
from urllib.parse import urlparse

from mutagen import id3
import mutagen.aiff
import mutagen.apev2
import mutagen.dsf
import mutagen.mp3
import mutagen.trueaudio

from picard import log
from picard.config import get_config
from picard.coverart.image import (
    CoverArtImageError,
    TagCoverArtImage,
)
from picard.coverart.utils import types_from_id3
from picard.file import File
from picard.formats.mutagenext import (
    compatid3,
    delall_ci,
)
from picard.metadata import Metadata
from picard.util import (
    encode_filename,
    sanitize_date,
)
from picard.util.tags import parse_comment_tag


UNSUPPORTED_TAGS = {'r128_album_gain', 'r128_track_gain'}

id3.GRP1 = compatid3.GRP1


class Id3Encoding(IntEnum):
    LATIN1 = 0
    UTF16 = 1
    UTF16BE = 2
    UTF8 = 3

    def from_config(id3v2_encoding):
        return {
            'utf-8': Id3Encoding.UTF8,
            'utf-16': Id3Encoding.UTF16
        }.get(id3v2_encoding, Id3Encoding.LATIN1)


def id3text(text, encoding):
    """Returns a string which only contains code points which can
    be encododed with the given numeric id3 encoding.
    """

    if encoding == Id3Encoding.LATIN1:
        return text.encode("latin1", "replace").decode("latin1")
    return text


def _remove_people_with_role(tags, frames, role):
    for frame in tags.values():
        if frame.FrameID in frames:
            for people in list(frame.people):
                if people[0] == role:
                    frame.people.remove(people)


class ID3File(File):

    """Generic ID3-based file."""
    _IsMP3 = False

    __upgrade = {
        'XSOP': 'TSOP',
        'TXXX:ALBUMARTISTSORT': 'TSO2',
        'TXXX:COMPOSERSORT': 'TSOC',
        'TXXX:mood': 'TMOO',
    }

    __translate = {
        # In same sequence as defined at http://id3.org/id3v2.4.0-frames
        # 'TIT1': 'grouping', # Depends on itunes_compatible_grouping
        'TIT2': 'title',
        'TIT3': 'subtitle',
        'TALB': 'album',
        'TSST': 'discsubtitle',
        'TSRC': 'isrc',
        'TPE1': 'artist',
        'TPE2': 'albumartist',
        'TPE3': 'conductor',
        'TPE4': 'remixer',
        'TEXT': 'lyricist',
        'TCOM': 'composer',
        'TENC': 'encodedby',
        'TBPM': 'bpm',
        'TKEY': 'key',
        'TLAN': 'language',
        'TCON': 'genre',
        'TMED': 'media',
        'TMOO': 'mood',
        'TCOP': 'copyright',
        'TPUB': 'label',
        'TDOR': 'originaldate',
        'TDRC': 'date',
        'TSSE': 'encodersettings',
        'TSOA': 'albumsort',
        'TSOP': 'artistsort',
        'TSOT': 'titlesort',
        'WCOP': 'license',
        'WOAR': 'website',
        'COMM': 'comment',
        'TOAL': 'originalalbum',
        'TOPE': 'originalartist',
        'TOFN': 'originalfilename',

        # The following are informal iTunes extensions to id3v2:
        'TCMP': 'compilation',
        'TSOC': 'composersort',
        'TSO2': 'albumartistsort',
        'MVNM': 'movement'
    }
    __rtranslate = dict([(v, k) for k, v in __translate.items()])
    __translate['GRP1'] = 'grouping'  # Always read, but writing depends on itunes_compatible_grouping

    __translate_freetext = {
        'MusicBrainz Artist Id': 'musicbrainz_artistid',
        'MusicBrainz Album Id': 'musicbrainz_albumid',
        'MusicBrainz Album Artist Id': 'musicbrainz_albumartistid',
        'MusicBrainz Album Type': 'releasetype',
        'MusicBrainz Album Status': 'releasestatus',
        'MusicBrainz TRM Id': 'musicbrainz_trmid',
        'MusicBrainz Release Track Id': 'musicbrainz_trackid',
        'MusicBrainz Disc Id': 'musicbrainz_discid',
        'MusicBrainz Work Id': 'musicbrainz_workid',
        'MusicBrainz Release Group Id': 'musicbrainz_releasegroupid',
        'MusicBrainz Original Album Id': 'musicbrainz_originalalbumid',
        'MusicBrainz Original Artist Id': 'musicbrainz_originalartistid',
        'MusicBrainz Album Release Country': 'releasecountry',
        'MusicIP PUID': 'musicip_puid',
        'Acoustid Fingerprint': 'acoustid_fingerprint',
        'Acoustid Id': 'acoustid_id',
        'SCRIPT': 'script',
        'LICENSE': 'license',
        'CATALOGNUMBER': 'catalognumber',
        'BARCODE': 'barcode',
        'ASIN': 'asin',
        'MusicMagic Fingerprint': 'musicip_fingerprint',
        'ARTISTS': 'artists',
        'DIRECTOR': 'director',
        'WORK': 'work',
        'Writer': 'writer',
        'SHOWMOVEMENT': 'showmovement',
    }
    __rtranslate_freetext = dict([(v, k) for k, v in __translate_freetext.items()])
    __translate_freetext['writer'] = 'writer'  # For backward compatibility of case

    # Freetext fields that are loaded case-insensitive
    __rtranslate_freetext_ci = {
        'replaygain_album_gain': 'REPLAYGAIN_ALBUM_GAIN',
        'replaygain_album_peak': 'REPLAYGAIN_ALBUM_PEAK',
        'replaygain_album_range': 'REPLAYGAIN_ALBUM_RANGE',
        'replaygain_track_gain': 'REPLAYGAIN_TRACK_GAIN',
        'replaygain_track_peak': 'REPLAYGAIN_TRACK_PEAK',
        'replaygain_track_range': 'REPLAYGAIN_TRACK_RANGE',
        'replaygain_reference_loudness': 'REPLAYGAIN_REFERENCE_LOUDNESS',
    }
    __translate_freetext_ci = dict([(b.lower(), a) for a, b in __rtranslate_freetext_ci.items()])

    # Obsolete tag names which will still be loaded, but will get renamed on saving
    __rename_freetext = {
        'Artists': 'ARTISTS',
        'Work': 'WORK',
    }
    __rrename_freetext = dict([(v, k) for k, v in __rename_freetext.items()])

    _tipl_roles = {
        'engineer': 'engineer',
        'arranger': 'arranger',
        'producer': 'producer',
        'DJ-mix': 'djmixer',
        'mix': 'mixer',
    }
    _rtipl_roles = dict([(v, k) for k, v in _tipl_roles.items()])

    __other_supported_tags = ("discnumber", "tracknumber",
                              "totaldiscs", "totaltracks",
                              "movementnumber", "movementtotal")
    __tag_re_parse = {
        'TRCK': re.compile(r'^(?P<tracknumber>\d+)(?:/(?P<totaltracks>\d+))?$'),
        'TPOS': re.compile(r'^(?P<discnumber>\d+)(?:/(?P<totaldiscs>\d+))?$'),
        'MVIN': re.compile(r'^(?P<movementnumber>\d+)(?:/(?P<movementtotal>\d+))?$')
    }

    def __init__(self, filename):
        super().__init__(filename)
        self.__casemap = {}

    def build_TXXX(self, encoding, desc, values):
        """Construct and return a TXXX frame."""
        # This is here so that plugins can customize the behavior of TXXX
        # frames in particular via subclassing.
        # discussion: https://github.com/metabrainz/picard/pull/634
        # discussion: https://github.com/metabrainz/picard/pull/635
        # Used in the plugin "Compatible TXXX frames"
        # PR: https://github.com/metabrainz/picard-plugins/pull/83
        return id3.TXXX(encoding=encoding, desc=desc, text=values)

    def _load(self, filename):
        log.debug("Loading file %r", filename)
        self.__casemap = {}
        file = self._get_file(encode_filename(filename))
        tags = file.tags or {}
        config = get_config()
        itunes_compatible = config.setting['itunes_compatible_grouping']
        rating_user_email = id3text(config.setting['rating_user_email'], Id3Encoding.LATIN1)
        rating_steps = config.setting['rating_steps']
        # upgrade custom 2.3 frames to 2.4
        for old, new in self.__upgrade.items():
            if old in tags and new not in tags:
                f = tags.pop(old)
                tags.add(getattr(id3, new)(encoding=f.encoding, text=f.text))
        metadata = Metadata()
        for frame in tags.values():
            frameid = frame.FrameID
            if frameid in self.__translate:
                name = self.__translate[frameid]
                if frameid.startswith('T') or frameid in {"GRP1", "MVNM"}:
                    for text in frame.text:
                        if text:
                            metadata.add(name, text)
                elif frameid == 'COMM':
                    for text in frame.text:
                        if text:
                            if frame.lang == 'eng':
                                name = '%s:%s' % (name, frame.desc)
                            else:
                                name = '%s:%s:%s' % (name, frame.lang, frame.desc)
                            metadata.add(name, text)
                else:
                    metadata.add(name, frame)
            elif frameid == 'TIT1':
                name = 'work' if itunes_compatible else 'grouping'
                for text in frame.text:
                    if text:
                        metadata.add(name, text)
            elif frameid == "TMCL":
                for role, name in frame.people:
                    if role == 'performer':
                        role = ''
                    if role:
                        metadata.add('performer:%s' % role, name)
                    else:
                        metadata.add('performer', name)
            elif frameid == "TIPL":
                # If file is ID3v2.3, TIPL tag could contain TMCL
                # so we will test for TMCL values and add to TIPL if not TMCL
                for role, name in frame.people:
                    if role in self._tipl_roles and name:
                        metadata.add(self._tipl_roles[role], name)
                    else:
                        if role == 'performer':
                            role = ''
                        if role:
                            metadata.add('performer:%s' % role, name)
                        else:
                            metadata.add('performer', name)
            elif frameid == 'TXXX':
                name = frame.desc
                name_lower = name.lower()
                if name in self.__rename_freetext:
                    name = self.__rename_freetext[name]
                if name_lower in self.__translate_freetext_ci:
                    orig_name = name
                    name = self.__translate_freetext_ci[name_lower]
                    self.__casemap[name] = orig_name
                elif name in self.__translate_freetext:
                    name = self.__translate_freetext[name]
                elif ((name in self.__rtranslate)
                      != (name in self.__rtranslate_freetext)):
                    # If the desc of a TXXX frame conflicts with the name of a
                    # Picard tag, load it into ~id3:TXXX:desc rather than desc.
                    #
                    # This basically performs an XOR, making sure that 'name'
                    # is in __rtranslate or __rtranslate_freetext, but not
                    # both. (Being in both implies we support reading it both
                    # ways.) Currently, the only tag in both is license.
                    name = '~id3:TXXX:' + name
                for text in frame.text:
                    metadata.add(name, text)
            elif frameid == 'USLT':
                name = 'lyrics'
                if frame.desc:
                    name += ':%s' % frame.desc
                metadata.add(name, frame.text)
            elif frameid == 'UFID' and frame.owner == 'http://musicbrainz.org':
                metadata['musicbrainz_recordingid'] = frame.data.decode('ascii', 'ignore')
            elif frameid in self.__tag_re_parse.keys():
                m = self.__tag_re_parse[frameid].search(frame.text[0])
                if m:
                    for name, value in m.groupdict().items():
                        if value is not None:
                            metadata[name] = value
                else:
                    log.error("Invalid %s value '%s' dropped in %r", frameid, frame.text[0], filename)
            elif frameid == 'APIC':
                try:
                    coverartimage = TagCoverArtImage(
                        file=filename,
                        tag=frameid,
                        types=types_from_id3(frame.type),
                        comment=frame.desc,
                        support_types=True,
                        data=frame.data,
                        id3_type=frame.type,
                    )
                except CoverArtImageError as e:
                    log.error('Cannot load image from %r: %s' % (filename, e))
                else:
                    metadata.images.append(coverartimage)
            elif frameid == 'POPM':
                # Rating in ID3 ranges from 0 to 255, normalize this to the range 0 to 5
                if frame.email == rating_user_email:
                    rating = int(round(frame.rating / 255.0 * (rating_steps - 1)))
                    metadata.add('~rating', rating)

        if 'date' in metadata:
            sanitized = sanitize_date(metadata.getall('date')[0])
            if sanitized:
                metadata['date'] = sanitized

        self._info(metadata, file)
        return metadata

    def _save(self, filename, metadata):
        """Save metadata to the file."""
        log.debug("Saving file %r", filename)
        tags = self._get_tags(filename)
        config = get_config()
        if config.setting['clear_existing_tags']:
            cover = tags.getall('APIC') if config.setting["preserve_images"] else None
            tags.clear()
            if cover:
                tags.setall('APIC', cover)
        images_to_save = list(metadata.images.to_be_saved_to_tags())
        if images_to_save:
            tags.delall('APIC')

        encoding = Id3Encoding.from_config(config.setting['id3v2_encoding'])

        if 'tracknumber' in metadata:
            if 'totaltracks' in metadata:
                text = '%s/%s' % (metadata['tracknumber'], metadata['totaltracks'])
            else:
                text = metadata['tracknumber']
            tags.add(id3.TRCK(encoding=Id3Encoding.LATIN1, text=id3text(text, Id3Encoding.LATIN1)))

        if 'discnumber' in metadata:
            if 'totaldiscs' in metadata:
                text = '%s/%s' % (metadata['discnumber'], metadata['totaldiscs'])
            else:
                text = metadata['discnumber']
            tags.add(id3.TPOS(encoding=Id3Encoding.LATIN1, text=id3text(text, Id3Encoding.LATIN1)))

        if 'movementnumber' in metadata:
            if 'movementtotal' in metadata:
                text = '%s/%s' % (metadata['movementnumber'], metadata['movementtotal'])
            else:
                text = metadata['movementnumber']
            tags.add(id3.MVIN(encoding=Id3Encoding.LATIN1, text=id3text(text, Id3Encoding.LATIN1)))

        # This is necessary because mutagens HashKey for APIC frames only
        # includes the FrameID (APIC) and description - it's basically
        # impossible to save two images, even of different types, without
        # any description.
        counters = defaultdict(lambda: 0)
        for image in images_to_save:
            desc = desctag = image.comment
            if counters[desc] > 0:
                if desc:
                    desctag = "%s (%i)" % (desc, counters[desc])
                else:
                    desctag = "(%i)" % counters[desc]
            counters[desc] += 1
            tags.add(id3.APIC(encoding=Id3Encoding.LATIN1,
                              mime=image.mimetype,
                              type=image.id3_type,
                              desc=id3text(desctag, Id3Encoding.LATIN1),
                              data=image.data))

        tmcl = mutagen.id3.TMCL(encoding=encoding, people=[])
        tipl = mutagen.id3.TIPL(encoding=encoding, people=[])
        for name, values in metadata.rawitems():
            values = [id3text(v, encoding) for v in values]
            name = id3text(name, encoding)
            name_lower = name.lower()

            if not self.supports_tag(name):
                continue
            elif name == 'performer' or name.startswith('performer:'):
                if ':' in name:
                    role = name.split(':', 1)[1]
                else:
                    role = 'performer'
                for value in values:
                    if config.setting['write_id3v23']:
                        # TIPL will be upgraded to IPLS
                        tipl.people.append([role, value])
                    else:
                        tmcl.people.append([role, value])
            elif name == 'comment' or name.startswith('comment:'):
                (lang, desc) = parse_comment_tag(name)
                if desc.lower()[:4] == 'itun':
                    tags.delall('COMM:' + desc)
                    tags.add(id3.COMM(encoding=Id3Encoding.LATIN1, desc=desc, lang='eng', text=[v + '\x00' for v in values]))
                else:
                    tags.add(id3.COMM(encoding=encoding, desc=desc, lang=lang, text=values))
            elif name.startswith('lyrics:') or name == 'lyrics':
                if ':' in name:
                    desc = name.split(':', 1)[1]
                else:
                    desc = ''
                for value in values:
                    tags.add(id3.USLT(encoding=encoding, desc=desc, text=value))
            elif name in self._rtipl_roles:
                for value in values:
                    tipl.people.append([self._rtipl_roles[name], value])
            elif name == 'musicbrainz_recordingid':
                tags.add(id3.UFID(owner='http://musicbrainz.org', data=bytes(values[0], 'ascii')))
            elif name == '~rating':
                rating_user_email = id3text(config.setting['rating_user_email'], Id3Encoding.LATIN1)
                # Search for an existing POPM frame to get the current playcount
                for frame in tags.values():
                    if frame.FrameID == 'POPM' and frame.email == rating_user_email:
                        count = getattr(frame, 'count', 0)
                        break
                else:
                    count = 0

                # Convert rating to range between 0 and 255
                rating = int(round(float(values[0]) * 255 / (config.setting['rating_steps'] - 1)))
                tags.add(id3.POPM(email=rating_user_email, rating=rating, count=count))
            elif name == 'grouping':
                if config.setting['itunes_compatible_grouping']:
                    tags.add(id3.GRP1(encoding=encoding, text=values))
                else:
                    tags.add(id3.TIT1(encoding=encoding, text=values))
            elif name == 'work' and config.setting['itunes_compatible_grouping']:
                tags.add(id3.TIT1(encoding=encoding, text=values))
                tags.delall('TXXX:Work')
                tags.delall('TXXX:WORK')
            elif name in self.__rtranslate:
                frameid = self.__rtranslate[name]
                if frameid.startswith('W'):
                    valid_urls = all([all(urlparse(v)[:2]) for v in values])
                    if frameid == 'WCOP':
                        # Only add WCOP if there is only one license URL, otherwise use TXXX:LICENSE
                        if len(values) > 1 or not valid_urls:
                            tags.delall('WCOP')
                            tags.add(self.build_TXXX(encoding, self.__rtranslate_freetext[name], values))
                        else:
                            tags.delall('TXXX:' + self.__rtranslate_freetext[name])
                            tags.add(id3.WCOP(url=values[0]))
                    elif frameid == 'WOAR' and valid_urls:
                        tags.delall('WOAR')
                        for url in values:
                            tags.add(id3.WOAR(url=url))
                elif frameid.startswith('T') or frameid == 'MVNM':
                    if config.setting['write_id3v23']:
                        if frameid == 'TMOO':
                            tags.add(self.build_TXXX(encoding, 'mood', values))
                    # No need to care about the TMOO tag being added again as it is
                    # automatically deleted by Mutagen if id2v23 is selected
                    tags.add(getattr(id3, frameid)(encoding=encoding, text=values))
                    if frameid == 'TSOA':
                        tags.delall('XSOA')
                    elif frameid == 'TSOP':
                        tags.delall('XSOP')
                    elif frameid == 'TSO2':
                        tags.delall('TXXX:ALBUMARTISTSORT')
            elif name_lower in self.__rtranslate_freetext_ci:
                if name_lower in self.__casemap:
                    description = self.__casemap[name_lower]
                else:
                    description = self.__rtranslate_freetext_ci[name_lower]
                delall_ci(tags, 'TXXX:' + description)
                tags.add(self.build_TXXX(encoding, description, values))
            elif name in self.__rtranslate_freetext:
                description = self.__rtranslate_freetext[name]
                if description in self.__rrename_freetext:
                    tags.delall('TXXX:' + self.__rrename_freetext[description])
                tags.add(self.build_TXXX(encoding, description, values))
            elif name.startswith('~id3:'):
                name = name[5:]
                if name.startswith('TXXX:'):
                    tags.add(self.build_TXXX(encoding, name[5:], values))
                else:
                    frameclass = getattr(id3, name[:4], None)
                    if frameclass:
                        tags.add(frameclass(encoding=encoding, text=values))
            # don't save private / already stored tags
            elif not name.startswith("~") and name not in self.__other_supported_tags:
                tags.add(self.build_TXXX(encoding, name, values))

        if tmcl.people:
            tags.add(tmcl)
        if tipl.people:
            tags.add(tipl)

        self._remove_deleted_tags(metadata, tags)

        self._save_tags(tags, encode_filename(filename))

        if self._IsMP3 and config.setting["remove_ape_from_mp3"]:
            try:
                mutagen.apev2.delete(encode_filename(filename))
            except BaseException:
                pass

    def _remove_deleted_tags(self, metadata, tags):
        """Remove the tags from the file that were deleted in the UI"""
        config = get_config()

        for name in metadata.deleted_tags:
            real_name = self._get_tag_name(name)
            try:
                if name.startswith('performer:'):
                    role = name.split(':', 1)[1]
                    _remove_people_with_role(tags, ['TMCL', 'TIPL', 'IPLS'], role)
                elif name.startswith('comment:') or name == 'comment':
                    (lang, desc) = parse_comment_tag(name)
                    for key, frame in list(tags.items()):
                        if (frame.FrameID == 'COMM' and frame.desc == desc
                            and frame.lang == lang):
                            del tags[key]
                elif name.startswith('lyrics:') or name == 'lyrics':
                    if ':' in name:
                        desc = name.split(':', 1)[1]
                    else:
                        desc = ''
                    for key, frame in list(tags.items()):
                        if frame.FrameID == 'USLT' and frame.desc == desc:
                            del tags[key]
                elif name in self._rtipl_roles:
                    role = self._rtipl_roles[name]
                    _remove_people_with_role(tags, ['TIPL', 'IPLS'], role)
                elif name == 'musicbrainz_recordingid':
                    for key, frame in list(tags.items()):
                        if frame.FrameID == 'UFID' and frame.owner == 'http://musicbrainz.org':
                            del tags[key]
                elif name == 'license':
                    tags.delall(real_name)
                    tags.delall('TXXX:' + self.__rtranslate_freetext[name])
                elif real_name == 'POPM':
                    rating_user_email = id3text(config.setting['rating_user_email'], Id3Encoding.LATIN1)
                    for key, frame in list(tags.items()):
                        if frame.FrameID == 'POPM' and frame.email == rating_user_email:
                            del tags[key]
                elif real_name in self.__translate:
                    tags.delall(real_name)
                elif name.lower() in self.__rtranslate_freetext_ci:
                    delall_ci(tags, 'TXXX:' + self.__rtranslate_freetext_ci[name.lower()])
                elif real_name in self.__translate_freetext:
                    tags.delall('TXXX:' + real_name)
                    if real_name in self.__rrename_freetext:
                        tags.delall('TXXX:' + self.__rrename_freetext[real_name])
                elif not name.startswith("~id3:") and name not in self.__other_supported_tags:
                    tags.delall('TXXX:' + name)
                elif name.startswith("~id3:"):
                    frameid = name[5:]
                    tags.delall(frameid)
                elif name in self.__other_supported_tags:
                    del tags[real_name]
            except KeyError:
                pass

    @classmethod
    def supports_tag(cls, name):
        return ((name and not name.startswith("~") and name not in UNSUPPORTED_TAGS)
                or name == "~rating"
                or name.startswith("~id3"))

    def _get_tag_name(self, name):
        if name in self.__rtranslate:
            return self.__rtranslate[name]
        elif name in self.__rtranslate_freetext:
            return self.__rtranslate_freetext[name]
        elif name == '~rating':
            return 'POPM'
        elif name == 'tracknumber':
            return 'TRCK'
        elif name == 'discnumber':
            return 'TPOS'
        elif name == 'movementnumber':
            return 'MVIN'
        else:
            return None

    def _get_file(self, filename):
        raise NotImplementedError()

    def _get_tags(self, filename):
        try:
            return compatid3.CompatID3(encode_filename(filename))
        except mutagen.id3.ID3NoHeaderError:
            return compatid3.CompatID3()

    def _save_tags(self, tags, filename):
        config = get_config()
        if config.setting['write_id3v1']:
            v1 = 2
        else:
            v1 = 0

        if config.setting['write_id3v23']:
            tags.update_to_v23()
            separator = config.setting['id3v23_join_with']
            tags.save(filename, v2_version=3, v1=v1, v23_sep=separator)
        else:
            tags.update_to_v24()
            tags.save(filename, v2_version=4, v1=v1)

    def format_specific_metadata(self, metadata, tag, settings=None):
        if not settings:
            settings = get_config().setting

        if not settings["write_id3v23"]:
            return super().format_specific_metadata(metadata, tag, settings)

        values = metadata.getall(tag)
        if not values:
            return values

        if tag == "originaldate":
            values = [v[:4] for v in values]
        elif tag == "date":
            values = [(v[:4] if len(v) < 10 else v) for v in values]

        # If this is a multi-valued field, then it needs to be flattened,
        # unless it's TIPL or TMCL which can still be multi-valued.
        if (len(values) > 1 and tag not in ID3File._rtipl_roles
                and not tag.startswith("performer:")):
            join_with = settings["id3v23_join_with"]
            values = [join_with.join(values)]

        return values


class MP3File(ID3File):

    """MP3 file."""
    EXTENSIONS = [".mp3", ".mp2", ".m2a"]
    NAME = "MPEG-1 Audio"
    _IsMP3 = True
    _File = mutagen.mp3.MP3

    def _get_file(self, filename):
        return self._File(filename, ID3=compatid3.CompatID3)

    def _info(self, metadata, file):
        super()._info(metadata, file)
        id3version = ''
        if file.tags is not None and file.info.layer == 3:
            id3version = ' - ID3v%d.%d' % (file.tags.version[0], file.tags.version[1])
        metadata['~format'] = 'MPEG-1 Layer %d%s' % (file.info.layer, id3version)


class TrueAudioFile(ID3File):

    """TTA file."""
    EXTENSIONS = [".tta"]
    NAME = "The True Audio"
    _File = mutagen.trueaudio.TrueAudio

    def _get_file(self, filename):
        return self._File(filename, ID3=compatid3.CompatID3)


class NonCompatID3File(ID3File):
    """Base class for ID3 files which do not support setting `compatid3.CompatID3`."""

    def _get_file(self, filename):
        return self._File(filename, known_frames=compatid3.known_frames)

    def _get_tags(self, filename):
        file = self._get_file(filename)
        if file.tags is None:
            file.add_tags()
        return file.tags

    def _save_tags(self, tags, filename):
        config = get_config()
        if config.setting['write_id3v23']:
            compatid3.update_to_v23(tags)
            separator = config.setting['id3v23_join_with']
            tags.save(filename, v2_version=3, v23_sep=separator)
        else:
            tags.update_to_v24()
            tags.save(filename, v2_version=4)


class DSFFile(NonCompatID3File):

    """DSF file."""
    EXTENSIONS = [".dsf"]
    NAME = "DSF"
    _File = mutagen.dsf.DSF


class AiffFile(NonCompatID3File):

    """AIFF file."""
    EXTENSIONS = [".aiff", ".aif", ".aifc"]
    NAME = "Audio Interchange File Format (AIFF)"
    _File = mutagen.aiff.AIFF


try:
    import mutagen.dsdiff

    class DSDIFFFile(NonCompatID3File):

        """DSF file."""
        EXTENSIONS = [".dff"]
        NAME = "DSDIFF"
        _File = mutagen.dsdiff.DSDIFF

except ImportError:
    DSDIFFFile = None
