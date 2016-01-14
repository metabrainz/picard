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
from picard.const import TIMESTAMP_FORMAT
from picard.coverart.image import TagCoverArtImage, CoverArtImageError
from picard.file import File
from picard.formats.id3 import types_from_id3, image_type_as_id3_num
from picard.metadata import Metadata
from picard.util import encode_filename, sanitize_date, sanitize_int, pack_performer, unpack_performer

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
from collections import defaultdict
from os import path
from time import strftime, gmtime, gmtime


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

    __load_tags = {
        # The following are taken from official V-Comment spec. at:
        # http://www.xiph.org/vorbis/doc/v-comment.html
        "title": "title",
        #"version": "~releasecomment",
        "album": "album",
        "tracknumber": "tracknumber",
        "artist": "artist",
        "performer": "performer",
        "copyright": "copyright",
        "license": "license",
        "organization": "label",
        #"description": "?",
        "genre": "genre",
        "date": "date",
        "location": "recordinglocation",
        "contact": "web_official_label",
        "isrc": "isrc",

        # The following have been derived from Jaikoz compatibility
        # http://www.jthink.net/jaudiotagger/tagmapping.html
        "acoustid_fingerprint": "acoustid_fingerprint",
        "acoustid_id": "acoustid_id",
        "albumartist": "albumartist",
        "albumartists": "albumartists",
        "albumartistsort": "albumartistsort",
        "albumsort": "albumsort",
        "arranger": "arranger",
        "artist": "artist",
        "artists": "artists",
        "artistsort": "artistsort",
        "asin": "asin",
        "barcode": "barcode",
        "bpm": "bpm",
        "fbpm": "bpm",
        "catalognumber": "catalognumber",
        "comment": "comment",
        "compilation": "compilation",
        "composer": "composer",
        "composersort": "composersort",
        "conductor": "conductor",
        "country": "country",
        "discnumber": "discnumber",
        "djmixer": "djmixer",
        "vendor": "encodedby",
        "engineer": "engineer",
        "grouping": "grouping",
        "key": "key",
        "label": "label",
        "language": "language",
        "lyricist": "lyricist",
        "lyrics": "lyrics",
        "media": "media",
        "mixer": "mixer",
        "mood": "mood",
        "musicbrainz_albumartistid": "musicbrainz_albumartistid",
        "musicbrainz_albumid": "musicbrainz_albumid",
        "musicbrainz_artistid": "musicbrainz_artistid",
        "musicbrainz_discid": "musicbrainz_discid",
        "musicbrainz_original_albumid": "musicbrainz_original_albumid",
        "musicbrainz_recordingid": "musicbrainz_recordingid",
        "musicbrainz_release_groupid": "musicbrainz_releasegroupid",
        "musicbrainz_workid": "musicbrainz_workid",
        "occasion": "occasion",
        "original album": "originalalbum",
        "original artist": "originalartist",
        "original lyricist": "originallyricist",
        "originaldate": "originaldate",
        "original_year": "originalyear",
        "producer": "producer",
        "quality": "quality",
        "releasecountry": "releasecountry",
        "musicbrainz_albumstatus": "releasestatus",
        "musicbrainz_albumtype": "releasetype",
        "remixer": "remixer",
        "script": "script",
        "tags": "keywords",
        "tempo": "tempo",
        "titlesort": "titlesort",
        "disctotal": "totaldiscs",
        "tracktotal": "totaltracks",
        "url_discogs_artist_site": "web_discogs_artist",
        "url_discogs_release_site": "web_discogs_release",
        "url_lyrics_site": "web_lyrics",
        "url_official_artist_site": "web_official_artist", # changed from website for compatibility with jaikoz
        "url_official_release_site": "web_official_release",
        "url_wikipedia_artist_site": "web_wikipedia_artist",
        "url_wikipedia_release_site": "web_wikipedia_release",
        "rating": "~rating",

        # The following are Picard specific tags
        "album genre": "albumgenre",
        "album rating": "albumrating",
        "category": "category",
        "discsubtitle": "discsubtitle",
        "encoding time": "encodingtime",
        "keywords": "keywords",
        "musicbrainz_labelid": "musicbrainz_labelid",
        "musicbrainz_releasegroupid": "musicbrainz_releasegroupid",
        "musicbrainz_trackid": "musicbrainz_trackid",
        "musicbrainz_original_artistid": "musicbrainz_original_artistid",
        "musicip fingerprint": "musicip_fingerprint",
        "musicip puid": "musicip_puid",
        "play delay": "playdelay",
        "recording date": "recordingdate",
        "recording copyright": "recordingcopyright",
        "subtitle": "subtitle",
        "tagged date": "~tagtime",
        "writer": "writer",
        "work": "work",
        "url_coverart_site": "web_coverart",
        "url_discogs_label_site": "web_discogs_label",
        "url_discogs_master_site": "web_discogs_releasegroup",
        "url_musicbrainz_artist_site": "web_musicbrainz_artist",
        "url_musicbrainz_label_site": "web_musicbrainz_label",
        "url_musicbrainz_recording_site": "web_musicbrainz_recording",
        "url_musicbrainz_release_site": "web_musicbrainz_release",
        "url_musicbrainz_releasegroup_site": "web_musicbrainz_releasegroup",
        "url_musicbrainz_work_site": "web_musicbrainz_work",
        "url_wikipedia_label_site": "web_wikipedia_label",
        "url_wikipedia_work_site": "web_wikipedia_work",
        "year": "year",

        # The following are required for compatibility with other tools
        "album artist": "albumartist", # mediamonkey compatibility
        "disc": "discnumber", # mediamonkey compatibility
        "ensemble": "albumartist", # mediamonkey compatibility
        "original date": "originaldate", # mediamonkey compatibility
        "original year": "originalyear", # mediamonkey compatibility
        "original title": "originalalbum", # mediamonkey compatibility
        "encoder": "encodersettings", # mediamonkey compatibility
    }
    __save_tags = defaultdict(list)
    for tag, meta in __load_tags.iteritems():
        __save_tags[meta].append(tag.upper())

    _supported_tags = __save_tags.keys()

    __compatibility = {
        "musicbrainz_trmid": "", # Obsolete
        "format": "media", # Picard < 1.4
        "musicbrainz_albumartist": "albumartist", # Picard 0.70
        "musicbrainz_albumartistsortname": "albumartistsort", # Picard 0.70
        "musicbrainz_nonalbum": "", # Picard 0.70
        "musicbrainz_sortname": "artistsort", # Picard 0.70
        "musicbrainz_variousartists": "compilation", # Picard 0.70
        "originalyear": "original year", # Picard < 1.4 compatibility
        "releasestatus": "musicbrainz_albumstatus", # Picard < 1.4 compatibility
        "releasetype": "musicbrainz_albumtype", # Picard < 1.4 compatibility
        "totaltracks": "tracktotal", # Picard < 1.4 compatibility
        "totaldiscs": "disctotal", # Picard < 1.4 compatibility
        "website": "url_official_artist_site", # Picard < 1.4 compatibility
        #"musicip_fingerprint": "",
        #"fingerprint": "",
    }

    __date_tags = [
        'date',
        'year',
        'originaldate',
        'originalyear',
        'recordingdate',
        '~tagtime',
    ]

    __int_tags = [
        'discnumber',
        'tracknumber',
        'totaldiscs',
        'totaltracks',
    ]


    def _load(self, filename):
        log.debug("Loading file: %r", filename)
        file = self._File(encode_filename(filename))
        metadata = Metadata()
        self._info(metadata, file)
        tags = file.tags

        # Fix old tag naming and make it compatible with Jaikoz
        # From 1.3 ReleaseTrackID exists - before 1.3 only TrackID
        if ('musicbrainz_recordingid' not in tags
                and 'musicbrainz_trackid' in tags):
            tags['musicbrainz_recordingid'] = tags['musicbrainz_trackid']
            if 'musicbrainz_releasetrackid'in tags:
                log.info('Vorbis: File %r: Upgrading obsolete MBID tags ReleaseTrackId->TrackId->RecordingID',
                    path.split(filename)[1])
                tags['musicbrainz_trackid'] = tags['musicbrainz_releasetrackid']
            else:
                log.info('Vorbis: File %r: Upgrading obsolete MBID tags TrackId->RecordingID',
                    path.split(filename)[1])
                del tags['musicbrainz_trackid']
        # Delete releasetrackid if it still exists since recordingid, trackid will be populated from MB
        if 'musicbrainz_releasetrackid'in tags:
            del tags['musicbrainz_releasetrackid']

        for old, new in self.__compatibility.iteritems():
            if old not in tags:
                continue
            if new:
                if new in tags:
                    if tags[old] != tags[new]:
                        log.warning('Vorbis: File %r: Cannot upgrade text tag - new tag already exists: %s=>%s',
                            path.split(filename)[1], old, new)
                        continue
                else:
                    tags[new] = tags[old]
                    log.info('Vorbis: File %r: Upgrading tag: %s=>%s',
                        path.split(filename)[1], old, new)
            del tags[old]

        saved_name = {}
        saved_values = {}
        file_tags = set([k.upper() for k in tags.keys()])
        for name, values in tags.iteritems():
            if name.startswith('rating:') or name == 'rating':
                # rating:email=value
                name, email = name.split(':', 1) if ':' in name else (name, '')
                if email and email != config.setting['rating_user_email']:
                    metadata['~vorbis:%s:%s' % (name, email)] = values
                    log.info('Vorbis: File %r: Loading rating for a different user: %s:%s=%r',
                        path.split(filename)[1], name, email, value)
                    continue
                values = [unicode(int(round(float(v) / 99.0 * (config.setting['rating_steps'] - 1)))) for v in values]

            if name in self.__load_tags:
                tag = self.__load_tags[name]
                if tag in saved_name:
                    if saved_values[tag] == values:
                        continue
                    old_name = saved_name[tag]
                    if (
                            self.__save_tags[tag].index(name)
                            and self.__saved_tags[tag].index(old_name)
                            and self.__save_tags[tag].index(name) > self.__saved_tags[tag].index(old_name)
                        ):
                        log.warning("Vorbis: File %r: Multiple file tags which map to same Picard tag (%s) have differing values: " +
                            "Using %s=%r rather than %s=%r " +\
                            "(as likely to have been updated by another tagging tool).",
                            path.split(filename)[1], tag, name, values, old_name, saved_values[tag])
                    else:
                        log.warning("Vorbis: File %r: Multiple file tags which map to same Picard tag (%s) have differing values: " +
                            "Using %s=%r rather than %s=%r " +\
                            "(as likely to have been updated by another tagging tool).",
                            path.split(filename)[1], tag, old_name, saved_values[tag], name, values)
                        continue
                saved_name[tag] = name
                saved_values[tag] = values

                if tag in self.__date_tags:
                    # YYYY-00-00 => YYYY
                    values = [sanitize_date(v) for v in values]
                elif tag in self.__int_tags:
                    values = [sanitize_int(v) for v in values]

                if tag == 'date':
                    if not set(self.__save_tags['year']) & file_tags:
                        metadata['year'] = [v[:4] for v in values]
                elif tag == 'year':
                    if not set(self.__save_tags['date']) & file_tags:
                        metadata['date'] = values
                elif tag == 'originaldate':
                    if not set(self.__save_tags['originalyear']) & file_tags:
                        metadata['originalyear'] = [v[:4] for v in values]
                elif tag == 'originalyear':
                    if not set(self.__save_tags['originaldate']) & file_tags:
                        metadata['originaldate'] = values
                elif tag == 'performer':
                    # performer="Joe Barr (Piano)" => performer:piano="Joe Barr"
                    # performer="Piano=Joe Barr" => performer:piano="Joe Barr"
                    for value in values:
                        role, value = unpack_performer(value)
                        metadata.add('%s:%s' % (name, role), value)
                    continue
                elif tag in ['lyrics', 'comment']:
                    # transform "lyrics=desc=text" to "lyrics:desc=text"
                    for value in values:
                        desc, value = value.split('=', 1) if '=' in value else ('', value)
                        desc = ':' + desc if desc else ''
                        metadata.add('%s%s' % (name, desc), value)
                    continue
                elif tag == 'albumrating':
                    values = [unicode(round(float(v) / 99.0 * 5.0, 1)) for v in values]
                elif tag == "musicip_fingerprint":
                    for value in values:
                        if value.startswith("MusicMagic Fingerprint"):
                            metadata.add(tag, value[22:])
                        else:
                            metadata.add('~vorbis:musicip_fingerprint', value)
                    continue
            elif name in self._supported_tags:
                tag = '~vorbis:%s' % name
                log.info('Vorbis: File %r: Loading Vorbis-specific metadata: %s=%r',
                    path.split(filename)[1], tag, values)
            elif name != "metadata_block_picture":
                tag = name
                log.info('Vorbis: File %r: Loading user metadata: %s=%r',
                    path.split(filename)[1], name, values)
            else:
                for value in values:
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
            metadata[tag] = values

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

        tags = defaultdict(list)
        performers = []
        for tag, values in metadata.rawitems():
            if tag == '~rating':
                # Save rating according to:
                #   https://quodlibet.readthedocs.org/en/latest/development/formats.html
                #   https://github.com/quodlibet/quodlibet/blob/master/quodlibet/docs/development/formats.rst
                names = self.__save_tags[tag]
                if config.setting['rating_user_email']:
                    names = ['%s:%s' % (n, config.setting['rating_user_email']) for n in names]
                values = [unicode(int(round(float(v) * 99.0 / (config.setting['rating_steps'] - 1)))) for v in values]
            elif tag == 'albumrating':
                names = self.__save_tags[tag]
                values = [unicode(int(round(float(v) * 99.0 / 5.0))) for v in values]
            elif (tag.startswith('lyrics:') or tag == 'lyrics'
                or tag.startswith('comment:') or tag == 'comment'):
                # comment:desc="text" => comment="desc=text"
                # lyrics:desc="text" => "lyrics="desc=text"
                tag, desc = tag.split(':', 1) if ':' in tag else (tag, '')
                names = self.__save_tags[tag]
                if desc:
                    values = [desc + '=' + v for v in values]
            elif tag == "date" or tag == "originaldate":
                # YYYY-00-00 => YYYY
                names = self.__save_tags[tag]
                values = [sanitize_date(v) for v in values]
            elif tag.startswith('performer:'):
                # transform "performer:Piano=Joe Barr" to "performer=Joe Barr (Piano)"
                role = tag.split(':', 1)[1]
                values = [pack_performer(role, v) for v in values]
                if 'vocal' in role:
                    performers = values + performers
                else:
                    performers.extend(values)
                continue
            elif tag == "musicip_fingerprint":
                names = self.__save_tags[tag]
                values = ["MusicMagic Fingerprint%s" % v for v in values]
            elif tag in self.__save_tags:
                names = self.__save_tags[tag]
            elif tag.startswith("~vorbis:"):
                if tag.startswith('~vorbis:rating:'):
                    log.info('Vorbis: File %r: Saving rating for a different user: %s=%r',
                        path.split(filename)[1], tag, values)
                else:
                    log.info('Vorbis: File %r: Saving Vorbis-specific metadata: %s=%r',
                        path.split(filename)[1], tag, values)
                names = [tag[8:]]
            elif tag.startswith("~"):
                continue
            # don't save user tags with same name as a standard load name
            elif tag in self.__load_tags:
                log.warning('Vorbis: File %r: Cannot save user metadata with standard key name: %s=%r',
                    path.split(filename)[1], name.upper(), values)
                continue
            else:
                names = [tag]
                log.info('Vorbis: File %r: Saving user metadata: %s=%r',
                    path.split(filename)[1], tag, values)
            for name in names:
                tags[name.upper().encode('utf-8')].extend(values)

        if performers:
            for name in self.__save_tags['performer']:
                tags[name] = performers

        for image in metadata.images_to_be_saved_to_tags:
            picture = mutagen.flac.Picture()
            picture.data = image.data
            picture.mime = image.mimetype
            picture.desc = image.comment
            picture.type = image_type_as_id3_num(image.maintype)
            self.save_image(file, tags, picture)

        for tag in self.__save_tags["~tagtime"]:
            tags[tag] = [strftime(TIMESTAMP_FORMAT, gmtime())]

        file.tags.update(tags)
        self.save_file(file)

    def save_image(self, file, tags, picture):
        tags["metadata_block_picture"].append(
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
        log.error("Vorbis: File %r: Unknown Ogg format - not one of: %s",
            filename, ', '.join([v[1] for v in results]))
        raise mutagen.ogg.error("Vorbis: File %r: Unknown Ogg format - not one of: %s"
            % (filename, ', '.join([v[1] for v in results])))
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
