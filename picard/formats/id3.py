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
from mutagen import id3
from picard.metadata import Metadata
from picard.file import File
from picard.formats.mutagenext import compatid3
from picard.util import encode_filename, sanitize_date


# Ugly, but... I need to save the text in ISO-8859-1 even if it contains
# unsupported characters and this better than encoding, decoding and
# again encoding.
def patched_EncodedTextSpec_write(self, frame, value):
    if hasattr(self, 'encodings'):
        enc, term = self.encodings[frame.encoding]
    else:
        enc, term = self._encodings[frame.encoding]
    return value.encode(enc, 'ignore') + term
id3.EncodedTextSpec.write = patched_EncodedTextSpec_write


class ID3File(File):
    """Generic ID3-based file."""
    _File = None
    _IsMP3 = False

    __translate = {
        'TPE1': 'artist',
        'TPE2': 'albumartist',
        'TPE3': 'conductor',
        'TPE4': 'remixer',
        'TCOM': 'composer',
        'TCON': 'genre',
        'TALB': 'album',
        'TIT1': 'grouping',
        'TIT2': 'title',
        'TIT3': 'subtitle',
        'TSST': 'discsubtitle',
        'TEXT': 'lyricist',
        'TCMP': 'compilation',
        'TDRC': 'date',
        'XDOR': 'date',
        'COMM': 'comment',
        'TMOO': 'mood',
        'TMED': 'media',
        'TBPM': 'bpm',
        'WOAR': 'website',
        'TSRC': 'isrc',
        'TENC': 'encodedby',
        'TCOP': 'copyright',
        'TSOA': 'albumsort',
        'TSOP': 'artistsort',
        'TSOT': 'titlesort',
        'TPUB': 'label',
    }
    __rtranslate = dict([(v, k) for k, v in __translate.iteritems()])

    __translate_freetext = {
        'MusicBrainz Artist Id': 'musicbrainz_artistid',
        'MusicBrainz Album Id': 'musicbrainz_albumid',
        'MusicBrainz Album Artist Id': 'musicbrainz_albumartistid',
        'MusicBrainz Album Type': 'releasetype',
        'MusicBrainz Album Status': 'releasestatus',
        'MusicBrainz TRM Id': 'musicbrainz_trmid',
        'MusicBrainz Disc Id': 'musicbrainz_discid',
        'MusicIP PUID': 'musicip_puid',
        'ALBUMARTISTSORT': 'albumartistsort',
        'CATALOGNUMBER': 'catalognumber',
        'BARCODE': 'barcode',
    }
    __rtranslate_freetext = dict([(v, k) for k, v in __translate_freetext.iteritems()])

    __tipl_roles = ['engineer', 'producer']

    def _load(self):
        file = self._File(encode_filename(self.filename), ID3=compatid3.CompatID3)
        tags = file.tags or {}
        metadata = Metadata()
        for frame in tags.values():
            frameid = frame.FrameID
            if frameid in self.__translate:
                name = self.__translate[frameid]
                if frameid.startswith('T'):
                    for text in frame.text:
                        metadata.add(name, unicode(text))
                elif frameid == 'COMM':
                    for text in frame.text:
                        metadata.add('%s:%s' % (name, frame.desc), unicode(text))
                else:
                    metadata.add(name, unicode(frame))
            elif frameid == "TMCL":
                for role, name in frame.people:
                    metadata.add('performer:%s' % role, name)
            elif frameid == "TIPL":
                for role, name in frame.people:
                    if role in self.__tipl_roles:
                        metadata.add(role, name)
            elif frameid == 'TXXX' and frame.desc in self.__translate_freetext:
                name = self.__translate_freetext[frame.desc]
                for text in frame.text:
                    metadata.add(name, unicode(text))
            elif frameid == 'UFID' and frame.owner == 'http://musicbrainz.org':
                metadata['musicbrainz_trackid'] = unicode(frame.data)
            elif frameid == 'TRCK':
                value = frame.text[0].split('/')
                if len(value) > 1:
                    metadata['tracknumber'], metadata['totaltracks'] = value[:2]
                else:
                    metadata['tracknumber'] = value[0]
            elif frameid == 'TPOS':
                value = frame.text[0].split('/')
                if len(value) > 1:
                    metadata['discnumber'], metadata['totaldiscs'] = value[:2]
                else:
                    metadata['discnumber'] = value[0]
            elif frameid == 'APIC':
                metadata.add('~artwork', (frame.mime, frame.data))

        if 'date' in metadata:
            metadata['date'] = sanitize_date(metadata.getall('date')[0])

        self.metadata.update(metadata)
        self._info(file)

    def _save(self):
        """Save metadata to the file."""
        try:
            tags = compatid3.CompatID3(encode_filename(self.filename))
        except mutagen.id3.ID3NoHeaderError:
            tags = compatid3.CompatID3()
        metadata = self.metadata

        if self.config.setting['clear_existing_tags']:
            tags.clear()
        if self.config.setting['remove_images_from_tags']:
            tags.delall('APIC')

        if self.config.setting['write_id3v1']:
            v1 = 2
        else:
            v1 = 0
        encoding = {'utf-8': 3, 'utf-16': 1}.get(self.config.setting['id3v2_encoding'], 0)

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

        if self.config.setting['save_images_to_tags']:
            images = self.metadata.getall('~artwork')
            for mime, data in images:
                tags.add(id3.APIC(encoding=0, mime=mime, type=3, desc='', data=data))

        tmcl = mutagen.id3.TMCL(encoding=encoding, people=[])
        tipl = mutagen.id3.TIPL(encoding=encoding, people=[])

        id3.TCMP = compatid3.TCMP
        tags.delall('TCMP')
        for name, values in self.metadata.rawitems():
            if name.startswith('performer:'):
                role = name.split(':', 1)[1]
                for value in values:
                    tmcl.people.append([role, value])
            elif name in self.__tipl_roles:
                for value in values:
                    tipl.people.append([name, value])
            elif name == 'musicbrainz_trackid':
                tags.add(id3.UFID(owner='http://musicbrainz.org', data=str(values[0])))
            elif name in self.__rtranslate:
                frameid = self.__rtranslate[name]
                if frameid.startswith('W'):
                    tags.add(getattr(id3, frameid)(url=values[0]))
                elif frameid.startswith('T'):
                    tags.add(getattr(id3, frameid)(encoding=encoding, text=values))
            elif name in self.__rtranslate_freetext:
                tags.add(id3.TXXX(encoding=encoding, desc=self.__rtranslate_freetext[name], text=values))
            elif name.startswith('~id3:'):
                name = name[5:]
                if name.startswith('TXXX:'):
                    tags.add(id3.TXXX(encoding=encoding, desc=name[5:], text=values))

        if tmcl.people:
            tags.add(tmcl)
        if tipl.people:
            tags.add(tipl)

        if self.config.setting['write_id3v23']:
            tags.update_to_v23()
            tags.save(encode_filename(self.filename), v2=3, v1=v1)
        else:
            tags.update_to_v24()
            tags.save(encode_filename(self.filename), v2=4, v1=v1)

        if self._IsMP3 and self.config.setting["remove_ape_from_mp3"]:
            try: mutagen.apev2.delete(encode_filename(self.filename))
            except: pass


class MP3File(ID3File):
    """MP3 file."""
    EXTENSIONS = [".mp3", ".mp2"]
    NAME = "MPEG-1 Audio"
    _File = mutagen.mp3.MP3
    _IsMP3 = True
    def _info(self, file):
        super(MP3File, self)._info(file)
        self.metadata['~format'] = 'MPEG-1 Layer %d' % file.info.layer

class TrueAudioFile(ID3File):
    """TTA file."""
    EXTENSIONS = [".tta"]
    NAME = "The True Audio"
    _File = mutagen.trueaudio.TrueAudio
    def _info(self, file):
        super(TrueAudioFile, self)._info(file)
        self.metadata['~format'] = self.NAME
