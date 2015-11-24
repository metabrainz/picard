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
from picard.metadata import Metadata
from picard.util import encode_filename, sanitize_date, sanitize_int, pack_performer, unpack_performer, isurl

import mutagen.apev2
import mutagen.monkeysaudio
import mutagen.musepack
import mutagen.wavpack
import mutagen.optimfrog
from .mutagenext import tak

from collections import defaultdict
from os import path
from time import strftime, gmtime

# APEv2 metadata keys supported are based on those of mediamonkey / musicbee
# since these represent implementations of APEv2 support that have a pedigree.
#
# Picard extensions to mediamonkey / musicbee support will, where possible,
# conform to the official specifications in order to maximise compatibility
# with other players.
#
# See http://wiki.hydrogenaud.io/index.php?title=APE_key
# or http://age.hobba.nl/audio/mirroredpages/apekey.html
# which are (at the time of writing) identical.
#
# Note: This version can either store a single piece of cover art or store all
# cover art depending on a constant setting. Cover art is sorted by type in a
# defined priority sequence in order that a single piece is e.g. front cover
# rather than picture of CD, and to store in priority sequence if multiple
# cover art is saved.

class APEv2File(File):

    """Generic APEv2-based file."""
    _File = None

    # This table is derived from official specifications and
    # empirical test files created by MediaMonkey, MusicBee and mp3tag
    # plus Musicbrainz specific values

    __save_tags = {
        'acoustid_fingerprint': ["Acoustid Fingerprint"],
        'acoustid_id': ["Acoustid ID"],
        'album': ["Album"],
        'albumartist': ["Album Artist", "Band"], # mediamonkey compatibility
        'albumartists': ["Album Artists"],
        'albumartistsort': ["AlbumArtistSort"],
        'albumgenre': ["Album Genre"],
        'albumrating': ["Album Rating"],
        'albumsort': ["AlbumSort"],
        'arranger': ["Arranger", "Involved People"],
        'artist': ["Artist", "Display Artist"], # musicbee compatibility
        'artists': ["Artists"],
        'artistsort': ["ArtistSort"],
        'asin': ["ASIN"],
        'barcode': ["EAN/UPC"],
        'bpm': ["BPM"],
        'catalognumber': ["Catalog"],
        'category': ["Category"],
        'comment': ["Comment"],
        'compilation': ["Compilation"],
        'composer': ["Composer"],
        'composersort': ["ComposerSort"],
        'conductor': ["Conductor"],
        'copyright': ["Copyright"],
        'country': ["Country"],
        'date': ["Year"],
        'discnumber': ["Disc"],
        'discsubtitle': ["DiscSubtitle"],
        'djmixer': ["DJMixer", "Involved People"],
        'encodedby': ["EncodedBy"],
        'encodersettings': ["Encoder"],
        'encodingtime': ["EncodingTime"],
        'engineer': ["Engineer", "Involved People"],
        'genre': ["Genre"],
        'grouping': ["ContentGroup", "Grouping"], # mediamonkey compatibility
        'isrc': ["ISRC"],
        'key': ["InitialKey"],
        'keywords': ["Keywords"],
        'label': ["Publisher"],
        'language': ["Language"],
        'license': ["License"],
        'lyricist': ["Lyricist"],
        'lyrics': ["Lyrics"],
        'media': ["Media"],
        'mixer': ["Mixer", "Involved People"],
        'mood': ["Mood"],
        'musicbrainz_albumartistid': ["MusicBrainz_AlbumArtistId"],
        'musicbrainz_albumid': ["MusicBrainz_AlbumId"],
        'musicbrainz_artistid': ["MusicBrainz_ArtistId"],
        'musicbrainz_discid': ["MusicBrainz_DiscId"],
        'musicbrainz_labelid': ["MusicBrainz_LabelId"],
        'musicbrainz_original_albumid': ["MusicBrainz_Original_AlbumId"],
        'musicbrainz_original_artistid': ["MusicBrainz_Original_ArtistId"],
        'musicbrainz_recordingid': ["MusicBrainz_RecordingId"],
        'musicbrainz_releasegroupid': ["MusicBrainz_ReleaseGroupId"],
        'musicbrainz_trackid': ["MusicBrainz_TrackId"],
        'musicbrainz_workid': ["MusicBrainz_WorkId"],
        'musicip_fingerprint': ["MusicMagic Fingerprint"],
        'musicip_puid': ["MusicMagic PUID"],
        'occasion': ["Occasion"],
        'originalalbum': ["Original Title"],
        'originalartist': ["Original Artist"],
        'originaldate': ["OriginalDate"],
        'originallyricist': ["Original Lyricist"],
        'originalyear': ["OriginalYear"],
        'performer': ["Performer", "Involved People"],
        'playdelay': ["Play Delay"],
        'producer': ["Producer", "Involved People"],
        'quality': ["Quality"],
        'recordingcopyright': ["Publicationright"],
        'recordingdate': ["Record Date"],
        'recordinglocation': ["Record Location"],
        'releasecountry': ["ReleaseCountry"],
        'releasestatus': ["MusicBrainz_AlbumStatus"],
        'releasetype': ["MusicBrainz_AlbumType"],
        'remixer': ["MixArtist"],
        'script': ["Script"],
        'subtitle': ["Subtitle"],
        'tempo': ["Tempo"],
        'title': ["Title"],
        'titlesort': ["TitleSort"],
        'totaldiscs': ["Disc"],
        'totaltracks': ["Track"],
        'tracknumber': ["Track"],
        'web_discogs_artist': ["Discogs Artist URL"],
        'web_discogs_label': ["Discogs Label URL"],
        'web_discogs_release': ["Discogs Release URL"],
        'web_discogs_releasegroup': ["Discogs Release Master URL"],
        'web_lyrics': ["Lyrics URL"],
        'web_official_artist': ["Bibliography"],
        'web_official_label': ["Official Label URL"],
        'web_official_release': ["Official Release URL"],
        'web_wikipedia_artist': ["Wikipedia Artist URL"],
        'web_wikipedia_label': ["Wikipedia Label URL"],
        'web_wikipedia_release': ["Abstract"],
        'web_wikipedia_work': ["Wikipedia Work URL"],
        'work': ["Work"],
        'writer': ["Writer"],
        'year': ["Release Year"],
        # Unclear what should happen if config.setting['enable_ratings'] == False
        # ~rating current saved as-is - mediamonkey/musicbee use values 0-5
        '~rating': ["Rating"],
        '~tagtime': ["TaggedDate"],
        'web_coverart': ["Cover Art URL"],
        'web_musicbrainz_artist': ["MusicBrainz Artist URL"],
        'web_musicbrainz_label': ["MusicBrainz Label URL"],
        'web_musicbrainz_recording': ["MusicBrainz Recording URL"],
        'web_musicbrainz_release': ["MusicBrainz Release URL"],
        'web_musicbrainz_releasegroup': ["MusicBrainz Release Group URL"],
        'web_musicbrainz_work': ["MusicBrainz Work URL"],
        # None: ["iTunesMediaType"],
    }
    __load_tags = defaultdict(list)
    for meta, tags in __save_tags.iteritems():
        for tag in tags:
            __load_tags[tag.lower()].append(meta)

    __involvedpeople = [k for k, v in __save_tags.iteritems() if "Involved People" in v]

    _supported_tags = __save_tags.keys()

    __compatibility = {
        "musicbrainz_trmid": '', # Obsolete
        "musicbrainz_variousartists": __save_tags['compilation'][0], # Picard < 0.7
        "musicbrainz_albumartist": __save_tags['albumartist'][0], # Picard < 0.7
        "musicbrainz_albumartistsortname": __save_tags['albumartistsort'][0], # Picard < 0.7
        "musicbrainz_sortname": __save_tags['artistsort'][0], # Picard < 0.7
        "musicbrainz_nonalbum": '', # Picard < 0.7
        "mediatype": __save_tags['media'][0], # Picard < 0.7
        "format": __save_tags['media'][0], # Picard 1.0-1.3
        "weblink": __save_tags['web_official_artist'][0], # Picard < 1.4
        #"MusicMagic Fingerprint": '', # Obsolete
        #"musicip_fingerprint": '', # Obsolete
    }

    # Add Picard backward compatibility for tags saved with metadata names
    #for tags in __load_tags.values():
    #    if len(tags) == 1:
    #        name = __save_tags[tags[0]] if tags[0] in __save_tags else tags[0]
    #        tag = tags[0][1:] if tags[0].startswith('~') else tags[0]
    #        if tag not in __load_tags and name != tag:
    #            __compatibility[tag] = name

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

    # Priority for image selection for single embedded image
    __image_types = [
        "track",
        "front",
        "poster",
        "liner",
        "medium",
        "booklet",
        "back",
        "tray",
        "other",
    ]

    def _load(self, filename):
        log.debug("Loading file: %r", filename)
        file = self._File(encode_filename(filename))
        metadata = Metadata()
        self._info(metadata, file)
        if not file.tags:
            return metadata
        tags = file.tags

        # Fix old tag naming and make it compatible with Jaikoz
        t = {}
        for tag in tags.keys():
            if tag.lower() in [
                    'musicbrainz_recordingid',
                    'musicbrainz_trackid',
                    'musicbrainz_releasetrackid'
                ]:
                t[tag.lower()] = tag
        # From 1.3 ReleaseTrackID exists - before 1.3 only TrackID
        if ('musicbrainz_recordingid' not in t
                and 'musicbrainz_trackid' in t):
            tags['musicbrainz_recordingid'] = tags[t['musicbrainz_trackid']]
            del tags[t['musicbrainz_trackid']]
            if 'musicbrainz_releasetrackid' in t:
                log.info('APEv2: File %r: Upgrading obsolete MBID tags ReleaseTrackId->TrackId->RecordingID',
                    path.split(filename)[1])
                tags['musicbrainz_trackid'] = tags[t['musicbrainz_releasetrackid']]
            else:
                log.info('APEv2: File %r: Upgrading obsolete MBID tags TrackId->RecordingID',
                    path.split(filename)[1])
        # Delete releasetrackid if it still exists since recordingid, trackid will be populated from MB
        if 'musicbrainz_releasetrackid'in t:
            del tags[t['musicbrainz_releasetrackid']]

        for old, new in self.__compatibility.iteritems():
            if old not in tags:
                continue
            if new:
                if new in tags:
                    log.warning('APEv2: File %r: Cannot upgrade text tag - new tag already exists: %s=>%s',
                        path.split(filename)[1], old, new)
                    continue
                tags[new] = tags[old]
                log.info('APEv2: File %r: Upgrading tag: %s=>%s',
                    path.split(filename)[1], old, new)
            del tags[old]

        saved_tags = {}
        file_tags = set(tags.keys())
        related_values = []
        for tag_name, values in tags.iteritems():
            name = tag_name.lower()
            if name == "related":
                continue
            elif values.kind == mutagen.apev2.BINARY and name.startswith("cover art ("):
                if '\0' in values.value:
                    descr, data = values.value.split('\0', 1)
                    try:
                        coverartimage = TagCoverArtImage(
                            file=filename,
                            tag=name,
                            data=data,
                        )
                    except CoverArtImageError as e:
                        log.error('APEv2: File %r: Cannot load image: %s - error: %s',
                            filename, tag_name, e)
                    else:
                        metadata.append_image(coverartimage)
                else:
                    log.warning('APEv2: File %r: Cover art skipped - invalid format: %s',
                        path.split(filename)[1], tag_name)
                continue
            elif name.startswith("cover art ("): # but not binary
                log.warning('APEv2: File %r: Cover art ignored - not binary data: %s',
                    path.split(filename)[1], tag_name)
                continue
            elif values.kind == mutagen.apev2.BINARY: # Binary but not cover art
                log.warning('APEv2: File %r: Invalid binary metadata ignored: %s',
                    path.split(filename)[1], tag_name)
                continue

            values = unicode(values)
            #log.info("%s=>%r",tag_name, values)
            if type(values) != "list":
                values = [values]
            if len(values) == 1:
                if '\x00' in values[0]:
                    # musicbee compatibility - stored as a single string
                    values = values[0].split('\x00')
                elif name in ['involved people', 'display artist'] and ';' in values[0]:
                    # mediamonkey compatibility - involved people stored as a single string
                    # musicbee compatibility - displayartist = '; '.join(artists), artist = '\0'.join(artists)
                    values = values[0].split(';')
            values = [v.replace("\r\n", "\n").strip() for v in values]

            if name in self.__load_tags:
                tag_names = self.__load_tags[name]
                if name in ["involved people", "performer"]:
                    for value in values:
                        role, person = unpack_performer(value)
                        if not role or role not in tags:
                            role = 'performer:%s' % role
                        metadata.add_unique(role, person)
                    continue
                for tag in tag_names:
                    if tag in saved_tags:
                        if saved_tags[tag] != values:
                            log.warning('APEv2: File %r: Tag %s=>%s has different data to previous tag: %r != %r',
                                path.split(filename)[1], tag_name, tag, values, saved_tags[tag])
                        continue
                    saved_tags[tag] = values

                    if tag in self.__date_tags:
                        # YYYY-00-00 => YYYY
                        values = [sanitize_date(v) for v in values]
                    elif tag in self.__int_tags:
                        values = [sanitize_int(v) for v in values]

                    if tag == "date":
                        metadata['date'] = values
                        if not set(self.__save_tags['year']) & file_tags:
                            metadata['year'] = [v[:4] for v in values]
                    elif tag == "year":
                        metadata['year'] = values
                        if not set(self.__save_tags['date']) & file_tags:
                            metadata['date'] = values
                    elif tag == "originaldate":
                        metadata['originaldate'] = values
                        if not set(self.__save_tags['originalyear']) & file_tags:
                            metadata['originalyear'] = [v[:4] for v in values]
                    elif tag == "originalyear":
                        metadata['originalyear'] = values
                        if not set(self.__save_tags['originaldate']) & file_tags:
                            metadata['originaldate'] = values
                    elif tag == "tracknumber":
                        track = values[0].split('/', 2) if '/' in values[0] else [values[0]]
                        metadata["tracknumber"] = sanitize_int(track[0])
                        if len(track) > 1:
                            metadata["totaltracks"] = sanitize_int(track[1])
                    elif tag in ["totaltracks", "totaldiscs"]:
                        continue
                    elif tag == "discnumber":
                        disc = values[0].split('/', 2) if '/' in values[0] else [values[0]]
                        metadata["discnumber"] = sanitize_int(disc[0])
                        if len(disc) > 1:
                            metadata["totaldiscs"] = sanitize_int(disc[1])
                    elif tag == '~rating':
                        # Unclear what should happen if config.setting['enable_ratings'] == False
                        # Rating in WMA ranges from 0 to 99, normalize this to the range 0 to 5
                        metadata["~rating"] = unicode(int(round(
                            float(unicode(values[0])) / 5.0 * (config.setting['rating_steps'] - 1)
                            )))
                    elif tag == 'albumrating':
                        # Unclear what should happen if config.setting['enable_ratings'] == False
                        # Rating in WMA ranges from 0 to 99, normalize this to the range 0 to 5
                        metadata["albumrating"] = unicode(round(
                            float(unicode(values[0])) / 5.0 * (config.setting['rating_steps'] - 1), 1
                            ))
                    else:
                        for value in values:
                            if tag in ['comment', 'lyrics']:
                                id, value = unpack_performer(value)
                                colon = ':' if id else ''
                                metadata.add('%s%s%s' % (tag, colon, id), value)
                            elif tag in self.__save_tags and "involved people" in self.__save_tags[tag]:
                                # If we have e.g. loaded engineer from "involved people" don't duplicate
                                metadata.add_unique(tag, value)
                            else:
                                # But e.g. label can have duplicates
                                metadata.add(tag, value)
            # name not in self.__load_tags - so not standard Picard metadata
            elif name in self._supported_tags:
                tag = '~apev2:%s' % name
                log.info('APEv2: File %r: Loading APEv2 specific metadata which conflicts with known Picard tag: %s=%r',
                    path.split(filename)[1], tag, values)
                metadata[tag] = values
            else:
                log.info('APEv2: File %r: Loading user metadata: %s=%r',
                    path.split(filename)[1], name, values)
                metadata[name] = values

        return metadata

    def _save(self, filename, metadata):
        """Save metadata to the file."""
        log.debug("Saving file: %r", filename)
        try:
            tags = mutagen.apev2.APEv2(encode_filename(filename))
        except mutagen.apev2.APENoHeaderError:
            tags = mutagen.apev2.APEv2()
        if config.setting["clear_existing_tags"]:
            tags.clear()
        elif metadata.images_to_be_saved_to_tags:
            for name, value in tags.items():
                if name.lower().startswith('cover art (') and value.kind == mutagen.apev2.BINARY:
                    del tags[name]

        t = defaultdict(list)
        performers = []
        production = []
        for name, value in metadata.iteritems():
            value = value.encode('utf-8').replace("\r\n", "\n").replace("\n", "\r\n")
            name, desc = name.split(':', 1) if ':' in name else (name, '')
            if name in [
                        'totaltracks', 'totaldiscs',
                    ]:
                # These tags are handled manually below
                continue
            else:
                tag_names = self.__save_tags[name] if name in self.__save_tags else [name]
                for tag in tag_names:
                    if name == 'tracknumber':
                        if 'totaltracks' in metadata:
                            t[tag].append('%s/%s' % (value, metadata['totaltracks']))
                        else:
                            t[tag].append(value)
                    elif name == 'discnumber':
                        if 'totaldiscs' in metadata:
                            t[tag].append('%s/%s' % (value, metadata['totaldiscs']))
                        else:
                            t[tag].append(value)
                    elif name == "~rating":
                        # Unclear what should happen if config.setting['enable_ratings'] == False
                        t[tag].append(str(float(value) * 5.0 / (config.setting['rating_steps'] - 1)))
                    elif name in ['comment', 'lyrics']:
                        equals = '=' if desc else ''
                        t[tag].append('%s%s%s' % (desc, equals, value))
                    elif tag == "Involved People":
                        # Performers and non-performers are separated here
                        # so that performers appear first in the Involved People
                        if name == 'performer':
                            # And vocalists appear before instrument performers
                            value = pack_performer(desc, value)
                            if 'vocal' in desc:
                                performers.insert(0, value)
                            else:
                                performers.append(value)
                        else:
                            production.append(pack_performer(name, value))
                    elif name in self.__save_tags:
                        if isurl(value):
                            t["Related"].append(value)
                        t[tag].append(value)
                    elif name.startswith('~apev2:'):
                        log.info('APEv2: File %r: Saving APEv2 specific metadata which conflicts with known Picard tag: %s=%r',
                            path.split(filename)[1], name, value)
                        t[name[7:]].append(value)
                    elif not name.startswith('~'):
                        if name.lower() not in self.__load_tags:
                            log.info('APEv2: File %r: Saving user metadata: %s=%s',
                                path.split(filename)[1], name, value)
                            if isurl(value):
                                t["Related"].append(value)
                            t[name.title()].append(value)
                        else:
                            log.warning('APEv2: File %r: Conflict with standard metadata %s - Unable to save user metadata: %s=%s',
                                path.split(filename)[1], self.__load_tags[name][0], name, value)

        if performers:
            t["Performer"] = performers
        if performers or production:
            t["Involved People"] = performers + production

        t["TaggedDate"] = strftime(TIMESTAMP_FORMAT, gmtime())

        for name, values in t.iteritems():
            if len(values) == 1 and isurl(values[0]):
                tags[name] = mutagen.apev2.APEValue(values[0], mutagen.apev2.EXTERNAL)
            else:
                tags[name] = values if len(values) > 1 else values[0]

        # Although spec only allows one image, musicbee supports multiple images
        # and Mutagen allows us to create multiple images.
        # The previous version said that "the spec only supports a single image"
        # however the formal APEv2 specification does not support images at all.
        # The code below saves multiple images in priority sequence
        # with the intention that players that do not support multiple images
        # will see only the first, highest-priority image and ignore the others
        # however there is no guarantee that the sequence they are created
        # is the same sequence that they are written to the file or that
        # a player will show the first image.
        # To avoid saving > 1 image, set single_image = True.
        single_image = True
        images_sorted = defaultdict(list)
        for image in metadata.images_to_be_saved_to_tags:
            images_sorted[image.maintype].append(image)

        for type in images_sorted:
            if type not in self.__image_types:
                log.debug('APEv2: File %r: Adding unknown cover art type to end of priority list: %s',
                    path.split(filename)[1], type)
                self.__image_types.append(type)

        for type in self.__image_types:
            if type in images_sorted:
                images = images_sorted[type]
                i = '' if len(images) == 1 or single_image else 1
                for image in images:
                    num = ' #%d' % i if i else ''
                    cover_filename = key = 'Cover Art (%s)%s' % (image.maintype.title(), num)
                    cover_filename += image.extension
                    tags[key] = mutagen.apev2.APEValue(cover_filename.encode('utf-8') + '\0' + image.data, mutagen.apev2.BINARY)
                    if i:
                        i += 1
                    if single_image:
                            break
                if single_image:
                    break
                del images_sorted[type]

        tags.save(encode_filename(filename))


class MusepackFile(APEv2File):

    """Musepack file."""
    EXTENSIONS = [".mpc", ".mp+"]
    NAME = "Musepack"
    _File = mutagen.musepack.Musepack

    def _info(self, metadata, file):
        super(MusepackFile, self)._info(metadata, file)
        metadata['~format'] = "Musepack, SV%d" % file.info.version


class WavPackFile(APEv2File):

    """WavPack file."""
    EXTENSIONS = [".wv"]
    NAME = "WavPack"
    _File = mutagen.wavpack.WavPack

    def _info(self, metadata, file):
        super(WavPackFile, self)._info(metadata, file)
        metadata['~format'] = "%s (%s)" % (self.NAME, file.info.version)

    def _save_and_rename(self, old_filename, metadata):
        """Includes an additional check for WavPack correction files"""
        wvc_filename = old_filename.replace(".wv", ".wvc")
        if path.isfile(wvc_filename):
            if config.setting["rename_files"] or config.setting["move_files"]:
                self._rename(wvc_filename, metadata)
        return File._save_and_rename(self, old_filename, metadata)


class OptimFROGFile(APEv2File):

    """OptimFROG file."""
    EXTENSIONS = [".ofr", ".ofs", ".off"]
    # .ofr=Standard, .ofs=DualStream, .off=IEEE float
    NAME = "OptimFROG"
    _File = mutagen.optimfrog.OptimFROG

    def _info(self, metadata, file):
        super(OptimFROGFile, self)._info(metadata, file)
        if file.filename.lower().endswith(".off"):
            metadata['~format'] = "OptimFROG IEEE Float Audio"
        elif file.filename.lower().endswith(".ofs"):
            metadata['~format'] = "OptimFROG DualStream Audio"
        else:
            metadata['~format'] = "OptimFROG Lossless Audio"


class MonkeysAudioFile(APEv2File):

    """Monkey's Audio file."""
    EXTENSIONS = [".ape"]
    NAME = "Monkey's Audio"
    _File = mutagen.monkeysaudio.MonkeysAudio

    def _info(self, metadata, file):
        super(MonkeysAudioFile, self)._info(metadata, file)
        metadata['~format'] = '%s - version %.2f' % (self.NAME, file.info.version)


class TAKFile(APEv2File):

    """TAK file."""
    EXTENSIONS = [".tak"]
    NAME = "Tom's lossless Audio Kompressor"
    _File = tak.TAK
