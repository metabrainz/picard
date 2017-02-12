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
from PyQt4 import QtCore, QtGui, QtNetwork
from picard import config, log
from picard.album import Album
from picard.coverart.image import CoverArtImage, CoverArtImageError
from picard.track import Track
from picard.file import File
from picard.util import encode_filename


class ActiveLabel(QtGui.QLabel):

    """Clickable QLabel."""

    clicked = QtCore.pyqtSignal()
    imageDropped = QtCore.pyqtSignal(QtCore.QUrl)

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
            if url.scheme() in ('http', 'file'):
                event.acceptProposedAction()
                break

    def dropEvent(self, event):
        accepted = False
        for url in event.mimeData().urls():
            if url.scheme() in ('http', 'file'):
                accepted = True
                self.imageDropped.emit(url)
        if accepted:
            event.acceptProposedAction()


class CoverArtThumbnail(ActiveLabel):

    def __init__(self, active=False, drops=False, *args, **kwargs):
        super(CoverArtThumbnail, self).__init__(active, drops, *args, **kwargs)
        self.data = None
        self.shadow = QtGui.QPixmap(":/images/CoverArtShadow.png")
        self.release = None
        self.setPixmap(self.shadow)
        self.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        self.clicked.connect(self.open_release_page)
        self.imageDropped.connect(self.fetch_remote_image)

    def __eq__(self, other):
        if self.data and other.data:
            return self.data.data == other.data.data
        else:
            return False

    def show(self):
        self.set_data(self.data, True)

    def set_data(self, data, force=False, pixmap=None):
        if not force and self.data == data:
            return

        self.data = data
        if not force and self.parent().isHidden():
            return

        cover = self.shadow
        if self.data:
            if pixmap is None:
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(self.data.data)
            if not pixmap.isNull():
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
        self.setPixmap(cover)

    def set_metadata(self, metadata):
        data = None
        if metadata and metadata.images:
            for image in metadata.images:
                if image.is_front_image():
                    data = image
                    break
            else:
                # There's no front image, choose the first one available
                data = metadata.images[0]
        self.set_data(data)
        release = None
        if metadata:
            release = metadata.get("musicbrainz_albumid", None)
        if release:
            self.setActive(True)
            self.setToolTip(_(u"View release on MusicBrainz"))
        else:
            self.setActive(False)
            self.setToolTip("")
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
        # Kills off any borders
        self.setStyleSheet('''QGroupBox{background-color:none;border:1px;}''')
        self.setFlat(True)
        self.item = None
        self.cover_art_label = QtGui.QLabel('')
        self.cover_art_label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        self.cover_art = CoverArtThumbnail(False, True, parent)
        self.orig_cover_art_label = QtGui.QLabel('')
        self.orig_cover_art = CoverArtThumbnail(False, False, parent)
        self.orig_cover_art_label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        self.orig_cover_art.setHidden(True)
        self.layout.addWidget(self.cover_art_label)
        self.layout.addWidget(self.cover_art)
        self.layout.addWidget(self.orig_cover_art_label)
        self.layout.addWidget(self.orig_cover_art)
        self.setLayout(self.layout)

    def _show(self):
        # We want to show the 2 coverarts only if they are different
        # and orig_cover_art is not None
        if getattr(self.orig_cover_art, 'data', None) is None or self.cover_art == self.orig_cover_art:
            self.orig_cover_art.setHidden(True)
            self.cover_art_label.setText('')
            self.orig_cover_art_label.setText('')
        else:
            self.orig_cover_art.setHidden(False)
            self.cover_art_label.setText('New Cover-Art')
            self.orig_cover_art_label.setText('Original Cover-Art')

    def show(self):
        self.cover_art.show()
        if self.orig_cover_art.data:
            self.orig_cover_art.show()
            self._show()
        QtGui.QGroupBox.show(self)

    def set_metadata(self, metadata, orig_metadata, item):
        self.cover_art.set_metadata(metadata)
        self.orig_cover_art.set_metadata(orig_metadata)
        self._show()
        if item:
            self.item = item

    def fetch_remote_image(self, url):
        if self.item is None:
            return
        if url.scheme() == 'http':
            path = url.encodedPath()
            if url.hasQuery():
                path += '?' + url.encodedQuery()
            self.tagger.xmlws.get(url.encodedHost(), url.port(80), path,
                                  partial(self.on_remote_image_fetched, url),
                                  xml=False,
                                  priority=True, important=True)
        elif url.scheme() == 'file':
            path = encode_filename(unicode(url.toLocalFile()))
            if os.path.exists(path):
                mime = 'image/png' if path.lower().endswith('.png') else 'image/jpeg'
                with open(path, 'rb') as f:
                    data = f.read()
                self.load_remote_image(url, mime, data)

    def on_remote_image_fetched(self, url, data, reply, error):
        mime = reply.header(QtNetwork.QNetworkRequest.ContentTypeHeader)
        if mime in ('image/jpeg', 'image/png'):
            self.load_remote_image(url, mime, data)
        elif reply.url().hasQueryItem("imgurl"):
            # This may be a google images result, try to get the URL which is encoded in the query
            url = QtCore.QUrl(reply.url().queryItemValue("imgurl"))
            self.fetch_remote_image(url)
        else:
            log.warning("Can't load image with MIME-Type %s", mime)

    def load_remote_image(self, url, mime, data):
        try:
            coverartimage = CoverArtImage(
                url=url.toString(),
                data=data
            )
        except CoverArtImageError as e:
            log.warning("Can't load image: %s" % unicode(e))
            return
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(data)
        self.cover_art.set_data([mime, data], pixmap=pixmap)
        self._show()
        if isinstance(self.item, Album):
            album = self.item
            album.metadata.append_image(coverartimage)
            for track in album.tracks:
                track.metadata.append_image(coverartimage)
            for file in album.iterfiles():
                file.metadata.append_image(coverartimage)
        elif isinstance(self.item, Track):
            track = self.item
            track.metadata.append_image(coverartimage)
            for file in track.iterfiles():
                file.metadata.append_image(coverartimage)
        elif isinstance(self.item, File):
            file = self.item
            file.metadata.append_image(coverartimage)
