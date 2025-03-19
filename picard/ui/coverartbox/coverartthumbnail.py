# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2011 Lukáš Lalinský
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009, 2018-2024 Philipp Wolfer
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2012-2014 Wieland Hoffmann
# Copyright (C) 2013-2014, 2017-2024 Laurent Monin
# Copyright (C) 2014 Francois Ferrand
# Copyright (C) 2015 Sophist-UK
# Copyright (C) 2016 Ville Skyttä
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Paul Roub
# Copyright (C) 2017-2019 Antonio Larrosa
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2021 Louis Sautier
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 ShubhamBhut
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


from PyQt6 import (
    QtCore,
    QtGui,
)

from picard import log
from picard.const import MAX_COVERS_TO_STACK
from picard.coverart.image import CoverArtImageIOError
from picard.i18n import gettext as _

from picard.ui.colors import interface_colors
from picard.ui.widgets import ActiveLabel


THUMBNAIL_WIDTH = 128
COVERART_WIDTH = THUMBNAIL_WIDTH - 7


class CoverArtThumbnail(ActiveLabel):
    image_dropped = QtCore.pyqtSignal(QtCore.QUrl, bytes)

    def __init__(self, active=False, drops=False, pixmap_cache=None, parent=None):
        super().__init__(active=active, parent=parent)
        self.data = None
        self.has_common_images = None
        self.release = None
        self.tagger = QtCore.QCoreApplication.instance()
        window_handle = self.window().windowHandle()
        if window_handle:
            self.pixel_ratio = window_handle.screen().devicePixelRatio()
            window_handle.screenChanged.connect(self.screen_changed)
        else:
            self.pixel_ratio = self.tagger.primaryScreen().devicePixelRatio()
        self._pixmap_cache = pixmap_cache
        self._update_default_pixmaps()
        self.setPixmap(self.shadow)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.setMargin(0)
        self.setAcceptDrops(drops)
        self.clicked.connect(self.open_release_page)
        self.related_images = []
        self.current_pixmap_key = None

    def screen_changed(self, screen):
        pixel_ratio = screen.devicePixelRatio()
        log.debug("screen changed, pixel ratio %s", pixel_ratio)
        if pixel_ratio != self.pixel_ratio:
            self.pixel_ratio = pixel_ratio
            self._update_default_pixmaps()
            if self.data:
                self.set_data(self.data, force=True, has_common_images=self.has_common_images)
            else:
                self.setPixmap(self.shadow)

    def _update_default_pixmaps(self):
        w, h = self.scaled(THUMBNAIL_WIDTH, THUMBNAIL_WIDTH)
        self.shadow = self._load_cached_default_pixmap(":/images/CoverArtShadow.png", w, h)
        self.file_missing_pixmap = self._load_cached_default_pixmap(":/images/image-missing.png", w, h)

    def _load_cached_default_pixmap(self, pixmap_path, w, h):
        key = hash((pixmap_path, self.pixel_ratio))
        try:
            pixmap = self._pixmap_cache[key]
        except KeyError:
            pixmap = QtGui.QPixmap(pixmap_path)
            pixmap = pixmap.scaled(w, h, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
            pixmap.setDevicePixelRatio(self.pixel_ratio)
            self._pixmap_cache[key] = pixmap
        return pixmap

    def __eq__(self, other):
        if len(self.data) or len(other.data):
            return self.current_pixmap_key == other.current_pixmap_key
        else:
            return True

    def dragEnterEvent(self, event):
        event.setDropAction(QtCore.Qt.DropAction.CopyAction)
        event.accept()

    def dropEvent(self, event):
        if event.proposedAction() == QtCore.Qt.DropAction.IgnoreAction:
            event.acceptProposedAction()
            return

        accepted = False
        # Chromium includes the actual data of the dragged image in the drop event. This
        # is useful for Google Images, where the url links to the page that contains the image
        # so we use it if the downloaded url is not an image.
        mime_data = event.mimeData()
        dropped_data = bytes(mime_data.data('application/octet-stream'))

        if not dropped_data:
            dropped_data = bytes(mime_data.data('application/x-qt-image'))

        if not dropped_data:
            # Maybe we can get something useful from a dropped HTML snippet.
            dropped_data = bytes(mime_data.data('text/html'))

        if not accepted:
            for url in mime_data.urls():
                if url.scheme() in {'https', 'http', 'file'}:
                    accepted = True
                    log.debug("Dropped %s url (with %d bytes of data)",
                              url.toString(), len(dropped_data or ''))
                    self.image_dropped.emit(url, dropped_data)

        if not accepted:
            if mime_data.hasImage():
                image_bytes = QtCore.QByteArray()
                image_buffer = QtCore.QBuffer(image_bytes)
                mime_data.imageData().save(image_buffer, 'JPEG')
                dropped_data = bytes(image_bytes)

                accepted = True
                log.debug("Dropped %d bytes of Qt image data", len(dropped_data))
                self.image_dropped.emit(QtCore.QUrl(''), dropped_data)

        if accepted:
            event.setDropAction(QtCore.Qt.DropAction.CopyAction)
            event.accept()

    def scaled(self, *dimensions):
        return (round(self.pixel_ratio * dimension) for dimension in dimensions)

    def show(self):
        self.set_data(self.data, True)

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

        key = hash(tuple(sorted(self.data, key=lambda x: x.types_as_string())) + (has_common_images, self.pixel_ratio))
        try:
            pixmap = self._pixmap_cache[key]
        except KeyError:
            if len(self.data) == 1:
                pixmap = QtGui.QPixmap()
                try:
                    if pixmap.loadFromData(self.data[0].data):
                        pixmap = self.decorate_cover(pixmap)
                    else:
                        pixmap = self.file_missing_pixmap
                except CoverArtImageIOError:
                    pixmap = self.file_missing_pixmap
            else:
                pixmap = self.render_cover_stack(self.data, has_common_images)
            self._pixmap_cache[key] = pixmap

        self.setPixmap(pixmap)
        self.current_pixmap_key = key

    def decorate_cover(self, pixmap):
        offx = offy = 1
        w = h = COVERART_WIDTH
        cover = QtGui.QPixmap(self.shadow)
        cover.setDevicePixelRatio(self.pixel_ratio)
        pixmap = pixmap.scaled(*self.scaled(w, h), QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
        pixmap.setDevicePixelRatio(self.pixel_ratio)
        painter = QtGui.QPainter(cover)
        bgcolor = QtGui.QColor.fromRgb(0, 0, 0, 128)
        painter.fillRect(QtCore.QRectF(offx, offy, w, h), bgcolor)
        self._draw_centered(painter, pixmap, w, h, offx, offy)
        painter.end()
        return cover

    @staticmethod
    def _draw_centered(painter, pixmap, width, height, offset_x=0, offset_y=0):
        pixel_ratio = pixmap.devicePixelRatio()
        x = int(offset_x + (width - pixmap.width() / pixel_ratio) // 2)
        y = int(offset_y + (height - pixmap.height() / pixel_ratio) // 2)
        painter.drawPixmap(x, y, pixmap)

    def render_cover_stack(self, data, has_common_images):
        w = h = THUMBNAIL_WIDTH
        displacements = 20
        limited = len(data) > MAX_COVERS_TO_STACK
        if limited:
            data_to_paint = data[:MAX_COVERS_TO_STACK - 1]
            offset = displacements * len(data_to_paint)
        else:
            data_to_paint = data
            offset = displacements * (len(data_to_paint) - 1)
        stack_width, stack_height = (w + offset, h + offset)
        pixmap = QtGui.QPixmap(*self.scaled(stack_width, stack_height))
        pixmap.setDevicePixelRatio(self.pixel_ratio)
        bgcolor = self.palette().color(QtGui.QPalette.ColorRole.Window)
        painter = QtGui.QPainter(pixmap)
        painter.fillRect(QtCore.QRectF(0, 0, stack_width, stack_height), bgcolor)
        cx = stack_width - w // 2
        cy = h // 2

        def calculate_cover_coordinates(pixmap, cx, cy):
            pixel_ratio = pixmap.devicePixelRatio()
            x = int(cx - pixmap.width() / pixel_ratio // 2)
            y = int(cy - pixmap.height() / pixel_ratio // 2)
            return x, y

        if limited:
            # Draw the default background three times to indicate that there are more
            # covers than the ones displayed
            x, y = calculate_cover_coordinates(self.shadow, cx, cy)
            for _i in range(3):
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
                try:
                    if not thumb.loadFromData(image.data):
                        thumb = self.file_missing_pixmap
                except CoverArtImageIOError:
                    thumb = self.file_missing_pixmap
            thumb = self.decorate_cover(thumb)
            x, y = calculate_cover_coordinates(thumb, cx, cy)
            painter.drawPixmap(x, y, thumb)
            cx -= displacements
            cy += displacements
        if not has_common_images:
            # Draw a highlight around the first cover to indicate that
            # images are not common to all selected items
            color = interface_colors.get_qcolor('first_cover_hl')
            border_length = 10
            for k in range(border_length):
                color.setAlpha(255 - k * 255 // border_length)
                painter.setPen(color)
                x_offset = x + COVERART_WIDTH + k
                # Horizontal line above the cover
                painter.drawLine(x, y - k - 1, x_offset + 1, y - k - 1)
                # Vertical line right of the cover
                painter.drawLine(x_offset + 2, y - 1 - k, x_offset + 2, y + COVERART_WIDTH + 4)
            # A bit of shadow
            for k in range(5):
                bgcolor.setAlpha(80 + k * 255 // 7)
                painter.setPen(bgcolor)
                painter.drawLine(x + COVERART_WIDTH + 2, y + COVERART_WIDTH + 2 + k, x + COVERART_WIDTH + border_length + 2, y + COVERART_WIDTH + 2 + k)
        painter.end()
        return pixmap.scaled(*self.scaled(w, h), QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)

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
            release = metadata.get('musicbrainz_albumid', None)
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
