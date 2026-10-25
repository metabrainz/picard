# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2012-2013, 2017 Wieland Hoffmann
# Copyright (C) 2013 Michael Wiencek
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2018, 2020-2021, 2023-2025 Laurent Monin
# Copyright (C) 2018-2022, 2024-2026 Philipp Wolfer
# Copyright (C) 2024 Suryansh Shakya
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from collections.abc import MutableMapping
import os
import struct

import mutagen
from mutagen import version as mutagen_version
from mutagen._iff import assert_valid_chunk_id
from mutagen._riff import RiffFile
from mutagen._util import loadfile
import mutagen.wave

from picard import log
from picard.config import get_config
from picard.formats.id3 import NonCompatID3File


# ---------------------------------------------------------------------------
# BEGIN mutagen workaround (PICARD-3519)
#
# Some tools (e.g. streaming encoders or converters that write WAV data to a
# pipe) store a placeholder size such as 0xFFFFFFFF in the RIFF root chunk
# and/or the ``data`` chunk header because the final size is not known while
# writing. mutagen mishandles these oversized sizes in two ways:
#
#   * WaveStreamInfo derives the audio length from the *declared* ``data`` chunk
#     size, so the reported length is wildly inflated.
#   * Saving tags raises ``struct.error: 'I' format requires
#     0 <= number <= 4294967295`` because mutagen adds the inserted ID3 chunk
#     size to the already maxed-out root RIFF size.
#
# Both are mutagen defects. This whole section is a temporary workaround; once a
# fixed mutagen is released and required, set MUTAGEN_RIFF_FIXED_VERSION to that
# version. The workaround then becomes a no-op on fixed installs, and the entire
# block (plus its two one-line call sites marked "mutagen workaround" in
# WAVFile) can be deleted wholesale.
#
# Upstream issue: https://github.com/quodlibet/mutagen/issues/654 (open)
# ---------------------------------------------------------------------------

# Set to the first mutagen version that fixes the RIFF size handling once known.
# ``None`` means "not fixed in any released version yet", so the workaround
# always runs.
MUTAGEN_RIFF_FIXED_VERSION = None


def _mutagen_needs_riff_workaround():
    """True while the running mutagen still has the RIFF size defects."""
    if MUTAGEN_RIFF_FIXED_VERSION is None:
        return True
    return mutagen_version < MUTAGEN_RIFF_FIXED_VERSION


def _iter_wav_chunks(fileobj, file_size):
    """Yield ``(offset, chunk_id, declared_size, max_size)`` for the RIFF root
    chunk and each of its top-level subchunks.

    ``declared_size`` is the size stored in the chunk header, ``max_size`` is the
    largest size that still fits inside the file after the chunk's 8 byte header.
    A valid chunk size never exceeds ``max_size``; anything larger is bogus.
    Yields nothing if the file is not a RIFF file.
    """
    fileobj.seek(0)
    if fileobj.read(4) != b'RIFF':
        return
    pos = 0
    while pos + 8 <= file_size:
        fileobj.seek(pos + 4)
        declared_size = struct.unpack('<I', fileobj.read(4))[0]
        max_size = file_size - (pos + 8)
        chunk_id = b'RIFF' if pos == 0 else None
        if chunk_id is None:
            fileobj.seek(pos)
            chunk_id = fileobj.read(4)
        yield pos, chunk_id, declared_size, max_size
        size = min(declared_size, max_size)
        # The root RIFF chunk contains the subchunks, so descend into it:
        # its payload starts with the 4 byte "WAVE" form type at offset 8.
        pos = 12 if pos == 0 else pos + 8 + size + (size & 1)


def repair_wav_chunk_sizes(filename):
    """Clamp oversized RIFF/WAVE chunk sizes in-place to fit the actual file.

    See the "mutagen workaround (PICARD-3519)" banner above. Any chunk size
    larger than the bytes remaining in the file is clamped. Well-formed files
    (and files read by a fixed mutagen) are left untouched.
    """
    if not _mutagen_needs_riff_workaround():
        return
    file_size = os.path.getsize(filename)
    with open(filename, 'r+b') as fileobj:
        for offset, chunk_id, declared_size, max_size in _iter_wav_chunks(fileobj, file_size):
            if declared_size > max_size:
                fileobj.seek(offset + 4)
                fileobj.write(struct.pack('<I', max_size))
                log.warning(
                    "Repairing invalid WAV %s chunk size in %r: %d -> %d",
                    chunk_id.decode('ascii', 'replace').rstrip(),
                    filename,
                    declared_size,
                    max_size,
                )


def correct_inflated_wav_length(metadata, filename):
    """Rescale an inflated ``metadata.length`` to match the real ``data`` size.

    See the "mutagen workaround (PICARD-3519)" banner above. Read-only: this
    never modifies the file. No-op on well-formed files and on a fixed mutagen.
    """
    if not _mutagen_needs_riff_workaround():
        return
    declared_size = actual_size = None
    try:
        file_size = os.path.getsize(filename)
        with open(filename, 'rb') as fileobj:
            for _offset, chunk_id, declared, max_size in _iter_wav_chunks(fileobj, file_size):
                if chunk_id == b'data':
                    declared_size, actual_size = declared, min(declared, max_size)
                    break
    except OSError:
        return
    if declared_size and declared_size > actual_size:
        metadata.length = int(metadata.length * actual_size / declared_size)


# END mutagen workaround (PICARD-3519)
# ---------------------------------------------------------------------------


# See https://exiftool.org/TagNames/RIFF.html
TRANSLATE_RIFF_INFO = {
    # Minimal, as e.g. supported by Windows Explorer,
    # Audacity and foobar2000
    'IART': 'artist',
    'ICMT': 'comment',
    'ICOP': 'copyright',
    'ICRD': 'date',
    'IGNR': 'genre',
    'INAM': 'title',
    'IPRD': 'album',
    'ITRK': 'tracknumber',
    # Extended, not well supported by other tools
    'ICNT': 'releasecountry',
    'IENC': 'encodedby',
    'IENG': 'engineer',
    'ILNG': 'language',
    'IMED': 'media',
    'IMUS': 'composer',
    'IPRO': 'producer',
    'IWRI': 'writer',
}

R_TRANSLATE_RIFF_INFO = {v: k for k, v in TRANSLATE_RIFF_INFO.items()}


def translate_tag_to_riff_name(name):
    if name.startswith('comment:'):
        name = 'comment'
    return R_TRANSLATE_RIFF_INFO.get(name, None)


class RiffListInfo(MutableMapping):
    """Allows loading / saving RIFF INFO tags from / to RIFF files."""

    def __init__(self, encoding='windows-1252'):
        self.encoding = encoding
        self.__tags = {}
        self.__deleted_tags = set()

    @loadfile()
    def load(self, filething):
        """Load the INFO tags from the file."""
        riff_file = RiffFile(filething.fileobj)
        info = self.__find_info_chunk(riff_file.root)
        if info:
            for tag in info.subchunks():
                self.__tags[tag.id] = self.__decode_data(tag.read())

    @loadfile(writable=True)
    def save(self, filething):
        """Save the INFO tags to the file."""
        riff_file = RiffFile(filething.fileobj)
        info = self.__find_info_chunk(riff_file.root)
        if not info:
            info = riff_file.insert_chunk('LIST', b'INFO')
        for name, value in self.__tags.items():
            self.__save_tag_data(info, name, value)
        for name in self.__deleted_tags:
            self.__delete_tag(info, name)

    @loadfile(writable=True)
    def delete(self, filething):
        """Deletes the INFO chunk completely from the file."""
        riff_file = RiffFile(filething.fileobj)
        info = self.__find_info_chunk(riff_file.root)
        if info:
            info.delete()

    @staticmethod
    def __find_info_chunk(parent):
        for chunk in parent.subchunks():
            if chunk.id == 'LIST' and chunk.name == 'INFO':
                return chunk
        return None

    @staticmethod
    def __find_subchunk(parent, name):
        for chunk in parent.subchunks():
            if chunk.id == name:
                return chunk
        return None

    def __save_tag_data(self, info, name, value):
        data = self.__encode_data(value)
        chunk = self.__find_subchunk(info, name)
        if chunk:
            chunk.resize(len(data))
            chunk.write(data)
            return chunk
        else:
            return info.insert_chunk(name, data)

    def __delete_tag(self, info, name):
        chunk = self.__find_subchunk(info, name)
        if chunk:
            chunk.delete()

    @staticmethod
    def __decode_data(value):
        try:  # Always try first to decode as Unicode
            value = value.decode('utf-8')
        except UnicodeDecodeError:  # Fall back to Windows-1252 encoding
            value = value.decode('windows-1252', errors='replace')
        return value.rstrip('\0')

    def __encode_data(self, value):
        return value.encode(self.encoding, errors='simplify') + b'\x00'

    def __contains__(self, name):
        return self.__tags.__contains__(name)

    def __getitem__(self, key):
        return self.__tags.get(key)

    def __setitem__(self, key, value):
        assert_valid_chunk_id(key)
        self.__tags[key] = value
        self.__deleted_tags.discard(key)

    def __delitem__(self, key):
        if key in self.__tags:
            del self.__tags[key]
        self.__deleted_tags.add(key)

    def __iter__(self):
        return iter(self.__tags)

    def __len__(self):
        return len(self.__tags)

    def __repr__(self):
        return repr(self.__tags)

    def __str__(self):
        return str(self.__tags)


class WAVFile(NonCompatID3File):
    EXTENSIONS = (".wav",)
    NAME = "Microsoft WAVE"
    _File = mutagen.wave.WAVE

    def _info(self, metadata, file):
        super()._info(metadata, file)
        metadata['~format'] = self.NAME
        correct_inflated_wav_length(metadata, file.filename)  # mutagen workaround (PICARD-3519)
        config = get_config()
        info = RiffListInfo(encoding=config.setting['wave_riff_info_encoding'])
        info.load(file.filename)
        for tag, value in info.items():
            if tag in TRANSLATE_RIFF_INFO:
                name = TRANSLATE_RIFF_INFO[tag]
                if name not in metadata:
                    metadata[name] = value

    def _save(self, filename, metadata):
        repair_wav_chunk_sizes(filename)  # mutagen workaround (PICARD-3519)

        super()._save(filename, metadata)

        # Save RIFF LIST INFO
        config = get_config()
        if config.setting['write_wave_riff_info']:
            info = RiffListInfo(encoding=config.setting['wave_riff_info_encoding'])
            if config.setting['clear_existing_tags']:
                info.delete(filename)
            for name, values in metadata.rawitems():
                name = translate_tag_to_riff_name(name)
                if name:
                    value = ", ".join(values)
                    info[name] = value
            for name in metadata.deleted_tags:
                name = translate_tag_to_riff_name(name)
                if name:
                    del info[name]
            info.save(filename)
        elif config.setting['remove_wave_riff_info']:
            info = RiffListInfo(encoding=config.setting['wave_riff_info_encoding'])
            info.delete(filename)
