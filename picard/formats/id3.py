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

import mutagen.apev2
import mutagen.mp3
import mutagen.trueaudio
try:
    import mutagen.aiff
except ImportError:
    mutagen.aiff = None

import re
from collections import defaultdict
from mutagen import id3
from picard import config, log
from picard.coverart.image import TagCoverArtImage, CoverArtImageError
from picard.metadata import Metadata
from picard.file import File
from picard.formats.mutagenext import compatid3
from picard.util import encode_filename, sanitize_date
from urlparse import urlparse


# Ugly, but... I need to save the text in ISO-8859-1 even if it contains
# unsupported characters and this better than encoding, decoding and
# again encoding.
def patched_EncodedTextSpec_write(self, frame, value):
    try:
        enc, term = self._encodings[frame.encoding]
    except AttributeError:
        enc, term = self.encodings[frame.encoding]
    return value.encode(enc, 'ignore') + term

id3.EncodedTextSpec.write = patched_EncodedTextSpec_write


# One more "monkey patch". The ID3 spec says that multiple text
# values should be _separated_ by the string terminator, which
# means that e.g. 'a\x00' are two values, 'a' and ''.
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


id3.TCMP = compatid3.TCMP
id3.TSO2 = compatid3.TSO2
id3.TSOC = compatid3.TSOC

__ID3_IMAGE_TYPE_MAP = {
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

__ID3_REVERSE_IMAGE_TYPE_MAP = dict([(v, k) for k, v in __ID3_IMAGE_TYPE_MAP.iteritems()])


def image_type_from_id3_num(id3type):
    return __ID3_REVERSE_IMAGE_TYPE_MAP.get(id3type, "other")


def image_type_as_id3_num(texttype):
    return __ID3_IMAGE_TYPE_MAP.get(texttype, 0)


def types_from_id3(id3type):
    return [unicode(image_type_from_id3_num(id3type))]


class ID3File(File):

    """Generic ID3-based file."""
    _IsMP3 = False

    __upgrade = {
        'XSOP': 'TSOP',
        'TXXX:ALBUMARTISTSORT': 'TSO2',
        'TXXX:COMPOSERSORT': 'TSOC',
    }

    __translate = {
        # In same sequence as defined at http://id3.org/id3v2.4.0-frames
        'TIT1': 'grouping',
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

        # The following are informal iTunes extensions to id3v2:
        'TCMP': 'compilation',
        'TSOC': 'composersort',
        'TSO2': 'albumartistsort',
    }
    __rtranslate = dict([(v, k) for k, v in __translate.iteritems()])

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
        'Artists': 'artists',
        'Work': 'work',
        'Writer': 'writer',
    }
    __rtranslate_freetext = dict([(v, k) for k, v in __translate_freetext.iteritems()])
    __translate_freetext['writer'] = 'writer'  # For backward compatibility of case

    _tipl_roles = {
        'engineer': 'engineer',
        'arranger': 'arranger',
        'producer': 'producer',
        'DJ-mix': 'djmixer',
        'mix': 'mixer',
    }
    _rtipl_roles = dict([(v, k) for k, v in _tipl_roles.iteritems()])

    __other_supported_tags = ("discnumber", "tracknumber",
                              "totaldiscs", "totaltracks")
    __tag_re_parse = {
        'TRCK': re.compile(r'^(?P<tracknumber>\d+)(?:/(?P<totaltracks>\d+))?$'),
        'TPOS': re.compile(r'^(?P<discnumber>\d+)(?:/(?P<totaldiscs>\d+))?$')
    }

    def _load(self, filename):
        log.debug("Loading file %r", filename)
        file = self._get_file(encode_filename(filename))
        tags = file.tags or {}
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
                if frameid.startswith('T'):
                    for text in frame.text:
                        if text:
                            metadata.add(name, unicode(text))
                elif frameid == 'COMM':
                    for text in frame.text:
                        if text:
                            metadata.add('%s:%s' % (name, frame.desc), unicode(text))
                else:
                    metadata.add(name, unicode(frame))
            elif frameid == "TMCL":
                for role, name in frame.people:
                    if role or name:
                        metadata.add('performer:%s' % role, name)
            elif frameid == "TIPL":
                # If file is ID3v2.3, TIPL tag could contain TMCL
                # so we will test for TMCL values and add to TIPL if not TMCL
                for role, name in frame.people:
                    if role in self._tipl_roles and name:
                        metadata.add(self._tipl_roles[role], name)
                    else:
                        metadata.add('performer:%s' % role, name)
            elif frameid == 'TXXX':
                name = frame.desc
                if name in self.__translate_freetext:
                    name = self.__translate_freetext[name]
                elif ((name in self.__rtranslate) !=
                        (name in self.__rtranslate_freetext)):
                    # If the desc of a TXXX frame conflicts with the name of a
                    # Picard tag, load it into ~id3:TXXX:desc rather than desc.
                    #
                    # This basically performs an XOR, making sure that 'name'
                    # is in __rtranslate or __rtranslate_freetext, but not
                    # both. (Being in both implies we support reading it both
                    # ways.) Currently, the only tag in both is license.
                    name = '~id3:TXXX:' + name
                for text in frame.text:
                    metadata.add(name, unicode(text))
            elif frameid == 'USLT':
                name = 'lyrics'
                if frame.desc:
                    name += ':%s' % frame.desc
                metadata.add(name, unicode(frame.text))
            elif frameid == 'UFID' and frame.owner == 'http://musicbrainz.org':
                metadata['musicbrainz_recordingid'] = frame.data.decode('ascii', 'ignore')
            elif frameid in self.__tag_re_parse.keys():
                m = self.__tag_re_parse[frameid].search(frame.text[0])
                if m:
                    for name, value in m.groupdict().iteritems():
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
                    )
                except CoverArtImageError as e:
                    log.error('Cannot load image from %r: %s' % (filename, e))
                else:
                    metadata.append_image(coverartimage)
            elif frameid == 'POPM':
                # Rating in ID3 ranges from 0 to 255, normalize this to the range 0 to 5
                if frame.email == config.setting['rating_user_email']:
                    rating = unicode(int(round(frame.rating / 255.0 * (config.setting['rating_steps'] - 1))))
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

        if config.setting['clear_existing_tags']:
            tags.clear()
        if metadata.images_to_be_saved_to_tags:
            tags.delall('APIC')

        encoding = {'utf-8': 3, 'utf-16': 1}.get(config.setting['id3v2_encoding'], 0)

        if 'tracknumber' in metadata:
            if 'totaltracks' in metadata:
                text = '%s/%s' % (metadata['tracknumber'], metadata['totaltracks'])
            else:
                text = metadata['tracknumber']
            tags.add(id3.TRCK(encoding=0, text=text))

        if 'discnumber' in metadata:
            if 'totaldiscs' in metadata:
                text = '%s/%s' % (metadata['discnumber'], metadata['totaldiscs'])
            else:
                text = metadata['discnumber']
            tags.add(id3.TPOS(encoding=0, text=text))

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
            tags.add(id3.APIC(encoding=0,
                              mime=image.mimetype,
                              type=image_type_as_id3_num(image.maintype),
                              desc=desctag,
                              data=image.data))

        tmcl = mutagen.id3.TMCL(encoding=encoding, people=[])
        tipl = mutagen.id3.TIPL(encoding=encoding, people=[])

        tags.delall('TCMP')
        for name, values in metadata.rawitems():
            if name.startswith('performer:'):
                role = name.split(':', 1)[1]
                for value in values:
                    tmcl.people.append([role, value])
            elif name.startswith('comment:'):
                desc = name.split(':', 1)[1]
                if desc.lower()[:4] == "itun":
                    tags.delall('COMM:' + desc)
                    tags.add(id3.COMM(encoding=0, desc=desc, lang='eng', text=[v + u'\x00' for v in values]))
                else:
                    tags.add(id3.COMM(encoding=encoding, desc=desc, lang='eng', text=values))
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
                tags.add(id3.UFID(owner='http://musicbrainz.org', data=str(values[0])))
            elif name == '~rating':
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
            elif name in self.__rtranslate:
                frameid = self.__rtranslate[name]
                if frameid.startswith('W'):
                    valid_urls = all([all(urlparse(v)[:2]) for v in values])
                    if frameid == 'WCOP':
                        # Only add WCOP if there is only one license URL, otherwise use TXXX:LICENSE
                        if len(values) > 1 or not valid_urls:
                            tags.add(id3.TXXX(encoding=encoding, desc=self.__rtranslate_freetext[name], text=values))
                        else:
                            tags.add(id3.WCOP(url=values[0]))
                    elif frameid == 'WOAR' and valid_urls:
                        for url in values:
                            tags.add(id3.WOAR(url=url))
                elif frameid.startswith('T'):
                    tags.add(getattr(id3, frameid)(encoding=encoding, text=values))
                    if frameid == 'TSOA':
                        tags.delall('XSOA')
                    elif frameid == 'TSOP':
                        tags.delall('XSOP')
                    elif frameid == 'TSO2':
                        tags.delall('TXXX:ALBUMARTISTSORT')
            elif name in self.__rtranslate_freetext:
                tags.add(id3.TXXX(encoding=encoding, desc=self.__rtranslate_freetext[name], text=values))
            elif name.startswith('~id3:'):
                name = name[5:]
                if name.startswith('TXXX:'):
                    tags.add(id3.TXXX(encoding=encoding, desc=name[5:], text=values))
                else:
                    frameclass = getattr(id3, name[:4], None)
                    if frameclass:
                        tags.add(frameclass(encoding=encoding, text=values))
            # don't save private / already stored tags
            elif not name.startswith("~") and not name in self.__other_supported_tags:
                tags.add(id3.TXXX(encoding=encoding, desc=name, text=values))

        if tmcl.people:
            tags.add(tmcl)
        if tipl.people:
            tags.add(tipl)

        self._save_tags(tags, encode_filename(filename))

        if self._IsMP3 and config.setting["remove_ape_from_mp3"]:
            try:
                mutagen.apev2.delete(encode_filename(filename))
            except:
                pass

    def _get_file(self, filename):
        raise NotImplementedError()

    def _get_tags(self, filename):
        try:
            return compatid3.CompatID3(encode_filename(filename))
        except mutagen.id3.ID3NoHeaderError:
            return compatid3.CompatID3()

    def _save_tags(self, tags, filename):
        if config.setting['write_id3v1']:
            v1 = 2
        else:
            v1 = 0

        if config.setting['write_id3v23']:
            tags.update_to_v23(join_with=config.setting['id3v23_join_with'])
            tags.save(filename, v2_version=3, v1=v1)
        else:
            tags.update_to_v24()
            tags.save(filename, v2_version=4, v1=v1)

    def supports_tag(self, name):
        return name in self.__rtranslate or name in self.__rtranslate_freetext\
            or name.startswith('performer:')\
            or name.startswith('lyrics:') or name == 'lyrics'\
            or name in self.__other_supported_tags

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
                values = [(v[:4] if len(v) < 10 else v) for v in values]

            # If this is a multi-valued field, then it needs to be flattened,
            # unless it's TIPL or TMCL which can still be multi-valued.

            if (len(values) > 1 and not name in ID3File._rtipl_roles
                    and not name.startswith("performer:")):
                values = [join_with.join(values)]

            copy[name] = values

        return copy


class MP3File(ID3File):

    """MP3 file."""
    EXTENSIONS = [".mp3", ".mp2", ".m2a"]
    NAME = "MPEG-1 Audio"
    _IsMP3 = True

    def _get_file(self, filename):
        return mutagen.mp3.MP3(filename, ID3=compatid3.CompatID3)

    def _info(self, metadata, file):
        super(MP3File, self)._info(metadata, file)
        id3version = ''
        if file.tags is not None and file.info.layer == 3:
            id3version = ' - ID3v%d.%d' % (file.tags.version[0], file.tags.version[1])
        metadata['~format'] = 'MPEG-1 Layer %d%s' % (file.info.layer, id3version)


class TrueAudioFile(ID3File):

    """TTA file."""
    EXTENSIONS = [".tta"]
    NAME = "The True Audio"

    def _get_file(self, filename):
        return mutagen.trueaudio.TrueAudio(filename, ID3=compatid3.CompatID3)

    def _info(self, metadata, file):
        super(TrueAudioFile, self)._info(metadata, file)
        metadata['~format'] = self.NAME


if mutagen.aiff:
    class AiffFile(ID3File):

        """AIFF file."""
        EXTENSIONS = [".aiff", ".aif", ".aifc"]
        NAME = "Audio Interchange File Format (AIFF)"

        def _get_file(self, filename):
            return mutagen.aiff.AIFF(filename)

        def _get_tags(self, filename):
            file = self._get_file(filename)
            if file.tags is None:
                file.add_tags()
            return file.tags

        def _save_tags(self, tags, filename):
            if config.setting['write_id3v23']:
                tags.update_to_v23()
                separator = config.setting['id3v23_join_with']
                tags.save(filename, v2_version=3, v23_sep=separator)
            else:
                tags.update_to_v24()
                tags.save(filename, v2_version=4)

        def _info(self, metadata, file):
            super(AiffFile, self)._info(metadata, file)
            metadata['~format'] = self.NAME
else:
    AiffFile = None
