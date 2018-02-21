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
from functools import partial
from PyQt5 import QtCore, QtGui, QtNetwork, QtWidgets
from picard import config, log
from picard.album import Album
from picard.coverart.image import CoverArtImage, CoverArtImageError
from picard.track import Track
from picard.file import File
from picard.util import imageinfo
from picard.util.lrucache import LRUCache
from picard.const import MAX_COVERS_TO_STACK


class ActiveLabel(QtWidgets.QLabel):
    """Clickable QLabel."""

    clicked = QtCore.pyqtSignal()
    image_dropped = QtCore.pyqtSignal(QtCore.QUrl, QtCore.QByteArray)

    def __init__(self, active=True, drops=False, *args):
        super().__init__(*args)
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
        event.acceptProposedAction()

    def dropEvent(self, event):
        accepted = False
        # Chromium includes the actual data of the dragged image in the drop event. This
        # is useful for Google Images, where the url links to the page that contains the image
        # so we use it if the downloaded url is not an image.
        mime_data = event.mimeData()
        dropped_data = mime_data.data('application/octet-stream')

        if not dropped_data:
            dropped_data = mime_data.data('application/x-qt-image')

        try:
            mime = imageinfo.identify(dropped_data)[2]
            if mime in ('image/jpeg', 'image/png'):
                accepted = True
                self.image_dropped.emit(QtCore.QUrl(''), dropped_data)
        except imageinfo.IdentificationError:
            pass

        if not accepted:
            for url in event.mimeData().urls():
                if url.scheme() in ('https', 'http', 'file'):
                    accepted = True
                    self.image_dropped.emit(url, dropped_data)

        if not accepted:
            if mime_data.hasImage():
                image_bytes = QtCore.QByteArray()
                image_buffer = QtCore.QBuffer(image_bytes)
                mime_data.imageData().save(image_buffer, 'JPEG')

                accepted = True
                self.image_dropped.emit(QtCore.QUrl(''), image_bytes)

        if accepted:
            event.acceptProposedAction()


class CoverArtThumbnail(ActiveLabel):

    def __init__(self, active=False, drops=False, pixmap_cache=None, *args, **kwargs):
        super().__init__(active, drops, *args, **kwargs)
        self.data = None
        self.has_common_images = None
        self.shadow = QtGui.QPixmap(":/images/CoverArtShadow.png")
        self.pixel_ratio = self.tagger.primaryScreen().devicePixelRatio()
        w, h = self.scaled(128, 128)
        self.shadow = self.shadow.scaled(w, h, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.shadow.setDevicePixelRatio(self.pixel_ratio)
        self.release = None
        self.setPixmap(self.shadow)
        self.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        self.clicked.connect(self.open_release_page)
        self.related_images = []
        self._pixmap_cache = pixmap_cache
        self.current_pixmap_key = None

    def __eq__(self, other):
        if len(self.data) or len(other.data):
            return self.current_pixmap_key == other.current_pixmap_key
        else:
            return True

    def scaled(self, *dimensions):
        return (self.pixel_ratio * dimension for dimension in dimensions)

    def show(self):
        self.set_data(self.data, True)

    def decorate_cover(self, pixmap):
        offx, offy, w, h = self.scaled(1, 1, 121, 121)
        cover = QtGui.QPixmap(self.shadow)
        pixmap = pixmap.scaled(w, h, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        pixmap.setDevicePixelRatio(self.pixel_ratio)
        painter = QtGui.QPainter(cover)
        bgcolor = QtGui.QColor.fromRgb(0, 0, 0, 128)
        painter.fillRect(QtCore.QRectF(offx, offy, w, h), bgcolor)
        x = offx + (w - pixmap.width()) // 2
        y = offy + (h - pixmap.height()) // 2
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

        w, h, displacements = self.scaled(128, 128, 20)
        key = hash(tuple(sorted(self.data, key=lambda x: x.types_as_string())) + (has_common_images,))
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
                cx = stack_width - w // 2
                cy = h // 2
                if limited:
                    x, y = (cx - self.shadow.width() // 2, cy - self.shadow.height() // 2)
                    for i in range(3):
                        painter.drawPixmap(x, y, self.shadow)
                        x -= displacements // 3
                        y += displacements // 3
                    cx -= displacements
                    cy += displacements
                else:
                    cx = stack_width - w // 2
                    cy = h // 2
                for image in reversed(data_to_paint):
                    if isinstance(image, QtGui.QPixmap):
                        thumb = image
                    else:
                        thumb = QtGui.QPixmap()
                        thumb.loadFromData(image.data)
                    thumb = self.decorate_cover(thumb)
                    x, y = (cx - thumb.width() // 2, cy - thumb.height() // 2)
                    painter.drawPixmap(x, y, thumb)
                    cx -= displacements
                    cy += displacements
                if not has_common_images:
                    color = QtGui.QColor("darkgoldenrod")
                    border_length = 10
                    for k in range(border_length):
                        color.setAlpha(255 - k * 255 // border_length)
                        painter.setPen(color)
                        painter.drawLine(x, y - k - 1, x + 121 + k + 1, y - k - 1)
                        painter.drawLine(x + 121 + k + 2, y - 1 - k, x + 121 + k + 2, y + 121 + 4)
                    for k in range(5):
                        bgcolor.setAlpha(80 + k * 255 // 7)
                        painter.setPen(bgcolor)
                        painter.drawLine(x + 121 + 2, y + 121 + 2 + k, x + 121 + border_length + 2, y + 121 + 2 + k)
                painter.end()
                pixmap = pixmap.scaled(w, h, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self._pixmap_cache[key] = pixmap

        pixmap.setDevicePixelRatio(self.pixel_ratio)
        self.setPixmap(pixmap)
        self.current_pixmap_key = key

    def set_metadata(self, metadata):
        data = None
        self.related_images = []
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
            text = _("View release on MusicBrainz")
        else:
            self.setActive(False)
            text = ""
        if hasattr(metadata, 'has_common_images'):
            if has_common_images:
                note = _('Common images on all tracks')
            else:
                note = _('Tracks contain different images')
            if text:
                text += '<br />'
            text += '<i>%s</i>' % note
        self.setToolTip(text)
        self.release = release

    def open_release_page(self):
        lookup = self.tagger.get_file_lookup()
        lookup.album_lookup(self.release)


def set_image_replace(obj, coverartimage):
    obj.metadata.set_front_image(coverartimage)


def set_image_append(obj, coverartimage):
    obj.metadata.append_image(coverartimage)


class CoverArtBox(QtWidgets.QGroupBox):

    def __init__(self, parent):
        super().__init__("")
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setSpacing(6)
        self.parent = parent
        # Kills off any borders
        self.setStyleSheet('''QGroupBox{background-color:none;border:1px;}''')
        self.setFlat(True)
        self.item = None
        self.pixmap_cache = LRUCache(40)
        self.cover_art_label = QtWidgets.QLabel('')
        self.cover_art_label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        self.cover_art = CoverArtThumbnail(False, True, self.pixmap_cache, parent)
        self.cover_art.image_dropped.connect(self.fetch_remote_image)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.orig_cover_art_label = QtWidgets.QLabel('')
        self.orig_cover_art = CoverArtThumbnail(False, False, self.pixmap_cache, parent)
        self.orig_cover_art_label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        self.show_details_button = QtWidgets.QPushButton(_('Show more details'), self)
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
            self.cover_art_label.setText(_('New Cover Art'))
            self.orig_cover_art_label.setText(_('Original Cover Art'))

    def show(self):
        self.update_display(True)
        super().show()

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

        if fallback_data is not None:
            self.load_remote_image(url, None, fallback_data)

        if url.scheme() in ('http', 'https'):
            path = url.path(QtCore.QUrl.FullyEncoded)
            if url.hasQuery():
                path += '?' + url.query(QtCore.QUrl.FullyEncoded)
            if url.scheme() == 'https':
                port = 443
            else:
                port = 80
            self.tagger.webservice.get(string_(url.encodedHost()), url.port(port), string_(path),
                                  partial(self.on_remote_image_fetched, url, fallback_data=fallback_data),
                                  parse_response_type=None,
                                  priority=True, important=True)
        elif url.scheme() == 'file':
            path = os.path.normpath(os.path.realpath(url.toLocalFile().rstrip("\0")))
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
                types=['front'],
                data=data
            )
        except CoverArtImageError as e:
            log.warning("Can't load image: %s" % e)
            return

        if config.setting["load_image_behavior"] == 'replace':
            set_image = set_image_replace
        else:
            set_image = set_image_append

        if isinstance(self.item, Album):
            album = self.item
            album.enable_update_metadata_images(False)
            set_image(album, coverartimage)
            for track in album.tracks:
                set_image(track, coverartimage)
                track.metadata_images_changed.emit()
            for file in album.iterfiles():
                set_image(file, coverartimage)
                file.metadata_images_changed.emit()
                file.update()
            album.enable_update_metadata_images(True)
            album.update_metadata_images()
            album.update(False)
        elif isinstance(self.item, Track):
            track = self.item
            track.album.enable_update_metadata_images(False)
            set_image(track, coverartimage)
            track.metadata_images_changed.emit()
            for file in track.iterfiles():
                set_image(file, coverartimage)
                file.metadata_images_changed.emit()
                file.update()
            track.album.enable_update_metadata_images(True)
            track.album.update_metadata_images()
            track.album.update(False)
        elif isinstance(self.item, File):
            file = self.item
            set_image(file, coverartimage)
            file.metadata_images_changed.emit()
            file.update()
        self.cover_art.set_metadata(self.item.metadata)
        self.show()

    def set_load_image_behavior(self, behavior):
        config.setting["load_image_behavior"] = behavior

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        if self.show_details_button.isVisible():
            name = _('Show more details...')
            show_more_details_action = QtWidgets.QAction(name, self.parent)
            show_more_details_action.triggered.connect(self.show_cover_art_info)
            menu.addAction(show_more_details_action)

        if self.orig_cover_art.isVisible():
            name = _('Keep original cover art')
            use_orig_value_action = QtWidgets.QAction(name, self.parent)
            use_orig_value_action.triggered.connect(self.item.keep_original_images)
            menu.addAction(use_orig_value_action)

        if not menu.isEmpty():
            menu.addSeparator()

        load_image_behavior_group = QtWidgets.QActionGroup(self.parent, exclusive=True)
        action = load_image_behavior_group.addAction(QtWidgets.QAction(_('Replace front cover art on drop'), self.parent, checkable=True))
        action.triggered.connect(partial(self.set_load_image_behavior, behavior='replace'))
        if config.setting["load_image_behavior"] == 'replace':
            action.setChecked(True)
        menu.addAction(action)
        action = load_image_behavior_group.addAction(QtWidgets.QAction(_('Append front cover art on drop'), self.parent, checkable=True))
        action.triggered.connect(partial(self.set_load_image_behavior, behavior='append'))
        if config.setting["load_image_behavior"] == 'append':
            action.setChecked(True)
        menu.addAction(action)

        menu.exec_(event.globalPos())
        event.accept()
