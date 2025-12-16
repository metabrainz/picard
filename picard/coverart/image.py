# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007 Oliver Charles
# Copyright (C) 2007, 2010-2011 Lukáš Lalinský
# Copyright (C) 2007-2011, 2014, 2018-2024 Philipp Wolfer
# Copyright (C) 2011 Michael Wiencek
# Copyright (C) 2011-2012, 2015 Wieland Hoffmann
# Copyright (C) 2013-2015, 2018-2024 Laurent Monin
# Copyright (C) 2016 Ville Skyttä
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Antonio Larrosa
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2024 Giorgio Fontanive
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


from hashlib import blake2b
import os
import shutil
import tempfile

from PyQt6.QtCore import (
    QCoreApplication,
    QMutex,
    QUrl,
)

from picard import log
from picard.config import get_config
from picard.const.defaults import DEFAULT_COVER_IMAGE_FILENAME
from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)
from picard.coverart.utils import (
    TYPES_SEPARATOR,
    Id3ImageType,
    image_type_as_id3_num,
    translated_types_as_string,
)
from picard.metadata import Metadata
from picard.util import (
    decode_filename,
    encode_filename,
    imageinfo,
    is_absolute_path,
    periodictouch,
    sanitize_filename,
)
from picard.util.filenaming import (
    make_save_path,
    make_short_filename,
)
from picard.util.scripttofilename import script_to_filename


_datafiles = dict()
_datafile_mutex = QMutex()


class DataHash:
    def __init__(self, data: bytes, prefix='picard', suffix=''):
        self._filename: str | None = None
        _datafile_mutex.lock()
        try:
            self._hash = blake2b(data).hexdigest()
            if self._hash not in _datafiles:
                # store tmp file path in  _datafiles[self._hash] ASAP
                (fd, _datafiles[self._hash]) = tempfile.mkstemp(prefix=prefix, suffix=suffix)
                filepath = _datafiles[self._hash]
                tagger = QCoreApplication.instance()
                tagger.register_cleanup(self.delete_file)
                periodictouch.register_file(filepath)
                with os.fdopen(fd, 'wb') as imagefile:
                    imagefile.write(data)
                log.debug("Saving image data %s to %r", self._hash[:16], filepath)
            self._filename = _datafiles[self._hash]
        finally:
            _datafile_mutex.unlock()

    def __eq__(self, other):
        return self._hash == other._hash

    def __lt__(self, other):
        return self._hash < other._hash

    def hash(self):
        return self._hash

    def delete_file(self):
        if not self._hash or self._hash not in _datafiles:
            return

        _datafile_mutex.lock()
        try:
            filepath = _datafiles[self._hash]
            try:
                os.unlink(filepath)
                periodictouch.unregister_file(filepath)
            except BaseException as e:
                log.debug("Failed to delete file %r: %s", filepath, e)

            del _datafiles[self._hash]
        except KeyError:
            log.error("Hash %s not found in cache for file: %r", self._hash[:16], self._filename)
        finally:
            self._hash = None
            self._filename = None
            _datafile_mutex.unlock()

    @property
    def data(self):
        if self._filename:
            with open(self._filename, 'rb') as imagefile:
                return imagefile.read()
        return None

    @property
    def filename(self):
        return self._filename


class CoverArtImageError(Exception):
    pass


class CoverArtImageIOError(CoverArtImageError):
    pass


class CoverArtImageIdentificationError(CoverArtImageError):
    pass


class CoverArtImage:
    # Indicate if types are provided by the source, ie. CAA or certain file
    # formats may have types associated with cover art, but some other sources
    # don't provide such information
    support_types = False
    # Indicates that the source supports multiple types per image.
    support_multi_types = False
    # `is_front` has to be explicitly set, it is used to handle CAA is_front
    # indicator
    is_front: bool | None = None
    sourceprefix: str = 'URL'

    def __init__(
        self,
        url=None,
        types: list[str] | None = None,
        comment: str = '',
        data: bytes | None = None,
        support_types: bool | None = None,
        support_multi_types: bool | None = None,
        id3_type: Id3ImageType | None = None,
    ):
        if types is None:
            self.types = []
        else:
            self.types = types
        if url is not None:
            if not isinstance(url, QUrl):
                self.url = QUrl(url)
            else:
                self.url = url
        else:
            self.url = None
        self.comment = comment
        self.datahash = None
        # thumbnail is used to link to another CoverArtImage, ie. for PDFs
        self.thumbnail = None
        self.external_file_coverart = None
        self.can_be_saved_to_tags = True
        self.can_be_saved_to_disk = True
        self.can_be_saved_to_metadata = True
        self.can_be_filtered = True
        self.can_be_processed = True
        if support_types is not None:
            self.support_types = support_types
        if support_multi_types is not None:
            self.support_multi_types = support_multi_types
        if data is not None:
            self.set_tags_data(data)
        try:
            self.id3_type = id3_type
        except ValueError:
            log.warning("Invalid ID3 image type %r in %r", type, self)
            self.id3_type = Id3ImageType.OTHER

    @property
    def source(self):
        if self.url is not None:
            return "%s: %s" % (self.sourceprefix, self.url.toString())
        else:
            return "%s" % self.sourceprefix

    def is_front_image(self):
        """Indicates if image is considered as a 'front' image.
        It depends on few things:
            - if `is_front` was set, it is used over anything else
            - if `types` was set, search for 'front' in it
            - if `support_types` is False, default to True for any image
            - if `support_types` is True, default to False for any image
        """
        if not self.can_be_saved_to_metadata:
            # ignore thumbnails
            return False
        if self.is_front is not None:
            return self.is_front
        if 'front' in self.types:
            return True
        return self.support_types is False

    def imageinfo_as_string(self):
        if self.datahash is None:
            return ""
        return "w=%d h=%d mime=%s ext=%s datalen=%d file=%s" % (
            self.width,
            self.height,
            self.mimetype,
            self.extension,
            self.datalength,
            self.tempfile_filename,
        )

    def dimensions_as_string(self):
        if self.datahash is None:
            return ""
        return f"{self.width}x{self.height}"

    def _repr(self):
        if self.url is not None:
            yield "url=%r" % self.url.toString()
        if self.types:
            yield "types=%r" % self.types
        yield 'support_types=%r' % self.support_types
        yield 'support_multi_types=%r' % self.support_multi_types
        if self.is_front is not None:
            yield "is_front=%r" % self.is_front
        if self.comment:
            yield "comment=%r" % self.comment

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, ", ".join(self._repr()))

    def _str(self):
        if self.url is not None:
            yield "from %s" % self.url.toString()
        if self.types:
            yield "of type %s" % ','.join(self.types)
        if self.comment:
            yield "and comment '%s'" % self.comment

    def __str__(self):
        output = self.__class__.__name__
        s = tuple(self._str())
        if s:
            output += ' ' + ' '.join(s)
        return output

    def __eq__(self, other):
        if self and other:
            if self.support_types and other.support_types:
                if self.support_multi_types and other.support_multi_types:
                    return (self.datahash, self.types) == (other.datahash, other.types)
                else:
                    return (self.datahash, self.maintype) == (other.datahash, other.maintype)
            else:
                return self.datahash == other.datahash
        return not self and not other

    def __lt__(self, other):
        """Try to provide constant ordering"""
        stypes = self.normalized_types()
        otypes = other.normalized_types()
        if stypes != otypes:
            sfront = self.is_front_image()
            ofront = other.is_front_image()
            if sfront != ofront:
                # front image first
                ret = sfront
            else:
                # lower number of types first
                # '-' == unknown type always last
                ret = stypes < otypes or '-' in otypes
        elif self.comment != other.comment:
            # shortest comment first, alphabetical
            scomment = self.comment or ''
            ocomment = other.comment or ''
            ret = scomment < ocomment
        else:
            # arbitrary order based on data, but should be constant
            ret = self.datahash < other.datahash
        return ret

    def __hash__(self):
        if self.datahash is None:
            return 0
        return hash(self.datahash.hash())

    def set_tags_data(self, data: bytes):
        """Store image data in a file, if data already exists in such file
        it will be re-used and no file write occurs
        """
        if self.datahash:
            self.datahash.delete_file()
            self.datahash = None

        try:
            info = imageinfo.identify(data)
            self.width, self.height = info.width, info.height
            self.mimetype = info.mime
            self.extension = info.extension
            self.datalength = info.datalen
        except imageinfo.IdentificationError as e:
            raise CoverArtImageIdentificationError(e) from e

        try:
            self.datahash = DataHash(data, suffix=self.extension)
        except OSError as e:
            raise CoverArtImageIOError(e) from e

    def set_external_file_data(self, data: bytes):
        self.external_file_coverart = CoverArtImage(data=data, url=self.url)

    @property
    def maintype(self):
        """Returns one type only, even for images having more than one type set.
        This is mostly used when saving cover art to tags because most formats
        don't support multiple types for one image.
        Images coming from CAA can have multiple types (ie. 'front, booklet').
        """
        if self.is_front_image() or not self.types or 'front' in self.types:
            return 'front'
        # TODO: do something better than randomly using the first in the list
        return self.types[0]

    @property
    def id3_type(self) -> Id3ImageType:
        """Returns the ID3 APIC image type.
        If explicitly set the type is returned as is, otherwise it is derived
        from `maintype`. See http://www.id3.org/id3v2.4.0-frames"""
        if self._id3_type is not None:
            return self._id3_type
        else:
            return image_type_as_id3_num(self.maintype)

    @id3_type.setter
    def id3_type(self, type: Id3ImageType | None):
        """Explicitly sets the ID3 APIC image type.
        If set to None the type will be derived from `maintype`."""
        if type is not None:
            type = Id3ImageType(type)
        self._id3_type = type

    def _make_image_filename(self, filename, dirname, _metadata, win_compat, win_shorten_path):
        metadata = Metadata()
        metadata.copy(_metadata)
        metadata['coverart_maintype'] = self.maintype
        metadata['coverart_comment'] = self.comment
        if self.is_front:
            metadata.add_unique('coverart_types', 'front')
        for cover_type in self.types:
            metadata.add_unique('coverart_types', cover_type)
        filename = script_to_filename(filename, metadata)
        if not filename:
            filename = DEFAULT_COVER_IMAGE_FILENAME
        dirname = os.path.normpath(dirname)
        if not is_absolute_path(filename):
            filename = os.path.normpath(os.path.join(dirname, filename))
        try:
            basedir = os.path.commonpath((dirname, os.path.dirname(filename)))
            relpath = os.path.relpath(filename, start=basedir)
        except ValueError:
            basedir = os.path.dirname(filename)
            relpath = os.path.basename(filename)
        relpath = make_short_filename(basedir, relpath, win_shorten_path=win_shorten_path)
        filename = os.path.join(basedir, relpath)
        filename = make_save_path(filename, win_compat=win_compat, mac_compat=IS_MACOS)
        return encode_filename(filename)

    def save(self, dirname: str, metadata: Metadata, counters: dict[str, int]):
        """Saves this image.

        :dirname: The name of the directory that contains the audio file
        :metadata: A metadata object
        :counters: A dictionary mapping filenames to the amount of how many
                    images with that filename were already saved in `dirname`.
        """
        if self.external_file_coverart is not None:
            self.external_file_coverart.save(dirname, metadata, counters)
            return
        if not self.can_be_saved_to_disk:
            return
        config = get_config()
        win_compat = IS_WIN or config.setting['windows_compatibility']
        win_shorten_path = win_compat and not config.setting['windows_long_paths']
        if config.setting['image_type_as_filename'] and not self.is_front_image():
            filename = sanitize_filename(self.maintype, win_compat=win_compat)
            log.debug("Make cover filename from types: %r -> %r", self.types, filename)
        else:
            filename = config.setting['cover_image_filename']
            log.debug("Using default cover image filename %r", filename)
        filename = self._make_image_filename(filename, dirname, metadata, win_compat, win_shorten_path)

        overwrite = config.setting['save_images_overwrite']
        ext = encode_filename(self.extension)
        image_filename = self._next_filename(filename, counters)
        while os.path.exists(image_filename + ext) and not overwrite:
            if not self._is_write_needed(image_filename + ext):
                break
            image_filename = self._next_filename(filename, counters)
        else:
            new_filename = image_filename + ext
            # Even if overwrite is enabled we don't need to write the same
            # image multiple times
            if not self._is_write_needed(new_filename):
                return
            log.debug("Saving cover image to %r", new_filename)
            try:
                new_dirname = os.path.dirname(new_filename)
                if not os.path.isdir(new_dirname):
                    os.makedirs(new_dirname)
                shutil.copyfile(self.tempfile_filename, new_filename)
            except OSError as e:
                raise CoverArtImageIOError(e) from e

    @staticmethod
    def _next_filename(filename, counters):
        if counters[filename]:
            new_filename = "%s (%d)" % (decode_filename(filename), counters[filename])
        else:
            new_filename = filename
        counters[filename] += 1
        return encode_filename(new_filename)

    def _is_write_needed(self, filename):
        if os.path.exists(filename) and os.path.getsize(filename) == self.datalength:
            log.debug("Identical file size, not saving %r", filename)
            return False
        return True

    @property
    def data(self):
        """Reads the data from the temporary file created for this image.
        May raise CoverArtImageIOError
        """
        try:
            return self.datahash.data
        except OSError as e:
            raise CoverArtImageIOError(e) from e

    @property
    def tempfile_filename(self) -> str | None:
        if self.datahash:
            return self.datahash.filename

    def normalized_types(self):
        if self.types and self.support_types:
            # ensure front type is first, if any
            # the rest is sorted
            types_front = ['front'] if 'front' in self.types else []
            types_without_front = sorted(set(t for t in self.types if t != 'front'))
            types = types_front + types_without_front
        elif self.is_front_image():
            types = ['front']
        else:
            types = ['-']
        return tuple(types)

    def types_as_string(self, translate=True, separator: str = TYPES_SEPARATOR):
        types = self.normalized_types()
        if translate:
            return translated_types_as_string(types, separator)
        else:
            return separator.join(types)


class CaaCoverArtImage(CoverArtImage):
    """Image from Cover Art Archive"""

    support_types = True
    support_multi_types = True
    sourceprefix = 'CAA'

    def __init__(self, url, types=None, is_front=False, comment='', data=None):
        super().__init__(url=url, types=types, comment=comment, data=data)
        self.is_front = is_front


class CaaThumbnailCoverArtImage(CaaCoverArtImage):
    """Used for thumbnails of CaaCoverArtImage objects, together with thumbnail
    property"""

    def __init__(self, url, types=None, is_front=False, comment='', data=None):
        super().__init__(url=url, types=types, comment=comment, data=data)
        self.is_front = False
        self.can_be_saved_to_disk = False
        self.can_be_saved_to_tags = False
        self.can_be_saved_to_metadata = False
        self.can_be_filtered = False
        self.can_be_processed = False


class TagCoverArtImage(CoverArtImage):
    """Image from file tags"""

    def __init__(
        self,
        file,
        tag=None,
        types=None,
        is_front=None,
        support_types=False,
        comment='',
        data=None,
        support_multi_types=False,
        id3_type=None,
    ):
        self.sourcefile = file
        self.tag = tag
        super().__init__(url=None, types=types, comment=comment, data=data, id3_type=id3_type)
        self.support_types = support_types
        self.support_multi_types = support_multi_types
        if is_front is not None:
            self.is_front = is_front

    @property
    def source(self):
        if self.tag:
            return 'Tag %s from %s' % (self.tag, self.sourcefile)
        else:
            return 'File %s' % (self.sourcefile)

    def _repr(self):
        yield '%r' % self.sourcefile
        if self.tag is not None:
            yield 'tag=%r' % self.tag
        yield from super()._repr()

    def _str(self):
        yield 'from %r' % self.sourcefile
        yield from super()._str()


class LocalFileCoverArtImage(CoverArtImage):
    sourceprefix = 'LOCAL'

    def __init__(self, filepath, types=None, comment='', support_types=False, support_multi_types=False):
        url = QUrl.fromLocalFile(filepath).toString()
        super().__init__(url=url, types=types, comment=comment)
        self.support_types = support_types
        self.support_multi_types = support_multi_types
