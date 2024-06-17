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
from picard.config import get_config
from picard.coverart.image import CoverArtImageIOError
from picard.coverart.utils import translated_types_as_string
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
    NUM_COLS = 3

    _columns = {}
    _labels = ()
    _tooltips = {}
    artwork_columns = ()

    def __init__(self, parent=None):
        super().__init__(self.NUM_ROWS, self.NUM_COLS, parent=parent)

        h_header = self.horizontalHeader()
        h_header.setDefaultSectionSize(self.H_SIZE)
        h_header.setStretchLastSection(True)

        v_header = self.verticalHeader()
        v_header.setDefaultSectionSize(self.V_SIZE)

        self.setHorizontalHeaderLabels(self._labels)
        for colname, index in self._columns.items():
            self.horizontalHeaderItem(index).setToolTip(self._tooltips.get(colname, None))

    def get_column_index(self, name):
        return self._columns[name]


class ArtworkTableSimple(ArtworkTable):
    TYPE_COLUMN_SIZE = 140

    _columns = {
        'type': 0,
        'new': 1,
        'external': 2,
    }

    _labels = (_("Type"), _("New Tags Cover"), _("New External Cover"),)
    artwork_columns = ('new', 'external',)
    _tooltips = {
        'new': _("New cover art embedded into tags"),
        'external': _("New cover art saved as a separate file"),
    }

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setColumnWidth(self.get_column_index('type'), self.TYPE_COLUMN_SIZE)


class ArtworkTableExisting(ArtworkTable):
    NUM_COLS = 4

    _columns = {
        'orig': 0,
        'type': 1,
        'new': 2,
        'external': 3,
    }

    _labels = (_("Existing Cover"), _("Type"), _("New Tags Cover"), _("New External Cover"),)
    artwork_columns = ('orig', 'new', 'external',)
    _tooltips = {
        'new': _("New cover art embedded into tags"),
        'external': _("New cover art saved as a separate file"),
    }


class ArtworkRow:
    def __init__(self, orig_image=None, new_image=None, types=None):
        self.orig_image = orig_image
        self.new_image = new_image
        self.types = types
        self.new_external_image = None
        if self.new_image:
            self.new_external_image = self.new_image.external_file_coverart


class InfoDialog(PicardDialog):

    def __init__(self, obj, parent=None):
        super().__init__(parent=parent)
        self.obj = obj
        self.ui = Ui_InfoDialog()
        self._pixmaps = {
            'missing': QtGui.QPixmap(":/images/image-missing.png"),
            'arrow': QtGui.QPixmap(":/images/arrow.png"),
        }

        self.new_images = sorted(obj.metadata.images) or []
        self.orig_images = []
        artworktable_class = ArtworkTableSimple

        has_new_external_images = any(image.external_file_coverart for image in self.new_images)
        has_new_different_images = obj.orig_metadata.images != obj.metadata.images
        has_orig_images = hasattr(obj, 'orig_metadata') and obj.orig_metadata.images
        if has_orig_images and (has_new_different_images or has_new_external_images):
            is_track = isinstance(obj, Track)
            is_linked_file = isinstance(obj, File) and isinstance(obj.parent_item, Track)
            is_album_with_files = isinstance(obj, Album) and obj.get_num_total_files() > 0
            if is_track or is_linked_file or is_album_with_files:
                self.orig_images = sorted(obj.orig_metadata.images)
                artworktable_class = ArtworkTableExisting

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

    def _artwork_infos(self, image):
        """Information about image, as list of strings"""
        if image.comment:
            yield image.comment
        bytes_size_decimal = bytes2human.decimal(image.datalength)
        bytes_size_binary = bytes2human.binary(image.datalength)
        yield f"{bytes_size_decimal} ({bytes_size_binary})"
        if image.width and image.height:
            yield f"{image.width} x {image.height}"
        yield image.mimetype

    def _artwork_tooltip(self, message, image):
        """Format rich-text tooltip text"""
        fmt = _("<strong>%(message)s</strong><br />"
                "Temporary file: <em>%(tempfile)s</em><br />"
                "Source: <em>%(sourcefile)s</em>")
        return fmt % {
            'message': message,
            'tempfile': escape(image.tempfile_filename),
            'sourcefile': escape(image.source),
        }

    def _display_artwork_image_cell(self, row_index, colname):
        """Display artwork image, depending on source (new/orig), in the proper column"""
        col_index = self.artwork_table.get_column_index(colname)
        pixmap = None
        infos = None
        source = 'orig_image'
        if colname == 'new':
            source = 'new_image'
        elif colname == 'external':
            source = 'new_external_image'
        image = getattr(self.artwork_rows[row_index], source)
        item = QtWidgets.QTableWidgetItem()

        if image:
            try:
                data = None
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
                    item.setToolTip(self._artwork_tooltip(_("Double-click to open in external viewer"), image))
                    item.setData(QtCore.Qt.ItemDataRole.UserRole, image)
            except CoverArtImageIOError:
                log.error(traceback.format_exc())
                pixmap = self._pixmaps['missing']
                item.setToolTip(self._artwork_tooltip(_("Missing temporary file"), image))
            infos = "<br />".join(escape(t) for t in self._artwork_infos(image))

        img_wgt = ArtworkCoverWidget(pixmap=pixmap, text=infos)
        self.artwork_table.setCellWidget(row_index, col_index, img_wgt)
        self.artwork_table.setItem(row_index, col_index, item)

    def _display_artwork_type_cell(self, row_index):
        """Display type cell, with arrow if this row has both new & orig images"""
        artwork_row = self.artwork_rows[row_index]
        if artwork_row.new_image and artwork_row.orig_image:
            type_pixmap = self._pixmaps['arrow']
            type_size = ArtworkCoverWidget.SIZE // 2
        else:
            type_pixmap = None
            type_size = None

        col_index = self.artwork_table.get_column_index('type')
        type_item = QtWidgets.QTableWidgetItem()
        type_wgt = ArtworkCoverWidget(
            pixmap=type_pixmap,
            size=type_size,
            text=translated_types_as_string(artwork_row.types),
        )
        self.artwork_table.setCellWidget(row_index, col_index, type_wgt)
        self.artwork_table.setItem(row_index, col_index, type_item)

    def _build_artwork_rows(self):
        """Generate artwork rows, trying to match orig/new image types"""
        # we work on a copy, since will pop matched images
        new_images = self.new_images[:]
        if self.orig_images:
            for orig_image in self.orig_images:
                types = orig_image.normalized_types()
                # let check if we can find a new image exactly matching this type
                found_new_image = None
                for i, new_image in enumerate(new_images):
                    if new_image.normalized_types() == types:
                        # we found one, pop it from new_images, we don't want to match it again
                        found_new_image = new_images.pop(i)
                        break
                yield ArtworkRow(orig_image=orig_image, new_image=found_new_image, types=types)
        # now, remaining images that weren't matched to orig images
        for new_image in new_images:
            yield ArtworkRow(new_image=new_image, types=new_image.normalized_types())

    def _display_artwork_rows(self):
        """Display rows of images and types in artwork tab"""
        self.artwork_rows = dict(enumerate(self._build_artwork_rows()))
        for row_index in self.artwork_rows:
            self.artwork_table.insertRow(row_index)
            self._display_artwork_type_cell(row_index)
            for colname in self.artwork_table.artwork_columns:
                self._display_artwork_image_cell(row_index, colname)

    def _display_artwork_tab(self):
        if not self.new_images and not self.orig_images:
            self.tab_hide(self.ui.artwork_tab)
            return
        self._display_artwork_rows()
        self.artwork_table.itemDoubleClicked.connect(self.show_item)
        self.artwork_table.verticalHeader().resizeSections(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        config = get_config()
        for colname in self.artwork_table.artwork_columns:
            tags_image_not_used = colname == 'new' and not config.setting['save_images_to_tags']
            file_image_not_used = colname == 'external' and not config.setting['save_images_to_files']
            if tags_image_not_used or file_image_not_used:
                col_index = self.artwork_table.get_column_index(colname)
                self.artwork_table.setColumnHidden(col_index, True)

    def tab_hide(self, widget):
        tab = self.ui.tabWidget
        index = tab.indexOf(widget)
        tab.removeTab(index)

    def show_item(self, item):
        data = item.data(QtCore.Qt.ItemDataRole.UserRole)
        # Check if this function isn't triggered by cell in Type column
        if not data:
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
        super().__init__(file_, parent=parent)
        self.setWindowTitle(_("Info") + " - " + file_.base_filename)

    def _display_info_tab(self):
        file_ = self.obj
        text = format_file_info(file_)
        self.ui.info.setText(text)


class AlbumInfoDialog(InfoDialog):

    def __init__(self, album, parent=None):
        super().__init__(album, parent=parent)
        self.setWindowTitle(_("Album Info"))

    def _display_info_tab(self):
        album = self.obj
        if album._tracks_loaded:
            self.ui.info.setText(format_tracklist(album))
        else:
            self.tab_hide(self.ui.info_tab)


class TrackInfoDialog(InfoDialog):

    def __init__(self, track, parent=None):
        super().__init__(track, parent=parent)
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
        super().__init__(cluster, parent=parent)
        self.setWindowTitle(_("Cluster Info"))

    def _display_info_tab(self):
        tab = self.ui.info_tab
        tabWidget = self.ui.tabWidget
        tab_index = tabWidget.indexOf(tab)
        tabWidget.setTabText(tab_index, _("&Info"))
        self.ui.info.setText(format_tracklist(self.obj))
