# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2012-2014, 2017, 2019 Wieland Hoffmann
# Copyright (C) 2013-2014, 2018-2024 Laurent Monin
# Copyright (C) 2014, 2017, 2020 Sophist-UK
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017-2019 Antonio Larrosa
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2018-2024 Philipp Wolfer
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


from collections import (
    defaultdict,
    namedtuple,
)
from html import escape
import re
import traceback

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import log
from picard.album import Album
from picard.coverart.image import CoverArtImageIOError
from picard.file import File
from picard.i18n import (
    gettext as _,
    ngettext,
)
from picard.track import Track
from picard.util import (
    bytes2human,
    format_time,
    open_local_path,
    union_sorted_lists,
)

from picard.ui import PicardDialog
from picard.ui.colors import interface_colors
from picard.ui.forms.ui_infodialog import Ui_InfoDialog
from picard.ui.util import StandardButton


class ArtworkCoverWidget(QtWidgets.QWidget):
    """A QWidget that can be added to artwork column cell of ArtworkTable."""

    SIZE = 170

    def __init__(self, pixmap=None, text=None, size=None, parent=None):
        super().__init__(parent=parent)
        layout = QtWidgets.QVBoxLayout()

        if pixmap is not None:
            if size is None:
                size = self.SIZE
            image_label = QtWidgets.QLabel()
            image_label.setPixmap(pixmap.scaled(size, size,
                                                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                                QtCore.Qt.TransformationMode.SmoothTransformation))
            image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(image_label)

        if text is not None:
            text_label = QtWidgets.QLabel()
            text_label.setText(text)
            text_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            text_label.setWordWrap(True)
            layout.addWidget(text_label)

        self.setLayout(layout)


class ArtworkTable(QtWidgets.QTableWidget):
    H_SIZE = 200
    V_SIZE = 230

    NUM_ROWS = 0
    NUM_COLS = 2

    _columns = {}
    _labels = ()

    def __init__(self, parent=None):
        super().__init__(self.NUM_ROWS, self.NUM_COLS, parent=parent)

        h_header = self.horizontalHeader()
        h_header.setDefaultSectionSize(self.H_SIZE)
        h_header.setStretchLastSection(True)

        v_header = self.verticalHeader()
        v_header.setDefaultSectionSize(self.V_SIZE)

        self.setHorizontalHeaderLabels(self._labels)

    def get_column_index(self, name):
        return self._columns[name]


class ArtworkTableSimple(ArtworkTable):
    TYPE_COLUMN_SIZE = 140

    _columns = {
        'type': 0,
        'new_cover': 1,
    }

    _labels = (_("Type"), _("Cover"),)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setColumnWidth(self.get_column_index('type'), self.TYPE_COLUMN_SIZE)


class ArtworkTableExisting(ArtworkTable):
    NUM_COLS = 3

    _columns = {
        'existing_cover': 0,
        'type': 1,
        'new_cover': 2,
    }

    _labels = (_("Existing Cover"), _("Type"), _("New Cover"),)


class InfoDialog(PicardDialog):

    def __init__(self, obj, parent=None):
        super().__init__(parent)
        self.obj = obj
        self.ui = Ui_InfoDialog()
        self._pixmaps = {
            'missing': QtGui.QPixmap(":/images/image-missing.png"),
            'arrow': QtGui.QPixmap(":/images/arrow.png"),
        }

        self.images = obj.metadata.images or []
        self.existing_images = []
        artworktable_class = ArtworkTableSimple

        has_orig_images = getattr(obj, 'orig_metadata', None) is not None and obj.orig_metadata.images
        if has_orig_images and obj.orig_metadata.images != obj.metadata.images:
            is_track = isinstance(obj, Track)
            is_linked_file = isinstance(obj, File) and isinstance(obj.parent, Track)
            is_album_with_files = isinstance(obj, Album) and obj.get_num_total_files() > 0
            if is_track or is_linked_file or is_album_with_files:
                if self.images:
                    self.existing_images = obj.orig_metadata.images
                    artworktable_class = ArtworkTableExisting
                else:
                    self.images = obj.orig_metadata.images

        self.ui.setupUi(self)
        self.ui.buttonBox.addButton(
            StandardButton(StandardButton.CLOSE), QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self.ui.buttonBox.accepted.connect(self.accept)

        # Add the ArtworkTable to the ui
        self.ui.artwork_table = artworktable_class(parent=self)
        self.ui.artwork_table.setObjectName('artwork_table')
        self.ui.artwork_tab.layout().addWidget(self.ui.artwork_table)
        self.setTabOrder(self.ui.tabWidget, self.ui.artwork_table)
        self.setTabOrder(self.ui.artwork_table, self.ui.buttonBox)

        self.setWindowTitle(_("Info"))
        self.artwork_table = self.ui.artwork_table
        self._display_tabs()

    def _display_tabs(self):
        self._display_info_tab()
        self._display_error_tab()
        self._display_artwork_tab()

    def _display_error_tab(self):
        if hasattr(self.obj, 'errors') and self.obj.errors:
            self._show_errors(self.obj.errors)
        else:
            self.tab_hide(self.ui.error_tab)

    def _show_errors(self, errors):
        if errors:
            color = interface_colors.get_color('log_error')
            text = '<br />'.join(map(
                lambda s: '<font color="%s">%s</font>' % (color, text_as_html(s)), errors))
            self.ui.error.setText(text + '<hr />')

    def _types_to_rows(self, type_col):
        """Build a dict of lists to match types to rows"""
        types_to_rows = defaultdict(list)
        for row in range(0, self.artwork_table.rowCount()):
            type_item = self.artwork_table.item(row, type_col)
            types = type_item.data(QtCore.Qt.ItemDataRole.UserRole)
            types_to_rows[types].append(row)
        return types_to_rows

    def _display_artwork(self, images, cover_art_column_name):
        """Draw artwork in corresponding cell if image type matches type in Type column.

        Arguments:
        images -- The images to be drawn.
        cover_art_column_name -- Column in which images are to be drawn. Can be 'new_cover' or 'existing_cover'.
        """
        artwork_col = self.artwork_table.get_column_index(cover_art_column_name)
        type_col = self.artwork_table.get_column_index('type')
        types_to_rows = self._types_to_rows(type_col)
        for image in images:
            try:
                # find first row matching the image types, if any
                row = types_to_rows[image.types_as_string()].pop(0)
            except IndexError:
                # no row found
                continue

            data = None
            pixmap = None
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.ItemDataRole.UserRole, image)
            try:
                if image.thumbnail:
                    try:
                        data = image.thumbnail.data
                    except CoverArtImageIOError as e:
                        log.warning(e)
                else:
                    data = image.data
                if data:
                    pixmap = QtGui.QPixmap()
                    pixmap.loadFromData(data)
                    item.setToolTip(
                        _("Double-click to open in external viewer\n"
                        "Temporary file: %(tempfile)s\n"
                        "Source: %(sourcefile)s") % {
                            'tempfile': image.tempfile_filename,
                            'sourcefile': image.source,
                        })
            except CoverArtImageIOError:
                log.error(traceback.format_exc())
                pixmap = self._pixmaps['missing']
                item.setToolTip(
                    _("Missing temporary file: %(tempfile)s\n"
                    "Source: %(sourcefile)s") % {
                        'tempfile': image.tempfile_filename,
                        'sourcefile': image.source,
                    })
            infos = []
            if image.comment:
                infos.append(image.comment)
            infos.append("%s (%s)" %
                         (bytes2human.decimal(image.datalength),
                          bytes2human.binary(image.datalength)))
            if image.width and image.height:
                infos.append("%d x %d" % (image.width, image.height))
            infos.append(image.mimetype)

            img_wgt = ArtworkCoverWidget(pixmap=pixmap, text="\n".join(infos))
            self.artwork_table.setCellWidget(row, artwork_col, img_wgt)
            self.artwork_table.setItem(row, artwork_col, item)

    def _display_artwork_type(self):
        """Display image type in Type column.
        If both existing covers and new covers are to be displayed, take union of both cover types list.
        """
        types = [image.types_as_string() for image in self.images]
        if isinstance(self.artwork_table, ArtworkTableExisting):
            existing_types = [image.types_as_string() for image in self.existing_images]
            # Merge both types and existing types list in sorted order.
            types = union_sorted_lists(types, existing_types)
            pixmap = self._pixmaps['arrow']
            size = ArtworkCoverWidget.SIZE // 2
        else:
            pixmap = None
            size = None
        type_col = self.artwork_table.get_column_index('type')
        for row, artwork_type in enumerate(types):
            self.artwork_table.insertRow(row)
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.ItemDataRole.UserRole, artwork_type)
            type_wgt = ArtworkCoverWidget(pixmap=pixmap, size=size, text=artwork_type)
            self.artwork_table.setCellWidget(row, type_col, type_wgt)
            self.artwork_table.setItem(row, type_col, item)

    def _display_artwork_tab(self):
        if not self.images and not self.existing_images:
            self.tab_hide(self.ui.artwork_tab)
            return
        self._display_artwork_type()
        if self.images:
            self._display_artwork(self.images, 'new_cover')
        if self.existing_images:
            self._display_artwork(self.existing_images, 'existing_cover')
        self.artwork_table.itemDoubleClicked.connect(self.show_item)
        self.artwork_table.verticalHeader().resizeSections(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

    def tab_hide(self, widget):
        tab = self.ui.tabWidget
        index = tab.indexOf(widget)
        tab.removeTab(index)

    def show_item(self, item):
        data = item.data(QtCore.Qt.ItemDataRole.UserRole)
        # Check if this function isn't triggered by cell in Type column
        if isinstance(data, str):
            return
        filename = data.tempfile_filename
        if filename:
            open_local_path(filename)


def format_file_info(file_):
    info = []
    info.append((_("Filename:"), file_.filename))
    if '~format' in file_.orig_metadata:
        info.append((_("Format:"), file_.orig_metadata['~format']))
    if '~filesize' in file_.orig_metadata:
        size = file_.orig_metadata['~filesize']
        try:
            sizestr = "%s (%s)" % (bytes2human.decimal(size), bytes2human.binary(size))
        except ValueError:
            sizestr = _("unknown")
        info.append((_("Size:"), sizestr))
    if file_.orig_metadata.length:
        info.append((_("Length:"), format_time(file_.orig_metadata.length)))
    if '~bitrate' in file_.orig_metadata:
        info.append((_("Bitrate:"), "%s kbps" % file_.orig_metadata['~bitrate']))
    if '~sample_rate' in file_.orig_metadata:
        info.append((_("Sample rate:"), "%s Hz" % file_.orig_metadata['~sample_rate']))
    if '~bits_per_sample' in file_.orig_metadata:
        info.append((_("Bits per sample:"), str(file_.orig_metadata['~bits_per_sample'])))
    if '~channels' in file_.orig_metadata:
        ch = file_.orig_metadata['~channels']
        if ch == '1':
            ch = _("Mono")
        elif ch == '2':
            ch = _("Stereo")
        info.append((_("Channels:"), ch))
    return '<br/>'.join(map(lambda i: '<b>%s</b> %s' %
                            (escape(i[0]), escape(i[1])), info))


def format_tracklist(cluster):
    info = []
    info.append('<b>%s</b> %s' % (_("Album:"), escape(cluster.metadata['album'])))
    info.append('<b>%s</b> %s' % (_("Artist:"), escape(cluster.metadata['albumartist'])))
    info.append("")
    TrackListItem = namedtuple('TrackListItem', 'number, title, artist, length')
    tracklists = defaultdict(list)
    if isinstance(cluster, Album):
        objlist = cluster.tracks
    else:
        objlist = cluster.iterfiles(False)
    for obj_ in objlist:
        m = obj_.metadata
        artist = m['artist'] or m['albumartist'] or cluster.metadata['albumartist']
        track = TrackListItem(m['tracknumber'], m['title'], artist,
                              m['~length'])
        tracklists[obj_.discnumber].append(track)

    def sorttracknum(track):
        try:
            return int(track.number)
        except ValueError:
            try:
                # This allows to parse values like '3' but also '3/10'
                m = re.search(r'^\d+', track.number)
                return int(m.group(0))
            except AttributeError:
                return 0

    ndiscs = len(tracklists)
    for discnumber in sorted(tracklists):
        tracklist = tracklists[discnumber]
        if ndiscs > 1:
            info.append('<b>%s</b>' % (_("Disc %d") % discnumber))
        lines = ['%s %s - %s (%s)' % item for item in sorted(tracklist, key=sorttracknum)]
        info.append('<b>%s</b><br />%s<br />' % (_("Tracklist:"),
                    '<br />'.join(escape(s).replace(' ', '&nbsp;') for s in lines)))
    return '<br/>'.join(info)


def text_as_html(text):
    return '<br />'.join(escape(str(text))
        .replace('\t', ' ')
        .replace(' ', '&nbsp;')
        .splitlines())


class FileInfoDialog(InfoDialog):

    def __init__(self, file_, parent=None):
        super().__init__(file_, parent)
        self.setWindowTitle(_("Info") + " - " + file_.base_filename)

    def _display_info_tab(self):
        file_ = self.obj
        text = format_file_info(file_)
        self.ui.info.setText(text)


class AlbumInfoDialog(InfoDialog):

    def __init__(self, album, parent=None):
        super().__init__(album, parent)
        self.setWindowTitle(_("Album Info"))

    def _display_info_tab(self):
        album = self.obj
        if album._tracks_loaded:
            self.ui.info.setText(format_tracklist(album))
        else:
            self.tab_hide(self.ui.info_tab)


class TrackInfoDialog(InfoDialog):

    def __init__(self, track, parent=None):
        super().__init__(track, parent)
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
        info_files = [format_file_info(file_) for file_ in track.files]
        text += '<hr />' + '<hr />'.join(info_files)
        self.ui.info.setText(text)


class ClusterInfoDialog(InfoDialog):

    def __init__(self, cluster, parent=None):
        super().__init__(cluster, parent)
        self.setWindowTitle(_("Cluster Info"))

    def _display_info_tab(self):
        tab = self.ui.info_tab
        tabWidget = self.ui.tabWidget
        tab_index = tabWidget.indexOf(tab)
        tabWidget.setTabText(tab_index, _("&Info"))
        self.ui.info.setText(format_tracklist(self.obj))
