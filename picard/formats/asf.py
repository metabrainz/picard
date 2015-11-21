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
from picard.const import METADATA_PROVIDER, METADATA_COPYRIGHT, TIMESTAMP_FORMAT
from picard.coverart.image import TagCoverArtImage, CoverArtImageError
from picard.file import File
from picard.formats.id3 import types_from_id3, image_type_as_id3_num
from picard.metadata import Metadata
from picard.util import encode_filename, pack_performer, unpack_performer, sanitize_date, sanitize_int

from mutagen.asf import ASF, ASFByteArrayAttribute, ASFGUIDAttribute

import json
from os import path
import struct
from time import strftime, gmtime, gmtime


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


def unpack_lyrics_sync(data):
    """
    Helper function to unpack image data from a WM/Lyrics_Synchronised tag.

    The data has the following format: see https://msdn.microsoft.com/en-gb/library/windows/desktop/ms697057(v=vs.85).aspx
    1 byte: Timestamp format (1/2), see https://msdn.microsoft.com/en-gb/library/windows/desktop/dd758001(v=vs.85).aspx
    1 byte: Content type (0-1), see https://msdn.microsoft.com/en-gb/library/windows/desktop/dd758001(v=vs.85).aspx
    4 bytes: Lyrics data length in LE format
    Description, null terminated UTF-16-LE string
    The Lyrics in the given length. The Lyrics are a sequence of  null-terminated, wide-character strings each followed by a 32-bit time stamp in the timestamp format specified. These are converted to a list of tuples, each tupe consisting of the decoded string, followed by a timestamp.
    """
    timestamp_type, content_type, size = struct.unpack_from("<bbi", data)
    pos = 6
    description = ""
    while data[pos:pos+2] != "\x00\x00":
        description += data[pos:pos+2]
        pos += 2
    pos += 2
    lyrics = data[pos:pos+size]
    text = []
    pos = 0
    while pos < size:
        phrase = ""
        while lyrics[pos:pos+2] != "\x00\x00":
            phrase += lyrics[pos:pos+2]
            pos += 2
        pos += 2
        timestamp = struct.unpack_from("<i", lyrics[pos:pos+4])
        pos += 4
        text.append((phrase.decode("utf-16-le"), timestamp[0]))

    return (description.decode("utf-16-le"), text, timestamp_type, content_type)


def pack_lyrics_sync(text=('', 0), description="", timestamp_format=2, content_type=1):
    """
    Helper function to pack image data for a WM/Lyrics_Synchronised tag.
    See unpack_image for a description of the data format.
    """
    lyrics = ""
    for tuple in text:
        lyrics += unicode(tuple[0]).encode("utf-16-le") + "\x00\x00"
        lyrics += struct.pack("<i", tuple[1])
    tag_data = struct.pack("<bbi", timestamp_format, content_type, len(lyrics))
    tag_data += description.encode("utf-16-le") + "\x00\x00"
    tag_data += lyrics
    return tag_data


def unpack_wmtext(data):
    """
    Helper function to unpack image data from a WM/UserWebURL tag.

    The data has the following format:
    Description, null terminated UTF-16-LE string
    URL, null terminated UTF-16-LE string
    """
    pos = 0
    description = ""
    while data[pos:pos+2] != "\x00\x00":
        description += data[pos:pos+2]
        pos += 2
    pos += 2
    text = ""
    while data[pos:pos+2] != "\x00\x00":
        text += data[pos:pos+2]
        pos += 2
    return (description.decode("utf-16-le"), text.decode("utf-16-le"))


def pack_wmtext(text, description=""):
    """
    Helper function to pack image data for a WM/UserWebURL tag.
    See unpack_wmtext for a description of the data format.
    """
    tag_data = description.encode("utf-16-le") + "\x00\x00"
    tag_data += text.encode("utf-16-le") + "\x00\x00"
    return tag_data


class ASFFile(File):

    """
    ASF (WMA) metadata reader/writer
    See http://msdn.microsoft.com/en-us/library/ms867702.aspx for official
    WMA tag specifications.
    Picard metadata not explicitly mapped to ASF keys is saved in WM/Text.
    Unknown ASF keys are loaded and saved to Picard metadata as '~asf:*'
    """

    EXTENSIONS = [".wma", ".wmv", ".asf"]
    NAME = "Windows Media Audio"

    __load_tags = {
        # Official MS tags in sequence https://msdn.microsoft.com/en-us/library/ms867702.aspx#wm_metadata_usage_topic4
        'Author': 'artist',
        'Copyright': 'copyright',
        'Description': 'comment', # Multiplex comment* tags into this field
        # Rating - per MS recommendation use WM/SharedUserRating
        'Title': 'title',
        'WM/AlbumArtist': 'albumartist',
        'WM/AlbumCoverURL': 'web_coverart',
        'WM/AlbumTitle': 'album',
        'WM/AudioFileURL': 'web_official_release',
        # WM/AudioSourceURL - unsupported
        'WM/AuthorURL': 'web_official_artist',
        'WM/BeatsPerMinute': 'bpm',
        'WM/Category': 'category',
        'WM/Codec': '~codec',
        'WM/Composer': 'composer',
        'WM/Conductor': 'conductor',
        # WM/ContentDistributor - unsupported
        'WM/ContentGroupDescription': 'grouping',
        # WM/Director - unsupported
        # WM/DVDID - unsupported
        'WM/EncodedBy': 'encodedby',
        'WM/EncodingSettings': 'encodersettings', # ID3 TSSE
        'WM/EncodingTime': 'encodingtime',
        'WM/Genre': 'genre',
        # WM/GenreID - per MS recommendation use WM/Genre
        'WM/InitialKey': 'key',
        'WM/ISRC': 'isrc',
        'WM/Language': 'language',
        'WM/Lyrics': 'lyrics', # Only "lyrics" or first "lyrics:" will be included
        'WM/Lyrics_Synchronised': '~lyrics_sync', # Special encode/decode
        # WM/MCDI - unsupported
        # WM/MediaClassPrimaryID - support to be added from Release Type
        # WM/MediaClassSecondaryID - support to be added from Release Type
        # WM/MediaCredits - unsupported
        # WM/MediaIsDelay - unsupported
        # WM/MediaIsFinale - unsupported
        # WM/MediaIsLive - write only support to be added from Secondary Release Type
        # WM/MediaIsPremiere - unsupported
        # WM/MediaIsRepeat - unsupported
        # WM/MediaIsSAP - unsupported
        # WM/MediaIsSubtitled - unsupported
        'WM/MediaIsStereo': '~stereo',
        # WM/MediaNetworkAffiliation - unsupported
        # WM/MediaOriginalBroadcastDateTime - unsupported
        # WM/MediaOriginalChannel- unsupported
        # WM/MediaStationCallSign - unsupported
        # WM/MediaStationName - unsupported
        'WM/ModifiedBy': 'remixer',
        'WM/Mood': 'mood',
        'WM/OriginalAlbumTitle': 'originalalbum', # ID3 TOAL plugin support
        'WM/OriginalArtist': 'originalartist', # ID3 TOPE plugin support
        # WM/OriginalFilename - not supported
        'WM/OriginalLyricist': 'originallyricist', # ID3 TOLY plugin support
        'WM/OriginalReleaseTime': 'originaldate',
        'WM/OriginalReleaseYear': 'originalyear',
        # WM/ParentalRating - unsupported
        # WM/ParentalRatingReason - unsupported
        'WM/PartOfSet': 'discnumber',
        # WM/Period - unsupported
        # WM/Picture - see code below
        'WM/PlaylistDelay': 'playdelay',
        'WM/Producer': 'producer',
        # WM/PromotionURL - unsupported
        # WM/Provider - "MusicBrainz"
        # WM/ProviderCopyright - MusicBrainz copyright based on https://musicbrainz.org/doc/About/Data_License
        'WM/ProviderRating': 'albumrating',
        'WM/ProviderStyle': 'albumgenre',
        'WM/Publisher': 'label',
        # WM/RadioStationName - unsupported
        # WM/RadioStationOwner - unsupported
        'WM/SetSubTitle': 'discsubtitle',
        'WM/SharedUserRating': '~rating',
        'WM/SubTitle': 'subtitle',
        # WM/SubTitleDescription - unsupported
        # WM/Text - stores arbitrary tags
        # WM/ToolName' - mapped in some tools to ID3 TSSE
        # WM/ToolVersion - unsupported
        # WM/Track - per MS recommendation use WM/TrackNumber
        'WM/TrackNumber': 'tracknumber',
        'WM/UniqueFileIdentifier': 'musicbrainz_recordingid',
        # WM/UserWebURL - # Multiplex web_* tags into this field
        # WM/WMCollectionGroupID - unsupported
        # WM/WMCollectionID - unsupported
        # WM/WMContentID - unsupported
        'WM/Writer': 'lyricist',
        'WM/Year': 'date',

        # The following are Jaikoz-compatible extensions to metadata definitions
        # See http://www.jthink.net/jaudiotagger/tagmapping.html
        'WM/AlbumArtistSortOrder': 'albumartistsort',
        'WM/AlbumSortOrder': 'albumsort',
        'WM/Arranger': 'arranger',
        'WM/Artists': 'artists',
        'WM/AlbumArtists': 'albumartists',
        'WM/ArtistSortOrder': 'artistsort',
        'ASIN': 'asin',
        'WM/Barcode': 'barcode',
        'WM/CatalogNo': 'catalognumber',
        'WM/ComposerSortOrder': 'composersort',
        'WM/DiscogsArtistUrl': 'web_discogs_artist',
        'WM/DiscogsReleaseUrl': 'web_discogs_release',
        'WM/DiscTotal': 'totaldiscs',
        'WM/DJMixer': 'djmixer',
        'WM/Engineer': 'engineer',
        'WM/IsCompilation': 'compilation',
        'WM/LyricsUrl': 'web_lyrics',
        'WM/Media': 'media',
        'WM/Mixer': 'mixer',
        'WM/OriginalArtist': 'originalartist',
        'WM/OriginalLyricist': 'originallyricist',
        'WM/Script': 'script',
        'WM/TitleSortOrder': 'titlesort',
        'WM/TrackTotal': 'totaltracks',
        'WM/WikipediaArtistUrl': 'web_wikipedia_artist',
        'WM/WikipediaReleaseUrl': 'web_wikipedia_release',
        'WM/Work': 'work',

        # The following are Picard specific extensions to metadata definitions
        'Acoustid/Id': 'acoustid_id',
        'Acoustid/Fingerprint': 'acoustid_fingerprint',
        'MusicBrainz/Album Artist Id': 'musicbrainz_albumartistid',
        'MusicBrainz/Album Id': 'musicbrainz_albumid',
        'MusicBrainz/Album Release Country': 'releasecountry',
        'MusicBrainz/Album Type': 'releasetype',
        'MusicBrainz/Artist Id': 'musicbrainz_artistid',
        'MusicBrainz/Disc Id': 'musicbrainz_discid',
        'MusicBrainz/Label Id': 'musicbrainz_labelid',
        'MusicBrainz/Original Album Id': 'musicbrainz_original_albumid',
        'MusicBrainz/Original Artist Id': 'musicbrainz_original_artistid',
        'MusicBrainz/Release Group Id': 'musicbrainz_releasegroupid',
        'MusicBrainz/Track Id': 'musicbrainz_trackid',
        'MusicBrainz/Album Release Country': 'releasecountry',
        'MusicBrainz/Album Status': 'releasestatus',
        'MusicBrainz/Work Id': 'musicbrainz_workid',
        'MusicIP/PUID': 'musicip_puid',
        'MusicIP/Fingerprint': 'musicip_fingerprint',
        'WM/Country': 'country',
        'WM/DiscogsLabelUrl': 'web_discogs_label',
        'WM/DiscogsMasterUrl': 'web_discogs_releasegroup',
        'WM/Keywords': 'keywords',
        'WM/LicenseUrl': 'license',
        'WM/MusicbrainzArtistUrl': 'web_musicbrainz_artist',
        'WM/MusicbrainzLabelUrl': 'web_musicbrainz_label',
        'WM/MusicbrainzRecordingUrl': 'web_musicbrainz_recording',
        'WM/MusicbrainzReleaseUrl': 'web_musicbrainz_release',
        'WM/MusicbrainzReleaseGroupUrl': 'web_musicbrainz_releasegroup',
        'WM/MusicbrainzWorkUrl': 'web_musicbrainz_work',
        'WM/Occasion': 'occasion',
        'WM/OfficialLabelUrl': 'web_official_label',
        'WM/Performers': 'performer:',
        'WM/Phonoright': 'recordingcopyright',
        'WM/RecordingDate': 'recordingdate',
        'WM/RecordingLocation': 'recordinglocation',
        'WM/Quality': 'quality',
        'WM/TaggedDate': '~tagtime',
        'WM/Tempo': 'tempo',
        'WM/WikipediaLabelUrl': 'web_wikipedia_label',
        'WM/WikipediaWorkUrl': 'web_wikipedia_work',
        'WM/LyricistComposer': 'writer',
    }
    __save_tags = dict([(b, a) for a, b in __load_tags.iteritems()])
    __load_tags['CopyrightURL'] = 'copyright' # Depending on whether copyright is a URL or not

    _supported_tags = __save_tags.keys()

    __compatibility = {
        'WM/ARTISTS': 'WM/Artists',
        'WM/Track': 'WM/TrackNumber',
        'WM/ToolName': 'WM/EncodingSettings', # Compatibility with e.g. MediaMonkey
        'WM/OfficialReleaseUrl': 'WM/AudioFileURL',
        'LICENSE': 'WM/License',
        'musicbee/OCCASION': 'WM/Occasion', # musicbee compatibility
        'musicbee/QUALITY': 'WM/Quality', # musicbee compatibility
        'musicbee/KEYWORDS': 'WM/Keywords', # musicbee compatibility
        'foobar2000/TOTALDISCS': 'WM/DiscTotal', # musicbee compatibility
        'MusicBrainz/TRM Id': '', # Obsolete
        'MusicBrainz/AlbumArtistId': __save_tags['musicbrainz_albumartistid'], # Picard 0.70
        'MusicBrainz/AlbumArtistSortName': __save_tags['albumartistsort'], # Picard 0.70
        'MusicBrainz/AlbumArtist': __save_tags['albumartist'], # Picard 0.70
        'MusicBrainz/AlbumId': __save_tags['musicbrainz_albumid'], # Picard 0.70
        'MusicBrainz/AlbumReleaseCountry': __save_tags['releasecountry'], # Picard 0.70
        'MusicBrainz/AlbumReleaseDate': __save_tags['date'], # Picard 0.70
        'MusicBrainz/AlbumStatus': __save_tags['releasestatus'], # Picard 0.70
        'MusicBrainz/AlbumType': __save_tags['releasetype'], # Picard 0.70
        'MusicBrainz/ArtistId': __save_tags['musicbrainz_artistid'], # Picard 0.70
        'MusicBrainz/RecordingId': __save_tags['musicbrainz_recordingid'], # Picard 0.70
        'MusicBrainz/SortName': __save_tags['artistsort'], # Picard 0.70
        'MusicBrainz/Status': __save_tags['releasestatus'], # Picard 0.70
        'MusicBrainz/TotalTracks': __save_tags['totaltracks'], # Picard 0.70
        'MusicBrainz/TrackId': __save_tags['musicbrainz_trackid'], # Picard 0.70
        'MusicBrainz/VariousArtists': __save_tags['compilation'], # Picard 0.70
        'MusicBrainz/NonAlbum': '', # Picard 0.70
        #'MusicIP/Fingerprint': '',
    }

    __ignore_keys_when_loading = [
        'WM/Provider', 'WM/ProviderCopyright',
        'WM/MediaClassSecondaryID',
        'WM/UserWebURL', 'WM/Artists', 'WM/AlbumArtists',
        'SDB/Rating', # mediamonkey compatibility
    ]

    __MediaClassPrimaryGUID = {
        "music": "D1607DBC-E323-4BE2-86A1-48A42A28441E", # Use for music files. Do not use for audio that is not music.
        "non-music": "01CD0F29-DA4E-4157-897B-6275D50C4F11", # Use for audio files that are not music.
        "video": "DB9830BD-3AB3-4FAB-8A37-1A995F7FF74B", # Use for video files.
        "data": "FCF24A76-9A57-4036-990D-E35DD8B244E1", # Use for files that are neither audio or video.
    }

    __MediaClassSecondaryGUID_audio = {
        "audiobook": "E0236BEB-C281-4EDE-A36D-7AF76A3D45B5",
        "spokenword": "3A172A13-2BD9-4831-835B-114F6A95943F",
        "interview": "1B824A67-3F80-4E3E-9CDE-F7361B0F5F1B",
    }

    __MediaClassSecondaryGUID_video = {
        "musicvideo": "E3E689E2-BA8C-4330-96DF-A0EEEFFA6876",
    }

    __multi_value_keys = [
        # Following keys are allowed to be multi-value in ASF specification, see
        # https://msdn.microsoft.com/en-gb/library/windows/desktop/dd743065(v=vs.85).aspx
        'Author', 'WM/AlbumArtist', 'WM/AlbumCoverURL', 'WM/Category',
        'WM/Composer', 'WM/Conductor', 'WM/Director', 'WM/Genre', 'WM/GenreID',
        'WM/Language', 'WM/Lyrics_Synchronised', 'WM/Mood', 'WM/Picture',
        'WM/Producer', 'WM/PromotionURL', 'WM/UserWebURL', 'WM/Writer',
        # The following bespoke tags are also not to be joined
        'WM/Performers',
        # Following tags are not lists to be made single-value
        'WM/SharedUserRating',
    ]

    __load_date_tags = [
        'WM/OriginalReleaseTime',
        'WM/Year',
        'WM/RecordingDate',
        'WM/TaggedDate',
    ]

    __load_int_tags = [
        'WM/PartOfSet',
        'WM/TrackNumber',
        'WM/DiscTotal',
        'WM/TrackTotal',
    ]

    TAG_JOINER = '; '
    TEXT_JOINER = '\n\n\0'

    def _load(self, filename):
        log.debug("Loading file: %r", filename)
        file = ASF(encode_filename(filename))
        tags = file.tags

        # Fix old tag naming and make it compatible with Jaikoz
        # From 1.3 ReleaseTrackID exists - before 1.3 only TrackID
        if ('MusicBrainz/Recording Id' not in tags
            and 'WM/UniqueFileIdentifier' not in tags
            and 'MusicBrainz/Track Id' in tags):
            tags['WM/UniqueFileIdentifier'] = tags['MusicBrainz/Track Id']
            if 'MusicBrainz/Release Track Id' in tags:
                log.info('ASF: File %r: Upgrading obsolete MBID tags ReleaseTrackId->TrackId->RecordingID',
                    path.split(filename)[1])
                tags['MusicBrainz/Track Id'] = tags['MusicBrainz/Release Track Id']
            else:
                log.info('ASF: File %r: Upgrading obsolete MBID tags TrackId->RecordingID',
                    path.split(filename)[1])
                del tags['MusicBrainz/Track Id']
        # Delete releasetrackid if it still exists since recordingid, trackid will be populated from MB
        if 'MusicBrainz/Release Track Id' in tags:
            del tags['MusicBrainz/Release Track Id']

        for old, new in self.__compatibility.iteritems():
            if old not in tags:
                continue
            if new:
                if (new in tags
                        and old != 'MusicBrainz/AlbumReleaseDate'
                        and new != 'WM/Year'): # Picard 0.70
                    log.warning('ASF: File %r: Cannot upgrade text tag - new tag already exists: %s=>%s',
                        path.split(filename)[1], old, new)
                    continue
                tags[new] = tags[old]
                log.info('ASF: File %r: Upgrading tag: %s=>%s',
                    path.split(filename)[1], old, new)
            del tags[old]

        metadata = Metadata()
        self._info(metadata, file)
        for name, values in tags.items():
            if name in self.__load_date_tags:
                values = [sanitize_date(unicode(v)) for v in values]
            elif name in self.__load_int_tags:
                values = [sanitize_int(unicode(v)) for v in values]
            if name == 'WM/Picture':
                for image in values:
                    (mime, data, type, description) = unpack_image(image.value)
                    try:
                        coverartimage = TagCoverArtImage(
                            file=filename,
                            tag=name,
                            types=types_from_id3(type),
                            comment=description,
                            support_types=True,
                            data=data,
                        )
                    except CoverArtImageError as e:
                        log.error('ASF: File %r: Cannot load image: %s', filename, e)
                    else:
                        metadata.append_image(coverartimage)
                continue
            elif name in self.__ignore_keys_when_loading:
                continue
            elif name == 'WM/MediaClassPrimaryID':
                if values[0] == self.__MediaClassPrimaryGUID['video']:
                    metadata['~video'] = '1'
                continue
            elif name == 'Author':
                metadata['artists'] = values[1:]
                values = values[:1]
            elif name == 'WM/AlbumArtist':
                metadata['albumartists'] = values[1:]
                values = values[:1]
            elif name in ['Description', 'WM/Lyrics']:
                name = self.__load_tags[name]
                for value in values:
                    value = unicode(value)
                    line = value.split('\n', 1)[0] if '\n' in value else value
                    desc, value = value.split('=', 1) if '=' in line else ('', value)
                    colon = ':' if desc else ''
                    value = value.split(self.TEXT_JOINER) if self.TEXT_JOINER in value else value
                    metadata['%s%s%s' % (name, colon, desc)] = value
                continue
            elif name == 'WM/Lyrics_Synchronised':
                for value in values:
                    desc, data, timestamp_format, content_type = unpack_lyrics_sync(str(value))
                    colon = ':' if desc else ''
                    metadata.add(
                        '~lyrics_sync%s%s' % (colon, desc),
                        json.dumps(
                            {
                                'timestamp_format': timestamp_format,
                                'content_type': content_type,
                                'text': data,
                            },
                            sort_keys=True
                        )
                    )
                continue
            elif name == 'WM/PartOfSet':
                discdata = unicode(values[0])
                discdata = discdata.split('/') if '/' in discdata else [discdata]
                if len(discdata) > 1:
                    metadata["totaldiscs"] = discdata[1]
                    values = discdata[0]
            elif name == 'WM/Performers':
                for value in values:
                    value = unicode(value)
                    # We save as one performer per line but in case another tool has joined them...
                    names = value.split(self.TAG_JOINER.strip()) if self.TAG_JOINER in value else [value]
                    for name in names:
                        role, name = unpack_performer(name)
                        metadata.add('performer:%s' % role, name)
                continue
            elif name == 'WM/SharedUserRating':
                # Unclear what should happen if config.setting['enable_ratings'] == False
                # Rating in WMA ranges from 0 to 99, normalize this to the range 0 to 5
                values[0] = int(round(int(unicode(values[0])) / 99.0 * (config.setting['rating_steps'] - 1)))
            elif name == 'WM/Text':
                for value in values:
                    name, value = unpack_wmtext(str(value))
                    metadata.add(name, value)
                    known_tag = name.split(':', 1)[0] if ':' in name else name
                    if (known_tag not in self._supported_tags
                        and known_tag + ':' not in self._supported_tags):
                        log.info('ASF: File %r: Loading user metadata: %s=%s',
                            path.split(filename)[1], name, value)
                continue
            elif name == 'WM/Track':
                metadata['tracknumber'] = str(int(unicode(values[0]))+1)
            if name in self.__load_tags:
                name = self.__load_tags[name]
            elif '/' in name:
                log.info('ASF: File %r: Loading ASF-specific metadata: %s=%r',
                    path.split(filename)[1], name, [unicode(v) for v in values])
                name = '~asf:'+ name
            else:
                continue
            values = filter(bool, map(unicode, values))
            log.debug("%s->%r"% (name, values))
            if values:
                metadata[name] = values
        return metadata

    def _save(self, filename, metadata):
        log.debug("Saving file: %r", filename)
        file = ASF(encode_filename(filename))
        tags = file.tags

        if config.setting['clear_existing_tags']:
            tags.clear()
        cover = []
        for image in metadata.images_to_be_saved_to_tags:
            tag_data = pack_image(image.mimetype, image.data,
                                    image_type_as_id3_num(image.maintype),
                                    image.comment)
            cover.append(ASFByteArrayAttribute(tag_data))
        if cover:
            tags['WM/Picture'] = cover

        description = []
        performers = []
        lyrics = []
        lyrics_sync = []
        user_tags = {}
        web_urls = []
        for name, values in metadata.rawitems():
            if name.startswith('~lyrics_sync:') or name == '~lyrics_sync':
                desc = name.split(':', 1)[1] if ':' in name else ''
                for value in values:
                    lyrics_json = json.loads(value)
                    lyrics_sync.append(
                        ASFByteArrayAttribute(
                            pack_lyrics_sync(
                                text=lyrics_json['text'],
                                description=desc,
                                timestamp_format=lyrics_json['timestamp_format'],
                                content_type=lyrics_json['content_type']
                            )
                        )
                    )
                continue
            elif name.startswith('lyrics:') or name == 'lyrics':
                name, desc = name.split(':', 1) if ':' in name else (name, '')
                values = self.TEXT_JOINER.join(values)
                if desc:
                    lyrics.append(desc + '=' + values)
                else:
                    lyrics.insert(0, values)
                continue
            elif name.startswith('comment:') or name == 'comment':
                name, desc = name.split(':', 1) if ':' in name else (name, '')
                values = self.TEXT_JOINER.join(values)
                if desc:
                    description.append(desc + '=' + values)
                else:
                    description.insert(0, values)
                continue
            elif name.startswith('performer:'):
                role = name.split(':' ,1)[1]
                for value in values:
                    if 'vocal' in role:
                        performers.insert(0, pack_performer(role, value))
                    else:
                        performers.append(pack_performer(role, value))
                continue
            elif name == '~rating':
                # Unclear what should happen if config.setting['enable_ratings'] == False
                values[0] = str(int(round(float(values[0]) * 99.0 / (config.setting['rating_steps'] - 1))))
            elif name == 'discnumber' and 'totaldiscs' in metadata:
                values[0] = '%s/%s' % (metadata['discnumber'], metadata['totaldiscs'])
            elif name == 'artist':
                values += metadata.getall('artists')
            elif name == 'albumartist':
                values += metadata.getall('albumartists')
            elif ((name.startswith('web_') or name.startswith('web_'))
                and (name not in ['web_coverart', 'web_official_release', 'web_official_artist'])):
                desc = self.__save_tags[name] if name in self.__save_tags else ''
                # If an unofficial web tag, add to official WM/UserWebURL as well
                web_urls.extend(
                    [ASFByteArrayAttribute(pack_wmtext(v, description=desc))
                    for v in values]
                )
            if name not in self.__save_tags:
                if name.startswith('~asf:'):
                    name = name[5:]
                    tags[name] = map(unicode, values)
                    log.info('ASF: File %r: Saving ASF-specific metadata: %s=%r',
                        path.split(filename)[1], name, values)
                elif not name.startswith('~'):
                    user_tags[name] = values
                    known_tag = name.split(':', 1)[0] if ':' in name else name
                    if (known_tag not in self._supported_tags
                        and known_tag + ':' not in self._supported_tags):
                        log.info('ASF: File %r: Saving user metadata: %s=%r',
                            path.split(filename)[1], name, values)
                continue
            else:
                name = self.__save_tags[name]
#            if name not in self.__multi_value_keys:
#                values = ['; '.join(values)]
            tags[name] = map(unicode, values)

        if description:
            tags['Description'] = description
        if lyrics:
            tags['WM/Lyrics'] = lyrics
        if lyrics_sync:
            tags['WM/Lyrics_Synchronised'] = lyrics_sync
        if performers:
            tags['WM/Performers'] = performers
        if user_tags:
            tags['WM/Text'] = [ASFByteArrayAttribute(pack_wmtext(v, description=k))
                    for k, vs in user_tags.iteritems() for v in vs]
        if web_urls:
            tags['WM/UserWebURL'] = web_urls

        tags['WM/Provider'] = METADATA_PROVIDER
        tags['WM/ProviderCopyright'] = METADATA_COPYRIGHT
        tags['WM/TaggedDate'] = strftime(TIMESTAMP_FORMAT, gmtime())
        # Set WM classes
        if "~datatrack" in metadata and metadata["~datatrack"] == "1":
            tags['WM/MediaClassPrimaryID'] = [ ASFGUIDAttribute(self.__MediaClassPrimaryGUID['data']) ]
        elif "~video" in metadata and metadata["~video"] == "1":
            tags['WM/MediaClassPrimaryID'] = [ ASFGUIDAttribute(self.__MediaClassPrimaryGUID['video']) ]
            tags['WM/MediaClassSecondaryID'] = [ ASFGUIDAttribute(self.__MediaClassSecondaryGUID_video['musicvideo']) ]
        else:
            for type in self.__MediaClassSecondaryGUID_audio:
                if type in metadata.getall('releasetype'):
                    tags['WM/MediaClassPrimaryID'] = [ ASFGUIDAttribute(self.__MediaClassPrimaryGUID['non-music']) ]
                    tags['WM/MediaClassSecondaryID'] = [ ASFGUIDAttribute(self.__MediaClassSecondaryGUID_audio[type]) ]
                    break
            else:
                tags['WM/MediaClassPrimaryID'] = [ ASFGUIDAttribute(self.__MediaClassPrimaryGUID['music']) ]

        file.save()

    def _info(self, metadata, file):
        super(ASFFile, self)._info(metadata, file)
        if hasattr(file.info, 'codec_description') and file.info.codec_description:
            metadata['~format'] = "%s (%s)" % (metadata['~format'], file.info.codec_description)
        if hasattr(file.info, 'codec_name') and file.info.codec_name:
            metadata['~codec'] = file.info.codec_name
