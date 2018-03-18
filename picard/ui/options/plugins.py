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

import os.path
import sys
from functools import partial
from operator import attrgetter
from PyQt5 import QtCore, QtGui, QtWidgets
from picard import config, log
from picard.const import (
    USER_PLUGIN_DIR,
    PLUGINS_API,
    PLUGIN_ACTION_NONE,
    PLUGIN_ACTION_INSTALL,
    PLUGIN_ACTION_UPDATE,
    PLUGIN_ACTION_UNINSTALL,
)
from picard.ui import HashableTreeWidgetItem
from picard.ui.options import OptionsPage, register_options_page
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
        self.items = {}
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
        self.tagger.pluginmanager.plugin_installed.connect(self.plugin_installed)
        self.tagger.pluginmanager.plugin_updated.connect(self.plugin_updated)
        self.ui.plugins.header().setStretchLastSection(False)
        self.ui.plugins.header().setSectionResizeMode(COLUMN_NAME, QtWidgets.QHeaderView.Stretch)
        self.ui.plugins.header().setSectionResizeMode(COLUMN_VERSION, QtWidgets.QHeaderView.Stretch)
        self.ui.plugins.header().resizeSection(COLUMN_ACTION, 100)
        self.ui.plugins.setSortingEnabled(True)

    def save_state(self):
        header = self.ui.plugins.header()
        config.persist["plugins_list_state"] = header.saveState()
        config.persist["plugins_list_sort_section"] = header.sortIndicatorSection()
        config.persist["plugins_list_sort_order"] = header.sortIndicatorOrder()
        try:
            selected = self.items[self.ui.plugins.selectedItems()[COLUMN_NAME]].module_name
        except IndexError:
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
            for i, p in self.items.items():
                if selected == p.module_name:
                    self.ui.plugins.setCurrentItem(i)
                    self.ui.plugins.scrollToItem(i)
                    break
        else:
            self.ui.plugins.setCurrentItem(self.ui.plugins.topLevelItem(0))

    def _populate(self):
        self.ui.details.setText("<b>" + _("No plugins installed.") + "</b>")
        self._user_interaction(False)
        plugins = sorted(self.tagger.pluginmanager.plugins, key=attrgetter('name'))
        enabled_plugins = config.setting["enabled_plugins"]
        available_plugins = dict([(p.module_name, p.version) for p in
                                  self.tagger.pluginmanager.available_plugins])
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

        for plugin in sorted(self.tagger.pluginmanager.available_plugins, key=attrgetter('name')):
            if plugin.module_name not in installed:
                plugin.can_be_downloaded = True
                self.add_plugin_item(plugin)

        self._user_interaction(True)

    def _remove_all(self):
        for i, p in self.items.items():
            idx = self.ui.plugins.indexOfTopLevelItem(i)
            self.ui.plugins.takeTopLevelItem(idx)
        self.items = {}

    def restore_defaults(self):
        # Plugin manager has to be updated
        for plugin in self.tagger.pluginmanager.plugins:
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
        self.tagger.pluginmanager.query_available_plugins(callback=self._reload)

    def plugin_installed(self, plugin):
        if not plugin.compatible:
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setText(_("The plugin '%s' is not compatible with this version of Picard.") % plugin.name)
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.setDefaultButton(QtWidgets.QMessageBox.Ok)
            msgbox.exec_()
            return
        plugin.new_version = ""
        plugin.enabled = False
        plugin.can_be_updated = False
        plugin.can_be_downloaded = False
        for i, p in self.items.items():
            if plugin.module_name == p.module_name:
                if i.checkState(COLUMN_NAME) == QtCore.Qt.Checked:
                    plugin.enabled = True
                self.add_plugin_item(plugin, item=i)
                self.ui.plugins.setCurrentItem(i)
                self.change_details()
                break
        else:
            self.add_plugin_item(plugin)

    def plugin_updated(self, plugin_name):
        for i, p in self.items.items():
            if plugin_name == p.module_name:
                p.can_be_updated = False
                p.can_be_downloaded = False
                p.marked_for_update = True
                item = self.ui.plugins.currentItem()
                self.ui.plugins.itemWidget(item, COLUMN_VERSION).setText(_("Updated"))
                self.ui.plugins.itemWidget(item, COLUMN_VERSION).setEnabled(False)
                msgbox = QtWidgets.QMessageBox(self)
                msgbox.setText(
                    _("The plugin '%s' will be upgraded to version %s on next run of Picard.")
                    % (p.name, p.new_version))
                msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msgbox.setDefaultButton(QtWidgets.QMessageBox.Ok)
                msgbox.exec_()
                self.add_plugin_item(p, item=i)
                self.ui.plugins.setCurrentItem(i)
                self.change_details()
                break

    def uninstall_plugin(self):
        plugin = self.items[self.ui.plugins.selectedItems()[COLUMN_NAME]]
        buttonReply = QtWidgets.QMessageBox.question(self, _("Uninstall plugin?"),
                _("Do you really want to uninstall the plugin '%s' ?") % plugin.name,
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if buttonReply == QtWidgets.QMessageBox.Yes:
            self.tagger.pluginmanager.remove_plugin(plugin.module_name)
            item = self.ui.plugins.currentItem()
            plugin.is_uninstalled = True
            plugin.enabled = False

            if plugin.module_name in config.setting["enabled_plugins"]:
                config.setting["enabled_plugins"].remove(plugin.module_name)

            self.ui.plugins.itemWidget(item, COLUMN_ACTION).setText(_("Uninstalled"))
            self.ui.plugins.itemWidget(item, COLUMN_ACTION).setEnabled(False)
            item.setCheckState(COLUMN_NAME, QtCore.Qt.Unchecked)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsUserCheckable)

    def add_plugin_item(self, plugin, item=None):
        if item is None:
            item = PluginTreeWidgetItem(self.ui.plugins)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        item.setText(COLUMN_NAME, plugin.name)
        item.setSortData(COLUMN_NAME, plugin.name.lower())
        if plugin.enabled:
            item.setCheckState(COLUMN_NAME, QtCore.Qt.Checked)
        else:
            item.setCheckState(COLUMN_NAME, QtCore.Qt.Unchecked)

        if plugin.marked_for_update:
            item.setText(COLUMN_VERSION, plugin.new_version)
        else:
            item.setText(COLUMN_VERSION, plugin.version)

        def download_processor(action):
            self.ui.plugins.setCurrentItem(item)
            self.download_plugin(action)

        def uninstall_processor():
            self.ui.plugins.setCurrentItem(item)
            self.uninstall_plugin()

        bt_action = PLUGIN_ACTION_NONE
        if plugin.is_uninstalled:
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsUserCheckable)

        if plugin.can_be_downloaded:
            bt_action = PLUGIN_ACTION_INSTALL
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsUserCheckable)
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
        self.items[item] = plugin
        return item

    def save(self):
        enabled_plugins = []
        for item, plugin in self.items.items():
            if item.checkState(COLUMN_NAME) == QtCore.Qt.Checked:
                enabled_plugins.append(plugin.module_name)
        config.setting["enabled_plugins"] = enabled_plugins
        self.save_state()

    def change_details(self):
        try:
            plugin = self.items[self.ui.plugins.selectedItems()[COLUMN_NAME]]
        except IndexError:
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
                self.tagger.pluginmanager.install_plugin(path, action=PLUGIN_ACTION_INSTALL)

    def download_plugin(self, action):
        selected = self.ui.plugins.selectedItems()[COLUMN_NAME]
        plugin = self.items[selected]

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

        self.tagger.pluginmanager.install_plugin(
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
            self.tagger.pluginmanager.install_plugin(path, action=PLUGIN_ACTION_INSTALL)


register_options_page(PluginsOptionsPage)
