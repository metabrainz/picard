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

from mutagen import id3
from picard.plugins.picardmutagen.mutagenext import compatid3


def read_id3_tags(tags, metadata):
    """Read tags from an ID3 object to Picard's metadata."""

    def read_text_frame(frame_id, name):
        if frame_id in tags:
            metadata[name] = unicode(tags[frame_id]) 

    def read_free_text_frame(desc, name):
        frames = tags.getall("TXXX:%s" % desc)
        if frames:
            metadata[name] = unicode(frames[0]) 

    read_text_frame("TPE1", "artist")
    read_text_frame("TPE2", "ensemble")
    read_text_frame("TPE3", "conductor")
    read_text_frame("TPE4", "remixer")
    read_text_frame("TCOM", "composer")
    read_text_frame("TALB", "album")
    read_text_frame("TIT2", "title")
    read_text_frame("TEXT", "lyricist")
    read_text_frame("TCMP", "compilation")

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
        metadata["musicbrainz_trackid"] = unicode(frames[0])
    read_free_text_frame("MusicBrainz Artist Id", "musicbrainz_trackid")
    read_free_text_frame("MusicBrainz Album Id", "musicbrainz_albumid")
    read_free_text_frame("MusicBrainz Album Artist Id",
                        "musicbrainz_albumartistid")

    read_free_text_frame("ALBUMARTIST", "albumartist")

    frames = tags.getall("APIC")
    if frames:
        metadata["~artwork"] = []
        for frame in frames:
            metadata["~artwork"].append((frame.mime, frame.data))

def write_id3_tags(tags, metadata, encoding, v23=False):
    """Write tags from Picard's metadata to an ID3 object."""

    def add_text_frame(frame_class, name):
        print name, name in metadata, metadata[name]
        if name in metadata:
            tags.add(frame_class(encoding=encoding,
                                 text=metadata[name]))
            print tags.pprint()

    def add_free_text_frame(desc, name):
        if name in metadata:
            tags.delall("TXXX:%s" % desc.upper())
            tags.add(id3.TXXX(encoding=encoding, desc=desc,
                              text=metadata[name]))

    add_text_frame(id3.TPE1, "artist")
    add_text_frame(id3.TPE2, "ensemble")
    add_text_frame(id3.TPE3, "conductor")
    add_text_frame(id3.TPE4, "remixer")
    add_text_frame(id3.TCOM, "composer")
    add_text_frame(id3.TALB, "album")
    add_text_frame(id3.TIT2, "title")
    add_text_frame(id3.TEXT, "lyricist")
    add_text_frame(compatid3.TCMP, "compilation")

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
    add_free_text_frame("MusicBrainz Artist Id", "musicbrainz_trackid")
    add_free_text_frame("MusicBrainz Album Id", "musicbrainz_albumid")
    add_free_text_frame("MusicBrainz Album Artist Id",
                        "musicbrainz_albumartistid")

    add_free_text_frame("ALBUMARTIST", "albumartist")

