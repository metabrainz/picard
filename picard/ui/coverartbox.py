# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2011 Lukáš Lalinský
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009, 2018-2023 Philipp Wolfer
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
import os
import re

from PyQt6 import (
    QtCore,
    QtGui,
    QtNetwork,
    QtWidgets,
)

from picard import log
from picard.album import Album
from picard.cluster import Cluster
from picard.config import get_config
from picard.const import MAX_COVERS_TO_STACK
from picard.coverart.image import (
    CoverArtImage,
    CoverArtImageError,
    CoverArtImageIOError,
)
from picard.file import File
from picard.i18n import gettext as _
from picard.item import FileListItem
from picard.track import Track
from picard.util import (
    imageinfo,
    normpath,
)
from picard.util.lrucache import LRUCache

from picard.ui.colors import interface_colors
from picard.ui.widgets import ActiveLabel


THUMBNAIL_WIDTH = 128
COVERART_WIDTH = THUMBNAIL_WIDTH - 7


class CoverArtThumbnail(ActiveLabel):
    image_dropped = QtCore.pyqtSignal(QtCore.QUrl, bytes)

    def __init__(self, active=False, drops=False, pixmap_cache=None, *args, **kwargs):
        super().__init__(active, drops, *args, **kwargs)
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


def set_image_replace(obj, coverartimage):
    obj.metadata.images.strip_front_images()
    obj.metadata.images.append(coverartimage)
    obj.metadata_images_changed.emit()


def set_image_append(obj, coverartimage):
    obj.metadata.images.append(coverartimage)
    obj.metadata_images_changed.emit()


def iter_file_parents(file):
    parent = file.parent
    if parent:
        yield parent
        if isinstance(parent, Track) and parent.album:
            yield parent.album
        elif isinstance(parent, Cluster) and parent.related_album:
            yield parent.related_album


HTML_IMG_SRC_REGEX = re.compile(r'<img .*?src="(.*?)"', re.UNICODE)


class CoverArtBox(QtWidgets.QGroupBox):

    def __init__(self, parent):
        super().__init__("")
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setSpacing(6)
        self.parent = parent
        self.tagger = QtCore.QCoreApplication.instance()
        # Kills off any borders
        self.setStyleSheet('''QGroupBox{background-color:none;border:1px;}''')
        self.setFlat(True)
        self.item = None
        self.pixmap_cache = LRUCache(40)
        self.cover_art_label = QtWidgets.QLabel('')
        self.cover_art_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.cover_art = CoverArtThumbnail(False, True, self.pixmap_cache, parent)
        self.cover_art.image_dropped.connect(self.fetch_remote_image)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.orig_cover_art_label = QtWidgets.QLabel('')
        self.orig_cover_art = CoverArtThumbnail(False, False, self.pixmap_cache, parent)
        self.orig_cover_art_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.show_details_button = QtWidgets.QPushButton(_('Show more details'), self)
        self.show_details_shortcut = QtGui.QShortcut(QtGui.QKeySequence(_("Ctrl+Shift+I")), self, self.show_cover_art_info)
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
            self.show_details_button.setVisible(bool(self.item and self.item.can_view_info))
            self.orig_cover_art.setVisible(False)
            self.cover_art_label.setText('')
            self.orig_cover_art_label.setText('')
        else:
            self.show_details_button.setVisible(True)
            self.orig_cover_art.setVisible(True)
            self.cover_art_label.setText(_('New Cover Art'))
            self.orig_cover_art_label.setText(_('Original Cover Art'))

    def set_item(self, item):
        if not item.can_show_coverart:
            self.cover_art.set_metadata(None)
            self.orig_cover_art.set_metadata(None)
            return

        if self.item and hasattr(self.item, 'metadata_images_changed'):
            self.item.metadata_images_changed.disconnect(self.update_metadata)
        self.item = item
        if hasattr(self.item, 'metadata_images_changed'):
            self.item.metadata_images_changed.connect(self.update_metadata)
        self.update_metadata()

    def update_metadata(self):
        if not self.item:
            return

        metadata = self.item.metadata
        orig_metadata = None
        if hasattr(self.item, 'orig_metadata'):
            orig_metadata = self.item.orig_metadata

        if not metadata or not metadata.images:
            self.cover_art.set_metadata(orig_metadata)
        else:
            self.cover_art.set_metadata(metadata)
        self.orig_cover_art.set_metadata(orig_metadata)
        self.update_display()

    def fetch_remote_image(self, url, fallback_data=None):
        if self.item is None:
            return

        if fallback_data:
            self.load_remote_image(url, fallback_data)

        if url.scheme() in {'http', 'https'}:
            self.tagger.webservice.download_url(
                url=url,
                handler=partial(self.on_remote_image_fetched, url, fallback_data=fallback_data),
                priority=True,
                important=True,
            )
        elif url.scheme() == 'file':
            path = normpath(url.toLocalFile().rstrip("\0"))
            if path and os.path.exists(path):
                with open(path, 'rb') as f:
                    data = f.read()
                self.load_remote_image(url, data)

    def on_remote_image_fetched(self, url, data, reply, error, fallback_data=None):
        if error:
            log.error("Failed loading remote image from %s: %s", url, reply.errorString())
            if fallback_data:
                self._load_fallback_data(url, fallback_data)
            return

        data = bytes(data)
        mime = reply.header(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader)
        # Some sites return a mime type with encoding like "image/jpeg; charset=UTF-8"
        mime = mime.split(';')[0]
        url_query = QtCore.QUrlQuery(url.query())
        log.debug('Fetched remote image with MIME-Type %s from %s', mime, url.toString())
        # If mime indicates only binary data we can try to guess the real mime type
        if (mime in {'application/octet-stream', 'binary/data'} or mime.startswith('image/')
              or imageinfo.supports_mime_type(mime)):
            try:
                self._try_load_remote_image(url, data)
                return
            except CoverArtImageError:
                pass
        if url_query.hasQueryItem("imgurl"):
            # This may be a google images result, try to get the URL which is encoded in the query
            url = QtCore.QUrl(url_query.queryItemValue("imgurl", QtCore.QUrl.ComponentFormattingOption.FullyDecoded))
            log.debug('Possible Google images result, trying to fetch imgurl=%s', url.toString())
            self.fetch_remote_image(url)
        elif url_query.hasQueryItem("mediaurl"):
            # Bing uses mediaurl
            url = QtCore.QUrl(url_query.queryItemValue("mediaurl", QtCore.QUrl.ComponentFormattingOption.FullyDecoded))
            log.debug('Possible Bing images result, trying to fetch imgurl=%s', url.toString())
            self.fetch_remote_image(url)
        else:
            log.warning("Can't load remote image with MIME-Type %s", mime)
            if fallback_data:
                self._load_fallback_data(url, fallback_data)

    def _load_fallback_data(self, url, data):
        try:
            log.debug("Trying to load image from dropped data")
            self._try_load_remote_image(url, data)
            return
        except CoverArtImageError as e:
            log.debug("Unable to identify dropped data format: %s", e)

        # Try getting image out of HTML (e.g. for Google image search detail view)
        try:
            html = data.decode()
            match_ = re.search(HTML_IMG_SRC_REGEX, html)
            if match_:
                url = QtCore.QUrl(match_.group(1))
        except UnicodeDecodeError as e:
            log.warning("Unable to decode dropped data format: %s", e)
        else:
            log.debug("Trying URL parsed from HTML: %s", url.toString())
            self.fetch_remote_image(url)

    def load_remote_image(self, url, data):
        try:
            self._try_load_remote_image(url, data)
        except CoverArtImageError as e:
            log.warning("Can't load image: %s", e)
            return

    def _try_load_remote_image(self, url, data):
        coverartimage = CoverArtImage(
            url=url.toString(),
            types=['front'],
            data=data
        )

        config = get_config()
        if config.setting['load_image_behavior'] == 'replace':
            set_image = set_image_replace
            debug_info = "Replacing with dropped %r in %r"
        else:
            set_image = set_image_append
            debug_info = "Appending dropped %r to %r"

        if isinstance(self.item, Album):
            album = self.item
            with album.suspend_metadata_images_update:
                set_image(album, coverartimage)
                for track in album.tracks:
                    track.suspend_metadata_images_update = True
                    set_image(track, coverartimage)
                for file in album.iterfiles():
                    set_image(file, coverartimage)
                    file.update(signal=False)
                for track in album.tracks:
                    track.suspend_metadata_images_update = False
            album.update(update_tracks=False)
        elif isinstance(self.item, FileListItem):
            parents = set()
            filelist = self.item
            with filelist.suspend_metadata_images_update:
                set_image(filelist, coverartimage)
                for file in filelist.iterfiles():
                    for parent in iter_file_parents(file):
                        parent.suspend_metadata_images_update = True
                        parents.add(parent)
                    set_image(file, coverartimage)
                    file.update(signal=False)
                for parent in parents:
                    set_image(parent, coverartimage)
                    parent.suspend_metadata_images_update = False
                    if isinstance(parent, Album):
                        parent.update(update_tracks=False)
                    else:
                        parent.update()
            filelist.update()
        elif isinstance(self.item, File):
            file = self.item
            set_image(file, coverartimage)
            file.update()
        else:
            debug_info = "Dropping %r to %r is not handled"

        log.debug(debug_info, coverartimage, self.item)
        return coverartimage

    def choose_local_file(self):
        file_chooser = QtWidgets.QFileDialog(self)
        extensions = ['*' + ext for ext in imageinfo.get_supported_extensions()]
        extensions.sort()
        file_chooser.setNameFilters([
            _("All supported image formats") + " (" + " ".join(extensions) + ")",
            _("All files") + " (*)",
        ])
        if file_chooser.exec():
            file_urls = file_chooser.selectedUrls()
            if file_urls:
                self.fetch_remote_image(file_urls[0])

    def set_load_image_behavior(self, behavior):
        config = get_config()
        config.setting['load_image_behavior'] = behavior

    def keep_original_images(self):
        self.item.keep_original_images()
        self.cover_art.set_metadata(self.item.metadata)
        self.show()

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        if self.show_details_button.isVisible():
            name = _("Show more details…")
            show_more_details_action = QtGui.QAction(name, self.parent)
            show_more_details_action.triggered.connect(self.show_cover_art_info)
            menu.addAction(show_more_details_action)

        if self.orig_cover_art.isVisible():
            name = _("Keep original cover art")
            use_orig_value_action = QtGui.QAction(name, self.parent)
            use_orig_value_action.triggered.connect(self.keep_original_images)
            menu.addAction(use_orig_value_action)

        if self.item and self.item.can_show_coverart:
            name = _("Choose local file…")
            choose_local_file_action = QtGui.QAction(name, self.parent)
            choose_local_file_action.triggered.connect(self.choose_local_file)
            menu.addAction(choose_local_file_action)

        if not menu.isEmpty():
            menu.addSeparator()

        load_image_behavior_group = QtGui.QActionGroup(self.parent)
        action = QtGui.QAction(_("Replace front cover art"), self.parent)
        action.setCheckable(True)
        action.triggered.connect(partial(self.set_load_image_behavior, behavior='replace'))
        load_image_behavior_group.addAction(action)
        config = get_config()
        if config.setting['load_image_behavior'] == 'replace':
            action.setChecked(True)
        menu.addAction(action)

        action = QtGui.QAction(_("Append front cover art"), self.parent)
        action.setCheckable(True)
        action.triggered.connect(partial(self.set_load_image_behavior, behavior='append'))
        load_image_behavior_group.addAction(action)
        if config.setting['load_image_behavior'] == 'append':
            action.setChecked(True)
        menu.addAction(action)

        menu.exec(event.globalPos())
        event.accept()
