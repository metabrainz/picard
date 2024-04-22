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


from functools import partial
from heapq import (
    heappop,
    heappush,
)

from PySide6 import (
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
from picard.file import File
from picard.i18n import gettext as _
from picard.script import iter_tagging_scripts_from_tuples
from picard.track import (
    NonAlbumTrack,
    Track,
)
from picard.util import (
    icontheme,
    iter_files_from_objects,
    normpath,
    restore_method,
)

from picard.ui.collectionmenu import CollectionMenu
from picard.ui.enums import MainAction
from picard.ui.itemviews.columns import (
    DEFAULT_COLUMNS,
    ITEM_ICON_COLUMN,
)
from picard.ui.ratingwidget import RatingWidget
from picard.ui.scriptsmenu import ScriptsMenu
from picard.ui.util import menu_builder
from picard.ui.widgets.tristatesortheaderview import TristateSortHeaderView


DEFAULT_SECTION_SIZE = 100


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
        else:
            self._visible_columns.discard(column)

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

    if album.release_group.versions_count is not None:
        releases_menu.setTitle(_("&Other versions (%d)") % album.release_group.versions_count)

    actions = _build_other_versions_actions(releases_menu, album, _alternative_versions(album))
    releases_menu.insertActions(action_loading, actions)
    releases_menu.removeAction(action_loading)


class BaseTreeView(QtWidgets.QTreeWidget):

    def __init__(self, window, parent=None):
        super().__init__(parent=parent)
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
            action.setDefaultWidget(RatingWidget(obj, parent=menu))
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
                CollectionMenu(selected_albums, _("Collections"), parent=menu),
            )

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

        scripts = config.setting['list_of_scripts']
        if scripts:
            scripts_menu = ScriptsMenu(iter_tagging_scripts_from_tuples(scripts), _("&Run scripts"), parent=menu)
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
        from picard.ui.itemviews import ClusterItem
        cluster_item = ClusterItem(cluster, sortable=not cluster.special, parent=parent_item)
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
