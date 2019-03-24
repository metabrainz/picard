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


from functools import partial
import traceback

from PyQt5.QtCore import QObject

from picard import (
    config,
    log,
)
from picard.coverart.image import (
    CoverArtImageIdentificationError,
    CoverArtImageIOError,
)
from picard.coverart.providers import (
    CoverArtProvider,
    cover_art_providers,
)


class CoverArt:

    def __init__(self, album, metadata, release):
        self._queue_new()
        self.album = album
        self.metadata = metadata
        self.release = release
        self.front_image_found = False

    def __repr__(self):
        return "CoverArt for %r" % (self.album)

    def retrieve(self):
        """Retrieve available cover art images for the release"""
        if (not config.setting["save_images_to_tags"] and not
                config.setting["save_images_to_files"]):
            log.debug("Cover art disabled by user options.")
            return

        self.providers = cover_art_providers()
        self.next_in_queue()

    def _set_metadata(self, coverartimage, data):
        try:
            coverartimage.set_data(data)
            if coverartimage.can_be_saved_to_metadata:
                log.debug("Cover art image stored to metadata: %r [%s]" % (
                    coverartimage,
                    coverartimage.imageinfo_as_string())
                )
                self.metadata.images.append(coverartimage)
                for track in self.album._new_tracks:
                    track.metadata.images.append(coverartimage)
                # If the image already was a front image,
                # there might still be some other non-CAA front
                # images in the queue - ignore them.
                if not self.front_image_found:
                    self.front_image_found = coverartimage.is_front_image()
            else:
                log.debug("Thumbnail for cover art image: %r [%s]" % (
                    coverartimage,
                    coverartimage.imageinfo_as_string())
                )
        except CoverArtImageIOError as e:
            self.album.error_append(e)
            self.album._finalize_loading(error=True)
            raise e
        except CoverArtImageIdentificationError as e:
            self.album.error_append(e)

    def _coverart_downloaded(self, coverartimage, data, http, error):
        """Handle finished download, save it to metadata"""
        self.album._requests -= 1

        if error:
            self.album.error_append('Coverart error: %s' % (http.errorString()))
        elif len(data) < 1000:
            log.warning("Not enough data, skipping %s" % coverartimage)
        else:
            self._message(
                N_("Cover art of type '%(type)s' downloaded for %(albumid)s from %(host)s"),
                {
                    'type': coverartimage.types_as_string(),
                    'albumid': self.album.id,
                    'host': coverartimage.host
                },
                echo=None
            )
            try:
                self._set_metadata(coverartimage, data)
            except CoverArtImageIOError:
                # It doesn't make sense to store/download more images if we can't
                # save them in the temporary folder, abort.
                return

        self.next_in_queue()

    def next_in_queue(self):
        """Downloads next item in queue.
           If there are none left, loading of album will be finalized.
        """
        if self.album.id not in self.album.tagger.albums:
            # album removed
            return

        if (self.front_image_found and
                config.setting["save_images_to_tags"] and not
                config.setting["save_images_to_files"] and
                config.setting["embed_only_one_front_image"]):
            # no need to continue
            self.album._finalize_loading(None)
            return

        if self._queue_empty():
            if self.providers:
                # requeue from next provider
                provider = self.providers.pop(0)
                ret = CoverArtProvider._STARTED
                try:
                    p = provider(self)
                    if p.enabled():
                        log.debug("Trying cover art provider %s ..." %
                                  provider.NAME)
                        ret = p.queue_images()
                    else:
                        log.debug("Skipping cover art provider %s ..." %
                                  provider.NAME)
                except BaseException:
                    log.error(traceback.format_exc())
                    raise
                finally:
                    if ret != CoverArtProvider.WAIT:
                        self.next_in_queue()
                    return
            else:
                # nothing more to do
                self.album._finalize_loading(None)
                return

        # We still have some items to try!
        coverartimage = self._queue_get()
        if not coverartimage.support_types and self.front_image_found:
            # we already have one front image, no need to try other type-less
            # sources
            log.debug("Skipping %r, one front image is already available",
                      coverartimage)
            self.next_in_queue()
            return

        # local files
        if coverartimage.url and coverartimage.url.scheme() == 'file':
            try:
                path = coverartimage.url.toLocalFile()
                with open(path, 'rb') as file:
                    self._set_metadata(coverartimage, file.read())
            except IOError as ioexcept:
                (errnum, errmsg) = ioexcept.args
                log.error("Failed to read %r: %s (%d)" %
                          (path, errmsg, errnum))
            except CoverArtImageIOError:
                # It doesn't make sense to store/download more images if we can't
                # save them in the temporary folder, abort.
                return
            self.next_in_queue()
            return

        # on the web
        self._message(
            N_("Downloading cover art of type '%(type)s' for %(albumid)s from %(host)s ..."),
            {
                'type': coverartimage.types_as_string(),
                'albumid': self.album.id,
                'host': coverartimage.host
            },
            echo=None
        )
        log.debug("Downloading %r" % coverartimage)
        self.album.tagger.webservice.download(
            coverartimage.host,
            coverartimage.port,
            coverartimage.path,
            partial(self._coverart_downloaded, coverartimage),
            priority=True,
            important=False
        )
        self.album._requests += 1

    def queue_put(self, coverartimage):
        """Add an image to queue"""
        log.debug("Queuing cover art image %r", coverartimage)
        self.__queue.append(coverartimage)

    def _queue_get(self):
        """Get next image and remove it from queue"""
        return self.__queue.pop(0)

    def _queue_empty(self):
        """Returns True if the queue is empty"""
        return not self.__queue

    def _queue_new(self):
        """Initialize the queue"""
        self.__queue = []

    def _message(self, *args, **kwargs):
        """Display message to status bar"""
        QObject.tagger.window.set_statusbar_message(*args, **kwargs)


def coverart(album, metadata, release):
    """Gets all cover art URLs from the metadata and then attempts to
    download the album art. """

    coverart = CoverArt(album, metadata, release)
    log.debug("New %r", coverart)
    coverart.retrieve()
