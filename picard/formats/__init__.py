# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2012 Lukáš Lalinský
# Copyright (C) 2008 Will
# Copyright (C) 2010, 2014, 2018-2020 Philipp Wolfer
# Copyright (C) 2013 Michael Wiencek
# Copyright (C) 2013, 2017-2021, 2024 Laurent Monin
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2017 Ville Skyttä
# Copyright (C) 2020 Gabriel Ferreira
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


from picard.formats.ac3 import AC3File
from picard.formats.apev2 import (
    AACFile,
    MonkeysAudioFile,
    MusepackFile,
    OptimFROGFile,
    TAKFile,
    WavPackFile,
)
from picard.formats.asf import ASFFile
from picard.formats.id3 import (
    AiffFile,
    DSDIFFFile,
    DSFFile,
    MP3File,
    TrueAudioFile,
)
from picard.formats.midi import MIDIFile
from picard.formats.mp4 import MP4File
from picard.formats.vorbis import (
    FLACFile,
    OggAudioFile,
    OggContainerFile,
    OggFLACFile,
    OggOpusFile,
    OggSpeexFile,
    OggTheoraFile,
    OggVideoFile,
    OggVorbisFile,
)
from picard.formats.wav import WAVFile


__all__ = [
    'DEFAULT_FORMATS',
]

DEFAULT_FORMATS = [
    AACFile,
    AC3File,
    AiffFile,
    ASFFile,
    DSFFile,
    FLACFile,
    MIDIFile,
    MonkeysAudioFile,
    MP3File,
    MP4File,
    MusepackFile,
    OggAudioFile,
    OggContainerFile,
    OggFLACFile,
    OggOpusFile,
    OggSpeexFile,
    OggTheoraFile,
    OggVideoFile,
    OggVorbisFile,
    OptimFROGFile,
    TAKFile,
    TrueAudioFile,
    WAVFile,
    WavPackFile,
]

if DSDIFFFile:
    DEFAULT_FORMATS.append(DSDIFFFile)
