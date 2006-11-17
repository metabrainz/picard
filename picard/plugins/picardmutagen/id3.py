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

import mutagen.apev2
import mutagen.mp3
import mutagen.trueaudio
from mutagen import id3
from picard.file import File
from picard.plugins.picardmutagen.mutagenext import compatid3
from picard.util import encode_filename

class ID3File(File):
    """Generic ID3-based file."""
    _File = None
    _IsMP3 = False

    def read(self):
        file = self._File(encode_filename(self.filename),
                          ID3=compatid3.CompatID3)
        if not file.tags:
            file.add_tags()
        tags = file.tags
        metadata = self.metadata
        
        def read_text_frame(frame_id, name):
            if frame_id in tags:
                metadata[name] = unicode(tags[frame_id]) 
    
        def read_free_text_frame(desc, name):
            frames = tags.getall("TXXX:%s" % desc)
            if frames:
                metadata[name] = unicode(frames[0]) 
    
        read_text_frame("TPE1", "artist")
        read_text_frame("TPE3", "conductor")
        read_text_frame("TPE4", "remixer")
        read_text_frame("TCOM", "composer")
        read_text_frame("TALB", "album")
        read_text_frame("TIT2", "title")
        read_text_frame("TEXT", "lyricist")
        read_text_frame("TCMP", "compilation")
        read_text_frame("TDRC", "date")
        read_text_frame("XDOR", "date")
    
        if self.config.setting["tpe2_albumartist"]:
            read_text_frame("TPE2", "albumartist")
        else:
            read_text_frame("TPE2", "ensemble")
            read_free_text_frame("ALBUMARTIST", "albumartist")
            
        if "TRCK" in tags:
            text = unicode(tags["TRCK"])
            if "/" in text:
                track, total = text.split("/")
                metadata["tracknumber"] = track
                metadata["totaltracks"] = total
            else:
                metadata["tracknumber"] = text
    
        if "TPOS" in tags:
            text = unicode(tags["TPOS"])
            if "/" in text:
                disc, total = text.split("/")
                metadata["discnumber"] = disc
                metadata["totaldiscs"] = total
            else:
                metadata["discnumber"] = text
    
        frames = tags.getall("UFID:http://musicbrainz.org")
        if frames:
            metadata["musicbrainz_trackid"] = unicode(frames[0].data)
        read_free_text_frame("MusicBrainz Artist Id", "musicbrainz_artistid")
        read_free_text_frame("MusicBrainz Album Id", "musicbrainz_albumid")
        read_free_text_frame("MusicBrainz Album Artist Id",
                            "musicbrainz_albumartistid")
    
        frames = tags.getall("APIC")
        if frames:
            for frame in frames:
                metadata.add("~artwork", (frame.mime, frame.data))

        self.metadata["~#length"] = int(file.info.length * 1000)
        self.orig_metadata.copy(self.metadata)

    def save(self):
        """Save metadata to the file."""
        try:
            tags = compatid3.CompatID3(encode_filename(self.filename))
        except mutagen.id3.ID3NoHeaderError:
            tags = compatid3.CompatID3()

        if self.config.setting["clear_existing_tags"]:
            tags.clear()

        if self.config.setting["write_id3v1"]:
            v1 = 2
        else:
            v1 = 0

        if self.config.setting["id3v2_encoding"].lower() == "utf-8":
            encoding = 3
        elif self.config.setting["id3v2_encoding"].lower() == "utf-16":
            encoding = 1
        else:
            encoding = 0

        metadata = self.metadata

        def add_text_frame(frame_class, name):
            if name in metadata:
                tags.add(frame_class(encoding=encoding,
                                     text=metadata[name]))

        def add_free_text_frame(desc, name):
            if name in metadata:
                tags.delall("TXXX:%s" % desc.upper())
                tags.add(id3.TXXX(encoding=encoding, desc=desc,
                                  text=metadata[name]))

        add_text_frame(id3.TPE1, "artist")
        add_text_frame(id3.TPE3, "conductor")
        add_text_frame(id3.TPE4, "remixer")
        add_text_frame(id3.TCOM, "composer")
        add_text_frame(id3.TALB, "album")
        add_text_frame(id3.TIT2, "title")
        add_text_frame(id3.TEXT, "lyricist")
        add_text_frame(compatid3.TCMP, "compilation")
        add_text_frame(id3.TDRC, "date")

        if self.config.setting["tpe2_albumartist"]:
            add_text_frame(id3.TPE2, "albumartist")
        else:
            add_text_frame(id3.TPE2, "ensemble")
            add_free_text_frame("ALBUMARTIST", "albumartist")
            
        if "tracknumber" in metadata:
            if "totaltracks" in metadata:
                text = "%s/%s" % (metadata["tracknumber"],
                                  metadata["totaltracks"])
            else:
                text = metadata["tracknumber"]
            tags.add(id3.TRCK(encoding=0, text=text))

        if "discnumber" in metadata:
            if "totaldiscs" in metadata:
                text = "%s/%s" % (metadata["discnumber"], 
                                  metadata["totaldiscs"])
            else:
                text = metadata["discnumber"]
            tags.add(id3.TPOS(encoding=0, text=text))

        if "comment" in metadata:
            tags.add(id3.COMM(encoding=encoding,
                              text=metadata["COMMENT"]))

        if "musicbrainz_trackid" in metadata:
            tags.add(id3.UFID(owner="http://musicbrainz.org",
                              data=metadata["musicbrainz_trackid"]))
        add_free_text_frame("MusicBrainz Artist Id", "musicbrainz_artistid")
        add_free_text_frame("MusicBrainz Album Id", "musicbrainz_albumid")
        add_free_text_frame("MusicBrainz Album Artist Id",
                            "musicbrainz_albumartistid")

        if self.config.setting["remove_images_from_tags"]:
            tags.delall("APIC")
        if self.config.setting["save_images_to_tags"]:
            if "~artwork" in self.metadata:
                for mime, data in self.metadata["~artwork"]:
                    tags.add(id3.APIC(encoding=0, mime=mime, type=3, desc="",
                                      data=data))

        if self.config.setting["write_id3v23"]:
            tags.update_to_v23()
            tags.save(encode_filename(self.filename), v2=3, v1=v1)
        else:
            tags.update_to_v24()
            tags.save(encode_filename(self.filename), v2=4, v1=v1)

        if self._IsMP3 and self.config.setting["strip_ape_tags"]:
            mutagen.apev2.delete(encode_filename(self.filename))


class MP3File(ID3File):
    """MP3 file."""
    _File = mutagen.mp3.MP3
    _IsMP3 = True


class TrueAudioFile(ID3File):
    """TTA file."""
    _File = mutagen.trueaudio.TrueAudio

