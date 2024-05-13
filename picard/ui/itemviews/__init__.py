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
# Copyright (C) 2021 Bob Swift
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
from functools import partial
from heapq import (
    heappop,
    heappush,
)

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import log
from picard.album import (
    Album,
    NatAlbum,
)
from picard.cluster import (
    Cluster,
    ClusterList,
    UnclusteredFiles,
)
from picard.config import get_config
from picard.extension_points.item_actions import (
    ext_point_album_actions,
    ext_point_cluster_actions,
    ext_point_clusterlist_actions,
    ext_point_file_actions,
    ext_point_track_actions,
)
from picard.file import (
    File,
    FileErrorType,
)
from picard.i18n import (
    N_,
    gettext as _,
    ngettext,
)
from picard.track import (
    NonAlbumTrack,
    Track,
)
from picard.util import (
    icontheme,
    iter_files_from_objects,
    natsort,
    normpath,
    restore_method,
    strxfrm,
)

from picard.ui.collectionmenu import CollectionMenu
from picard.ui.colors import interface_colors
from picard.ui.enums import MainAction
from picard.ui.itemviews.columns import (
    DEFAULT_COLUMNS,
    ITEM_ICON_COLUMN,
    ColumnAlign,
    ColumnSortType,
)
from picard.ui.ratingwidget import RatingWidget
from picard.ui.scriptsmenu import ScriptsMenu
from picard.ui.util import menu_builder
from picard.ui.widgets.tristatesortheaderview import TristateSortHeaderView


COLUMN_ICON_SIZE = 16
COLUMN_ICON_BORDER = 2
ICON_SIZE = QtCore.QSize(COLUMN_ICON_SIZE+COLUMN_ICON_BORDER,
                         COLUMN_ICON_SIZE+COLUMN_ICON_BORDER)

DEFAULT_SECTION_SIZE = 100


def get_match_color(similarity, basecolor):
    c1 = (basecolor.red(), basecolor.green(), basecolor.blue())
    c2 = (223, 125, 125)
    return QtGui.QColor(
        int(c2[0] + (c1[0] - c2[0]) * similarity),
        int(c2[1] + (c1[1] - c2[1]) * similarity),
        int(c2[2] + (c1[2] - c2[2]) * similarity))


class MainPanel(QtWidgets.QSplitter):

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.tagger = QtCore.QCoreApplication.instance()
        self.setChildrenCollapsible(False)
        self.window = window
        self.create_icons()
        self._views = [FileTreeView(window, self), AlbumTreeView(window, self)]
        self._selected_view = self._views[0]
        self._ignore_selection_changes = False

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
        TreeItem.text_color_secondary = self.palette() \
            .brush(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Text).color()
        TrackItem.track_colors = defaultdict(lambda: TreeItem.text_color, {
            File.NORMAL: interface_colors.get_qcolor('entity_saved'),
            File.CHANGED: TreeItem.text_color,
            File.PENDING: interface_colors.get_qcolor('entity_pending'),
            File.ERROR: interface_colors.get_qcolor('entity_error'),
        })
        FileItem.file_colors = defaultdict(lambda: TreeItem.text_color, {
            File.NORMAL: TreeItem.text_color,
            File.CHANGED: TreeItem.text_color,
            File.PENDING: interface_colors.get_qcolor('entity_pending'),
            File.ERROR: interface_colors.get_qcolor('entity_error'),
        })

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
        AlbumItem.icon_cd_saved_modified = icontheme.lookup('media-optical-saved-modified',
                                                            icontheme.ICON_SIZE_MENU)
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
        for view in self._views:
            view.setSortingEnabled(sort)

    def select_object(self, obj):
        item = obj.item
        for view in self._views:
            if view.indexFromItem(item).isValid():
                view.setCurrentItem(item)
                self._update_selection(view)
                break


class ConfigurableColumnsHeader(TristateSortHeaderView):

    def __init__(self, parent=None):
        super().__init__(QtCore.Qt.Orientation.Horizontal, parent)
        self._visible_columns = set([ITEM_ICON_COLUMN])

        self.sortIndicatorChanged.connect(self.on_sort_indicator_changed)

        # enable sorting, but don't actually use it by default
        # XXX it would be nice to be able to go to the 'no sort' mode, but the
        #     internal model that QTreeWidget uses doesn't support it
        self.setSortIndicator(-1, QtCore.Qt.SortOrder.AscendingOrder)

    def show_column(self, column, show):
        if column == ITEM_ICON_COLUMN:
            # The first column always visible
            # Still execute following to ensure it is shown
            show = True
        self.parent().setColumnHidden(column, not show)
        if show:
            self._visible_columns.add(column)
        elif column in self._visible_columns:
            self._visible_columns.remove(column)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        parent = self.parent()

        for i, column in enumerate(DEFAULT_COLUMNS):
            if i == ITEM_ICON_COLUMN:
                continue
            action = QtGui.QAction(_(column.title), parent)
            action.setCheckable(True)
            action.setChecked(i in self._visible_columns)
            action.setEnabled(not self.is_locked)
            action.triggered.connect(partial(self.show_column, i))
            menu.addAction(action)

        menu.addSeparator()
        restore_action = QtGui.QAction(_("Restore default columns"), parent)
        restore_action.setEnabled(not self.is_locked)
        restore_action.triggered.connect(self.restore_defaults)
        menu.addAction(restore_action)

        lock_action = QtGui.QAction(_("Lock columns"), parent)
        lock_action.setCheckable(True)
        lock_action.setChecked(self.is_locked)
        lock_action.toggled.connect(self.lock)
        menu.addAction(lock_action)

        menu.exec(event.globalPos())
        event.accept()

    def restore_defaults(self):
        self.parent().restore_default_columns()

    def paintSection(self, painter, rect, index):
        column = DEFAULT_COLUMNS[index]
        if column.is_icon:
            painter.save()
            super().paintSection(painter, rect, index)
            painter.restore()
            column.paint_icon(painter, rect)
        else:
            super().paintSection(painter, rect, index)

    def on_sort_indicator_changed(self, index, order):
        if DEFAULT_COLUMNS[index].is_icon:
            self.setSortIndicator(-1, QtCore.Qt.SortOrder.AscendingOrder)

    def lock(self, is_locked):
        super().lock(is_locked)

    def __str__(self):
        name = getattr(self.parent(), 'NAME', str(self.parent().__class__.__name__))
        return f"{name}'s header"


def _alternative_versions(album):
    config = get_config()
    versions = album.release_group.versions

    album_tracks_count = album.get_num_total_files() or len(album.tracks)
    preferred_countries = set(config.setting['preferred_release_countries'])
    preferred_formats = set(config.setting['preferred_release_formats'])
    ORDER_BEFORE, ORDER_AFTER = 0, 1

    alternatives = []
    for version in versions:
        trackmatch = countrymatch = formatmatch = ORDER_BEFORE
        if version['totaltracks'] != album_tracks_count:
            trackmatch = ORDER_AFTER
        if preferred_countries:
            countries = set(version['countries'])
            if not countries or not countries.intersection(preferred_countries):
                countrymatch = ORDER_AFTER
        if preferred_formats:
            formats = set(version['formats'])
            if not formats or not formats.intersection(preferred_formats):
                formatmatch = ORDER_AFTER
        group = (trackmatch, countrymatch, formatmatch)
        # order by group, name, and id on push
        heappush(alternatives, (group, version['name'], version['id'], version['extra']))

    while alternatives:
        yield heappop(alternatives)


def _build_other_versions_actions(releases_menu, album, alternative_versions):
    heading = QtGui.QAction(album.release_group.version_headings, parent=releases_menu)
    heading.setDisabled(True)
    font = heading.font()
    font.setBold(True)
    heading.setFont(font)
    yield heading

    prev_group = None
    for group, action_text, release_id, extra in alternative_versions:
        if group != prev_group:
            if prev_group is not None:
                sep = QtGui.QAction(parent=releases_menu)
                sep.setSeparator(True)
                yield sep
            prev_group = group
        action = QtGui.QAction(action_text, parent=releases_menu)
        action.setCheckable(True)
        if extra:
            action.setToolTip(extra)
        if album.id == release_id:
            action.setChecked(True)
        action.triggered.connect(partial(album.switch_release_version, release_id))
        yield action


def _add_other_versions(releases_menu, album, action_loading):

    alt_versions = list(_alternative_versions(album))

    alt_versions_count = len(alt_versions)
    if alt_versions_count > 1:
        releases_menu.setTitle(_("&Other versions (%d)") % alt_versions_count)

    actions = _build_other_versions_actions(releases_menu, album, alt_versions)
    releases_menu.insertActions(action_loading, actions)
    releases_menu.removeAction(action_loading)


class BaseTreeView(QtWidgets.QTreeWidget):

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.setAccessibleName(_(self.NAME))
        self.setAccessibleDescription(_(self.DESCRIPTION))
        self.tagger = QtCore.QCoreApplication.instance()
        self.window = window
        # Should multiple files dropped be assigned to tracks sequentially?
        self._move_to_multi_tracks = True

        self._init_header()

        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)

        self.setSortingEnabled(True)

        self.expand_all_action = QtGui.QAction(_("&Expand all"), self)
        self.expand_all_action.triggered.connect(self.expandAll)
        self.collapse_all_action = QtGui.QAction(_("&Collapse all"), self)
        self.collapse_all_action.triggered.connect(self.collapseAll)
        self.select_all_action = QtGui.QAction(_("Select &all"), self)
        self.select_all_action.triggered.connect(self.selectAll)
        self.select_all_action.setShortcut(QtGui.QKeySequence(_("Ctrl+A")))
        self.doubleClicked.connect(self.activate_item)
        self.setUniformRowHeights(True)

        self.icon_plugins = icontheme.lookup('applications-system', icontheme.ICON_SIZE_MENU)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if not item:
            return
        config = get_config()
        obj = item.obj
        plugin_actions = None
        can_view_info = self.window.actions[MainAction.VIEW_INFO].isEnabled()
        menu = QtWidgets.QMenu(self)
        menu.setSeparatorsCollapsible(True)

        def add_actions(*args):
            menu_builder(menu, self.window.actions, *args)

        if isinstance(obj, Track):
            add_actions(
                MainAction.VIEW_INFO if can_view_info else None,
            )
            plugin_actions = list(ext_point_track_actions)
            if obj.num_linked_files == 1:
                add_actions(
                    MainAction.PLAY_FILE,
                    MainAction.OPEN_FOLDER,
                    MainAction.TRACK_SEARCH,
                )
                plugin_actions.extend(ext_point_file_actions)
            add_actions(
                MainAction.BROWSER_LOOKUP,
                MainAction.GENERATE_FINGERPRINTS if obj.num_linked_files > 0 else None,
                '-',
                MainAction.REFRESH if isinstance(obj, NonAlbumTrack) else None,
            )
        elif isinstance(obj, Cluster):
            add_actions(
                MainAction.VIEW_INFO if can_view_info else None,
                MainAction.BROWSER_LOOKUP,
                MainAction.SUBMIT_CLUSTER,
                '-',
                MainAction.AUTOTAG,
                MainAction.ANALYZE,
                MainAction.CLUSTER if isinstance(obj, UnclusteredFiles) else MainAction.ALBUM_SEARCH,
                MainAction.GENERATE_FINGERPRINTS,
            )
            plugin_actions = list(ext_point_cluster_actions)
        elif isinstance(obj, ClusterList):
            add_actions(
                MainAction.AUTOTAG,
                MainAction.ANALYZE,
                MainAction.GENERATE_FINGERPRINTS,
            )
            plugin_actions = list(ext_point_clusterlist_actions)
        elif isinstance(obj, File):
            add_actions(
                MainAction.VIEW_INFO if can_view_info else None,
                MainAction.PLAY_FILE,
                MainAction.OPEN_FOLDER,
                MainAction.BROWSER_LOOKUP,
                MainAction.SUBMIT_FILE_AS_RECORDING,
                MainAction.SUBMIT_FILE_AS_RELEASE,
                '-',
                MainAction.AUTOTAG,
                MainAction.ANALYZE,
                MainAction.TRACK_SEARCH,
                MainAction.GENERATE_FINGERPRINTS,
            )
            plugin_actions = list(ext_point_file_actions)
        elif isinstance(obj, Album):
            add_actions(
                MainAction.VIEW_INFO if can_view_info else None,
                MainAction.BROWSER_LOOKUP,
                MainAction.GENERATE_FINGERPRINTS if obj.get_num_total_files() > 0 else None,
                '-',
                MainAction.REFRESH,
            )
            plugin_actions = list(ext_point_album_actions)

        add_actions(
            '-',
            MainAction.SAVE,
            MainAction.REMOVE,
        )

        if isinstance(obj, Album) and not isinstance(obj, NatAlbum) and obj.loaded:
            releases_menu = QtWidgets.QMenu(_("&Other versions"), menu)
            releases_menu.setToolTipsVisible(True)
            releases_menu.setEnabled(False)
            add_actions(
                '-',
                releases_menu,
            )
            action_more_details = releases_menu.addAction(_("Show &more details…"))
            action_more_details.triggered.connect(self.window.actions[MainAction.ALBUM_OTHER_VERSIONS].trigger)

            album = obj
            if len(self.selectedItems()) == 1 and album.release_group:
                action_loading = QtGui.QAction(_("Loading…"), parent=releases_menu)
                action_loading.setDisabled(True)
                action_other_versions_separator = QtGui.QAction(parent=releases_menu)
                action_other_versions_separator.setSeparator(True)
                releases_menu.insertActions(action_more_details, [action_loading, action_other_versions_separator])

                if album.release_group.loaded:
                    _add_other_versions(releases_menu, album, action_loading)
                else:
                    callback = partial(_add_other_versions, releases_menu, album, action_loading)
                    album.release_group.load_versions(callback)
                releases_menu.setEnabled(True)

        if config.setting['enable_ratings'] and \
           len(self.window.selected_objects) == 1 and isinstance(obj, Track):
            action = QtWidgets.QWidgetAction(menu)
            action.setDefaultWidget(RatingWidget(menu, obj))
            add_actions(
                '-',
                action,
            )

        # Using type here is intentional. isinstance will return true for the
        # NatAlbum instance, which can't be part of a collection.
        selected_albums = [a for a in self.window.selected_objects if type(a) == Album]  # pylint: disable=C0123 # noqa: E721
        if selected_albums:
            add_actions(
                '-',
                CollectionMenu(selected_albums, _("Collections"), menu),
            )

        scripts = config.setting['list_of_scripts']

        if plugin_actions:
            plugin_menu = QtWidgets.QMenu(_("P&lugins"), menu)
            plugin_menu.setIcon(self.icon_plugins)
            add_actions(
                '-',
                plugin_menu,
            )

            plugin_menus = {}
            for action in plugin_actions:
                action_menu = plugin_menu
                for index in range(1, len(action.MENU) + 1):
                    key = tuple(action.MENU[:index])
                    if key in plugin_menus:
                        action_menu = plugin_menus[key]
                    else:
                        action_menu = plugin_menus[key] = action_menu.addMenu(key[-1])
                action_menu.addAction(action)

        if scripts:
            scripts_menu = ScriptsMenu(scripts, _("&Run scripts"), menu)
            scripts_menu.setIcon(self.icon_plugins)
            add_actions(
                '-',
                scripts_menu,
            )

        if isinstance(obj, Cluster) or isinstance(obj, ClusterList) or isinstance(obj, Album):
            add_actions(
                '-',
                self.expand_all_action,
                self.collapse_all_action,
            )

        add_actions(self.select_all_action)
        menu.exec(event.globalPos())
        event.accept()

    @restore_method
    def restore_state(self):
        config = get_config()
        self.restore_default_columns()

        header_state = config.persist[self.header_state]
        header = self.header()
        if header_state and header.restoreState(header_state):
            log.debug("Restoring state of %s" % header)
            for i in range(0, self.columnCount()):
                header.show_column(i, not self.isColumnHidden(i))

        header.lock(config.persist[self.header_locked])

    def save_state(self):
        config = get_config()
        header = self.header()
        if header.prelock_state is not None:
            state = header.prelock_state
        else:
            state = header.saveState()
        log.debug("Saving state of %s" % header)
        config.persist[self.header_state] = state
        config.persist[self.header_locked] = header.is_locked

    def restore_default_columns(self):
        labels = [_(c.title) if not c.is_icon else '' for c in DEFAULT_COLUMNS]
        self.setHeaderLabels(labels)

        header = self.header()
        header.setStretchLastSection(True)
        header.setDefaultAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        header.setDefaultSectionSize(DEFAULT_SECTION_SIZE)

        for i, c in enumerate(DEFAULT_COLUMNS):
            header.show_column(i, c.is_default)
            if c.is_icon:
                header.resizeSection(i, c.header_icon_size_with_border.width())
                header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.Fixed)
            else:
                header.resizeSection(i, c.size if c.size is not None else DEFAULT_SECTION_SIZE)
                header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.Interactive)

        self.sortByColumn(-1, QtCore.Qt.SortOrder.AscendingOrder)

    def _init_header(self):
        header = ConfigurableColumnsHeader(self)
        self.setHeader(header)
        self.restore_state()

    def supportedDropActions(self):
        return QtCore.Qt.DropAction.CopyAction | QtCore.Qt.DropAction.MoveAction

    def mimeTypes(self):
        """List of MIME types accepted by this view."""
        return ['text/uri-list', 'application/picard.album-list']

    def dragEnterEvent(self, event):
        super().dragEnterEvent(event)
        self._handle_external_drag(event)

    def dragMoveEvent(self, event):
        super().dragMoveEvent(event)
        self._handle_external_drag(event)

    def _handle_external_drag(self, event):
        if event.isAccepted() and (not event.source() or event.mimeData().hasUrls()):
            event.setDropAction(QtCore.Qt.DropAction.CopyAction)
            event.accept()

    def startDrag(self, supportedActions):
        """Start drag, *without* using pixmap."""
        items = self.selectedItems()
        if items:
            drag = QtGui.QDrag(self)
            drag.setMimeData(self.mimeData(items))
            # Render the dragged element as drag representation
            item = self.currentItem()
            rectangle = self.visualItemRect(item)
            pixmap = QtGui.QPixmap(rectangle.width(), rectangle.height())
            self.viewport().render(pixmap, QtCore.QPoint(), QtGui.QRegion(rectangle))
            drag.setPixmap(pixmap)
            drag.exec(QtCore.Qt.DropAction.MoveAction)

    def mimeData(self, items):
        """Return MIME data for specified items."""
        album_ids = []
        files = []
        url = QtCore.QUrl.fromLocalFile
        for item in items:
            obj = item.obj
            if isinstance(obj, Album):
                album_ids.append(obj.id)
            elif obj.iterfiles:
                files.extend([url(f.filename) for f in obj.iterfiles()])
        mimeData = QtCore.QMimeData()
        mimeData.setData('application/picard.album-list', '\n'.join(album_ids).encode())
        if files:
            mimeData.setUrls(files)
        return mimeData

    def scrollTo(self, index, scrolltype=QtWidgets.QAbstractItemView.ScrollHint.EnsureVisible):
        # QTreeView.scrollTo resets the horizontal scroll position to 0.
        # Reimplemented to maintain current horizontal scroll position.
        hscrollbar = self.horizontalScrollBar()
        xpos = hscrollbar.value()
        super().scrollTo(index, scrolltype)
        hscrollbar.setValue(xpos)

    @staticmethod
    def drop_urls(urls, target, move_to_multi_tracks=True):
        files = []
        new_paths = []
        tagger = QtCore.QCoreApplication.instance()
        for url in urls:
            log.debug("Dropped the URL: %r", url.toString(QtCore.QUrl.UrlFormattingOption.RemoveUserInfo))
            if url.scheme() == 'file' or not url.scheme():
                filename = normpath(url.toLocalFile().rstrip('\0'))
                file = tagger.files.get(filename)
                if file:
                    files.append(file)
                else:
                    new_paths.append(filename)
            elif url.scheme() in {'http', 'https'}:
                file_lookup = tagger.get_file_lookup()
                file_lookup.mbid_lookup(url.path(), browser_fallback=False)
        if files:
            tagger.move_files(files, target, move_to_multi_tracks)
        if new_paths:
            tagger.add_paths(new_paths, target=target)

    def dropEvent(self, event):
        if event.proposedAction() == QtCore.Qt.DropAction.IgnoreAction:
            event.acceptProposedAction()
            return
        # Dropping with Alt key pressed forces all dropped files being
        # assigned to the same track.
        if event.modifiers() == QtCore.Qt.KeyboardModifier.AltModifier:
            self._move_to_multi_tracks = False
        QtWidgets.QTreeView.dropEvent(self, event)
        # The parent dropEvent implementation automatically accepts the proposed
        # action. Override this, for external drops we never support move (which
        # can result in file deletion, e.g. on Windows).
        if event.isAccepted() and (not event.source() or event.mimeData().hasUrls()):
            event.setDropAction(QtCore.Qt.DropAction.CopyAction)
            event.accept()

    def dropMimeData(self, parent, index, data, action):
        target = None
        if parent:
            if index == parent.childCount():
                item = parent
            else:
                item = parent.child(index)
            if item is not None:
                target = item.obj
        if target is None:
            target = self.default_drop_target
        log.debug("Drop target = %r", target)
        handled = False
        # text/uri-list
        urls = data.urls()
        if urls:
            # Use QTimer.singleShot to run expensive processing outside of the drop handler.
            QtCore.QTimer.singleShot(0, partial(self.drop_urls, urls, target, self._move_to_multi_tracks))
            handled = True
        # application/picard.album-list
        albums = data.data('application/picard.album-list')
        if albums:
            album_ids = bytes(albums).decode().split("\n")
            log.debug("Dropped albums = %r", album_ids)
            files = iter_files_from_objects(self.tagger.load_album(id) for id in album_ids)
            # Use QTimer.singleShot to run expensive processing outside of the drop handler.
            move_files = partial(self.tagger.move_files, list(files), target)
            QtCore.QTimer.singleShot(0, move_files)
            handled = True
        self._move_to_multi_tracks = True  # Reset for next drop
        return handled

    def activate_item(self, index):
        obj = self.itemFromIndex(index).obj
        # Double-clicking albums or clusters should expand them. The album info can be
        # viewed by using the toolbar button.
        if not isinstance(obj, (Album, Cluster)) and obj.can_view_info:
            self.window.view_info()

    def add_cluster(self, cluster, parent_item=None):
        if parent_item is None:
            parent_item = self.clusters
        cluster_item = ClusterItem(cluster, not cluster.special, parent_item)
        if cluster.hide_if_empty and not cluster.files:
            cluster_item.update()
            cluster_item.setHidden(True)
        else:
            cluster_item.add_files(cluster.files)

    def moveCursor(self, action, modifiers):
        if action in {QtWidgets.QAbstractItemView.CursorAction.MoveUp, QtWidgets.QAbstractItemView.CursorAction.MoveDown}:
            item = self.currentItem()
            if item and not item.isSelected():
                self.setCurrentItem(item)
        return QtWidgets.QTreeWidget.moveCursor(self, action, modifiers)

    @property
    def default_drop_target(self):
        return None


class FileTreeView(BaseTreeView):

    NAME = N_("file view")
    DESCRIPTION = N_("Contains unmatched files and clusters")

    header_state = 'file_view_header_state'
    header_locked = 'file_view_header_locked'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unmatched_files = ClusterItem(self.tagger.unclustered_files, False, self)
        self.unmatched_files.update()
        self.unmatched_files.setExpanded(True)
        self.clusters = ClusterItem(self.tagger.clusters, False, self)
        self.set_clusters_text()
        self.clusters.setExpanded(True)
        self.tagger.cluster_added.connect(self.add_file_cluster)
        self.tagger.cluster_removed.connect(self.remove_file_cluster)

    def add_file_cluster(self, cluster, parent_item=None):
        self.add_cluster(cluster, parent_item)
        self.set_clusters_text()

    def remove_file_cluster(self, cluster):
        cluster.item.setSelected(False)
        self.clusters.removeChild(cluster.item)
        self.set_clusters_text()

    def set_clusters_text(self):
        self.clusters.setText(ITEM_ICON_COLUMN, "%s (%d)" % (_("Clusters"), len(self.tagger.clusters)))

    @property
    def default_drop_target(self):
        return self.tagger.unclustered_files


class AlbumTreeView(BaseTreeView):

    NAME = N_("album view")
    DESCRIPTION = N_("Contains albums and matched files")

    header_state = 'album_view_header_state'
    header_locked = 'album_view_header_locked'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tagger.album_added.connect(self.add_album)
        self.tagger.album_removed.connect(self.remove_album)

    def add_album(self, album):
        if isinstance(album, NatAlbum):
            item = NatAlbumItem(album, True)
            self.insertTopLevelItem(0, item)
        else:
            item = AlbumItem(album, True, self)
        item.setIcon(ITEM_ICON_COLUMN, AlbumItem.icon_cd)
        for i, column in enumerate(DEFAULT_COLUMNS):
            font = item.font(i)
            font.setBold(True)
            item.setFont(i, font)
            item.setText(i, album.column(column.key))
        self.add_cluster(album.unmatched_files, item)

    def remove_album(self, album):
        album.item.setSelected(False)
        self.takeTopLevelItem(self.indexOfTopLevelItem(album.item))


class TreeItem(QtWidgets.QTreeWidgetItem):

    def __init__(self, obj, sortable, *args):
        super().__init__(*args)
        self.obj = obj
        if obj is not None:
            obj.item = self
        self.sortable = sortable
        self._sortkeys = {}

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

        this_column = DEFAULT_COLUMNS[column]

        if this_column.sort_type == ColumnSortType.SORTKEY:
            sortkey = this_column.sortkey(self.obj)
        elif this_column.sort_type == ColumnSortType.NAT:
            sortkey = natsort.natkey(self.text(column))
        else:
            sortkey = strxfrm(self.text(column))
        self._sortkeys[column] = sortkey
        return sortkey

    def update_colums_text(self, color=None, bgcolor=None):
        for i, column in enumerate(DEFAULT_COLUMNS):
            if color is not None:
                self.setForeground(i, color)
            if bgcolor is not None:
                self.setBackground(i, bgcolor)
            if column.is_icon:
                self.setSizeHint(i, column.header_icon_size_with_border)
            else:
                if column.align == ColumnAlign.RIGHT:
                    self.setTextAlignment(i, QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
                self.setText(i, self.obj.column(column.key))


class ClusterItem(TreeItem):

    def __init__(self, *args):
        super().__init__(*args)
        self.setIcon(ITEM_ICON_COLUMN, ClusterItem.icon_dir)

    def update(self, update_selection=True):
        self.update_colums_text()
        album = self.obj.related_album
        if self.obj.special and album and album.loaded:
            album.item.update(update_tracks=False)
        if update_selection and self.isSelected():
            TreeItem.window.update_selection(new_selection=False)

    def add_file(self, file):
        self.add_files([file])

    def add_files(self, files):
        if self.obj.hide_if_empty and self.obj.files:
            self.setHidden(False)
        self.update()
        # addChild used (rather than building an items list and adding with addChildren)
        # to be certain about item order in the cluster (addChildren adds in reverse order).
        # Benchmarked performance was not noticeably different.
        for file in files:
            item = FileItem(file, True)
            self.addChild(item)
            item.update()

    def remove_file(self, file):
        file.item.setSelected(False)
        self.removeChild(file.item)
        self.update()
        if self.obj.hide_if_empty and not self.obj.files:
            self.setHidden(True)


class AlbumItem(TreeItem):

    def update(self, update_tracks=True, update_selection=True):
        album = self.obj
        selection_changed = self.isSelected()
        if update_tracks:
            oldnum = self.childCount() - 1
            newnum = len(album.tracks)
            if oldnum > newnum:  # remove old items
                for i in range(oldnum - newnum):
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
                track.item = item
                item.update(update_album=False)
            if newnum > oldnum:  # add new items
                items = []
                for i in range(oldnum, newnum):
                    item = TrackItem(album.tracks[i], False)
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
            self.setIcon(ITEM_ICON_COLUMN, AlbumItem.icon_error)
            self.setToolTip(ITEM_ICON_COLUMN, _("Processing error(s): See the Errors tab in the Album Info dialog"))
        elif album.is_complete():
            if album.is_modified():
                self.setIcon(ITEM_ICON_COLUMN, AlbumItem.icon_cd_saved_modified)
                self.setToolTip(ITEM_ICON_COLUMN, _("Album modified and complete"))
            else:
                self.setIcon(ITEM_ICON_COLUMN, AlbumItem.icon_cd_saved)
                self.setToolTip(ITEM_ICON_COLUMN, _("Album unchanged and complete"))
        else:
            if album.is_modified():
                self.setIcon(ITEM_ICON_COLUMN, AlbumItem.icon_cd_modified)
                self.setToolTip(ITEM_ICON_COLUMN, _("Album modified"))
            else:
                self.setIcon(ITEM_ICON_COLUMN, AlbumItem.icon_cd)
                self.setToolTip(ITEM_ICON_COLUMN, _("Album unchanged"))
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
        fingerprint_column = DEFAULT_COLUMNS.pos('~fingerprint')
        if num_linked_files == 1:
            file = track.files[0]
            file.item = self
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
                icon_tooltip = ngettext('%i matched file', '%i matched files',
                    num_linked_files) % num_linked_files
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
                    for i in range(oldnum - newnum):
                        self.takeChild(newnum - 1).obj.item = None
                    oldnum = newnum
                for i in range(oldnum):  # update existing items
                    item = self.child(i)
                    file = track.files[i]
                    item.obj = file
                    file.item = item
                    item.update(update_track=False)
                if newnum > oldnum:  # add new items
                    items = []
                    for i in range(newnum - 1, oldnum - 1, -1):
                        item = FileItem(track.files[i], False)
                        item.update(update_track=False, update_selection=update_selection)
                        items.append(item)
                    self.addChildren(items)
            self.setExpanded(True)
        if track.errors:
            self.setIcon(ITEM_ICON_COLUMN, TrackItem.icon_error)
            self.setToolTip(ITEM_ICON_COLUMN, _("Processing error(s): See the Errors tab in the Track Info dialog"))
        else:
            self.setIcon(ITEM_ICON_COLUMN, icon)
            self.setToolTip(ITEM_ICON_COLUMN, icon_tooltip)
        self.update_colums_text(color=color, bgcolor=bgcolor)
        if update_selection and self.isSelected():
            TreeItem.window.update_selection(new_selection=False)
        if update_album:
            self.parent().update(update_tracks=False, update_selection=update_selection)


class FileItem(TreeItem):

    def update(self, update_track=True, update_selection=True):
        file = self.obj
        icon, icon_tooltip = FileItem.decide_file_icon_info(file)
        self.setIcon(ITEM_ICON_COLUMN, icon)
        self.setToolTip(ITEM_ICON_COLUMN, icon_tooltip)

        fingerprint_column = DEFAULT_COLUMNS.pos('~fingerprint')
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
        if file.state == File.ERROR:
            if file.error_type == FileErrorType.NOTFOUND:
                icon = FileItem.icon_error_not_found
                tooltip = _("File not found")
            elif file.error_type == FileErrorType.NOACCESS:
                icon = FileItem.icon_error_no_access
                tooltip = _("File permission error")
            else:
                icon = FileItem.icon_error
                tooltip = _("Processing error(s): See the Errors tab in the File Info dialog")
        elif isinstance(file.parent, Track):
            if file.state == File.NORMAL:
                icon = FileItem.icon_saved
                tooltip = _("Track saved")
            elif file.state == File.PENDING:
                index = FileItem._match_icon_index(file.similarity)
                icon = FileItem.match_pending_icons[index]
                tooltip = _("Pending")
            else:
                index = FileItem._match_icon_index(file.similarity)
                icon = FileItem.match_icons[index]
                tooltip = _(FileItem.match_icons_info[index])
        elif file.state == File.PENDING:
            icon = FileItem.icon_file_pending
            tooltip = _("Pending")
        else:
            icon = FileItem.icon_file
        return (icon, tooltip)

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
            tooltip = _('No fingerprint was calculated for this file, use "Scan" or "Generate AcoustID Fingerprints" to calculate the fingerprint.')
        return (icon, tooltip)
