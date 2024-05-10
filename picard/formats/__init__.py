# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2012 Lukáš Lalinský
# Copyright (C) 2008 Will
# Copyright (C) 2010, 2014, 2018-2020 Philipp Wolfer
# Copyright (C) 2013 Michael Wiencek
# Copyright (C) 2013, 2017-2021 Laurent Monin
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


from picard.extension_points.formats import register_format
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
from picard.formats.util import (  # noqa: F401 # pylint: disable=unused-import
    ext_to_format,
    guess_format,
    open_,
    supported_extensions,
    supported_formats,
)
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


register_format(AACFile)
register_format(AC3File)
register_format(AiffFile)
register_format(ASFFile)
if DSDIFFFile:
    register_format(DSDIFFFile)
register_format(DSFFile)
register_format(FLACFile)
register_format(MIDIFile)
register_format(MonkeysAudioFile)
register_format(MP3File)
register_format(MP4File)
register_format(MusepackFile)
register_format(OggAudioFile)
register_format(OggContainerFile)
register_format(OggFLACFile)
register_format(OggOpusFile)
register_format(OggSpeexFile)
register_format(OggTheoraFile)
register_format(OggVideoFile)
register_format(OggVorbisFile)
register_format(OptimFROGFile)
register_format(TAKFile)
register_format(TrueAudioFile)
register_format(WAVFile)
register_format(WavPackFile)
