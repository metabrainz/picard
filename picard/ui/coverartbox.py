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
from PyQt4 import QtCore, QtGui, QtNetwork
from picard.album import Album
from picard.track import Track
from picard.file import File
from picard.util import webbrowser2, encode_filename
from picard.const import AMAZON_STORE_ASSOCIATE_IDS


class ActiveLabel(QtGui.QLabel):
    """Clickable QLabel."""

    clicked = QtCore.pyqtSignal()
    imageDropped = QtCore.pyqtSignal(QtCore.QUrl)

    def __init__(self, active=True, *args):
        QtGui.QLabel.__init__(self, *args)
        self.setActive(active)
        self.setAcceptDrops(True)

    def setActive(self, active):
        self.active = active
        if self.active:
            self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        else:
            self.setCursor(QtGui.QCursor())

    def mouseReleaseEvent(self, event):
        if self.active:
            self.clicked.emit()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        accepted = False
        for url in event.mimeData().urls():
            if url.scheme() in ('http', 'file'):
                accepted = True
                self.imageDropped.emit(url)
        if accepted:
            event.acceptProposedAction()


class CoverArtBox(QtGui.QGroupBox):

    def __init__(self, parent):
        QtGui.QGroupBox.__init__(self, " ")
        self.layout = QtGui.QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins (7,7,0,0)
        # Kills off any borders
        self.setStyleSheet('''QGroupBox{background-color:none;border:1px;}''')
        self.setFlat(True)
        self.asin = None
        self.data = None
        self.item = None
        self.shadow = QtGui.QPixmap(":/images/CoverArtShadow.png")
        self.coverArt = ActiveLabel(False, parent)
        self.coverArt.setPixmap(self.shadow)
        self.coverArt.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        self.coverArt.clicked.connect(self.open_amazon)
        self.coverArt.imageDropped.connect(self.fetch_remote_image)
        self.layout.addWidget(self.coverArt, 0)
        self.setLayout(self.layout)

    def show(self):
        self.__set_data(self.data, True)
        QtGui.QGroupBox.show(self)

    def __set_data(self, data, force=False, pixmap=None):
        if not force and self.data == data:
            return

        self.data = data
        if not force and self.isHidden():
            return

        cover = self.shadow
        if self.data:
            if pixmap is None:
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(self.data[1])
            if not pixmap.isNull():
                cover = QtGui.QPixmap(self.shadow)
                pixmap = pixmap.scaled(121,121 , QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
                painter = QtGui.QPainter(cover)
                painter.drawPixmap(1, 1, pixmap)
                painter.end()
        self.coverArt.setPixmap(cover)

    def set_metadata(self, metadata, item):
        self.item = item
        data = None
        if metadata and metadata.images:
            data = metadata.images[0]
        self.__set_data(data)
        if metadata:
            asin = metadata.get("asin", None)
        else:
            asin = None
        if asin != self.asin:
            if asin:
                self.coverArt.setActive(True)
                self.coverArt.setToolTip(_(u"Buy the album on Amazon"))
            else:
                self.coverArt.setActive(False)
                self.coverArt.setToolTip("")
            self.asin = asin

    def open_amazon(self):
        # TODO: make this configurable
        store = "amazon.com"
        url = "http://%s/exec/obidos/ASIN/%s/%s?v=glance&s=music" % (
            store, self.asin, AMAZON_STORE_ASSOCIATE_IDS[store])
        webbrowser2.open(url)

    def fetch_remote_image(self, url):
        if self.item is None:
            return
        if url.scheme() == 'http':
            path = url.encodedPath()
            if url.hasQuery():
                path += '?' + url.encodedQuery()
            self.tagger.xmlws.get(url.encodedHost(), url.port(80), path,
                self.on_remote_image_fetched, xml=False,
                priority=True, important=True)
        elif url.scheme() == 'file':
            path = encode_filename(unicode(url.toLocalFile()))
            if os.path.exists(path):
                f = open(path, 'rb')
                mime = 'image/png' if '.png' in path.lower() else 'image/jpeg'
                data = f.read()
                f.close()
                self.load_remote_image(mime, data)

    def on_remote_image_fetched(self, data, reply, error):
        mime = reply.header(QtNetwork.QNetworkRequest.ContentTypeHeader)
        if mime not in ('image/jpeg', 'image/png'):
            self.log.warning("Can't load image with MIME-Type %s", str(mime))
            return
        return self.load_remote_image(mime, data)

    def load_remote_image(self, mime, data):
        pixmap = QtGui.QPixmap()
        if not pixmap.loadFromData(data):
            self.log.warning("Can't load image")
            return
        self.__set_data([mime, data], pixmap=pixmap)
        if isinstance(self.item, Album):
            album = self.item
            album.metadata.add_image(mime, data)
            for track in album.tracks:
                track.metadata.add_image(mime, data)
            for file in album.iterfiles():
                file.metadata.add_image(mime, data)
        elif isinstance(self.item, Track):
            track = self.item
            track.metadata.add_image(mime, data)
            for file in track.iterfiles():
                file.metadata.add_image(mime, data)
        elif isinstance(self.item, File):
            file = self.item
            file.metadata.add_image(mime, data)

