# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2011 Lukáš Lalinský
# Copyright (C) 2009-2011, 2014, 2018-2021 Philipp Wolfer
# Copyright (C) 2011-2014 Wieland Hoffmann
# Copyright (C) 2012-2013 Michael Wiencek
# Copyright (C) 2013 Calvin Walton
# Copyright (C) 2013-2014, 2018-2020 Laurent Monin
# Copyright (C) 2014-2015, 2017 Sophist-UK
# Copyright (C) 2016-2018 Sambhav Kothari
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


import struct

from mutagen.asf import (
    ASF,
    ASFByteArrayAttribute,
)

from picard import log
from picard.config import get_config
from picard.coverart.image import (
    CoverArtImageError,
    TagCoverArtImage,
)
from picard.coverart.utils import (
    image_type_as_id3_num,
    types_from_id3,
)
from picard.file import File
from picard.formats.mutagenext import delall_ci
from picard.metadata import Metadata
from picard.util import encode_filename


def unpack_image(data):
    """
    Helper function to unpack image data from a WM/Picture tag.

    The data has the following format:
    1 byte: Picture type (0-20), see ID3 APIC frame specification at
            http://www.id3.org/id3v2.4.0-frames
    4 bytes: Picture data length in LE format
    MIME type, null terminated UTF-16-LE string
    Description, null terminated UTF-16-LE string
    The image data in the given length
    """
    try:
        (type_, size) = struct.unpack_from("<bi", data)
    except struct.error as e:
        raise ValueError(e)
    data = data[5:]

    mime = b""
    while data:
        char, data = data[:2], data[2:]
        if char == b"\x00\x00":
            break
        mime += char
    else:
        raise ValueError("mime: missing data")

    mime = mime.decode("utf-16-le")

    description = b""
    while data:
        char, data = data[:2], data[2:]
        if char == b"\x00\x00":
            break
        description += char
    else:
        raise ValueError("desc: missing data")

    description = description.decode("utf-16-le")

    if size != len(data):
        raise ValueError("image data size mismatch")

    return (mime, data, type_, description)


def pack_image(mime, data, image_type=3, description=""):
    """
    Helper function to pack image data for a WM/Picture tag.
    See unpack_image for a description of the data format.
    """
    tag_data = struct.pack("<bi", image_type, len(data))
    tag_data += mime.encode("utf-16-le") + b"\x00\x00"
    tag_data += description.encode("utf-16-le") + b"\x00\x00"
    tag_data += data
    return tag_data


class ASFFile(File):

    """
    ASF (WMA) metadata reader/writer
    See http://msdn.microsoft.com/en-us/library/ms867702.aspx for official
    WMA tag specifications.
    """
    EXTENSIONS = [".wma", ".wmv", ".asf"]
    NAME = "Windows Media Audio"
    _File = ASF

    __TRANS = {
        'album': 'WM/AlbumTitle',
        'title': 'Title',
        'artist': 'Author',
        'albumartist': 'WM/AlbumArtist',
        'date': 'WM/Year',
        'originalalbum': 'WM/OriginalAlbumTitle',
        'originalartist': 'WM/OriginalArtist',
        'originaldate': 'WM/OriginalReleaseTime',
        'originalyear': 'WM/OriginalReleaseYear',
        'originalfilename': 'WM/OriginalFilename',
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
        'comment': 'Description',
        'genre': 'WM/Genre',
        'bpm': 'WM/BeatsPerMinute',
        'key': 'WM/InitialKey',
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
        'encodersettings': 'WM/EncodingSettings',
        'albumsort': 'WM/AlbumSortOrder',
        'albumartistsort': 'WM/AlbumArtistSortOrder',
        'artistsort': 'WM/ArtistSortOrder',
        'titlesort': 'WM/TitleSortOrder',
        'composersort': 'WM/ComposerSortOrder',
        'musicbrainz_recordingid': 'MusicBrainz/Track Id',
        'musicbrainz_trackid': 'MusicBrainz/Release Track Id',
        'musicbrainz_albumid': 'MusicBrainz/Album Id',
        'musicbrainz_artistid': 'MusicBrainz/Artist Id',
        'musicbrainz_albumartistid': 'MusicBrainz/Album Artist Id',
        'musicbrainz_trmid': 'MusicBrainz/TRM Id',
        'musicbrainz_discid': 'MusicBrainz/Disc Id',
        'musicbrainz_workid': 'MusicBrainz/Work Id',
        'musicbrainz_releasegroupid': 'MusicBrainz/Release Group Id',
        'musicbrainz_originalalbumid': 'MusicBrainz/Original Album Id',
        'musicbrainz_originalartistid': 'MusicBrainz/Original Artist Id',
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
        'artists': 'WM/ARTISTS',
        'director': 'WM/Director',
        'work': 'WM/Work',
        'website': 'WM/AuthorURL',
    }
    __RTRANS = dict([(b, a) for a, b in __TRANS.items()])

    # Tags to load case insensitive
    __TRANS_CI = {
        'replaygain_album_gain': 'REPLAYGAIN_ALBUM_GAIN',
        'replaygain_album_peak': 'REPLAYGAIN_ALBUM_PEAK',
        'replaygain_album_range': 'REPLAYGAIN_ALBUM_RANGE',
        'replaygain_track_gain': 'REPLAYGAIN_TRACK_GAIN',
        'replaygain_track_peak': 'REPLAYGAIN_TRACK_PEAK',
        'replaygain_track_range': 'REPLAYGAIN_TRACK_RANGE',
        'replaygain_reference_loudness': 'REPLAYGAIN_REFERENCE_LOUDNESS',
    }
    __RTRANS_CI = dict([(b.lower(), a) for a, b in __TRANS_CI.items()])

    def __init__(self, filename):
        super().__init__(filename)
        self.__casemap = {}

    def _load(self, filename):
        log.debug("Loading file %r", filename)
        config = get_config()
        self.__casemap = {}
        file = ASF(encode_filename(filename))
        metadata = Metadata()
        for name, values in file.tags.items():
            if name == 'WM/Picture':
                for image in values:
                    try:
                        (mime, data, type_, description) = unpack_image(image.value)
                    except ValueError as e:
                        log.warning('Cannot unpack image from %r: %s',
                                    filename, e)
                        continue
                    try:
                        coverartimage = TagCoverArtImage(
                            file=filename,
                            tag=name,
                            types=types_from_id3(type_),
                            comment=description,
                            support_types=True,
                            data=data,
                        )
                    except CoverArtImageError as e:
                        log.error('Cannot load image from %r: %s' %
                                  (filename, e))
                    else:
                        metadata.images.append(coverartimage)

                continue
            elif name == 'WM/SharedUserRating':
                # Rating in WMA ranges from 0 to 99, normalize this to the range 0 to 5
                values[0] = int(round(int(str(values[0])) / 99.0 * (config.setting['rating_steps'] - 1)))
            elif name == 'WM/PartOfSet':
                disc = str(values[0]).split("/")
                if len(disc) > 1:
                    metadata["totaldiscs"] = disc[1]
                    values[0] = disc[0]
            name_lower = name.lower()
            if name in self.__RTRANS:
                name = self.__RTRANS[name]
            elif name_lower in self.__RTRANS_CI:
                orig_name = name
                name = self.__RTRANS_CI[name_lower]
                self.__casemap[name] = orig_name
            else:
                continue
            values = [str(value) for value in values if value]
            if values:
                metadata[name] = values
        self._info(metadata, file)
        return metadata

    def _save(self, filename, metadata):
        log.debug("Saving file %r", filename)
        config = get_config()
        file = ASF(encode_filename(filename))
        tags = file.tags

        if config.setting['clear_existing_tags']:
            cover = tags['WM/Picture'] if config.setting['preserve_images'] else None
            tags.clear()
            if cover:
                tags['WM/Picture'] = cover
        cover = []
        for image in metadata.images.to_be_saved_to_tags():
            tag_data = pack_image(image.mimetype, image.data,
                                  image_type_as_id3_num(image.maintype),
                                  image.comment)
            cover.append(ASFByteArrayAttribute(tag_data))
        if cover:
            tags['WM/Picture'] = cover
        for name, values in metadata.rawitems():
            if name.startswith('lyrics:'):
                name = 'lyrics'
            elif name == '~rating':
                values = [int(values[0]) * 99 // (config.setting['rating_steps'] - 1)]
            elif name == 'discnumber' and 'totaldiscs' in metadata:
                values = ['%s/%s' % (metadata['discnumber'], metadata['totaldiscs'])]
            if name in self.__TRANS:
                name = self.__TRANS[name]
            elif name in self.__TRANS_CI:
                if name in self.__casemap:
                    name = self.__casemap[name]
                else:
                    name = self.__TRANS_CI[name]
                delall_ci(tags, name)
            else:
                continue
            tags[name] = values

        self._remove_deleted_tags(metadata, tags)

        file.save()

    def _remove_deleted_tags(self, metadata, tags):
        """Remove the tags from the file that were deleted in the UI"""
        for tag in metadata.deleted_tags:
            real_name = self._get_tag_name(tag)
            if real_name and real_name in tags:
                del tags[real_name]

    @classmethod
    def supports_tag(cls, name):
        return (name in cls.__TRANS
                or name in cls.__TRANS_CI
                or name in ('~rating', '~length', 'totaldiscs')
                or name.startswith('lyrics:'))

    def _get_tag_name(self, name):
        if name.startswith('lyrics:'):
            name = 'lyrics'
        if name == 'totaldiscs':
            return self.__TRANS['discnumber']
        elif name in self.__TRANS:
            return self.__TRANS[name]
        else:
            return None

    def _info(self, metadata, file):
        super()._info(metadata, file)
        filename = file.filename
        if isinstance(filename, bytes):
            filename = filename.decode()
        if filename.lower().endswith(".wmv"):
            metadata['~video'] = '1'
