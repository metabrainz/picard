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
from picard.file import File
from picard.formats.id3 import ID3_IMAGE_TYPE_MAP, ID3_REVERSE_IMAGE_TYPE_MAP
from picard.util import encode_filename
from picard.metadata import Metadata
from mutagen.asf import ASF, ASFByteArrayAttribute
import struct

def unpack_image(data):
    """
    Helper function to unpack image data from a WM/Picture tag.

    The data has the following format:
    1 byte: Picture type (0-20), see ID3 APIC frame specification at http://www.id3.org/id3v2.4.0-frames
    4 bytes: Picture data length in LE format
    MIME type, null terminated UTF-16-LE string
    Description, null terminated UTF-16-LE string
    The image data in the given length
    """
    (type, size) = struct.unpack_from("<bi", data)
    pos = 5
    mime = ""
    while data[pos:pos+2] != "\x00\x00":
        mime += data[pos:pos+2]
        pos += 2
    pos += 2
    description = ""
    while data[pos:pos+2] != "\x00\x00":
        description += data[pos:pos+2]
        pos += 2
    pos += 2
    image_data = data[pos:pos+size]
    return (mime.decode("utf-16-le"), image_data, type, description.decode("utf-16-le"))

def pack_image(mime, data, type=3, description=""):
    """
    Helper function to pack image data for a WM/Picture tag.
    See unpack_image for a description of the data format.
    """
    tag_data = struct.pack("<bi", type, len(data))
    tag_data += mime.encode("utf-16-le") + "\x00\x00"
    tag_data += description.encode("utf-16-le") + "\x00\x00"
    tag_data += data
    return tag_data

class ASFFile(File):
    """ASF (WMA) metadata reader/writer"""
    EXTENSIONS = [".wma"]
    NAME = "Windows Media Audio"

    __TRANS = {
        'album': 'WM/AlbumTitle',
        'title': 'Title',
        'artist': 'Author',
        'albumartist': 'WM/AlbumArtist',
        'date': 'WM/Year',
        'originaldate': 'WM/OriginalReleaseYear',
        'composer': 'WM/Composer',
        'lyricist': 'WM/Writer',
        'conductor': 'WM/Conductor',
        'remixer': 'WM/ModifiedBy',
        'producer': 'WM/Producer',
        'grouping': 'WM/ContentGroupDescription',
        'subtitle': 'WM/SubTitle',
        'discsubtitle': 'WM/SetSubTitle',
        'tracknumber': 'WM/TrackNumber',
        'discnumber': 'WM/PartOfSet',
        'comment:': 'Description',
        'genre': 'WM/Genre',
        'bpm': 'WM/BeatsPerMinute',
        'script': 'WM/Script',
        'language': 'WM/Language',
        'mood': 'WM/Mood',
        'isrc': 'WM/ISRC',
        'copyright': 'Copyright',
        'lyrics': 'WM/Lyrics',
        '~rating': 'WM/SharedUserRating',
        'media': 'WM/Media',
        'barcode': 'WM/Barcode',
        'catalognumber': 'WM/CatalogNo',
        'label': 'WM/Publisher',
        'encodedby': 'WM/EncodedBy',
        'albumsort': 'WM/AlbumSortOrder',
        'albumartistsort': 'WM/AlbumArtistSortOrder',
        'artistsort': 'WM/ArtistSortOrder',
        'titlesort': 'WM/TitleSortOrder',
        'musicbrainz_trackid': 'MusicBrainz/Track Id',
        'musicbrainz_albumid': 'MusicBrainz/Album Id',
        'musicbrainz_artistid': 'MusicBrainz/Artist Id',
        'musicbrainz_albumartistid': 'MusicBrainz/Album Artist Id',
        'musicbrainz_trmid': 'MusicBrainz/TRM Id',
        'musicbrainz_discid': 'MusicBrainz/Disc Id',
        'musicbrainz_workid': 'MusicBrainz/Work Id',
        'musicbrainz_releasegroupid': 'MusicBrainz/Release Group Id',
        'musicip_puid': 'MusicIP/PUID',
        'releasestatus': 'MusicBrainz/Album Status',
        'releasetype': 'MusicBrainz/Album Type',
        'releasecountry': 'MusicBrainz/Album Release Country',
        'acoustid_id': 'Acoustid/Id',
        'acoustid_fingerprint': 'Acoustid/Fingerprint',
        'compilation': 'WM/IsCompilation',
        'engineer': 'WM/Engineer',
        'asin': 'ASIN',
        'djmixer': 'WM/DJMixer',
        'mixer': 'WM/Mixer',
    }
    __RTRANS = dict([(b, a) for a, b in __TRANS.items()])

    def _load(self, filename):
        log.debug("Loading file %r", filename)
        file = ASF(encode_filename(filename))
        metadata = Metadata()
        for name, values in file.tags.items():
            if name == 'WM/Picture':
                for image in values:
                    (mime, data, type, description) = unpack_image(image.value)
                    imagetype = ID3_REVERSE_IMAGE_TYPE_MAP.get(type, "other")
                    metadata.add_image(mime, data, description=description,
                                       type_=imagetype)
                continue
            elif name not in self.__RTRANS:
                continue
            elif name == 'WM/SharedUserRating':
                # Rating in WMA ranges from 0 to 99, normalize this to the range 0 to 5
                values[0] = int(round(int(unicode(values[0])) / 99.0 * (config.setting['rating_steps'] - 1)))
            name = self.__RTRANS[name]
            values = filter(bool, map(unicode, values))
            if values:
                metadata[name] = values
        self._info(metadata, file)
        return metadata

    def _save(self, filename, metadata):
        log.debug("Saving file %r", filename)
        file = ASF(encode_filename(filename))

        if config.setting['clear_existing_tags']:
            file.tags.clear()
        if config.setting['save_images_to_tags']:
            cover = []
            for image in metadata.images:
                if config.setting["save_only_front_images_to_tags"] and image["type"] != "front":
                    continue
                imagetype = ID3_IMAGE_TYPE_MAP.get(image["type"], 0)
                tag_data = pack_image(image["mime"], image["data"], imagetype,
                                      image["description"])
                cover.append(ASFByteArrayAttribute(tag_data))
            if cover:
                file.tags['WM/Picture'] = cover

        for name, values in metadata.rawitems():
            if name.startswith('lyrics:'):
                name = 'lyrics'
            elif name == '~rating':
                values[0] = int(values[0]) * 99 / (config.setting['rating_steps'] - 1)
            if name not in self.__TRANS:
                continue
            name = self.__TRANS[name]
            file.tags[name] = map(unicode, values)
        file.save()

    def supports_tag(self, name):
        return name in self.__TRANS
