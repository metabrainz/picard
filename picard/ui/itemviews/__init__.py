# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011-2012 Lukáš Lalinský
# Copyright (C) 2007 Robert Kaye
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008 Hendrik van Antwerpen
# Copyright (C) 2008-2011, 2014-2015, 2018-2024 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2011 Tim Blechmann
# Copyright (C) 2011-2012 Chad Wilson
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012 Your Name
# Copyright (C) 2012-2013 Wieland Hoffmann
# Copyright (C) 2013-2014, 2016, 2018-2024 Laurent Monin
# Copyright (C) 2013-2014, 2017, 2020 Sophist-UK
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016 Simon Legner
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2021, 2025 Bob Swift
# Copyright (C) 2021 Louis Sautier
# Copyright (C) 2021 Petit Minion
# Copyright (C) 2023 certuna
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


from collections import defaultdict
from contextlib import suppress
from functools import partial

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import log
from picard.album import NatAlbum
from picard.cluster import Cluster, ClusterList
from picard.file import File
from picard.i18n import (
    N_,
    gettext as _,
    ngettext,
    sort_key,
)
from picard.track import Track
from picard.util import icontheme

from picard.ui.colors import interface_colors
from picard.ui.columns import (
    ColumnAlign,
    ColumnSortType,
    ImageColumn,
)
from picard.ui.itemviews.basetreeview import BaseTreeView
from picard.ui.itemviews.columns import (
    ALBUMVIEW_COLUMNS,
    FILEVIEW_COLUMNS,
)
from picard.ui.itemviews.custom_columns import DelegateColumn


def get_match_color(similarity, basecolor):
    c1 = (basecolor.red(), basecolor.green(), basecolor.blue())
    c2 = (223, 125, 125)
    return QtGui.QColor(
        int(c2[0] + (c1[0] - c2[0]) * similarity),
        int(c2[1] + (c1[1] - c2[1]) * similarity),
        int(c2[2] + (c1[2] - c2[2]) * similarity),
    )


class MainPanel(QtWidgets.QSplitter):
    def __init__(self, window, parent=None):
        super().__init__(parent=parent)
        self.tagger = QtCore.QCoreApplication.instance()
        self.setChildrenCollapsible(False)
        self.window = window
        self.create_icons()
        self._views = [
            FileTreeView(FILEVIEW_COLUMNS, window, parent=self),
            AlbumTreeView(ALBUMVIEW_COLUMNS, window, parent=self),
        ]
        self._selected_view = self._views[0]
        self._ignore_selection_changes = False
        self._sort_enabled = None  # None at start, bool once set_sorting is called

        # Create a layout for each view to include the filter box
        for view in self._views:
            container = QtWidgets.QWidget(self)
            layout = QtWidgets.QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            # Create and add filter box
            filter_box = view.setup_filter_box()
            layout.addWidget(filter_box)

            # Add view
            layout.addWidget(view)

            # Add the container to the splitter
            self.addWidget(container)

        def _view_update_selection(view):
            if not self._ignore_selection_changes:
                self._ignore_selection_changes = True
                self._update_selection(view)
                self._ignore_selection_changes = False

        for view in self._views:
            view.itemSelectionChanged.connect(partial(_view_update_selection, view))

        TreeItem.window = window
        TreeItem.base_color = self.palette().base().color()
        TreeItem.text_color = self.palette().text().color()
        TreeItem.text_color_secondary = (
            self.palette().brush(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Text).color()
        )
        TrackItem.track_colors = defaultdict(
            lambda: TreeItem.text_color,
            {
                File.State.NORMAL: interface_colors.get_qcolor('entity_saved'),
                File.State.CHANGED: TreeItem.text_color,
                File.State.PENDING: interface_colors.get_qcolor('entity_pending'),
                File.State.ERROR: interface_colors.get_qcolor('entity_error'),
            },
        )
        FileItem.file_colors = defaultdict(
            lambda: TreeItem.text_color,
            {
                File.State.NORMAL: TreeItem.text_color,
                File.State.CHANGED: TreeItem.text_color,
                File.State.PENDING: interface_colors.get_qcolor('entity_pending'),
                File.State.ERROR: interface_colors.get_qcolor('entity_error'),
            },
        )

    def set_processing(self, processing=True):
        self._ignore_selection_changes = processing

    def tab_order(self, tab_order, before, after):
        prev = before
        for view in self._views:
            tab_order(prev, view)
            prev = view
        tab_order(prev, after)

    def save_state(self):
        for view in self._views:
            view.save_state()

    def create_icons(self):
        if hasattr(QtWidgets.QStyle, 'SP_DirIcon'):
            ClusterItem.icon_dir = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirIcon)
        else:
            ClusterItem.icon_dir = icontheme.lookup('folder', icontheme.ICON_SIZE_MENU)
        AlbumItem.icon_cd = icontheme.lookup('media-optical', icontheme.ICON_SIZE_MENU)
        AlbumItem.icon_cd_modified = icontheme.lookup('media-optical-modified', icontheme.ICON_SIZE_MENU)
        AlbumItem.icon_cd_saved = icontheme.lookup('media-optical-saved', icontheme.ICON_SIZE_MENU)
        AlbumItem.icon_cd_saved_modified = icontheme.lookup('media-optical-saved-modified', icontheme.ICON_SIZE_MENU)
        AlbumItem.icon_error = icontheme.lookup('media-optical-error', icontheme.ICON_SIZE_MENU)
        TrackItem.icon_audio = QtGui.QIcon(":/images/track-audio.png")
        TrackItem.icon_video = QtGui.QIcon(":/images/track-video.png")
        TrackItem.icon_data = QtGui.QIcon(":/images/track-data.png")
        TrackItem.icon_error = icontheme.lookup('dialog-error', icontheme.ICON_SIZE_MENU)
        FileItem.icon_file = QtGui.QIcon(":/images/file.png")
        FileItem.icon_file_pending = QtGui.QIcon(":/images/file-pending.png")
        FileItem.icon_error = icontheme.lookup('dialog-error', icontheme.ICON_SIZE_MENU)
        FileItem.icon_error_not_found = icontheme.lookup('error-not-found', icontheme.ICON_SIZE_MENU)
        FileItem.icon_error_no_access = icontheme.lookup('error-no-access', icontheme.ICON_SIZE_MENU)
        FileItem.icon_saved = QtGui.QIcon(":/images/track-saved.png")
        FileItem.icon_fingerprint = icontheme.lookup('fingerprint', icontheme.ICON_SIZE_MENU)
        FileItem.icon_fingerprint_gray = icontheme.lookup('fingerprint-gray', icontheme.ICON_SIZE_MENU)
        FileItem.match_icons = [
            QtGui.QIcon(":/images/match-50.png"),
            QtGui.QIcon(":/images/match-60.png"),
            QtGui.QIcon(":/images/match-70.png"),
            QtGui.QIcon(":/images/match-80.png"),
            QtGui.QIcon(":/images/match-90.png"),
            QtGui.QIcon(":/images/match-100.png"),
        ]
        FileItem.match_icons_info = [
            N_("Bad match"),
            N_("Poor match"),
            N_("Ok match"),
            N_("Good match"),
            N_("Great match"),
            N_("Excellent match"),
        ]
        FileItem.match_pending_icons = [
            QtGui.QIcon(":/images/match-pending-50.png"),
            QtGui.QIcon(":/images/match-pending-60.png"),
            QtGui.QIcon(":/images/match-pending-70.png"),
            QtGui.QIcon(":/images/match-pending-80.png"),
            QtGui.QIcon(":/images/match-pending-90.png"),
            QtGui.QIcon(":/images/match-pending-100.png"),
        ]

    def _update_selection(self, selected_view):
        for view in self._views:
            if view != selected_view:
                view.clearSelection()
            else:
                self._selected_view = view
                self.window.update_selection([item.obj for item in view.selectedItems()])

    def update_current_view(self):
        self._update_selection(self._selected_view)

    def remove(self, objects):
        self._ignore_selection_changes = True
        self.tagger.remove(objects)
        self._ignore_selection_changes = False

        view = self._selected_view
        index = view.currentIndex()
        if index.isValid():
            # select the current index
            view.setCurrentIndex(index)
        else:
            self.update_current_view()

    def set_sorting(self, sort=True):
        if sort != self._sort_enabled:
            self._sort_enabled = sort
            log.debug("MainPanel sort=%r", sort)
            for view in self._views:
                view.setSortingEnabled(sort)

    def select_object(self, obj):
        item = obj.ui_item
        for view in self._views:
            if view.indexFromItem(item).isValid():
                view.setCurrentItem(item)
                self._update_selection(view)
                break

    def show_filter_bars(self, show_state: bool):
        """Toggle visibility of filter bars in both views."""
        for view in self._views:
            view.filter_box.setVisible(show_state)
            if show_state and view.hasFocus():
                view.filter_box.set_focus()
            else:
                view.filter_box.clear()


class FileTreeView(BaseTreeView):
    NAME = N_("file view")
    DESCRIPTION = N_("Contains unmatched files and clusters")

    header_state = 'file_view_header_state'
    header_locked = 'file_view_header_locked'

    def __init__(self, columns, window, parent=None):
        super().__init__(columns, window, parent=parent)
        self.unmatched_files = ClusterItem(self.tagger.unclustered_files, filterable=False, parent=self)
        self.unmatched_files.update()
        self.unmatched_files.setExpanded(True)
        self.clusters = ClusterItem(self.tagger.clusters, filterable=False, parent=self)
        self.set_clusters_text()
        self.clusters.setExpanded(True)
        self.tagger.cluster_added.connect(self.add_file_cluster)
        self.tagger.cluster_removed.connect(self.remove_file_cluster)

    def add_file_cluster(self, cluster, parent_item=None):
        self.add_cluster(cluster, parent_item)
        self.set_clusters_text()

    def remove_file_cluster(self, cluster):
        cluster.ui_item.setSelected(False)
        self.clusters.removeChild(cluster.ui_item)
        self.set_clusters_text()

    def set_clusters_text(self):
        self.clusters.setText(self.columns.pos('title'), "%s (%d)" % (_("Clusters"), len(self.tagger.clusters)))

    @property
    def default_drop_target(self):
        return self.tagger.unclustered_files


class AlbumTreeView(BaseTreeView):
    NAME = N_("album view")
    DESCRIPTION = N_("Contains albums and matched files")

    header_state = 'album_view_header_state'
    header_locked = 'album_view_header_locked'

    def __init__(self, columns, window, parent=None):
        super().__init__(columns, window, parent=parent)
        self.tagger.album_added.connect(self.add_album)
        self.tagger.album_removed.connect(self.remove_album)

    def add_album(self, album):
        if isinstance(album, NatAlbum):
            item = NatAlbumItem(album, sortable=True)
            self.insertTopLevelItem(0, item)
        else:
            item = AlbumItem(album, sortable=True, parent=self)
        item.setIcon(self.columns.status_icon_column, AlbumItem.icon_cd)
        for i, column in enumerate(self.columns):
            font = item.font(i)
            font.setBold(True)
            item.setFont(i, font)
            item.setText(i, album.column(column.key))
        self.add_cluster(album.unmatched_files, item)

    def remove_album(self, album):
        album.ui_item.setSelected(False)
        self.takeTopLevelItem(self.indexOfTopLevelItem(album.ui_item))


class TreeItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, obj, sortable=False, filterable=True, parent=None):
        super().__init__(parent)
        self._obj = None
        self.obj = obj
        self.sortable = sortable
        self.filterable = filterable
        self._sortkeys = {}
        self.post_init()

    @property
    def columns(self):
        """Get columns from the tree widget this item belongs to.
        Falls back to file-view columns while the item is not yet attached."""
        # Different views use different column sets: file view uses FILEVIEW_COLUMNS; album view uses ALBUMVIEW_COLUMNS (with the Match column)
        tree_widget = self.treeWidget()
        if tree_widget and hasattr(tree_widget, 'columns'):
            return tree_widget.columns
        # During construction some items call update() before being added to a view
        # Return a safe default to avoid crashes; once attached, the view columns apply
        return FILEVIEW_COLUMNS

    @property
    def obj(self):
        return self._obj

    @obj.setter
    def obj(self, obj):
        if self._obj:
            self._obj.ui_item = None
        self._obj = obj
        if obj is not None:
            obj.ui_item = self

    def post_init(self):
        pass

    def setText(self, column, text):
        self._sortkeys[column] = None
        return super().setText(column, text)

    def __lt__(self, other):
        tree_widget = self.treeWidget()
        if not self.sortable or not tree_widget:
            return False
        column = tree_widget.sortColumn()
        return self.sortkey(column) < other.sortkey(column)

    def sortkey(self, column):
        sortkey = self._sortkeys.get(column)
        if sortkey is not None:
            return sortkey

        this_column = self.columns[column]

        if this_column.sort_type == ColumnSortType.SORTKEY:
            sortkey = this_column.sortkey(self.obj)
        elif this_column.sort_type == ColumnSortType.NAT:
            sortkey = sort_key(self.text(column), numeric=True)
        else:
            sortkey = sort_key(self.text(column))
        self._sortkeys[column] = sortkey
        return sortkey

    def update_colums_text(self, color=None, bgcolor=None):
        # Local import to avoid cycles
        from picard.ui.itemviews.custom_columns import CustomColumn

        for i, column in enumerate(self.columns):
            if color is not None:
                self.setForeground(i, color)
            if bgcolor is not None:
                self.setBackground(i, bgcolor)
            if isinstance(column, ImageColumn):
                self.setSizeHint(i, column.size)
            elif isinstance(column, DelegateColumn):
                # Delegate columns are handled by delegate, just set size hint
                if hasattr(column, 'size'):
                    self.setSizeHint(i, column.size)
            else:
                if column.align == ColumnAlign.RIGHT:
                    self.setTextAlignment(i, QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)

                if isinstance(column, CustomColumn):
                    # Invalidate caches for this object to reflect tag changes
                    column.invalidate_cache(self.obj)
                    # Hide custom column values for container/group rows, but preserve Title and status icon.
                    # - ClusterList: Represents the "Clusters" root. Title is set elsewhere.
                    # - Special Cluster instances (e.g. "Unclustered Files"): Should show their Title
                    #   but no other per-entity values in custom columns.
                    is_group_row = isinstance(self.obj, ClusterList) or (
                        isinstance(self.obj, Cluster) and getattr(self.obj, 'special', False)
                    )
                    if is_group_row and (column.key != 'title' and not column.status_icon):
                        self.setText(i, "")
                        continue

                    try:
                        self.setText(i, column.provider.evaluate(self.obj))
                    except (AttributeError, TypeError, ValueError, KeyError, NotImplementedError) as exc:
                        log.debug("Custom column '%s' evaluate failed: %r", column.key, exc)
                    continue

                with suppress(AttributeError):
                    # Some objects like ClusterList don't have a column method
                    # Note: Do not log; it is very noisy.
                    # See: https://github.com/metabrainz/picard/pull/2714#issuecomment-3260286574
                    self.setText(i, self.obj.column(column.key))


class ClusterItem(TreeItem):
    def post_init(self):
        self.setIcon(self.columns.status_icon_column, ClusterItem.icon_dir)

    def update(self, update_selection=True):
        self.update_colums_text()
        album = self.obj.related_album
        if self.obj.special and album and album.loaded:
            album.ui_item.update(update_tracks=False)
        if update_selection and self.isSelected():
            TreeItem.window.update_selection(new_selection=False)

    def add_file(self, file):
        self.add_files([file])

    def add_files(self, files):
        if not self.obj.is_permanently_hidden:
            self.setHidden(False)
        self.update()
        # addChild used (rather than building an items list and adding with addChildren)
        # to be certain about item order in the cluster (addChildren adds in reverse order).
        # Benchmarked performance was not noticeably different.
        for file in files:
            item = FileItem(file, sortable=True)
            self.addChild(item)
            item.update()

    def remove_file(self, file):
        file.ui_item.setSelected(False)
        self.removeChild(file.ui_item)
        self.update()
        if self.obj.is_permanently_hidden:
            self.setHidden(True)


class AlbumItem(TreeItem):
    def update(self, update_tracks=True, update_selection=True):
        album = self.obj
        selection_changed = self.isSelected()
        if update_tracks:
            oldnum = self.childCount() - 1
            newnum = len(album.tracks)
            if oldnum > newnum:  # remove old items
                for _i in range(oldnum - newnum):
                    item = self.child(newnum)
                    selection_changed |= item.isSelected()
                    self.takeChild(newnum)
                oldnum = newnum
            # update existing items
            for i in range(oldnum):
                item = self.child(i)
                track = album.tracks[i]
                selection_changed |= item.isSelected() and item.obj != track
                item.obj = track
                item.update(update_album=False)
            if newnum > oldnum:  # add new items
                items = []
                for i in range(oldnum, newnum):
                    item = TrackItem(album.tracks[i])
                    item.setHidden(False)  # Workaround to make sure the parent state gets updated
                    items.append(item)
                # insertChildren behaves differently if sorting is disabled / enabled, which results
                # in different sort order of tracks in unsorted state. As we sort the tracks later
                # anyway make sure sorting is disabled here.
                tree_widget = self.treeWidget()
                if tree_widget:
                    sorting_enabled = tree_widget.isSortingEnabled()
                    tree_widget.setSortingEnabled(False)
                self.insertChildren(oldnum, items)
                if tree_widget:
                    tree_widget.setSortingEnabled(sorting_enabled)
                for item in items:  # Update after insertChildren so that setExpanded works
                    item.update(update_album=False)
        if album.errors:
            self.setIcon(self.columns.status_icon_column, AlbumItem.icon_error)
            self.setToolTip(
                self.columns.status_icon_column, _("Processing error(s): See the Errors tab in the Album Info dialog")
            )
        elif album.is_complete():
            if album.is_modified():
                self.setIcon(self.columns.status_icon_column, AlbumItem.icon_cd_saved_modified)
                self.setToolTip(self.columns.status_icon_column, _("Album modified and complete"))
            else:
                self.setIcon(self.columns.status_icon_column, AlbumItem.icon_cd_saved)
                self.setToolTip(self.columns.status_icon_column, _("Album unchanged and complete"))
        else:
            if album.is_modified():
                self.setIcon(self.columns.status_icon_column, AlbumItem.icon_cd_modified)
                self.setToolTip(self.columns.status_icon_column, _("Album modified"))
            else:
                self.setIcon(self.columns.status_icon_column, AlbumItem.icon_cd)
                self.setToolTip(self.columns.status_icon_column, _("Album unchanged"))
        self.update_colums_text()
        if selection_changed and update_selection:
            TreeItem.window.update_selection(new_selection=False)
        # Workaround for PICARD-1446: Expand/collapse indicator for the release
        # is briefly missing on Windows
        self.emitDataChanged()

    def __lt__(self, other):
        # Always show NAT entry on top, see also NatAlbumItem.__lt__
        if isinstance(other, NatAlbumItem):
            return not other.__lt__(self)
        return super().__lt__(other)


class NatAlbumItem(AlbumItem):
    def __lt__(self, other):
        # Always show NAT entry on top
        tree_widget = self.treeWidget()
        if not tree_widget:
            return True
        order = tree_widget.header().sortIndicatorOrder()
        return order == QtCore.Qt.SortOrder.AscendingOrder


class TrackItem(TreeItem):
    def update(self, update_album=True, update_files=True, update_selection=True):
        track = self.obj
        num_linked_files = track.num_linked_files
        fingerprint_column = self.columns.pos('~fingerprint')
        if num_linked_files == 1:
            file = track.files[0]
            file.ui_item = self
            color = TrackItem.track_colors[file.state]
            bgcolor = get_match_color(file.similarity, TreeItem.base_color)
            icon, icon_tooltip = FileItem.decide_file_icon_info(file)
            self.takeChildren()
            self.setExpanded(False)
            fingerprint_icon, fingerprint_tooltip = FileItem.decide_fingerprint_icon_info(file)
            self.setToolTip(fingerprint_column, fingerprint_tooltip)
            self.setIcon(fingerprint_column, fingerprint_icon)
        else:
            if num_linked_files == 0:
                icon_tooltip = _("There are no files matched to this track")
            else:
                icon_tooltip = ngettext('%i matched file', '%i matched files', num_linked_files) % num_linked_files
            self.setToolTip(fingerprint_column, "")
            self.setIcon(fingerprint_column, QtGui.QIcon())
            if track.ignored_for_completeness():
                color = TreeItem.text_color_secondary
            else:
                color = TreeItem.text_color
            bgcolor = get_match_color(1, TreeItem.base_color)
            if track.is_video():
                icon = TrackItem.icon_video
            elif track.is_data():
                icon = TrackItem.icon_data
            else:
                icon = TrackItem.icon_audio
            if update_files:
                oldnum = self.childCount()
                newnum = track.num_linked_files
                if oldnum > newnum:  # remove old items
                    for _i in range(oldnum - newnum):
                        self.takeChild(newnum - 1).obj = None
                    oldnum = newnum
                for i in range(oldnum):  # update existing items
                    item = self.child(i)
                    item.obj = track.files[i]
                    item.update(update_track=False)
                if newnum > oldnum:  # add new items
                    items = []
                    for i in range(newnum - 1, oldnum - 1, -1):
                        item = FileItem(track.files[i])
                        item.update(update_track=False, update_selection=update_selection)
                        items.append(item)
                    self.addChildren(items)
            self.setExpanded(True)
        if track.errors:
            self.setIcon(self.columns.status_icon_column, TrackItem.icon_error)
            self.setToolTip(
                self.columns.status_icon_column, _("Processing error(s): See the Errors tab in the Track Info dialog")
            )
        else:
            self.setIcon(self.columns.status_icon_column, icon)
            self.setToolTip(self.columns.status_icon_column, icon_tooltip)
        self.update_colums_text(color=color, bgcolor=bgcolor)
        if update_selection and self.isSelected():
            TreeItem.window.update_selection(new_selection=False)
        if update_album:
            self.parent().update(update_tracks=False, update_selection=update_selection)


class FileItem(TreeItem):
    def update(self, update_track=True, update_selection=True):
        file = self.obj
        icon, icon_tooltip = FileItem.decide_file_icon_info(file)
        self.setIcon(self.columns.status_icon_column, icon)
        self.setToolTip(self.columns.status_icon_column, icon_tooltip)

        fingerprint_column = self.columns.pos('~fingerprint')
        fingerprint_icon, fingerprint_tooltip = FileItem.decide_fingerprint_icon_info(file)
        self.setToolTip(fingerprint_column, fingerprint_tooltip)
        self.setIcon(fingerprint_column, fingerprint_icon)

        color = FileItem.file_colors[file.state]
        bgcolor = get_match_color(file.similarity, TreeItem.base_color)
        self.update_colums_text(color=color, bgcolor=bgcolor)
        if update_selection and self.isSelected():
            TreeItem.window.update_selection(new_selection=False)
        parent = self.parent()
        if isinstance(parent, TrackItem) and update_track:
            parent.update(update_files=False, update_selection=update_selection)

    @staticmethod
    def decide_file_icon_info(file):
        tooltip = ""
        if file.state == File.State.ERROR:
            if file.error_type == File.ErrorType.NOTFOUND:
                icon = FileItem.icon_error_not_found
                tooltip = _("File not found")
            elif file.error_type == File.ErrorType.NOACCESS:
                icon = FileItem.icon_error_no_access
                tooltip = _("File permission error")
            else:
                icon = FileItem.icon_error
                tooltip = _("Processing error(s): See the Errors tab in the File Info dialog")
        elif isinstance(file.parent_item, Track):
            if file.state == File.State.NORMAL:
                icon = FileItem.icon_saved
                tooltip = _("Track saved")
            elif file.state == File.State.PENDING:
                index = FileItem._match_icon_index(file.similarity)
                icon = FileItem.match_pending_icons[index]
                tooltip = _("Pending")
            else:
                index = FileItem._match_icon_index(file.similarity)
                icon = FileItem.match_icons[index]
                tooltip = _(FileItem.match_icons_info[index])
        elif file.state == File.State.PENDING:
            icon = FileItem.icon_file_pending
            tooltip = _("Pending")
        else:
            icon = FileItem.icon_file
        return (icon, tooltip)

    @staticmethod
    def _match_icon_index(similarity):
        return int(similarity * 5 + 0.5)

    @staticmethod
    def decide_fingerprint_icon_info(file):
        if getattr(file, 'acoustid_fingerprint', None):
            tagger = QtCore.QCoreApplication.instance()
            if tagger.acoustidmanager.is_submitted(file):
                icon = FileItem.icon_fingerprint_gray
                tooltip = _("Fingerprint has already been submitted")
            else:
                icon = FileItem.icon_fingerprint
                tooltip = _("Unsubmitted fingerprint")
        else:
            icon = QtGui.QIcon()
            tooltip = _(
                'No fingerprint was calculated for this file, use "Scan" or "Generate AcoustID Fingerprints" to calculate the fingerprint.'
            )
        return (icon, tooltip)
