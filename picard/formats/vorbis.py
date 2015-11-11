# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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
from picard.coverart.image import TagCoverArtImage, CoverArtImageError
from picard.file import File
from picard.formats.id3 import types_from_id3, image_type_as_id3_num
from picard.metadata import Metadata
from picard.util import encode_filename, sanitize_date, pack_performer, unpack_performer

import mutagen.flac
import mutagen.ogg
import mutagen.oggflac
import mutagen.oggspeex
import mutagen.oggtheora
import mutagen.oggvorbis
try:
    from mutagen.oggopus import OggOpus
    with_opus = True
except ImportError:
    OggOpus = None
    with_opus = False

import base64
from os import path
from time import strftime


class VCommentFile(File):

    """
    Generic VComment-based file.
    Specifications:
        Formal spec: http://www.xiph.org/vorbis/doc/v-comment.html
        In the wild: http://lists.xiph.org/pipermail/vorbis-dev/attachments/20090716/e2db9203/attachment-0001.xls
        See also: http://age.hobba.nl/audio/mirroredpages/ogg-tagging.html
        See also: http://www.mediamonkey.com/wiki/index.php/WebHelp:About_Track_Properties/4.0
    """
    _File = None

    __save_tags = {
        # The following are taken from official V-Comment spec. at:
        # http://www.xiph.org/vorbis/doc/v-comment.html
        "title": "TITLE",
        #"~releasecomment": "VERSION",
        "album": "ALBUM",
        "tracknumber": "TRACKNUMBER",
        "artist": "ARTIST",
        "performer": "PERFORMER",
        "copyright": "COPYRIGHT",
        "license": "LICENSE",
        "label": "ORGANIZATION",
        #"?": "DESCRIPTION",
        "genre": "GENRE",
        "date": "DATE",
        "recordinglocation": "LOCATION",
        "web_official_label": "CONTACT",
        "isrc": "ISRC",

        # The following are taken from field recommendations at:
        # http://age.hobba.nl/audio/mirroredpages/ogg-tagging.html
        "artist": "ARTIST",
        #"label": "PUBLISHER",
        "label": "LABEL",
        "discnumber": "DISCNUMBER",
        #"discnumber": "DISC",
        "barcode": "BARCODE", # Jaikoz
        #"barcode": "EAN/UPN",
        #"barcode": "PRODUCTNUMBER",
        #"catalognumber": "LABELNO",
        # "media": "SOURCEMEDIA", # Use Jakioz MEDIA
        #"?": "VERSION",
        "encodedby": "ENCODED-BY",
        # "encodedby": "VENDOR",
        "encodersettings": "ENCODING",
        "composer": "COMPOSER",
        "arranger": "ARRANGER",
        "lyricist": "LYRICIST",
        #"?": "AUTHOR",
        "conductor": "CONDUCTOR",
        "albumartist": "ENSEMBLE",
        #"?": "PART",
        #"?": "PARTNUMBER",
        "comment": "COMMENT",

        # The following have been derived from Jaikoz compatibility
        "acoustid_fingerprint": "ACOUSTID_FINGERPRINT",
        "acoustid_id": "ACOUSTID_ID",
        "albumartist": "ALBUMARTIST",
        "albumartists": "ALBUMARTISTS",
        "albumartistsort": "ALBUMARTISTSORT",
        "albumsort": "ALBUMSORT",
        "artistsort": "ARTISTSORT",
        "artists": "ARTISTS",
        "asin": "ASIN",
        "bpm": "BPM",
        "catalognumber": "CATALOGNUMBER", # Jaikoz
        "compilation": "COMPILATION",
        "composersort": "COMPOSERSORT",
        "country": "COUNTRY",
        "djmixer": "DJMIXER",
        "engineer": "ENGINEER",
        "grouping": "GROUPING",
        "key": "KEY",
        "language": "LANGUAGE",
        "lyrics": "LYRICS",
        "web_lyrics": "URL_LYRICS_SITE",
        "media": "MEDIA",
        "mixer": "MIXER",
        "mood": "MOOD",
        "occasion": "OCCASION",
        "web_official_artist": "URL_OFFICIAL_ARTIST_SITE", # Changed from website for compatibility with Jaikoz
        "web_official_release": "URL_OFFICIAL_RELEASE_SITE",
        "originalalbum": "ORIGINAL ALBUM",
        "originalartist": "ORIGINAL ARTIST",
        "originallyricist": "ORIGINAL LYRICIST",
        "producer": "PRODUCER",
        "quality": "QUALITY",
        "~rating": "RATING",
        "releasecountry": "RELEASECOUNTRY",
        "releasestatus": "MUSICBRAINZ_ALBUMSTATUS",
        "releasetype": "MUSICBRAINZ_ALBUMTYPE",
        "remixer": "REMIXER",
        "script": "SCRIPT",
        "tempo": "TEMPO",
        "titlesort": "TITLESORT",
        "totaldiscs": "DISCTOTAL",
        "totaltracks": "TRACKTOTAL",
        "web_wikipedia_artist": "URL_WIKIPEDIA_ARTIST_SITE",
        "web_wikipedia_release": "URL_WIKIPEDIA_RELEASE_SITE",

        # The following have been derived from mediamonkey/musicbee empirical usage
        #"grouping": "CONTENTGROUP",
        #"performer": "INVOLVED PEOPLE",

        # The following are Picard specific
        "albumgenre": "ALBUM GENRE",
        "albumrating": "ALBUM RATING",
        "category": "CATEGORY",
        "discsubtitle": "VOLUME",
        "encodingtime": "ENCODING TIME",
        "keywords": "KEYWORDS",
        "musicbrainz_albumartistid": "MUSICBRAINZ_ALBUMARTISTID",
        "musicbrainz_albumid": "MUSICBRAINZ_ALBUMID",
        "musicbrainz_artistid": "MUSICBRAINZ_ARTISTID",
        "musicbrainz_discid": "MUSICBRAINZ_DISCID",
        "musicbrainz_labelid": "MUSICBRAINZ_LABELID",
        "musicbrainz_original_albumid": "MUSICBRAINZ_ORIGINAL_ALBUMID",
        "musicbrainz_original_artistid": "MUSICBRAINZ_ORIGINAL_ARTISTID",
        "musicbrainz_recordingid": "MUSICBRAINZ_RECORDINGID",
        "musicbrainz_releasegroupid": "MUSICBRAINZ_RELEASEGROUPID",
        "musicbrainz_trackid": "MUSICBRAINZ_TRACKID",
        "musicbrainz_workid": "MUSICBRAINS_WORKID",
        "musicip_fingerprint": "FINGERPRINT",
        "musicip_puid": "MUSICIP PUID",
        "originaldate": "ORIGINAL DATE",
        "originalyear": "ORIGINAL YEAR",
        "playdelay": "PLAY DELAY",
        "recordingdate": "RECORDING DATE",
        "recordingcopyright": "RECORDING COPYRIGHT",
        "subtitle": "SUBTITLE",
        "~tagdate": "TAGGED DATE",
        "writer": "WRITER",
        "work": "WORK",
        "~web_coverart": "URL_COVERART_SITE",
        "web_discogs_artist": "URL_DISCOGS_ARTIST_SITE",
        "web_discogs_label": "URL_DISCOGS_LABEL_SITE",
        "web_discogs_release": "URL_DISCOGS_RELEASE_SITE",
        "web_discogs_releasegroup": "URL_DISCOGS_MASTER_SITE",
        "~web_musicbrainz_artist": "URL_MUSICBRAINZ_ARTIST_SITE",
        "~web_musicbrainz_label": "URL_MUSICBRAINZ_LABEL_SITE",
        "~web_musicbrainz_recording": "URL_MUSICBRAINZ_RECORDING_SITE",
        "~web_musicbrainz_release": "URL_MUSICBRAINZ_RELEASE_SITE",
        "~web_musicbrainz_releasegroup": "URL_MUSICBRAINZ_RELEASEGROUP_SITE",
        "~web_musicbrainz_work": "URL_MUSICBRAINZ_WORK_SITE",
        "web_wikipedia_label": "URL_WIKIPEDIA_LABEL_SITE",
        "web_wikipedia_work": "URL_WIKIPEDIA_WORK_SITE",
    }
    __load_tags = dict([(v.lower(), k) for k, v in __save_tags.iteritems()])

    _supported_tags = __save_tags.keys()

    __compatibility = {
        "musicbrainz_trmid": "",
        #"musicip_fingerprint": "",
        #"fingerprint": "",
        "totaltracks": "tracktotal",
        "totaldiscs": "disctotal",
        "disc": "discnumber",
        "website": "url_official_artist_site", # Backward compatibility with Picard < 1.4
        "original title": "original album", # Compatibility with mediamonkey
        "album artist": "albumartist", # Compatibility with mediamonkey
        "ensemble": "albumartist", # Compatibility with mediamonkey
        "ean/upn": "barcode", # See "in the wild" reference
        "productnumber": "barcode", # See "in the wild" reference
        "organization": "label", # See "in the wild" reference
        "publisher": "label", # See "in the wild" reference
        "labelno": "catalognumber", # See "in the wild" reference
        "sourcemedia": "media", # See "in the wild" reference
        "initialkey": "key", # See "in the wild" reference
    }

    def _load(self, filename):
        log.debug("Loading file: %r", filename)
        file = self._File(encode_filename(filename))
        metadata = Metadata()
        self._info(metadata, file)
        tags = file.tags

        # Fix old tag naming and make it compatible with Jaikoz
        if ('musicbrainz_recordingid' not in tags
                and 'musicbrainz_trackid' in tags
                and 'musicbrainz_releasetrackid'in tags):
            log.info('Vorbis: File %r: Upgrading obsolete MBID tags',
                path.split(filename)[1])
            tags['musicbrainz_recordingid'] = tags['musicbrainz_trackid']
            tags['musicbrainz_trackid'] = tags['musicbrainz_releasetrackid']
        if 'musicbrainz_releasetrackid'in tags:
            del tags['musicbrainz_releasetrackid']

        for old, new in self.__compatibility.iteritems():
            if old not in tags:
                continue
            if new:
                if new in tags:
                    log.warning('Vorbis: File %r: Cannot upgrade text tag - new tag already exists: %s=>%s',
                        path.split(filename)[1], old, new)
                    continue
                tags[new] = tags[old]
                log.info('Vorbis: File %r: Upgrading tag: %s=>%s',
                    path.split(filename)[1], old, new)
            del tags[old]

        for tag_name, values in tags.iteritems():
            for value in values:
                name = tag_name
                if name in ['date', 'original date']:
                    # YYYY-00-00 => YYYY
                    name = self.__load_tags[name]
                    value = sanitize_date(value)
                elif name == 'performer':
                    # performer="Joe Barr (Piano)" => performer:piano="Joe Barr"
                    # performer="Piano=Joe Barr" => performer:piano="Joe Barr"
                    name = self.__load_tags[name]
                    role, value = unpack_performer(value)
                    if not role:
                        log.info('Vorbis: File %r: Loading performer without instrument: %s',
                            path.split(filename)[1], value)
                    name += ':' + role
                elif name in ['lyrics', 'comment']:
                    # transform "lyrics=desc=text" to "lyrics:desc=text"
                    name = self.__load_tags[name]
                    if "=" in value:
                        desc, value = value.split('=', 1)
                        name += ':' + desc
                elif name.startswith('rating:') or name == 'rating':
                    # rating:email=value
                    name, email = name.split(':', 1) if ':' in name else (name, '')
                    if email and email != config.setting['rating_user_email']:
                        metadata['~vorbis:%s:%s' % (name, email)] = value
                        log.info('Vorbis: File %r: Loading rating for a different user: %s:%s=%r',
                            path.split(filename)[1], name, email, value)
                        continue
                    name = self.__load_tags[name]
                    value = unicode(int(round(float(value) / 99.0 * (config.setting['rating_steps'] - 1))))
                elif name == 'album rating':
                    name = self.__load_tags[name]
                    value = unicode(round(float(value) / 99.0 * (config.setting['rating_steps'] - 1), 1))
                elif name == "fingerprint":
                    if value.startswith("MusicMagic Fingerprint"):
                        name = self.__load_tags[name]
                        value = value[22:]
                    else:
                        name = '~vorbis:fingerprint'
                elif name in self.__load_tags:
                    name = self.__load_tags[name]
                elif name in self._supported_tags or (name + ':') in self._supported_tags:
                    name = '~vorbis:%s' % name
                elif name != "metadata_block_picture":
                    log.info('Vorbis: File %r: Loading user metadata: %s=%r',
                        path.split(filename)[1], name, value)
                else:
                    image = mutagen.flac.Picture(base64.standard_b64decode(value))
                    try:
                        coverartimage = TagCoverArtImage(
                            file=filename,
                            tag=name,
                            types=types_from_id3(image.type),
                            comment=image.desc,
                            support_types=True,
                            data=image.data,
                        )
                    except CoverArtImageError as e:
                        log.error('Vorbis: File %r: Cannot load image: %s', filename, e)
                    else:
                        metadata.append_image(coverartimage)
                    continue
                if name.startswith('~vorbis:') and not name.startswith('~vorbis:rating:'):
                    log.info('Vorbis: File %r: Loading Vorbis specific metadata: %s=%r',
                        path.split(filename)[1], name[8:], value)
                metadata.add(name, value)

        self.flac_load_pictures(file, filename, metadata)

        # Read the unofficial COVERART tags, for backward compatibility only
        if not "metadata_block_picture" in file.tags:
            try:
                for data in file["COVERART"]:
                    try:
                        coverartimage = TagCoverArtImage(
                            file=filename,
                            tag='COVERART',
                            data=base64.standard_b64decode(data)
                        )
                    except CoverArtImageError as e:
                        log.error('Vorbis: File %r: Cannot load COVERART image: %s', filename, e)
                    else:
                        metadata.append_image(coverartimage)
            except KeyError:
                pass
        return metadata

    def flac_load_pictures(self, file, filename, metadata):
        pass

    def _save(self, filename, metadata):
        """Save metadata to the file."""
        log.debug("Saving file: %r", filename)
        file = self._File(encode_filename(filename))
        if file.tags is None:
            file.add_tags()
        if config.setting["clear_existing_tags"]:
            file.tags.clear()
        self.flac_clear_pictures(file, metadata)

        tags = {}
        for name, value in metadata.iteritems():
            if name == '~rating':
                # Save rating according to:
                #   https://quodlibet.readthedocs.org/en/latest/development/formats.html
                #   https://github.com/quodlibet/quodlibet/blob/master/quodlibet/docs/development/formats.rst
                name = self.__save_tags[name]
                if config.setting['rating_user_email']:
                    name = 'rating:%s' % config.setting['rating_user_email']
                else:
                    name = 'rating'
                value = unicode(round(float(value) * 99.0 / (config.setting['rating_steps'] - 1), 1))
            elif name == 'albumrating':
                name = self.__save_tags[name]
                value = unicode(round(float(value) * 99.0 / (config.setting['rating_steps'] - 1), 1))
            elif (name.startswith('lyrics:') or name == 'lyrics'
                or name.startswith('comment:') or name == 'comment'):
                # comment:desc="text" => comment="desc=text"
                # lyrics:desc="text" => "lyrics="desc=text"
                name, desc = name.split(':', 1) if ':' in name else (name, '')
                name = self.__save_tags[name]
                value = desc + '=' + value if desc else value
            elif name == "date" or name == "originaldate":
                # YYYY-00-00 => YYYY
                name = self.__save_tags[name]
                value = sanitize_date(value)
            elif name.startswith('performer:'):
                # transform "performer:Piano=Joe Barr" to "performer=Joe Barr (Piano)"
                name, role = name.split(':', 1) if ':' in name else (name, '')
                name = self.__save_tags[name]
                if not role:
                    log.info('Vorbis: File %r: Saving performer without instrument: %s',
                        path.split(filename)[1], value)
                value = pack_performer(role, value)
            elif name == "musicip_fingerprint":
                name = self.__save_tags[name]
                value = "MusicMagic Fingerprint%s" % value
            elif name in self.__save_tags:
                name = self.__save_tags[name]
            elif name.startswith("~vorbis:"):
                name = name[8:]
                if name.startswith('rating:'):
                    log.info('Vorbis: File %r: Saving rating for a different user: %s=%r',
                        path.split(filename)[1], name, value)
                else:
                    log.info('Vorbis: File %r: Saving Vorbis specific metadata: %s=%r',
                        path.split(filename)[1], name, value)
            elif name.startswith("~"):
                continue
            # don't save user tags with same name as a standard load name
            elif name in self.__load_tags:
                log.warning('Vorbis: File %r: Cannot save user metadata with standard key name: %s=%r',
                    path.split(filename)[1], name.upper(), value)
                continue
            else:
                log.info('Vorbis: File %r: Saving user metadata: %s=%r',
                    path.split(filename)[1], name, value)
            tags.setdefault(name.upper().encode('utf-8'), []).append(value)

        for image in metadata.images_to_be_saved_to_tags:
            picture = mutagen.flac.Picture()
            picture.data = image.data
            picture.mime = image.mimetype
            picture.desc = image.comment
            picture.type = image_type_as_id3_num(image.maintype)
            self.save_image(file, tags, picture)

        tags[self.__save_tags["~tagdate"]] = [strftime('%Y-%m-%dT%H:%M:%S')]
        file.tags.update(tags)
        self.save_file(file)

    def save_image(self, file, tags, picture):
        tags.setdefault("metadata_block_picture", []).append(
            base64.standard_b64encode(picture.write()))

    def flac_clear_pictures(self, file, metadata):
        pass

    def save_file(self, file):
        file.save()


class FLACFile(VCommentFile):

    """FLAC file."""
    EXTENSIONS = [".flac"]
    NAME = "FLAC"
    _File = mutagen.flac.FLAC

    def flac_load_pictures(self, file, filename, metadata):
        for image in file.pictures:
            try:
                coverartimage = TagCoverArtImage(
                    file=filename,
                    tag='FLAC/PICTURE',
                    types=types_from_id3(image.type),
                    comment=image.desc,
                    support_types=True,
                    data=image.data,
                )
            except CoverArtImageError as e:
                log.error('Vorbis: File %r: Cannot load FLAC image: %s', filename, e)
            else:
                metadata.append_image(coverartimage)

    def flac_clear_pictures(self, file, metadata):
        if config.setting["clear_existing_tags"] or metadata.images_to_be_saved_to_tags:
            file.clear_pictures()

    def save_image(self, file, tags, picture):
        file.add_picture(picture)

    def save_file(self, file):
        if config.setting["remove_id3_from_flac"]:
            try:
                file.save(deleteid3=True)
            except TypeError:
                file.save()
        else:
            file.save()


class OggFLACFile(VCommentFile):

    """FLAC file."""
    EXTENSIONS = [".oggflac"]
    NAME = "Ogg FLAC"
    _File = mutagen.oggflac.OggFLAC


class OggSpeexFile(VCommentFile):

    """Ogg Speex file."""
    EXTENSIONS = [".spx"]
    NAME = "Speex"
    _File = mutagen.oggspeex.OggSpeex


class OggTheoraFile(VCommentFile):

    """Ogg Theora file."""
    EXTENSIONS = [".oggtheora"]
    NAME = "Ogg Theora"
    _File = mutagen.oggtheora.OggTheora


class OggVorbisFile(VCommentFile):

    """Ogg Vorbis file."""
    EXTENSIONS = [".ogg"]
    NAME = "Ogg Vorbis"
    _File = mutagen.oggvorbis.OggVorbis


class OggOpusFile(VCommentFile):

    """Ogg Opus file."""
    EXTENSIONS = [".opus"]
    NAME = "Ogg Opus"
    _File = OggOpus


def _select_ogg_type(filename, options):
    """Select the best matching Ogg file type."""
    fileobj = file(filename, "rb")
    results = []
    try:
        header = fileobj.read(128)
        results = [
            (option._File.score(filename, fileobj, header), option.__name__, option)
            for option in options]
    finally:
        fileobj.close()
    results.sort()
    if not results or results[-1][0] <= 0:
        raise mutagen.ogg.error("unknown Ogg audio format")
    return results[-1][2](filename)


def OggAudioFile(filename):
    """Generic Ogg audio file."""
    options = [OggFLACFile, OggSpeexFile, OggVorbisFile]
    return _select_ogg_type(filename, options)


OggAudioFile.EXTENSIONS = [".oga"]
OggAudioFile.NAME = "Ogg Audio"


def OggVideoFile(filename):
    """Generic Ogg video file."""
    options = [OggTheoraFile]
    return _select_ogg_type(filename, options)

OggVideoFile.EXTENSIONS = [".ogv"]
OggVideoFile.NAME = "Ogg Video"
