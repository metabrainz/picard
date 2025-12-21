# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2009, 2011-2013, 2017 Lukáš Lalinský
# Copyright (C) 2007-2011, 2015, 2018-2024 Philipp Wolfer
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008-2009 Nikolai Prokoschenko
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 David Hilton
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2012 Erik Wasser
# Copyright (C) 2012 Johannes Weißl
# Copyright (C) 2012 noobie
# Copyright (C) 2012-2014 Wieland Hoffmann
# Copyright (C) 2013 Calvin Walton
# Copyright (C) 2013-2014 Ionuț Ciocîrlan
# Copyright (C) 2013-2014, 2017, 2021 Sophist-UK
# Copyright (C) 2013-2014, 2017-2024 Laurent Monin
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016 Ville Skyttä
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017-2018 Antonio Larrosa
# Copyright (C) 2019 Joel Lintunen
# Copyright (C) 2020 Ray Bouchard
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2021 Petit Minion
# Copyright (C) 2021, 2023, 2025 Bob Swift
# Copyright (C) 2024 Giorgio Fontanive
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


from collections import Counter
from enum import (
    Enum,
    auto,
)
import fnmatch
from functools import partial
import os
import os.path
import re
import shutil
import time
from typing import (
    IO,
    TYPE_CHECKING,
)

from mutagen import (
    FileType,
    MutagenError,
)

from picard import (
    PICARD_APP_NAME,
    log,
)
from picard.config import get_config
from picard.const.defaults import DEFAULT_TIME_FORMAT
from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.item import MetadataItem
from picard.metadata import (
    Metadata,
    SimMatchTrack,
)
from picard.plugin import PluginFunctions
from picard.script import get_file_naming_script
from picard.tags import (
    calculated_tag_names,
    file_info_tag_names,
    preserved_tag_names,
)
from picard.tags.preserved import UserPreservedTags
from picard.util import (
    any_exception_isinstance,
    bytes2human,
    decode_filename,
    emptydir,
    encode_filename,
    find_best_match,
    format_time,
    is_absolute_path,
    normpath,
    thread,
    tracknum_and_title_from_filename,
)
from picard.util.filenaming import (
    get_available_filename,
    make_save_path,
    make_short_filename,
    move_ensure_casing,
)
from picard.util.scripttofilename import script_to_filename_with_metadata

from picard.ui.filter import Filter


if TYPE_CHECKING:
    from picard.cluster import Cluster
    from picard.track import Track


FILE_COMPARISON_WEIGHTS = {
    'album': 5,
    'artist': 4,
    'date': 4,
    'format': 2,
    'isvideo': 2,
    'length': 10,
    'releasecountry': 2,
    'releasetype': 14,
    'title': 13,
    'totaltracks': 4,
}


class File(MetadataItem):
    NAME = None
    # Logical tag format key and description for the family of this handler.
    # Subclasses should override for format families (e.g. ID3, Vorbis, APEv2).
    FORMAT_KEY = None
    FORMAT_DESCRIPTION = None
    # Whether date sanitization can be toggled for this format family via settings
    DATE_SANITIZATION_TOGGLEABLE = False

    EXTENSIONS = []

    class State(Enum):
        UNDEFINED = -1
        PENDING = 0
        NORMAL = 1
        CHANGED = 2
        ERROR = 3
        REMOVED = 4

    class LookupType(Enum):
        METADATA = auto()
        ACOUSTID = auto()

    class ErrorType(Enum):
        UNKNOWN = auto()
        NOTFOUND = auto()
        NOACCESS = auto()
        PARSER = auto()

    class PreserveTimesStatError(Exception):
        pass

    class PreserveTimesUtimeError(Exception):
        pass

    # in order to significantly speed up performance, the number of pending
    # files is cached, set @state.setter
    num_pending_files = 0

    def __init__(self, filename: str):
        super().__init__()
        self.filename: str = filename
        self.base_filename: str = os.path.basename(filename)
        self._state = File.State.UNDEFINED
        self.state: File.State = File.State.PENDING
        self.error_type: File.ErrorType = File.ErrorType.UNKNOWN

        self.similarity = 1.0
        self.parent_item: 'Cluster | Track | None' = None

        self._lookup_task = None

        self.acoustid_fingerprint = None
        self.acoustid_length = 0
        self.match_recordingid = None

    def __repr__(self):
        return '<%s %r>' % (type(self).__name__, self.base_filename)

    # pylint: disable=no-self-use
    def format_specific_metadata(self, metadata, tag, settings=None):
        """Can be overridden to customize how a tag is displayed in the UI.
        This is useful if a tag saved to the underlying format will differ from
        the internal representation in a way that would cause data loss. This is e.g.
        the case for some ID3v2.3 tags.

        Args:
            metadata: The metadata object to read the tag from
            tag: Name of the tag
            settings: Dictionary of settings. If not set, config.setting should be used

        Returns:
            An array of values for the tag
        """
        return metadata.getall(tag)

    def _format_specific_copy(self, metadata, settings=None):
        """Creates a copy of metadata, but applies format_specific_metadata() to the values."""
        copy = Metadata(
            deleted_tags=metadata.deleted_tags,
            images=metadata.images,
            length=metadata.length,
        )
        for name in metadata:
            copy[name] = self.format_specific_metadata(metadata, name, settings)
        return copy

    def _set_error(self, error):
        self.state = File.State.ERROR
        if any_exception_isinstance(error, FileNotFoundError):
            self.error_type = File.ErrorType.NOTFOUND
        elif any_exception_isinstance(error, PermissionError):
            self.error_type = File.ErrorType.NOACCESS
        elif any_exception_isinstance(error, MutagenError):
            self.error_type = File.ErrorType.PARSER
            self.error_append(
                _("The file failed to parse, either the file is damaged or has an unsupported file format.")
            )
        else:
            self.error_type = File.ErrorType.UNKNOWN
        self.error_append(str(error))

    def load(self, callback):
        thread.run_task(
            partial(self._load_check, self.filename),
            partial(self._loading_finished, callback),
            priority=1,
        )

    def _load_check(self, filename):
        # Check that file has not been removed since thread was queued
        # Don't load if we are stopping.
        if self.state != File.State.PENDING:
            log.debug("File not loaded because it was removed: %r", self.filename)
            return None
        if self.tagger.stopping:
            log.debug("File not loaded because %s is stopping: %r", PICARD_APP_NAME, self.filename)
            return None
        return self._load(filename)

    def _load(self, filename: str) -> Metadata:
        """Load metadata from the file."""
        raise NotImplementedError

    def _loading_finished(self, callback, result=None, error=None):
        if self.state != File.State.PENDING or self.tagger.stopping:
            return
        config = get_config()
        if error is not None:
            self._set_error(error)

            # If loading failed, force format guessing and try loading again
            try:
                alternative_file = self.tagger.format_registry.guess_format(self.filename)
            except (FileNotFoundError, OSError):
                log.error("Guessing format of %s failed", self.filename, exc_info=True)
                alternative_file = None

            if alternative_file:
                # Do not retry reloading exactly the same file format
                if type(alternative_file) != type(self):  # pylint: disable=unidiomatic-typecheck # noqa: E721
                    log.debug("Loading %r failed, retrying as %r", self, alternative_file)
                    self.remove()
                    alternative_file.load(callback)
                    return
                else:
                    alternative_file.remove()  # cleanup unused File object

            file_name, file_extension = os.path.splitext(self.base_filename)
            if file_extension not in self.tagger.format_registry.supported_extensions():
                log.error("Unsupported media file %r wrongly loaded. Removing …", self)
                callback(self, remove_file=True)
                return
        else:
            self.clear_errors()
            self.state = self.State.NORMAL
            postprocessors = []
            if config.setting['guess_tracknumber_and_title']:
                postprocessors.append(self._guess_tracknumber_and_title)
            self._copy_loaded_metadata(result, postprocessors)
        # use cached fingerprint from file metadata
        if not config.setting['ignore_existing_acoustid_fingerprints']:
            fingerprints = self.metadata.getall('acoustid_fingerprint')
            if fingerprints:
                self.set_acoustid_fingerprint(fingerprints[0])
        run_file_post_load_processors(self)
        callback(self)
        Filter.apply_filters()

    def _copy_loaded_metadata(self, metadata, postprocessors=None):
        metadata['~length'] = format_time(metadata.length)
        if postprocessors:
            for processor in postprocessors:
                processor(metadata)
        self.orig_metadata = metadata
        self.metadata.copy(metadata)

    def _guess_tracknumber_and_title(self, metadata):
        missing = {'tracknumber', 'title'} - set(metadata)
        if missing:
            guessed = tracknum_and_title_from_filename(self.base_filename)
            for m in missing:
                metadata[m] = getattr(guessed, m)

    def _copy_file_info_tags(self, to_metadata, from_metadata):
        for tag in file_info_tag_names():
            to_metadata[tag] = from_metadata[tag]

    def copy_metadata(self, metadata, preserve_deleted=True):
        saved_metadata = {}

        # Keep current value for special tags that got calculated from audio content
        for tag in calculated_tag_names():
            if tag not in metadata.deleted_tags and self.metadata[tag]:
                saved_metadata[tag] = self.metadata[tag]

        # Keep original values of preserved tags
        preserved_tags = UserPreservedTags()
        default_preserved_tags = set(preserved_tag_names())
        for tag, values in self.orig_metadata.rawitems():
            if tag in preserved_tags or tag in default_preserved_tags:
                saved_metadata[tag] = values
        deleted_tags = self.metadata.deleted_tags
        images_changed = self.metadata.images != metadata.images
        self.metadata.copy(metadata)
        self._copy_file_info_tags(metadata, self.orig_metadata)
        if preserve_deleted:
            for tag in deleted_tags:
                del self.metadata[tag]
        self.metadata.update(saved_metadata)

        if images_changed:
            self.metadata_images_changed.emit()

    def keep_original_images(self):
        if self.metadata.images != self.orig_metadata.images:
            self.metadata.images = self.orig_metadata.images.copy()
            self.update(signal=False)
            self.metadata_images_changed.emit()

    def has_error(self):
        return self.state == File.State.ERROR

    def save(self):
        self.set_pending()
        run_file_pre_save_processors(self)
        metadata = Metadata()
        metadata.copy(self.metadata)
        thread.run_task(
            partial(self._save_and_rename, self.filename, metadata),
            self._saving_finished,
            thread_pool=self.tagger.save_thread_pool,
        )

    def _preserve_times(self, filename, func):
        """Save filename times before calling func, and set them again"""
        try:
            # https://docs.python.org/3/library/os.html#os.utime
            # Since Python 3.3, ns parameter is available
            # The best way to preserve exact times is to use the st_atime_ns and st_mtime_ns
            # fields from the os.stat() result object with the ns parameter to utime.
            st = os.stat(filename)
        except OSError as why:
            errmsg = "Couldn't read timestamps from %r: %s" % (filename, why)
            raise self.PreserveTimesStatError(errmsg) from None
            # if we can't read original times, don't call func and let caller handle this
        func()
        try:
            os.utime(filename, ns=(st.st_atime_ns, st.st_mtime_ns))
        except OSError as why:
            errmsg = "Couldn't preserve timestamps for %r: %s" % (filename, why)
            raise self.PreserveTimesUtimeError(errmsg) from None
        return (st.st_atime_ns, st.st_mtime_ns)

    def _save_and_rename(self, old_filename, metadata):
        """Save the metadata."""
        config = get_config()
        # Check that file has not been removed since thread was queued
        # Also don't save if we are stopping.
        if self.state == File.State.REMOVED:
            log.debug("File not saved because it was removed: %r", self.filename)
            return None
        if self.tagger.stopping:
            log.debug("File not saved because %s is stopping: %r", PICARD_APP_NAME, self.filename)
            return None
        new_filename = old_filename
        if config.setting['enable_tag_saving']:
            save = partial(self._save, old_filename, metadata)
            if config.setting['preserve_timestamps']:
                try:
                    self._preserve_times(old_filename, save)
                except self.PreserveTimesUtimeError as why:
                    log.warning(why)
            else:
                save()
        # Rename files
        if config.setting['rename_files'] or config.setting['move_files']:
            new_filename = self._rename(old_filename, metadata, config.setting)
        # Move extra files (images, playlists, etc.)
        self._move_additional_files(old_filename, new_filename, config)
        # Delete empty directories
        if config.setting['delete_empty_dirs']:
            dirname = os.path.dirname(old_filename)
            try:
                emptydir.rm_empty_dir(dirname)
                head, tail = os.path.split(dirname)
                if not tail:
                    head, tail = os.path.split(head)
                while head and tail:
                    emptydir.rm_empty_dir(head)
                    head, tail = os.path.split(head)
            except OSError as why:
                log.warning("Error removing directory: %s", why)
            except emptydir.SkipRemoveDir as why:
                log.debug("Not removing empty directory: %s", why)
        # Save cover art images
        if config.setting['save_images_to_files']:
            self._save_images(os.path.dirname(new_filename), metadata)
        return new_filename

    def _saving_finished(self, result=None, error=None):
        # Handle file removed before save
        # Result is None if save was skipped
        if (self.state == File.State.REMOVED or self.tagger.stopping) and result is None:
            return
        old_filename = new_filename = self.filename
        if error is not None:
            self._set_error(error)
        else:
            self.filename = new_filename = result
            self.base_filename = os.path.basename(new_filename)
            length = self.orig_metadata.length
            temp_info = {}
            self._copy_file_info_tags(temp_info, self.orig_metadata)
            images_changed = self.orig_metadata.images != self.metadata.images
            # Copy new metadata to original metadata, applying format specific
            # conversions (e.g. for ID3v2.3)
            config = get_config()
            new_metadata = self._format_specific_copy(self.metadata, config.setting)
            if config.setting['clear_existing_tags']:
                self.orig_metadata = new_metadata
            else:
                self.orig_metadata.update(new_metadata)
            # After saving deleted tags should no longer be marked deleted
            self.metadata.clear_deleted()
            self.orig_metadata.clear_deleted()
            self.orig_metadata.length = length
            self.orig_metadata['~length'] = format_time(length)
            self.orig_metadata.update(temp_info)
            self.clear_errors()
            self.clear_pending(signal=False)
            self._update_filesystem_metadata(self.orig_metadata)
            if images_changed:
                self.metadata_images_changed.emit()

            # run post save hook
            run_file_post_save_processors(self)

        # Force update to ensure file status icon changes immediately after save
        self.update()

        if self.state != File.State.REMOVED:
            del self.tagger.files[old_filename]
            self.tagger.files[new_filename] = self

        if self.tagger.stopping:
            log.debug("Save of %r completed before stopping Picard", self.filename)

    def _save(self, filename: str, metadata: Metadata) -> None:
        """Save the metadata."""
        raise NotImplementedError

    def _script_to_filename(self, naming_format, file_metadata, file_extension, settings=None):
        if settings is None:
            config = get_config()
            settings = config.setting
        metadata = Metadata()
        if settings['clear_existing_tags']:
            # script_to_filename_with_metadata guarantees this is not modified
            metadata = file_metadata
        else:
            metadata.copy(self.orig_metadata)
            metadata.update(file_metadata)
        (filename, new_metadata) = script_to_filename_with_metadata(
            naming_format, metadata, file=self, settings=settings
        )
        basename = os.path.basename(filename)
        if not basename:
            old_name = os.path.splitext(os.path.basename(self.filename))[0]
            filename = os.path.join(os.path.dirname(filename), old_name)
        # NOTE: the filename generated by the naming script does not have a file extension
        ext = new_metadata.get('~extension', file_extension)
        return filename + '.' + ext.lstrip('.')

    def _fixed_splitext(self, filename):
        # In case the filename is blank and only has the extension
        # the real extension is in new_filename and ext is blank
        new_filename, ext = os.path.splitext(filename)
        if ext == '' and new_filename.lower() in self.EXTENSIONS:
            ext = new_filename
            new_filename = ''
        return new_filename, ext

    def _clean_file_extension(self, filename):
        """Takes a filename and converts the extension to lowercase.

        If the file has no extension a default extension for the format is used.

        Args:
            filename: The filename

        Returns: A tuple containing the filename with fixed extension and the extension itself.
        """
        filename, ext = self._fixed_splitext(filename)
        if not ext and self.EXTENSIONS:
            ext = self.EXTENSIONS[0]
        ext = ext.lower()
        return (filename + ext, ext)

    def _format_filename(self, new_dirname, new_filename, metadata, settings, naming_format):
        old_filename = new_filename
        new_filename, ext = self._clean_file_extension(new_filename)

        if naming_format:
            new_filename = self._script_to_filename(naming_format, metadata, ext, settings)
            if not settings['rename_files']:
                new_filename = os.path.join(os.path.dirname(new_filename), old_filename)
            if not settings['move_files']:
                new_filename = os.path.basename(new_filename)
            win_compat = IS_WIN or settings['windows_compatibility']
            win_shorten_path = win_compat and not settings['windows_long_paths']
            new_filename = make_short_filename(new_dirname, new_filename, win_shorten_path=win_shorten_path)
            new_filename = make_save_path(new_filename, win_compat=win_compat, mac_compat=IS_MACOS)
        return new_filename

    def make_filename(self, filename, metadata, settings=None, naming_format=None):
        """Constructs file name based on metadata and file naming formats."""
        if settings is None:
            config = get_config()
            settings = config.setting
        if naming_format is None:
            naming_format = get_file_naming_script(settings)
        if settings['move_files']:
            new_dirname = settings['move_files_to']
            if not is_absolute_path(new_dirname):
                new_dirname = os.path.join(os.path.dirname(filename), new_dirname)
        else:
            new_dirname = os.path.dirname(filename)
        new_filename = os.path.basename(filename)

        if settings['rename_files'] or settings['move_files']:
            new_filename = self._format_filename(new_dirname, new_filename, metadata, settings, naming_format)

        new_path = os.path.join(new_dirname, new_filename)
        return normpath(new_path, realpath=False)

    def _rename(self, old_filename, metadata, settings=None):
        new_filename = self.make_filename(old_filename, metadata, settings)
        if old_filename == new_filename:
            return old_filename

        new_dirname = os.path.dirname(new_filename)
        if not os.path.isdir(new_dirname):
            os.makedirs(new_dirname)
        new_filename = get_available_filename(new_filename, old_filename)
        log.debug("Moving file %r => %r", old_filename, new_filename)
        move_ensure_casing(old_filename, new_filename)
        return new_filename

    def _save_images(self, dirname, metadata):
        """Save the cover images to disk."""
        if not metadata.images:
            return
        counters = Counter()
        images = []
        config = get_config()
        if config.setting['save_only_one_front_image']:
            front = metadata.images.get_front_image()
            if front:
                images.append(front)
        if not images:
            images = metadata.images
        for image in images:
            image.save(dirname, metadata, counters)

    def _move_additional_files(self, old_filename, new_filename, config):
        """Move extra files, like images, playlists…"""
        if config.setting['move_files'] and config.setting['move_additional_files']:
            new_path = os.path.dirname(new_filename)
            old_path = os.path.dirname(old_filename)
            if new_path != old_path:
                patterns_string = config.setting['move_additional_files_pattern']
                patterns = self._compile_move_additional_files_pattern(patterns_string)
                try:
                    moves = self._get_additional_files_moves(old_path, new_path, patterns)
                    self._apply_additional_files_moves(moves)
                except OSError as why:
                    log.error("Failed to scan %r: %s", old_path, why)

    @staticmethod
    def _compile_move_additional_files_pattern(patterns_string):
        return {
            (re.compile(fnmatch.translate(pattern), re.IGNORECASE), pattern.startswith('.'))
            for pattern in set(patterns_string.lower().split())
        }

    def _get_additional_files_moves(self, old_path, new_path, patterns):
        if patterns:
            with os.scandir(old_path) as scan:
                for entry in scan:
                    is_hidden = entry.name.startswith('.')
                    for pattern_regex, match_hidden in patterns:
                        if is_hidden and not match_hidden:
                            continue
                        if pattern_regex.match(entry.name):
                            new_file_path = os.path.join(new_path, entry.name)
                            yield (entry.path, new_file_path)
                            break  # we are done with this file

    def _apply_additional_files_moves(self, moves):
        for old_file_path, new_file_path in moves:
            # FIXME we shouldn't do this from a thread!
            if self.tagger.files.get(decode_filename(old_file_path)):
                log.debug("File loaded in the tagger, not moving %r", old_file_path)
                continue
            log.debug("Moving %r to %r", old_file_path, new_file_path)
            try:
                shutil.move(old_file_path, new_file_path)
            except OSError as why:
                log.error("Failed to move %r to %r: %s", old_file_path, new_file_path, why)

    def remove(self, from_parent_item=True):
        if from_parent_item and self.parent_item:
            log.debug("Removing %r from %r", self, self.parent_item)
            self.parent_item.remove_file(self)
        self.tagger.acoustidmanager.remove(self)
        self.state = File.State.REMOVED

    def move(self, to_parent_item):
        # To be able to move a file the target must implement add_file(file)
        if hasattr(to_parent_item, 'add_file') and to_parent_item != self.parent_item:
            log.debug("Moving %r from %r to %r", self, self.parent_item, to_parent_item)
            self.clear_lookup_task()
            self.tagger._acoustid.stop_analyze(self)
            new_album = True
            if self.parent_item:
                new_album = self.parent_item.album != to_parent_item.album
                self.clear_pending()
                self.parent_item.remove_file(self, new_album=new_album)
            self.parent_item = to_parent_item
            self.parent_item.add_file(self, new_album=new_album)
            self.acoustid_update()
            return True
        else:
            return False

    def _move(self, to_parent_item):
        if to_parent_item != self.parent_item:
            log.debug("Moving %r from %r to %r", self, self.parent_item, to_parent_item)
            if self.parent_item:
                self.parent_item.remove_file(self)
            self.parent_item = to_parent_item
            self.acoustid_update()

    def set_acoustid_fingerprint(self, fingerprint, length=None):
        if not fingerprint:
            self.acoustid_fingerprint = None
            self.acoustid_length = 0
            self.tagger.acoustidmanager.remove(self)
        elif fingerprint != self.acoustid_fingerprint:
            self.acoustid_fingerprint = fingerprint
            self.acoustid_length = length or self.metadata.length // 1000
            self.tagger.acoustidmanager.add(self, None)
            self.acoustid_update()
        config = get_config()
        if config.setting['save_acoustid_fingerprints']:
            self.metadata['acoustid_fingerprint'] = fingerprint

    def acoustid_update(self):
        recording_id = None
        if self.parent_item and self.parent_item.can_link_fingerprint:
            recording_id = self.parent_item.orig_metadata['musicbrainz_recordingid']
            if not recording_id:
                recording_id = self.metadata['musicbrainz_recordingid']
        self.tagger.acoustidmanager.update(self, recording_id)
        self.update_item()

    @classmethod
    def supports_tag(cls, name: str) -> bool:
        """Returns whether tag ``name`` can be saved to the file."""
        return True

    def is_saved(self) -> bool:
        return self.similarity == 1.0 and self.state == File.State.NORMAL

    def _tags_to_update(self, ignored_tags):
        for name in set(self.metadata) | set(self.orig_metadata):
            if name.startswith('~'):
                continue
            if name in ignored_tags:
                continue
            if not self.supports_tag(name):
                continue
            yield name

    def update(self, signal=True):
        if not (self.state == File.State.ERROR and self.errors):
            config = get_config()
            clear_existing_tags = config.setting['clear_existing_tags']
            ignored_tags = set(config.setting['compare_ignore_tags'])

            for name in self._tags_to_update(ignored_tags):
                new_values = self.format_specific_metadata(self.metadata, name, config.setting)
                if not (new_values or clear_existing_tags or name in self.metadata.deleted_tags):
                    continue
                orig_values = self.orig_metadata.getall(name)
                if orig_values != new_values:
                    self.similarity = self.orig_metadata.compare(self.metadata, ignored_tags)
                    if self.state == File.State.NORMAL:
                        self.state = File.State.CHANGED
                    break
            else:
                self.similarity = 1.0
                if self.state in (File.State.CHANGED, File.State.NORMAL):
                    if self.metadata.images and self.orig_metadata.images != self.metadata.images:
                        self.state = File.State.CHANGED
                    else:
                        self.state = File.State.NORMAL
        if signal:
            log.debug("Updating file %r", self)
            self.update_item()

    @property
    def can_save(self) -> bool:
        """Return if this object can be saved."""
        return True

    @property
    def can_remove(self) -> bool:
        """Return if this object can be removed."""
        return True

    @property
    def can_edit_tags(self) -> bool:
        """Return if this object supports tag editing."""
        return True

    @property
    def can_analyze(self) -> bool:
        """Return if this object can be fingerprinted."""
        return True

    @property
    def can_autotag(self) -> bool:
        return True

    @property
    def can_refresh(self) -> bool:
        return False

    @property
    def can_view_info(self) -> bool:
        return True

    def _info(self, metadata: Metadata, file: FileType):
        if hasattr(file.info, 'length'):
            metadata.length = int(file.info.length * 1000)
        if hasattr(file.info, 'bitrate') and file.info.bitrate:
            metadata['~bitrate'] = file.info.bitrate / 1000.0
        if hasattr(file.info, 'sample_rate') and file.info.sample_rate:
            metadata['~sample_rate'] = file.info.sample_rate
        if hasattr(file.info, 'channels') and file.info.channels:
            metadata['~channels'] = file.info.channels
        if hasattr(file.info, 'bits_per_sample') and file.info.bits_per_sample:
            metadata['~bits_per_sample'] = file.info.bits_per_sample
        if self.NAME:
            metadata['~format'] = self.NAME
        else:
            metadata['~format'] = self.__class__.__name__.replace('File', '')
        self._update_filesystem_metadata(metadata)

    @classmethod
    def score(cls, filename: str, fileobj: IO[bytes], header_data: bytes) -> int:
        """Used to guess if the provided file matches this file format.

        If Picard needs to choose between multiple file formats it uses the returned
        score to select one. The score is an integer, and typically implementations
        check if the file extension matches and whether there are some expected
        magic bytes in the header data.

        When implementing a new file format by sub-classing `File`:

        1. If the new format is based on the mutagen library, set the class `_File`
           attribute to the mutagen file type class being used. You don't need to
           override this score method then. The default implementation will use the
           `score` method in the mutagen file type class.
        2. If you are implementing a file format without using mutagen, the default
           implementation of `score` will only check whether the file extension of the
           passed `filename` matches any extension in the class `EXTENSION` attribute.
           For better matching you can override `score`. A typical implementation will
           check for matching file extension and some magic bytes in the provided
           header_data.

        Example:

            @classmethod
            def score(cls, filename: str, fileobj: FileIO, header_data: bytes) -> int:
                filename = filename.lower()
                return return header.startswith(b"qoaf") + filename.lower().endswith(".qoa")

        Args:
            filename: Path to the file to check.
            fileobj: An open file handle for reading from the file.
            header_data: This will be passed some bytes form the file header. By
              default Picard passed in the first 128 bytes of data.
        """
        mutagen_file = getattr(cls, '_File', None)
        if mutagen_file and hasattr(mutagen_file, 'score'):
            return mutagen_file.score(str(filename), fileobj, header_data)
        else:
            _name, ext = os.path.splitext(filename)
            return ext.lower() in cls.EXTENSIONS

    def _update_filesystem_metadata(self, metadata):
        metadata['~dirname'] = os.path.dirname(self.filename)
        filename_no_ext, extension = os.path.splitext(os.path.basename(self.filename))
        metadata['~filename'] = filename_no_ext
        metadata['~extension'] = extension.lower()[1:]

        filename_encoded = encode_filename(self.filename)
        try:
            metadata['~filesize'] = os.path.getsize(filename_encoded)

            created = os.path.getctime(filename_encoded)
            created_timestamp = time.strftime(DEFAULT_TIME_FORMAT, time.localtime(created))
            metadata['~file_created_timestamp'] = created_timestamp

            modified = os.path.getmtime(filename_encoded)
            modified_timestamp = time.strftime(DEFAULT_TIME_FORMAT, time.localtime(modified))
            metadata['~file_modified_timestamp'] = modified_timestamp
        except OSError as ex:
            log.error(f"File access error: {ex}")

    @property
    def state(self):
        """Current state of the File object"""
        return self._state

    @state.setter
    def state(self, state):
        if state == self._state:
            return
        if state == File.State.PENDING:
            File.num_pending_files += 1
            self.tagger.tagger_stats_changed.emit()
        elif self._state == File.State.PENDING:
            File.num_pending_files -= 1
            self.tagger.tagger_stats_changed.emit()
        self._state = state

    def column(self, column: str) -> str:
        m = self.metadata
        if column == 'title' and not m['title']:
            return self.base_filename
        elif column == 'covercount':
            return self.cover_art_description()
        elif column == 'coverdimensions':
            return self.cover_art_dimensions()
        value = m[column]
        if not value and not get_config().setting['clear_existing_tags']:
            value = self.orig_metadata[column]
        if column == '~filesize':
            try:
                value = bytes2human.binary(value)
            except ValueError:
                pass
        elif column == '~bitrate':
            try:
                if value:
                    value = f"{float(value):.0f} kbps"
            except (ValueError, TypeError):
                pass
        return value

    def _lookup_finished(self, lookuptype, document, http, error):
        self._lookup_task = None

        if self.state == File.State.REMOVED:
            return
        if error:
            log.error(
                "Network error encountered during the lookup for %s. Error code: %s",
                self.filename,
                error,
            )
        try:
            tracks = document['recordings']
        except (KeyError, TypeError):
            tracks = None

        def statusbar(message):
            self.tagger.window.set_statusbar_message(
                message,
                {'filename': self.filename},
                timeout=3000,
            )

        if tracks:
            if lookuptype == File.LookupType.ACOUSTID:
                threshold = 0
            else:
                config = get_config()
                threshold = config.setting['file_lookup_threshold']

            trackmatch = self._match_to_track(tracks, threshold=threshold)
            if trackmatch is None:
                statusbar(N_("No matching tracks above the threshold for file '%(filename)s'"))
            else:
                statusbar(N_("File '%(filename)s' identified!"))
                (recording_id, release_group_id, release_id, acoustid, node) = trackmatch
                if lookuptype == File.LookupType.ACOUSTID:
                    self.metadata['acoustid_id'] = acoustid
                    self.tagger.acoustidmanager.add(self, recording_id)
                if release_group_id is not None:
                    releasegroup = self.tagger.get_release_group_by_id(release_group_id)
                    releasegroup.loaded_albums.add(release_id)
                    self.tagger.move_file_to_track(self, release_id, recording_id)
                else:
                    self.tagger.move_file_to_nat(self, recording_id)
        else:
            statusbar(N_("No matching tracks for file '%(filename)s'"))

        self.clear_pending()

    def _match_to_track(self, tracks, threshold=0):
        # multiple matches -- calculate similarities to each of them
        candidates = (self.metadata.compare_to_track(track, FILE_COMPARISON_WEIGHTS) for track in tracks)
        no_match = SimMatchTrack(similarity=-1, releasegroup=None, release=None, track=None)
        best_match = find_best_match(candidates, no_match)

        if best_match.similarity < threshold:
            return None
        else:
            track_id = best_match.result.track['id']
            release_group_id, release_id, node = None, None, None
            acoustid = best_match.result.track.get('acoustid', None)

            if best_match.result.release:
                release_group_id = best_match.result.releasegroup['id']
                release_id = best_match.result.release['id']
            elif 'title' in best_match.result.track:
                node = best_match.result.track
            return (track_id, release_group_id, release_id, acoustid, node)

    def lookup_metadata(self):
        """Try to identify the file using the existing metadata."""
        if self._lookup_task:
            return
        self.tagger.window.set_statusbar_message(
            N_("Looking up the metadata for file %(filename)s …"),
            {'filename': self.filename},
        )
        self.clear_lookup_task()
        metadata = self.metadata
        self.set_pending()
        config = get_config()
        self._lookup_task = self.tagger.mb_api.find_tracks(
            partial(self._lookup_finished, File.LookupType.METADATA),
            track=metadata['title'],
            artist=metadata['artist'],
            release=metadata['album'],
            tnum=metadata['tracknumber'],
            tracks=metadata['totaltracks'],
            qdur=str(metadata.length // 2000),
            isrc=metadata['isrc'],
            limit=config.setting['query_limit'],
        )

    def clear_lookup_task(self):
        if self._lookup_task:
            self.tagger.webservice.abort_task(self._lookup_task)
            self._lookup_task = None

    def set_pending(self):
        if self.state != File.State.REMOVED:
            self.state = File.State.PENDING
            self.update_item(update_selection=False)

    def clear_pending(self, signal=True):
        if self.state == File.State.PENDING:
            self.state = File.State.NORMAL
            # Update file to recalculate changed state
            self.update(signal=False)
            if signal:
                self.update_item(update_selection=False)

    def update_item(self, update_selection=True):
        if self.ui_item:
            self.ui_item.update(update_selection=update_selection)

    def iterfiles(self, save=False):
        yield self

    # --- Per-format feature toggles ---
    def is_date_sanitization_enabled(self) -> bool:
        """Determine whether date sanitization should be applied.

        Returns
        -------
        bool
            True if sanitization should be applied for this file's format, False otherwise.

        Notes
        -----
        This respects the per-format user configuration keyed by ``FORMAT_KEY``.
        If the current format does not support toggling (i.e.,
        ``DATE_SANITIZATION_TOGGLEABLE`` is False) or ``FORMAT_KEY`` is not set,
        this method returns True.
        """
        # If this format does not support toggling, always treat as enabled
        if not getattr(self.__class__, 'DATE_SANITIZATION_TOGGLEABLE', False):
            return True

        # If the format key is not set, always treat as enabled
        format_key = getattr(self.__class__, 'FORMAT_KEY', None)
        if not format_key:
            return True

        # Local import to avoid circular dependencies
        from picard.config import get_config  # pylint: disable=import-outside-toplevel

        try:
            disabled = get_config().setting['disable_date_sanitization_formats']
        except KeyError:
            return True
        else:
            return format_key not in disabled


file_post_load_processors = PluginFunctions(label='file_post_load_processors')
file_post_addition_to_track_processors = PluginFunctions(label='file_post_addition_to_track_processors')
file_post_removal_to_track_processors = PluginFunctions(label='file_post_removal_from_track_processors')
file_pre_save_processors = PluginFunctions(label='file_pre_save_processors')
file_post_save_processors = PluginFunctions(label='file_post_save_processors')


def run_file_post_load_processors(file_object):
    file_post_load_processors.run(file_object)


def run_file_post_addition_to_track_processors(track_object, file_object):
    file_post_addition_to_track_processors.run(track_object, file_object)


def run_file_post_removal_from_track_processors(track_object, file_object):
    file_post_removal_to_track_processors.run(track_object, file_object)


def run_file_pre_save_processors(file_object):
    file_pre_save_processors.run(file_object)


def run_file_post_save_processors(file_object):
    file_post_save_processors.run(file_object)
