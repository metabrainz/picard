# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006-2007 Lukáš Lalinský
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
# USA.
import os.path
import shutil
import sys
import tempfile
import traceback


from hashlib import md5
from os import fdopen, unlink
from PyQt4.QtCore import QObject
from picard import config, log
from picard.plugin import PluginFunctions, PluginPriority
from picard.similarity import similarity2
from picard.util import (
    encode_filename,
    linear_combination_of_weights,
    mimetype as mime,
    replace_win32_incompat,
)
from picard.util.textencoding import (
    replace_non_ascii,
    unaccent,
)
from picard.mbxml import artist_credit_from_node

MULTI_VALUED_JOINER = '; '


def save_this_image_to_tags(image):
    if not config.setting["save_only_front_images_to_tags"]:
        return True
    return image.is_front


class Image(object):

    """Wrapper around images. Instantiating an object of this class can raise
    an IOError or OSError due to the usage of tempfiles underneath.
    """

    def __init__(self, data, mimetype="image/jpeg", types=[u"front"],
                 comment="", filename=None, datahash="", is_front=True):
        self.description = comment
        (fd, self._tempfile_filename) = tempfile.mkstemp(prefix="picard")
        with fdopen(fd, "wb") as imagefile:
            imagefile.write(data)
            log.debug("Saving image (hash=%s) to %r" % (datahash,
                                                        self._tempfile_filename))
        self.datalength = len(data)
        self.extension = mime.get_extension(mime, ".jpg")
        self.filename = filename
        self.types = types
        self.is_front = is_front
        self.mimetype = mimetype

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
        if self.filename is not None:
            log.debug("Using the custom file name %s", self.filename)
            filename = self.filename
        elif config.setting["caa_image_type_as_filename"]:
            filename = self.maintype()
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
            shutil.copyfile(self._tempfile_filename, new_filename)

    @property
    def data(self):
        """Reads the data from the temporary file created for this image. May
        raise IOErrors or OSErrors.
        """
        with open(self._tempfile_filename, "rb") as imagefile:
            return imagefile.read()

    def _delete(self):
        log.debug("Unlinking %s", self._tempfile_filename)
        try:
            unlink(self._tempfile_filename)
        except OSError as e:
            log.error(traceback.format_exc())


class Metadata(dict):

    """List of metadata items with dict-like access."""

    __weights = [
        ('title', 22),
        ('artist', 6),
        ('album', 12),
        ('tracknumber', 6),
        ('totaltracks', 5),
    ]

    multi_valued_joiner = MULTI_VALUED_JOINER

    def __init__(self):
        super(Metadata, self).__init__()
        self.images = []
        self.length = 0

    def make_and_add_image(self, mime, data, filename=None, comment="",
                           types=[u"front"], is_front=True):
        """Build a new image object from ``data`` and adds it to this Metadata
        object. If an image with the same MD5 hash has already been added to
        any Metadata object, that file will be reused.

        Arguments:
        mime -- The mimetype of the image
        data -- The image data
        filename -- The image filename, without an extension
        comment -- image description or comment, default to ''
        types -- list of types, default to [u'front']
        is_front -- mark image as front image
        """
        m = md5()
        m.update(data)
        # ensure we have no hash conflict, even if data is the same
        # ie. CAA can have the same image uploaded twice with different types
        for p in (mime, filename, comment, types, is_front):
            m.update(repr(p))
        datahash = m.hexdigest()
        QObject.tagger.images.lock()
        image = QObject.tagger.images[datahash]
        if image is None:
            image = Image(data, mime, types, comment, filename,
                          datahash=datahash,
                          is_front=is_front)
            QObject.tagger.images[datahash] = image
        QObject.tagger.images.unlock()
        self.images.append(image)

    def remove_image(self, index):
        self.images.pop(index)

    def compare(self, other):
        parts = []

        if self.length and other.length:
            score = 1.0 - min(abs(self.length - other.length), 30000) / 30000.0
            parts.append((score, 8))

        for name, weight in self.__weights:
            a = self[name]
            b = other[name]
            if a and b:
                if name in ('tracknumber', 'totaltracks'):
                    try:
                        ia = int(a)
                        ib = int(b)
                    except ValueError:
                        ia = a
                        ib = b
                    score = 1.0 - abs(cmp(ia, ib))
                else:
                    score = similarity2(a, b)
                parts.append((score, weight))

        return linear_combination_of_weights(parts)

    def compare_to_release(self, release, weights):
        """
        Compare metadata to a MusicBrainz release. Produces a probability as a
        linear combination of weights that the metadata matches a certain album.
        """
        parts = self.compare_to_release_parts(release, weights)
        return (linear_combination_of_weights(parts), release)

    def compare_to_release_parts(self, release, weights):
        parts = []

        if "album" in self:
            b = release.title[0].text
            parts.append((similarity2(self["album"], b), weights["album"]))

        if "albumartist" in self and "albumartist" in weights:
            a = self["albumartist"]
            b = artist_credit_from_node(release.artist_credit[0])[0]
            parts.append((similarity2(a, b), weights["albumartist"]))

        if "totaltracks" in self:
            a = int(self["totaltracks"])
            if "title" in weights:
                b = int(release.medium_list[0].medium[0].track_list[0].count)
            else:
                b = int(release.medium_list[0].track_count[0].text)
            score = 0.0 if a > b else 0.3 if a < b else 1.0
            parts.append((score, weights["totaltracks"]))

        preferred_countries = config.setting["preferred_release_countries"]
        preferred_formats = config.setting["preferred_release_formats"]

        total_countries = len(preferred_countries)
        if total_countries:
            score = 0.0
            if "country" in release.children:
                try:
                    i = preferred_countries.index(release.country[0].text)
                    score = float(total_countries - i) / float(total_countries)
                except ValueError:
                    pass
            parts.append((score, weights["releasecountry"]))

        total_formats = len(preferred_formats)
        if total_formats:
            score = 0.0
            subtotal = 0
            for medium in release.medium_list[0].medium:
                if "format" in medium.children:
                    try:
                        i = preferred_formats.index(medium.format[0].text)
                        score += float(total_formats - i) / float(total_formats)
                    except ValueError:
                        pass
                    subtotal += 1
            if subtotal > 0:
                score /= subtotal
            parts.append((score, weights["format"]))

        if "releasetype" in weights:
            type_scores = dict(config.setting["release_type_scores"])
            if 'release_group' in release.children and 'type' in release.release_group[0].attribs:
                release_type = release.release_group[0].type
                score = type_scores.get(release_type, type_scores.get('Other', 0.5))
            else:
                score = 0.0
            parts.append((score, weights["releasetype"]))

        rg = QObject.tagger.get_release_group_by_id(release.release_group[0].id)
        if release.id in rg.loaded_albums:
            parts.append((1.0, 6))

        return parts

    def compare_to_track(self, track, weights):
        parts = []

        if 'title' in self:
            a = self['title']
            b = track.title[0].text
            parts.append((similarity2(a, b), weights["title"]))

        if 'artist' in self:
            a = self['artist']
            b = artist_credit_from_node(track.artist_credit[0])[0]
            parts.append((similarity2(a, b), weights["artist"]))

        a = self.length
        if a > 0 and 'length' in track.children:
            b = int(track.length[0].text)
            score = 1.0 - min(abs(a - b), 30000) / 30000.0
            parts.append((score, weights["length"]))

        releases = []
        if "release_list" in track.children and "release" in track.release_list[0].children:
            releases = track.release_list[0].release

        if not releases:
            sim = linear_combination_of_weights(parts)
            return (sim, None, None, track)

        result = (-1,)
        for release in releases:
            release_parts = self.compare_to_release_parts(release, weights)
            sim = linear_combination_of_weights(parts + release_parts)
            if sim > result[0]:
                rg = release.release_group[0] if "release_group" in release.children else None
                result = (sim, rg, release, track)

        return result

    def copy(self, other):
        self.clear()
        self.update(other)

    def update(self, other):
        for key in other.iterkeys():
            self.set(key, other.getall(key)[:])
        if other.images:
            self.images = other.images[:]
        if other.length:
            self.length = other.length

    def clear(self):
        dict.clear(self)
        self.images = []
        self.length = 0

    def getall(self, name):
        return dict.get(self, name, [])

    def get(self, name, default=None):
        values = dict.get(self, name, None)
        if values:
            return self.multi_valued_joiner.join(values)
        else:
            return default

    def __getitem__(self, name):
        return self.get(name, u'')

    def set(self, name, values):
        dict.__setitem__(self, name, values)

    def __setitem__(self, name, values):
        if not isinstance(values, list):
            values = [values]
        values = filter(None, map(unicode, values))
        if len(values):
            dict.__setitem__(self, name, values)
        else:
            self.pop(name, None)

    def add(self, name, value):
        if value or value == 0:
            self.setdefault(name, []).append(value)

    def add_unique(self, name, value):
        if value not in self.getall(name):
            self.add(name, value)

    def iteritems(self):
        for name, values in dict.iteritems(self):
            for value in values:
                yield name, value

    def items(self):
        """Returns the metadata items.

        >>> m.items()
        [("key1", "value1"), ("key1", "value2"), ("key2", "value3")]
        """
        return list(self.iteritems())

    def rawitems(self):
        """Returns the metadata items.

        >>> m.rawitems()
        [("key1", ["value1", "value2"]), ("key2", ["value3"])]
        """
        return dict.items(self)

    def apply_func(self, func):
        for key, values in self.rawitems():
            if not key.startswith("~"):
                self[key] = map(func, values)

    def strip_whitespace(self):
        """Strip leading/trailing whitespace.

        >>> m = Metadata()
        >>> m["foo"] = "  bar  "
        >>> m["foo"]
        "  bar  "
        >>> m.strip_whitespace()
        >>> m["foo"]
        "bar"
        """
        self.apply_func(lambda s: s.strip())


_album_metadata_processors = PluginFunctions()
_track_metadata_processors = PluginFunctions()


def register_album_metadata_processor(function, priority=PluginPriority.NORMAL):
    """Registers new album-level metadata processor."""
    _album_metadata_processors.register(function.__module__, function, priority)


def register_track_metadata_processor(function, priority=PluginPriority.NORMAL):
    """Registers new track-level metadata processor."""
    _track_metadata_processors.register(function.__module__, function, priority)


def run_album_metadata_processors(tagger, metadata, release):
    _album_metadata_processors.run(tagger, metadata, release)


def run_track_metadata_processors(tagger, metadata, release, track):
    _track_metadata_processors.run(tagger, metadata, track, release)
