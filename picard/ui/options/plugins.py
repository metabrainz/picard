# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2014 Shadab Zafar
# Copyright (C) 2015 Laurent Monin
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
from operator import attrgetter
import os.path
import sys

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from PyQt5.QtWidgets import QTreeWidgetItemIterator

from picard import (
    config,
    log,
)
from picard.const import (
    PLUGIN_ACTION_INSTALL,
    PLUGIN_ACTION_NONE,
    PLUGIN_ACTION_UNINSTALL,
    PLUGIN_ACTION_UPDATE,
    PLUGINS_API,
    USER_PLUGIN_DIR,
)

from picard.ui import HashableTreeWidgetItem
from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_plugins import Ui_PluginsOptionsPage

COLUMN_NAME, COLUMN_VERSION, COLUMN_ACTION = range(3)


class PluginTreeWidgetItem(HashableTreeWidgetItem):

    def __lt__(self, other):
        if (not isinstance(other, PluginTreeWidgetItem)):
            return super().__lt__(other)

        tree = self.treeWidget()
        if not tree:
            column = 0
        else:
            column = tree.sortColumn()

        return self.sortData(column) < other.sortData(column)

    def __init__(self, *args):
        super().__init__(*args)
        self._sortData = {}

    def sortData(self, column):
        return self._sortData.get(column, self.text(column))

    def setSortData(self, column, data):
        self._sortData[column] = data


class PluginsOptionsPage(OptionsPage):

    NAME = "plugins"
    TITLE = N_("Plugins")
    PARENT = None
    SORT_ORDER = 70
    ACTIVE = True

    options = [
        config.ListOption("setting", "enabled_plugins", []),
        config.Option("persist", "plugins_list_state", QtCore.QByteArray()),
        config.Option("persist", "plugins_list_sort_section", 0),
        config.Option("persist", "plugins_list_sort_order",
                      QtCore.Qt.AscendingOrder),
        config.Option("persist", "plugins_list_selected", ""),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_PluginsOptionsPage()
        self.ui.setupUi(self)
        #fix for PICARD-1226, QT bug (https://bugreports.qt.io/browse/QTBUG-22572) workaround
        self.ui.plugins.setStyleSheet('')
        self.ui.plugins.itemSelectionChanged.connect(self.change_details)
        self.ui.plugins.mimeTypes = self.mimeTypes
        self.ui.plugins.dropEvent = self.dropEvent
        self.ui.plugins.dragEnterEvent = self.dragEnterEvent
        if sys.platform == "win32":
            self.loader = "file:///%s"
        else:
            self.loader = "file://%s"
        self.ui.install_plugin.clicked.connect(self.open_plugins)
        self.ui.folder_open.clicked.connect(self.open_plugin_dir)
        self.ui.reload_list_of_plugins.clicked.connect(self.reload_list_of_plugins)
        self.manager = self.tagger.pluginmanager
        self.manager.plugin_installed.connect(self.plugin_installed)
        self.manager.plugin_updated.connect(self.plugin_updated)
        self.ui.plugins.header().setStretchLastSection(False)
        self.ui.plugins.header().setSectionResizeMode(COLUMN_NAME, QtWidgets.QHeaderView.Stretch)
        self.ui.plugins.header().setSectionResizeMode(COLUMN_VERSION, QtWidgets.QHeaderView.Stretch)
        self.ui.plugins.header().resizeSection(COLUMN_ACTION, 100)
        self.ui.plugins.setSortingEnabled(True)

    def items(self):
        iterator = QTreeWidgetItemIterator(self.ui.plugins, QTreeWidgetItemIterator.All)
        while iterator.value():
            item = iterator.value()
            iterator += 1
            plugin = item.data(COLUMN_NAME, QtCore.Qt.UserRole)
            yield (item, plugin)

    def find_by_name(self, plugin_name):
        for item, plugin in self.items():
            if plugin_name == plugin.module_name:
                return (item, plugin)
        return (None, None)

    def selected_plugin(self):
        try:
            item = self.ui.plugins.selectedItems()[0]
            return item.data(COLUMN_NAME, QtCore.Qt.UserRole)
        except IndexError:
            return None

    def save_state(self):
        header = self.ui.plugins.header()
        config.persist["plugins_list_state"] = header.saveState()
        config.persist["plugins_list_sort_section"] = header.sortIndicatorSection()
        config.persist["plugins_list_sort_order"] = header.sortIndicatorOrder()
        plugin = self.selected_plugin()
        if plugin:
            selected = plugin.module_name
        else:
            selected = ""
        config.persist["plugins_list_selected"] = selected

    def restore_state(self, restore_selection=False):
        header = self.ui.plugins.header()
        header.restoreState(config.persist["plugins_list_state"])
        idx = config.persist["plugins_list_sort_section"]
        order = config.persist["plugins_list_sort_order"]
        header.setSortIndicator(idx, order)
        self.ui.plugins.sortByColumn(idx, order)
        selected = restore_selection and config.persist["plugins_list_selected"]
        if selected:
            item, _unused_ = self.find_by_name(selected)
            if item:
                self.ui.plugins.setCurrentItem(item)
                self.ui.plugins.scrollToItem(item)
        else:
            self.ui.plugins.setCurrentItem(self.ui.plugins.topLevelItem(0))

    def _populate(self):
        self.ui.details.setText("<b>" + _("No plugins installed.") + "</b>")
        self._user_interaction(False)
        plugins = sorted(self.manager.plugins, key=attrgetter('name'))
        enabled_plugins = config.setting["enabled_plugins"]
        available_plugins = dict([(p.module_name, p.version) for p in
                                  self.manager.available_plugins])
        installed = []
        for plugin in plugins:
            plugin.enabled = plugin.module_name in enabled_plugins
            if plugin.module_name in available_plugins.keys():
                latest = available_plugins[plugin.module_name]
                if latest.split('.') > plugin.version.split('.'):
                    plugin.new_version = latest
                    plugin.can_be_updated = True
            self.add_plugin_item(plugin)
            installed.append(plugin.module_name)

        for plugin in sorted(self.manager.available_plugins, key=attrgetter('name')):
            if plugin.module_name not in installed:
                plugin.can_be_downloaded = True
                plugin.enabled = plugin.module_name in enabled_plugins
                self.add_plugin_item(plugin)

        self._user_interaction(True)

    def _remove_all(self):
        for item, _unused_ in self.items():
            idx = self.ui.plugins.indexOfTopLevelItem(item)
            self.ui.plugins.takeTopLevelItem(idx)

    def restore_defaults(self):
        # Plugin manager has to be updated
        for plugin in self.manager.plugins:
            plugin.enabled = False
        # Remove previous entries
        self._user_interaction(False)
        self._remove_all()
        super().restore_defaults()

    def load(self):
        self._populate()
        self.restore_state()

    def _reload(self):
        self._populate()
        self.restore_state(restore_selection=True)

    def _user_interaction(self, enabled):
        self.ui.plugins.blockSignals(not enabled)
        self.ui.plugins_container.setEnabled(enabled)

    def reload_list_of_plugins(self):
        self.ui.details.setText("")
        self._user_interaction(False)
        self.save_state()
        self._remove_all()
        self.manager.query_available_plugins(callback=self._reload)

    def plugin_installed(self, plugin):
        if not plugin.compatible:
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setText(_("The plugin '%s' is not compatible with this version of Picard.") % plugin.name)
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.setDefaultButton(QtWidgets.QMessageBox.Ok)
            msgbox.exec_()
            return
        plugin.new_version = ""
        plugin.enabled = True
        plugin.can_be_updated = False
        plugin.can_be_downloaded = False
        item, _unused_ = self.find_by_name(plugin.module_name)
        if item:
            self.add_plugin_item(plugin, item=item)
            self.ui.plugins.setCurrentItem(item)
            self.change_details()
        else:
            self.add_plugin_item(plugin)

    def plugin_updated(self, plugin_name):
        item, plugin = self.find_by_name(plugin_name)
        if item:
            plugin.can_be_updated = False
            plugin.can_be_downloaded = False
            plugin.marked_for_update = True
            col_version = self.ui.plugins.itemWidget(item, COLUMN_VERSION)
            col_version.setText(_("Updated"))
            col_version.setEnabled(False)
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setText(
                _("The plugin '%s' will be upgraded to version %s on next run of Picard.")
                % (plugin.name, plugin.new_version))
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.setDefaultButton(QtWidgets.QMessageBox.Ok)
            msgbox.exec_()
            self.add_plugin_item(plugin, item=item)
            self.ui.plugins.setCurrentItem(item)
            self.change_details()

    def uninstall_plugin(self):
        plugin = self.selected_plugin()
        if not plugin:
            return
        buttonReply = QtWidgets.QMessageBox.question(
            self,
            _("Uninstall plugin?"),
            _("Do you really want to uninstall the plugin '%s' ?") % plugin.name,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if buttonReply == QtWidgets.QMessageBox.Yes:
            self.manager.remove_plugin(plugin.module_name)
            item = self.ui.plugins.currentItem()
            plugin.is_uninstalled = True
            plugin.enabled = False

            if plugin.module_name in config.setting["enabled_plugins"]:
                config.setting["enabled_plugins"].remove(plugin.module_name)

            col_action = self.ui.plugins.itemWidget(item, COLUMN_ACTION)
            col_action.setText(_("Uninstalled"))
            col_action.setEnabled(False)
            item.setCheckState(COLUMN_NAME, QtCore.Qt.Unchecked)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsUserCheckable)

    def add_plugin_item(self, plugin, item=None):
        if item is None:
            item = PluginTreeWidgetItem(self.ui.plugins)
        item.setData(COLUMN_NAME, QtCore.Qt.UserRole, plugin)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        item.setText(COLUMN_NAME, plugin.name)
        item.setSortData(COLUMN_NAME, plugin.name.lower())

        def update_checkbox(item, enabled=None):
            plugin = item.data(COLUMN_NAME, QtCore.Qt.UserRole)
            if enabled is not None:
                plugin.enabled = bool(enabled)
            if plugin.enabled:
                item.setCheckState(COLUMN_NAME, QtCore.Qt.Checked)
            else:
                item.setCheckState(COLUMN_NAME, QtCore.Qt.Unchecked)

        update_checkbox(item)

        if plugin.marked_for_update:
            version = plugin.new_version
        else:
            version = plugin.version
        item.setText(COLUMN_VERSION, version)

        def download_processor(action):
            self.ui.plugins.setCurrentItem(item)
            self.download_plugin(action)

        def uninstall_processor():
            self.ui.plugins.setCurrentItem(item)
            self.uninstall_plugin()

        bt_action = PLUGIN_ACTION_NONE
        if plugin.is_uninstalled:
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsUserCheckable)
            update_checkbox(item, enabled=False)

        if plugin.can_be_downloaded:
            bt_action = PLUGIN_ACTION_INSTALL
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsUserCheckable)
            update_checkbox(item, enabled=False)
        else:
            bt_action = PLUGIN_ACTION_UNINSTALL

        if bt_action != PLUGIN_ACTION_NONE:
            labels = {
                PLUGIN_ACTION_INSTALL: N_("Install"),
                PLUGIN_ACTION_UNINSTALL: N_("Uninstall"),
            }
            label = _(labels[bt_action])
            if plugin.is_uninstalled:
                label = _("Uninstalled")
            button = QtWidgets.QPushButton(label)
            button.setMaximumHeight(button.fontMetrics().boundingRect(label).height() + 7)
            self.ui.plugins.setItemWidget(item, COLUMN_ACTION, button)
            if plugin.is_uninstalled:
                button.setEnabled(False)

            if bt_action == PLUGIN_ACTION_INSTALL:
                button.released.connect(partial(download_processor, bt_action))
            else:
                button.released.connect(uninstall_processor)

        if plugin.can_be_updated:
            label = _("Upgrade from %s to %s" % (plugin.version, plugin.new_version))
            if plugin.marked_for_update:
                label = _("Updated")
            button = QtWidgets.QPushButton(label)
            button.setMaximumHeight(button.fontMetrics().boundingRect(label).height() + 7)
            self.ui.plugins.setItemWidget(item, COLUMN_VERSION, button)
            if plugin.marked_for_update:
                button.setEnabled(False)

            button.released.connect(partial(download_processor, PLUGIN_ACTION_UPDATE))

        self.ui.plugins.header().resizeSections(QtWidgets.QHeaderView.ResizeToContents)
        return item

    def save(self):
        enabled_plugins = []
        for item, plugin in self.items():
            if item.checkState(COLUMN_NAME) == QtCore.Qt.Checked:
                enabled_plugins.append(plugin.module_name)
        config.setting["enabled_plugins"] = enabled_plugins
        self.save_state()

    def change_details(self):
        plugin = self.selected_plugin()
        if not plugin:
            return
        text = []
        if plugin.new_version:
            if plugin.marked_for_update:
                text.append("<b>" + _("Restart Picard to upgrade to new version") + ": " + plugin.new_version + "</b>")
            else:
                text.append("<b>" + _("New version available") + ": " + plugin.new_version + "</b>")
        if plugin.description:
            text.append(plugin.description + "<hr width='90%'/>")
        if plugin.name:
            text.append("<b>" + _("Name") + "</b>: " + plugin.name)
        if plugin.author:
            text.append("<b>" + _("Authors") + "</b>: " + plugin.author)
        if plugin.license:
            text.append("<b>" + _("License") + "</b>: " + plugin.license)
        text.append("<b>" + _("Files") + "</b>: " + plugin.files_list)
        self.ui.details.setText("<p>%s</p>" % "<br/>\n".join(text))

    def open_plugins(self):
        files, _filter = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "",
            QtCore.QDir.homePath(),
            "Picard plugin (*.py *.pyc *.zip)"
        )
        if files:
            for path in files:
                self.manager.install_plugin(path, action=PLUGIN_ACTION_INSTALL)

    def download_plugin(self, action):
        plugin = self.selected_plugin()
        if not plugin:
            return

        self.tagger.webservice.get(
            PLUGINS_API['host'],
            PLUGINS_API['port'],
            PLUGINS_API['endpoint']['download'],
            partial(self.download_handler, action, plugin=plugin),
            parse_response_type=None,
            priority=True,
            important=True,
            queryargs={"id": plugin.module_name}
        )

    def download_handler(self, action, response, reply, error, plugin):
        if error:
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setText(_("The plugin '%s' could not be downloaded.") % plugin.module_name)
            msgbox.setInformativeText(_("Please try again later."))
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.setDefaultButton(QtWidgets.QMessageBox.Ok)
            msgbox.exec_()
            log.error("Error occurred while trying to download the plugin: '%s'" % plugin.module_name)
            return

        self.manager.install_plugin(
            None,
            action,
            plugin_name=plugin.module_name,
            plugin_data=response,
        )

    def open_plugin_dir(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.loader % USER_PLUGIN_DIR, QtCore.QUrl.TolerantMode))

    def mimeTypes(self):
        return ["text/uri-list"]

    def dragEnterEvent(self, event):
        event.setDropAction(QtCore.Qt.CopyAction)
        event.accept()

    def dropEvent(self, event):
        for path in [os.path.normpath(u.toLocalFile()) for u in event.mimeData().urls()]:
            self.manager.install_plugin(path, action=PLUGIN_ACTION_INSTALL)


register_options_page(PluginsOptionsPage)
