# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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

import os.path
import traceback

from PyQt5 import (QtCore,
                   QtGui,
                   QtWidgets)

from picard import log
from picard.album import Album
from picard.coverart.image import CoverArtImageIOError
from picard.file import File
from picard.track import Track
from picard.ui import PicardDialog
from picard.ui.ui_infodialog import Ui_InfoDialog
from picard.util import (bytes2human,
                         encode_filename,
                         format_time,
                         htmlescape,
                         union_sorted_lists,
                         webbrowser2)


class ArtworkTable(QtWidgets.QTableWidget):
    def __init__(self, display_existing_art):
        QtWidgets.QTableWidget.__init__(self, 0, 2)
        self.display_existing_art = display_existing_art
        h_header = self.horizontalHeader()
        v_header = self.verticalHeader()
        h_header.setDefaultSectionSize(200)
        v_header.setDefaultSectionSize(230)
        if self.display_existing_art:
            self._existing_cover_col = 0
            self._type_col = 1
            self._new_cover_col = 2
            self.insertColumn(2)
            self.setHorizontalHeaderLabels([_("Existing Cover"), _("Type"),
                                            _("New Cover")])
            self.arrow_pixmap = QtGui.QPixmap(":/images/arrow.png")
        else:
            self._type_col = 0
            self._new_cover_col = 1
            self.setHorizontalHeaderLabels([_("Type"), _("Cover")])
            self.setColumnWidth(self._type_col, 140)

    def get_coverart_widget(self, pixmap, text):
        """Return a QWidget that can be added to artwork column cell of ArtworkTable."""
        coverart_widget = QtWidgets.QWidget()
        image_label = QtWidgets.QLabel()
        text_label = QtWidgets.QLabel()
        layout = QtWidgets.QVBoxLayout()
        image_label.setPixmap(pixmap.scaled(170, 170, QtCore.Qt.KeepAspectRatio,
                                            QtCore.Qt.SmoothTransformation))
        image_label.setAlignment(QtCore.Qt.AlignCenter)
        text_label.setText(text)
        text_label.setAlignment(QtCore.Qt.AlignCenter)
        text_label.setWordWrap(True)
        layout.addWidget(image_label)
        layout.addWidget(text_label)
        coverart_widget.setLayout(layout)
        return coverart_widget

    def get_type_widget(self, type_text):
        """Return a QWidget that can be added to type column cell of ArtworkTable.
        If both existing and new artwork are to be displayed, insert an arrow icon to make comparison
        obvious.
        """
        type_widget = QtWidgets.QWidget()
        type_label = QtWidgets.QLabel()
        layout = QtWidgets.QVBoxLayout()
        type_label.setText(type_text)
        type_label.setAlignment(QtCore.Qt.AlignCenter)
        type_label.setWordWrap(True)
        if self.display_existing_art:
            arrow_label = QtWidgets.QLabel()
            arrow_label.setPixmap(self.arrow_pixmap.scaled(170, 170, QtCore.Qt.KeepAspectRatio,
                                                           QtCore.Qt.SmoothTransformation))
            arrow_label.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(arrow_label)
            layout.addWidget(type_label)
        else:
            layout.addWidget(type_label)
        type_widget.setLayout(layout)
        return type_widget


class InfoDialog(PicardDialog):

    def __init__(self, obj, parent=None):
        PicardDialog.__init__(self, parent)
        self.obj = obj
        self.images = []
        self.existing_images = []
        self.ui = Ui_InfoDialog()
        self.display_existing_artwork = False

        if (isinstance(obj, File) and
                isinstance(obj.parent, Track) or
                isinstance(obj, Track) or
                (isinstance(obj, Album) and obj.get_num_total_files() > 0)):
            # Display existing artwork only if selected object is track object
            # or linked to a track object or it's an album with files
            if (getattr(obj, 'orig_metadata', None) is not None and
                    obj.orig_metadata.images and
                    obj.orig_metadata.images != obj.metadata.images):
                self.display_existing_artwork = True
                self.existing_images = obj.orig_metadata.images

        if obj.metadata.images:
            self.images = obj.metadata.images
        if not self.images and self.existing_images:
            self.images = self.existing_images
            self.existing_images = []
            self.display_existing_artwork = False
        self.ui.setupUi(self)
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)

        # Add the ArtworkTable to the ui
        self.ui.artwork_table = ArtworkTable(self.display_existing_artwork)
        self.ui.artwork_table.setObjectName("artwork_table")
        self.ui.vboxlayout1.addWidget(self.ui.artwork_table)
        if self.display_existing_artwork:
            self.resize(665, 436)
        self.setTabOrder(self.ui.tabWidget, self.ui.artwork_table)
        self.setTabOrder(self.ui.artwork_table, self.ui.buttonBox)

        self.setWindowTitle(_("Info"))
        self.artwork_table = self.ui.artwork_table
        self._display_tabs()

    def _display_tabs(self):
        self._display_info_tab()
        self._display_artwork_tab()

    def _display_artwork(self, images, col):
        """Draw artwork in corresponding cell if image type matches type in Type column.

        Arguments:
        images -- The images to be drawn.
        col -- Column in which images are to be drawn. Can be _new_cover_col or _existing_cover_col.
        """
        row = 0
        row_count = self.artwork_table.rowCount()
        for image in images:
            while row != row_count:
                image_type = self.artwork_table.item(row, self.artwork_table._type_col)
                if image_type and image_type.data(QtCore.Qt.UserRole) == image.types_as_string():
                    break
                row += 1
            if row == row_count:
                continue
            data = None
            try:
                if image.thumbnail:
                    try:
                        data = image.thumbnail.data
                    except CoverArtImageIOError as e:
                        log.warning(e)
                else:
                    data = image.data
            except CoverArtImageIOError:
                log.error(traceback.format_exc())
                continue
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.UserRole, image)
            pixmap = QtGui.QPixmap()
            if data is not None:
                pixmap.loadFromData(data)
                item.setToolTip(
                        _("Double-click to open in external viewer\n"
                          "Temporary file: %s\n"
                          "Source: %s") % (image.tempfile_filename, image.source))
            infos = []
            if image.comment:
                infos.append(image.comment)
            infos.append("%s (%s)" %
                         (bytes2human.decimal(image.datalength),
                          bytes2human.binary(image.datalength)))
            if image.width and image.height:
                infos.append("%d x %d" % (image.width, image.height))
            infos.append(image.mimetype)

            img_wgt = self.artwork_table.get_coverart_widget(pixmap, "\n".join(infos))
            self.artwork_table.setCellWidget(row, col, img_wgt)
            self.artwork_table.setItem(row, col, item)
            row += 1

    def _display_artwork_type(self):
        """Display image type in Type column.
        If both existing covers and new covers are to be displayed, take union of both cover types list.
        """
        types = [image.types_as_string() for image in self.images]
        if self.display_existing_artwork:
            existing_types = [image.types_as_string() for image in self.existing_images]
            # Merge both types and existing types list in sorted order.
            types = union_sorted_lists(types, existing_types)
        for row, artwork_type in enumerate(types):
            self.artwork_table.insertRow(row)
            type_wgt = self.artwork_table.get_type_widget(artwork_type)
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.UserRole, artwork_type)
            self.artwork_table.setCellWidget(row, self.artwork_table._type_col, type_wgt)
            self.artwork_table.setItem(row, self.artwork_table._type_col, item)

    def _display_artwork_tab(self):
        if not self.images:
            self.tab_hide(self.ui.artwork_tab)
        self._display_artwork_type()
        self._display_artwork(self.images, self.artwork_table._new_cover_col)
        if self.existing_images:
            self._display_artwork(self.existing_images, self.artwork_table._existing_cover_col)
        self.artwork_table.itemDoubleClicked.connect(self.show_item)

    def tab_hide(self, widget):
        tab = self.ui.tabWidget
        index = tab.indexOf(widget)
        tab.removeTab(index)

    def show_item(self, item):
        data = item.data(QtCore.Qt.UserRole)
        # Check if this function isn't triggered by cell in Type column
        if isinstance(data, str):
            return
        filename = data.tempfile_filename
        if filename:
            webbrowser2.open("file://" + filename)


class FileInfoDialog(InfoDialog):

    def __init__(self, file, parent=None):
        InfoDialog.__init__(self, file, parent)
        self.setWindowTitle(_("Info") + " - " + file.base_filename)

    @staticmethod
    def format_file_info(file):
        info = []
        info.append((_('Filename:'), file.filename))
        if '~format' in file.orig_metadata:
            info.append((_('Format:'), file.orig_metadata['~format']))
        try:
            size = os.path.getsize(encode_filename(file.filename))
            sizestr = "%s (%s)" % (bytes2human.decimal(size), bytes2human.binary(size))
            info.append((_('Size:'), sizestr))
        except:
            pass
        if file.orig_metadata.length:
            info.append((_('Length:'), format_time(file.orig_metadata.length)))
        if '~bitrate' in file.orig_metadata:
            info.append((_('Bitrate:'), '%s kbps' % file.orig_metadata['~bitrate']))
        if '~sample_rate' in file.orig_metadata:
            info.append((_('Sample rate:'), '%s Hz' % file.orig_metadata['~sample_rate']))
        if '~bits_per_sample' in file.orig_metadata:
            info.append((_('Bits per sample:'), string_(file.orig_metadata['~bits_per_sample'])))
        if '~channels' in file.orig_metadata:
            ch = file.orig_metadata['~channels']
            if ch == 1:
                ch = _('Mono')
            elif ch == 2:
                ch = _('Stereo')
            else:
                ch = string_(ch)
            info.append((_('Channels:'), ch))
        return '<br/>'.join(map(lambda i: '<b>%s</b><br/>%s' %
                                          (htmlescape(i[0]),
                                           htmlescape(i[1])), info))

    def _display_info_tab(self):
        file = self.obj
        text = FileInfoDialog.format_file_info(file)
        self.ui.info.setText(text)


class AlbumInfoDialog(InfoDialog):

    def __init__(self, album, parent=None):
        InfoDialog.__init__(self, album, parent)
        self.setWindowTitle(_("Album Info"))

    def _display_info_tab(self):
        tab = self.ui.info_tab
        album = self.obj
        tabWidget = self.ui.tabWidget
        tab_index = tabWidget.indexOf(tab)
        if album.errors:
            tabWidget.setTabText(tab_index, _("&Errors"))
            text = '<br />'.join(map(lambda s: '<font color="darkred">%s</font>' %
                                               '<br />'.join(htmlescape(s)
                                                             .replace('\t', ' ')
                                                             .replace(' ', '&nbsp;')
                                                             .splitlines()
                                                             ), album.errors)
                                 )
            self.ui.info.setText(text + '<hr />')
        else:
            tabWidget.setTabText(tab_index, _("&Info"))
            self.tab_hide(tab)


class TrackInfoDialog(FileInfoDialog):

    def __init__(self, track, parent=None):
        InfoDialog.__init__(self, track, parent)
        self.setWindowTitle(_("Track Info"))

    def _display_info_tab(self):
        track = self.obj
        tab = self.ui.info_tab
        tabWidget = self.ui.tabWidget
        tab_index = tabWidget.indexOf(tab)
        if track.num_linked_files == 0:
            tabWidget.setTabText(tab_index, _("&Info"))
            self.tab_hide(tab)
            return

        tabWidget.setTabText(tab_index, _("&Info"))
        text = ngettext("%i file in this track", "%i files in this track",
                        track.num_linked_files) % track.num_linked_files
        info_files = [FileInfoDialog.format_file_info(file) for file in track.linked_files]
        text += '<hr />' + '<hr />'.join(info_files)
        self.ui.info.setText(text)


class ClusterInfoDialog(InfoDialog):

    def __init__(self, cluster, parent=None):
        InfoDialog.__init__(self, cluster, parent)
        self.setWindowTitle(_("Cluster Info"))

    def _display_info_tab(self):
        tab = self.ui.info_tab
        cluster = self.obj
        tabWidget = self.ui.tabWidget
        tab_index = tabWidget.indexOf(tab)
        tabWidget.setTabText(tab_index, _("&Info"))
        info = []
        info.append("<b>%s</b> %s" % (_('Album:'),
                                      htmlescape(cluster.metadata["album"])))
        info.append("<b>%s</b> %s" % (_('Artist:'),
                                      htmlescape(cluster.metadata["albumartist"])))
        info.append("")
        lines = []
        for file in cluster.iterfiles(False):
            m = file.metadata
            artist = m["artist"] or m["albumartist"] or cluster.metadata["albumartist"]
            lines.append(m["tracknumber"] + " " +
                         m["title"] + " - " + artist + " (" +
                         m["~length"] + ")")
        info.append("<b>%s</b><br />%s" % (_('Tracklist:'),
                                           '<br />'.join(
                                                   [htmlescape(s).replace(' ', '&nbsp;') for s in lines])))
        self.ui.info.setText('<br/>'.join(info))
