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
from picard.config import get_config
from picard.coverart.image import (
    CoverArtImage,
    CoverArtImageError,
)
from picard.i18n import gettext as _
from picard.util import (
    imageinfo,
    normpath,
)
from picard.util.lrucache import LRUCache

from .coverartsetter import (
    CoverArtSetter,
    CoverArtSetterMode,
)
from .coverartthumbnail import CoverArtThumbnail
from .imageurldialog import ImageURLDialog

from picard.ui.util import FileDialog


HTML_IMG_SRC_REGEX = re.compile(r'<img .*?src="(.*?)"', re.UNICODE)


class CoverArtBox(QtWidgets.QGroupBox):

    def __init__(self, parent=None):
        super().__init__("", parent=parent)
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setSpacing(6)
        self.tagger = QtCore.QCoreApplication.instance()
        # Kills off any borders
        self.setStyleSheet('''QGroupBox{background-color:none;border:1px;}''')
        self.setFlat(True)
        self.item = None
        self.pixmap_cache = LRUCache(40)
        self.cover_art_label = QtWidgets.QLabel('')
        self.cover_art_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.cover_art = CoverArtThumbnail(drops=True, pixmap_cache=self.pixmap_cache, parent=self)
        self.cover_art.image_dropped.connect(self.fetch_remote_image)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.orig_cover_art_label = QtWidgets.QLabel('')
        self.orig_cover_art = CoverArtThumbnail(drops=False, pixmap_cache=self.pixmap_cache, parent=self)
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
        self.tagger.window.view_info(default_tab=1)

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
            mode = CoverArtSetterMode.REPLACE
        else:
            mode = CoverArtSetterMode.APPEND

        setter = CoverArtSetter(mode, coverartimage, self.item)
        setter.set_coverart()

        return coverartimage

    def choose_local_file(self):
        file_chooser = FileDialog(parent=self)
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

    def choose_image_from_url(self):
        url, ok = ImageURLDialog.display(parent=self)
        if ok:
            self.fetch_remote_image(url)

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
            name = _("Show &more details…")
            show_more_details_action = QtGui.QAction(name, parent=menu)
            show_more_details_action.triggered.connect(self.show_cover_art_info)
            menu.addAction(show_more_details_action)

        if self.orig_cover_art.isVisible():
            name = _("Keep original cover art")
            use_orig_value_action = QtGui.QAction(name, parent=menu)
            use_orig_value_action.triggered.connect(self.keep_original_images)
            menu.addAction(use_orig_value_action)

        if self.item and self.item.can_show_coverart:
            name = _("Choose local file…")
            choose_local_file_action = QtGui.QAction(name, parent=menu)
            choose_local_file_action.triggered.connect(self.choose_local_file)
            menu.addAction(choose_local_file_action)
            name = _("Add from URL…")
            choose_image_from_url_action = QtGui.QAction(name, parent=menu)
            choose_image_from_url_action.triggered.connect(self.choose_image_from_url)
            menu.addAction(choose_image_from_url_action)

        if not menu.isEmpty():
            menu.addSeparator()

        load_image_behavior_group = QtGui.QActionGroup(menu)
        action = QtGui.QAction(_("Replace front cover art"), parent=load_image_behavior_group)
        action.setCheckable(True)
        action.triggered.connect(partial(self.set_load_image_behavior, behavior='replace'))
        config = get_config()
        if config.setting['load_image_behavior'] == 'replace':
            action.setChecked(True)
        menu.addAction(action)

        action = QtGui.QAction(_("Append front cover art"), parent=load_image_behavior_group)
        action.setCheckable(True)
        action.triggered.connect(partial(self.set_load_image_behavior, behavior='append'))
        if config.setting['load_image_behavior'] == 'append':
            action.setChecked(True)
        menu.addAction(action)

        menu.exec(event.globalPos())
        event.accept()
