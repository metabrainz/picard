# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006,2011 Lukáš Lalinský
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

import os
import sys
from functools import partial
from PyQt4 import QtCore, QtGui, QtNetwork
from picard import config, log
from picard.album import Album
from picard.coverart.image import CoverArtImage, CoverArtImageError
from picard.coverart.imagelist import ImageList
from picard.track import Track
from picard.file import File
from picard.util import encode_filename, imageinfo
from picard.util.lrucache import LRUCache
from picard.const import MAX_COVERS_TO_STACK

if sys.platform == 'darwin':
    try:
        from Foundation import NSURL
        NSURL_IMPORTED = True
    except ImportError:
        NSURL_IMPORTED = False
        log.warning("Unable to import NSURL, file drag'n'drop might not work correctly")


class ActiveLabel(QtGui.QLabel):
    """Clickable QLabel."""

    clicked = QtCore.pyqtSignal()
    image_dropped = QtCore.pyqtSignal(QtCore.QUrl, QtCore.QByteArray)

    def __init__(self, active=True, drops=False, *args):
        QtGui.QLabel.__init__(self, *args)
        self.setMargin(0)
        self.setActive(active)
        self.setAcceptDrops(drops)

    def setActive(self, active):
        self.active = active
        if self.active:
            self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        else:
            self.setCursor(QtGui.QCursor())

    def mouseReleaseEvent(self, event):
        if self.active and event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()

    def dragEnterEvent(self, event):
        for url in event.mimeData().urls():
            if url.scheme() in ('https', 'http', 'file'):
                event.acceptProposedAction()
                break

    def dropEvent(self, event):
        accepted = False
        # Chromium includes the actual data of the dragged image in the drop event. This
        # is useful for Google Images, where the url links to the page that contains the image
        # so we use it if the downloaded url is not an image.
        dropped_data = event.mimeData().data('application/octet-stream')
        for url in event.mimeData().urls():
            if url.scheme() in ('https', 'http', 'file'):
                accepted = True
                self.image_dropped.emit(url, dropped_data)
        if accepted:
            event.acceptProposedAction()


class CoverArtThumbnail(ActiveLabel):

    def __init__(self, active=False, drops=False, pixmap_cache=None, *args, **kwargs):
        super(CoverArtThumbnail, self).__init__(active, drops, *args, **kwargs)
        self.data = None
        self.has_common_images = None
        self.shadow = QtGui.QPixmap(":/images/CoverArtShadow.png")
        self.release = None
        self.setPixmap(self.shadow)
        self.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        self.clicked.connect(self.open_release_page)
        self.image_dropped.connect(self.fetch_remote_image)
        self.related_images = ImageList()
        self._pixmap_cache = pixmap_cache
        self.current_pixmap_key = None

    def __eq__(self, other):
        if len(self.data) or len(other.data):
            return self.current_pixmap_key == other.current_pixmap_key
        else:
            return True

    def show(self):
        self.set_data(self.data, True)

    def decorate_cover(self, pixmap):
        offx, offy, w, h = (1, 1, 121, 121)
        cover = QtGui.QPixmap(self.shadow)
        pixmap = pixmap.scaled(w, h, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        painter = QtGui.QPainter(cover)
        bgcolor = QtGui.QColor.fromRgb(0, 0, 0, 128)
        painter.fillRect(QtCore.QRectF(offx, offy, w, h), bgcolor)
        x = offx + (w - pixmap.width()) / 2
        y = offy + (h - pixmap.height()) / 2
        painter.drawPixmap(x, y, pixmap)
        painter.end()
        return cover

    def set_data(self, data, force=False, has_common_images=True):
        if not force and self.data == data and self.has_common_images == has_common_images:
            return

        self.data = data
        self.has_common_images = has_common_images

        if not force and self.parent().isHidden():
            return

        if not self.data:
            self.setPixmap(self.shadow)
            self.current_pixmap_key = None
            return

        if len(self.data) == 1:
            has_common_images = True

        w, h, displacements = (128, 128, 20)
        key = hash(tuple(sorted(self.data)) + (has_common_images,))
        try:
            pixmap = self._pixmap_cache[key]
        except KeyError:
            if len(self.data) == 1:
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(self.data[0].data)
                pixmap = self.decorate_cover(pixmap)
            else:
                limited = len(self.data) > MAX_COVERS_TO_STACK
                if limited:
                    data_to_paint = data[:MAX_COVERS_TO_STACK - 1]
                    offset = displacements * len(data_to_paint)
                else:
                    data_to_paint = data
                    offset = displacements * (len(data_to_paint) - 1)
                stack_width, stack_height = (w + offset, h + offset)
                pixmap = QtGui.QPixmap(stack_width, stack_height)
                bgcolor = self.palette().color(QtGui.QPalette.Window)
                painter = QtGui.QPainter(pixmap)
                painter.fillRect(QtCore.QRectF(0, 0, stack_width, stack_height), bgcolor)
                cx = stack_width - w / 2
                cy = h / 2
                if limited:
                    x, y = (cx - self.shadow.width() / 2, cy - self.shadow.height() / 2)
                    for i in range(3):
                        painter.drawPixmap(x, y, self.shadow)
                        x -= displacements / 3
                        y += displacements / 3
                    cx -= displacements
                    cy += displacements
                else:
                    cx = stack_width - w / 2
                    cy = h / 2
                for image in reversed(data_to_paint):
                    if isinstance(image, QtGui.QPixmap):
                        thumb = image
                    else:
                        thumb = QtGui.QPixmap()
                        thumb.loadFromData(image.data)
                    thumb = self.decorate_cover(thumb)
                    x, y = (cx - thumb.width() / 2, cy - thumb.height() / 2)
                    painter.drawPixmap(x, y, thumb)
                    cx -= displacements
                    cy += displacements
                if not has_common_images:
                    color = QtGui.QColor("darkgoldenrod")
                    border_length = 10
                    for k in range(border_length):
                        color.setAlpha(255 - k * 255 / border_length)
                        painter.setPen(color)
                        painter.drawLine(x, y - k - 1, x + 121 + k + 1, y - k - 1)
                        painter.drawLine(x + 121 + k + 2, y - 1 - k, x + 121 + k + 2, y + 121 + 4)
                    for k in range(5):
                        bgcolor.setAlpha(80 + k * 255 / 7)
                        painter.setPen(bgcolor)
                        painter.drawLine(x + 121 + 2, y + 121 + 2 + k, x + 121 + border_length + 2, y + 121 + 2 + k)
                painter.end()
                pixmap = pixmap.scaled(w, h, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self._pixmap_cache[key] = pixmap

        self.setPixmap(pixmap)
        self.current_pixmap_key = key

    def set_metadata(self, metadata):
        data = None
        self.related_images = ImageList()
        if metadata and metadata.images:
            self.related_images = metadata.images
            data = [image for image in metadata.images if image.is_front_image()]
            if not data:
                # There's no front image, choose the first one available
                data = [metadata.images[0]]
        has_common_images = getattr(metadata, 'has_common_images', True)
        self.set_data(data, has_common_images=has_common_images)
        release = None
        if metadata:
            release = metadata.get("musicbrainz_albumid", None)
        if release:
            self.setActive(True)
            text = _(u"View release on MusicBrainz")
        else:
            self.setActive(False)
            text = ""
        if hasattr(metadata, 'has_common_images'):
            if has_common_images:
                note = _(u'Common images on all tracks')
            else:
                note = _(u'Tracks contain different images')
            if text:
                text += '<br />'
            text += '<i>%s</i>' % note
        self.setToolTip(text)
        self.release = release

    def open_release_page(self):
        lookup = self.tagger.get_file_lookup()
        lookup.albumLookup(self.release)

    def fetch_remote_image(self, url):
        return self.parent().fetch_remote_image(url)


class CoverArtBox(QtGui.QGroupBox):

    def __init__(self, parent):
        QtGui.QGroupBox.__init__(self, "")
        self.layout = QtGui.QVBoxLayout()
        self.layout.setSpacing(6)
        self.parent = parent
        # Kills off any borders
        self.setStyleSheet('''QGroupBox{background-color:none;border:1px;}''')
        self.setFlat(True)
        self.item = None
        self.pixmap_cache = LRUCache(40)
        self.cover_art_label = QtGui.QLabel('')
        self.cover_art_label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        self.cover_art = CoverArtThumbnail(False, True, self.pixmap_cache, parent)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.orig_cover_art_label = QtGui.QLabel('')
        self.orig_cover_art = CoverArtThumbnail(False, False, self.pixmap_cache, parent)
        self.orig_cover_art_label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        self.show_details_button = QtGui.QPushButton(_(u'Show more details'), self)
        self.layout.addWidget(self.cover_art_label)
        self.layout.addWidget(self.cover_art)
        self.layout.addWidget(self.orig_cover_art_label)
        self.layout.addWidget(self.orig_cover_art)
        self.layout.addWidget(self.show_details_button)
        self.layout.addSpacerItem(spacerItem)
        self.setLayout(self.layout)
        self.orig_cover_art.setHidden(True)
        self.show_details_button.setHidden(True)
        self.show_details_button.clicked.connect(self.show_cover_art_info)

    def show_cover_art_info(self):
        self.parent.view_info(default_tab=1)

    def update_display(self, force=False):
        if self.isHidden():
            if not force:
                # If the Cover art box is hidden and selection is updated
                # we should not update the display of child widgets
                return
            else:
                # Coverart box display was toggled.
                # Update the pixmaps and display them
                self.cover_art.show()
                self.orig_cover_art.show()

        # We want to show the 2 coverarts only if they are different
        # and orig_cover_art data is set and not the default cd shadow
        if self.orig_cover_art.data is None or self.cover_art == self.orig_cover_art:
            self.show_details_button.setVisible(bool(self.item and self.item.can_view_info()))
            self.orig_cover_art.setVisible(False)
            self.cover_art_label.setText('')
            self.orig_cover_art_label.setText('')
        else:
            self.show_details_button.setVisible(True)
            self.orig_cover_art.setVisible(True)
            self.cover_art_label.setText(_(u'New Cover Art'))
            self.orig_cover_art_label.setText(_(u'Original Cover Art'))

    def show(self):
        self.update_display(True)
        super(CoverArtBox, self).show()

    def set_metadata(self, metadata, orig_metadata, item):
        if not metadata or not metadata.images:
            self.cover_art.set_metadata(orig_metadata)
        else:
            self.cover_art.set_metadata(metadata)
        self.orig_cover_art.set_metadata(orig_metadata)
        self.item = item
        self.update_display()

    def fetch_remote_image(self, url, fallback_data=None):
        if self.item is None:
            return
        if url.scheme() in ('https', 'http'):
            path = url.encodedPath()
            if url.hasQuery():
                path += '?' + url.encodedQuery()
            if url.scheme() == 'https':
                port = 443
            else:
                port = 80
            self.tagger.xmlws.get(str(url.encodedHost()), url.port(port), str(path),
                                  partial(self.on_remote_image_fetched, url, fallback_data=fallback_data),
                                  xml=False,
                                  priority=True, important=True)
        elif url.scheme() == 'file':
            log.debug("Dropped the URL: %r", url.toString(QtCore.QUrl.RemoveUserInfo))
            if sys.platform == 'darwin' and unicode(url.path()).startswith('/.file/id='):
                # Workaround for https://bugreports.qt.io/browse/QTBUG-40449
                # OSX Urls follow the NSURL scheme and need to be converted
                if NSURL_IMPORTED:
                    path = os.path.normpath(os.path.realpath(unicode(NSURL.URLWithString_(str(url.toString())).filePathURL().path()).rstrip("\0")))
                    log.debug('OSX NSURL path detected. Dropped File is: %r', path)
                else:
                    log.error("Unable to get appropriate file path for %r", url.toString(QtCore.QUrl.RemoveUserInfo))
            else:
                # Dropping a file from iTunes gives a path with a NULL terminator
                path = os.path.normpath(os.path.realpath(unicode(url.toLocalFile()).rstrip("\0")))
            if path and os.path.exists(path):
                mime = 'image/png' if path.lower().endswith('.png') else 'image/jpeg'
                with open(path, 'rb') as f:
                    data = f.read()
                self.load_remote_image(url, mime, data)

    def on_remote_image_fetched(self, url, data, reply, error, fallback_data=None):
        mime = reply.header(QtNetwork.QNetworkRequest.ContentTypeHeader)
        if mime in ('image/jpeg', 'image/png'):
            self.load_remote_image(url, mime, data)
        elif url.hasQueryItem("imgurl"):
            # This may be a google images result, try to get the URL which is encoded in the query
            url = QtCore.QUrl(url.queryItemValue("imgurl"))
            self.fetch_remote_image(url)
        else:
            log.warning("Can't load remote image with MIME-Type %s", mime)
            if fallback_data:
                # Tests for image format obtained from file-magic
                try:
                    mime = imageinfo.identify(fallback_data)[2]
                except imageinfo.IdentificationError as e:
                    log.error("Unable to identify dropped data format: %s" % e)
                else:
                    log.debug("Trying the dropped %s data", mime)
                    self.load_remote_image(url, mime, fallback_data)

    def load_remote_image(self, url, mime, data):
        try:
            coverartimage = CoverArtImage(
                url=url.toString(),
                types=[u'front'],
                data=data
            )
        except CoverArtImageError as e:
            log.warning("Can't load image: %s" % unicode(e))
            return
        if isinstance(self.item, Album):
            album = self.item
            album.enable_update_metadata_images(False)
            for track in album.tracks:
                track.metadata.set_front_image(coverartimage)
                track.metadata_images_changed.emit()
            for file in album.iterfiles():
                file.metadata.set_front_image(coverartimage)
                file.metadata_images_changed.emit()
                file.update()
            album.enable_update_metadata_images(True)
            album.update_metadata_images()
            album.update(False)
        elif isinstance(self.item, Track):
            track = self.item
            track.album.enable_update_metadata_images(False)
            track.metadata.set_front_image(coverartimage)
            track.metadata_images_changed.emit()
            for file in track.iterfiles():
                file.metadata.set_front_image(coverartimage)
                file.metadata_images_changed.emit()
                file.update()
            track.album.enable_update_metadata_images(True)
            track.album.update_metadata_images()
            track.album.update(False)
        elif isinstance(self.item, File):
            file = self.item
            file.metadata.set_front_image(coverartimage)
            file.metadata_images_changed.emit()
            file.update()
        self.cover_art.set_metadata(self.item.metadata)
        self.show()
