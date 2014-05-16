# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Oliver Charles
# Copyright (C) 2007-2011 Philipp Wolfer
# Copyright (C) 2007, 2010, 2011 Lukáš Lalinský
# Copyright (C) 2011 Michael Wiencek
# Copyright (C) 2011-2012 Wieland Hoffmann
# Copyright (C) 2013-2014 Laurent Monin
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
import os.path
import shutil
import sys
import tempfile
import traceback

from collections import defaultdict
from functools import partial
from hashlib import md5
from os import fdopen, unlink
from PyQt4.QtCore import QUrl, QObject, QMutex
from picard import config, log
from picard.util import (
    encode_filename,
    replace_win32_incompat,
    imageinfo
)
from picard.util.textencoding import (
    replace_non_ascii,
    unaccent,
)


datafiles = defaultdict(lambda: None)
datafile_mutex = QMutex(QMutex.Recursive)


def get_filename_from_hash(datahash):
    datafile_mutex.lock()
    filename = datafiles[datahash]
    datafile_mutex.unlock()
    return filename


def set_filename_for_hash(datahash, filename):
    datafile_mutex.lock()
    datafiles[datahash] = filename
    datafile_mutex.unlock()


def delete_file_for_hash(datahash):
    filename = get_filename_from_hash(datahash)
    if filename is None:
        return
    try:
        os.unlink(filename)
    except:
        pass
    datafile_mutex.lock()
    del datafiles[datahash]
    datafile_mutex.unlock()


def store_data_for_hash(datahash, data, prefix='picard', suffix=''):
    filename = get_filename_from_hash(datahash)
    if filename is not None:
        return filename
    (fd, filename) = tempfile.mkstemp(prefix=prefix, suffix=suffix)
    QObject.tagger.register_cleanup(partial(delete_file_for_hash, datahash))
    with fdopen(fd, "wb") as imagefile:
        imagefile.write(data)
        set_filename_for_hash(datahash, filename)


def get_data_for_hash(datahash):
    filename = get_filename_from_hash(datahash)
    if filename is None:
        return None
    with open(filename, "rb") as imagefile:
        return imagefile.read()


class CoverArtImage:

    support_types = False
    # consider all images as front if types aren't supported by provider
    is_front = True
    sourceprefix = "URL"

    def __init__(self, url=None, types=[u'front'], comment='',
                 data=None):
        if url is not None:
            self.parse_url(url)
        else:
            self.url = None
        self.types = types
        self.comment = comment
        self.datahash = None
        if data is not None:
            self.set_data(data)

    def parse_url(self, url):
        self.url = QUrl(url)
        self.host = str(self.url.host())
        self.port = self.url.port(80)
        self.path = str(self.url.encodedPath())
        if self.url.hasQuery():
            self.path += '?' + str(self.url.encodedQuery())

    @property
    def source(self):
        if self.url is not None:
            return u"%s: %s" % (self.sourceprefix, self.url.toString())
        else:
            return u"%s" % self.sourceprefix

    def is_front_image(self):
        # CAA has a flag for "front" image, use it in priority
        if self.is_front:
            return True
        # no caa front flag, use type instead
        return u'front' in self.types

    def __repr__(self):
        p = []
        if self.url is not None:
            p.append("url=%r" % self.url.toString())
        p.append("types=%r" % self.types)
        if self.comment:
            p.append("comment=%r" % self.comment)
        return "%s(%s)" % (self.__class__.__name__, ", ".join(p))

    def __unicode__(self):
        p = [u'Image']
        if self.url is not None:
            p.append(u"from %s" % self.url.toString())
        p.append(u"of type %s" % u','.join(self.types))
        if self.comment:
            p.append(u"and comment '%s'" % self.comment)
        return u' '.join(p)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def set_data(self, data, filename=None):
        """Store image data in a file, if data already exists in such file
           it will be re-used and no file write occurs
           A reference counter is handling case where more than one
           cover art image are using the same data.
        """
        (self.width, self.height, self.mimetype, self.extension,
         self.datalength) = imageinfo.identify(data)
        self.filename = filename
        m = md5()
        m.update(data)
        self.datahash = m.hexdigest()
        store_data_for_hash(self.datahash, data, suffix=self.extension)

    @property
    def maintype(self):
        return self.types[0]

    def _make_image_filename(self, filename, dirname, metadata):
        if config.setting["ascii_filenames"]:
            if isinstance(filename, unicode):
                filename = unaccent(filename)
            filename = replace_non_ascii(filename)
        if not filename:
            filename = "cover"
        if not os.path.isabs(filename):
            filename = os.path.join(dirname, filename)
        # replace incompatible characters
        if config.setting["windows_compatibility"] or sys.platform == "win32":
            filename = replace_win32_incompat(filename)
        # remove null characters
        filename = filename.replace("\x00", "")
        return encode_filename(filename)

    def save(self, dirname, metadata, counters):
        """Saves this image.

        :dirname: The name of the directory that contains the audio file
        :metadata: A metadata object
        :counters: A dictionary mapping filenames to the amount of how many
                    images with that filename were already saved in `dirname`.
        """
        assert(self.tempfile_filename is not None)
        if self.filename is not None:
            log.debug("Using the custom file name %s", self.filename)
            filename = self.filename
        elif config.setting["caa_image_type_as_filename"]:
            filename = self.maintype
            log.debug("Make filename from types: %r -> %r", self.types, filename)
        else:
            log.debug("Using default file name %s",
                      config.setting["cover_image_filename"])
            filename = config.setting["cover_image_filename"]
        filename = self._make_image_filename(filename, dirname, metadata)

        overwrite = config.setting["save_images_overwrite"]
        ext = self.extension
        image_filename = filename
        if counters[filename] > 0:
            image_filename = "%s (%d)" % (filename, counters[filename])
        counters[filename] = counters[filename] + 1
        while os.path.exists(image_filename + ext) and not overwrite:
            if os.path.getsize(image_filename + ext) == self.datalength:
                log.debug("Identical file size, not saving %r", image_filename)
                break
            image_filename = "%s (%d)" % (filename, counters[filename])
            counters[filename] = counters[filename] + 1
        else:
            new_filename = image_filename + ext
            # Even if overwrite is enabled we don't need to write the same
            # image multiple times
            if (os.path.exists(new_filename) and
                    os.path.getsize(new_filename) == self.datalength):
                    log.debug("Identical file size, not saving %r", image_filename)
                    return
            log.debug("Saving cover images to %r", image_filename)
            new_dirname = os.path.dirname(image_filename)
            if not os.path.isdir(new_dirname):
                os.makedirs(new_dirname)
            shutil.copyfile(self.tempfile_filename, new_filename)

    @property
    def data(self):
        """Reads the data from the temporary file created for this image. May
        raise IOErrors or OSErrors.
        """
        return get_data_for_hash(self.datahash)

    @property
    def tempfile_filename(self):
        return get_filename_from_hash(self.datahash)

class CaaCoverArtImage(CoverArtImage):

    is_front = False
    support_types = True
    sourceprefix = u"CAA"


class TagCoverArtImage(CoverArtImage):

    def __init__(self, file, tag=None, types=[u'front'], is_front=True,
                 support_types=False, comment='', data=None):
        CoverArtImage.__init__(self, url=None, types=types, comment=comment,
                               data=data)
        self.sourcefile = file
        self.tag = tag
        self.is_front = is_front
        self.support_types = support_types

    @property
    def source(self):
       return u'Tag %s from %s' % (self.tag if self.tag else '', self.sourcefile)
