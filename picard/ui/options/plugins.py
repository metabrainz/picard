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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sortData = {}
        self.can_be_downloaded = False
        self.can_be_updated = False
        self.marked_for_update = False

    def __lt__(self, other):
        if (not isinstance(other, PluginTreeWidgetItem)):
            return super().__lt__(other)

        tree = self.treeWidget()
        if not tree:
            column = 0
        else:
            column = tree.sortColumn()

        return self.sortData(column) < other.sortData(column)

    def sortData(self, column):
        return self._sortData.get(column, self.text(column))

    def setSortData(self, column, data):
        self._sortData[column] = data

    def is_enabled(self):
        return self.checkState(COLUMN_NAME) == QtCore.Qt.Checked

    def enable(self, boolean):
        if boolean:
            self.setCheckState(COLUMN_NAME, QtCore.Qt.Checked)
        else:
            self.setCheckState(COLUMN_NAME, QtCore.Qt.Unchecked)

    def checkable(self, boolean):
        if boolean:
            self.setFlags(self.flags() | QtCore.Qt.ItemIsUserCheckable)
        else:
            self.setFlags(self.flags() ^ QtCore.Qt.ItemIsUserCheckable)



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
        header = self.ui.plugins.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(COLUMN_NAME, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(COLUMN_VERSION, QtWidgets.QHeaderView.Stretch)
        header.resizeSection(COLUMN_ACTION, 100)
        self.ui.plugins.setSortingEnabled(True)

    @staticmethod
    def item_plugin(item):
        return item.data(COLUMN_NAME, QtCore.Qt.UserRole)

    def items(self):
        iterator = QTreeWidgetItemIterator(self.ui.plugins, QTreeWidgetItemIterator.All)
        while iterator.value():
            item = iterator.value()
            iterator += 1
            plugin = self.item_plugin(item)
            yield (item, plugin)

    def find_by_name(self, plugin_name):
        for item, plugin in self.items():
            if plugin_name == plugin.module_name:
                return (item, plugin)
        return (None, None)

    def selected_item(self):
        try:
            return self.ui.plugins.selectedItems()[0]
        except IndexError:
            return None

    def selected_plugin(self):
        item = self.selected_item()
        if item:
            return self.item_plugin(item)
        else:
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

    def set_current_item(self, item, scroll=False):
        if scroll:
            self.ui.plugins.scrollToItem(item)
        self.ui.plugins.setCurrentItem(item)
        self.refresh_details(item)


    def restore_state(self):
        header = self.ui.plugins.header()
        header.restoreState(config.persist["plugins_list_state"])
        idx = config.persist["plugins_list_sort_section"]
        order = config.persist["plugins_list_sort_order"]
        header.setSortIndicator(idx, order)
        self.ui.plugins.sortByColumn(idx, order)
        selected = config.persist["plugins_list_selected"]
        item = None
        if selected:
            item, _unused_ = self.find_by_name(selected)
        if not item:
            item = self.ui.plugins.topLevelItem(0)
        if item:
            self.set_current_item(item, scroll=True)

    @staticmethod
    def is_plugin_enabled(plugin):
        return bool(plugin.module_name in config.setting["enabled_plugins"])

    def _populate(self):
        self.ui.details.setText("<b>" + _("No plugins installed.") + "</b>")
        self._user_interaction(False)
        plugins = sorted(self.manager.plugins, key=attrgetter('name'))
        available_plugins = dict([(p.module_name, p.version) for p in
                                  self.manager.available_plugins])
        installed = []
        for plugin in plugins:
            new_version = ''
            if plugin.module_name in available_plugins:
                latest = available_plugins[plugin.module_name]
                if latest.split('.') > plugin.version.split('.'):
                    new_version = latest
            self.update_plugin_item(None, plugin,
                                    enabled=self.is_plugin_enabled(plugin),
                                    can_be_updated=bool(new_version),
                                    new_version=new_version
                                   )
            installed.append(plugin.module_name)

        for plugin in sorted(self.manager.available_plugins, key=attrgetter('name')):
            if plugin.module_name not in installed:
                self.update_plugin_item(None, plugin,
                                        enabled=self.is_plugin_enabled(plugin),
                                        can_be_downloaded=True
                                       )

        self._user_interaction(True)

    def _remove_all(self):
        for item, _unused_ in self.items():
            idx = self.ui.plugins.indexOfTopLevelItem(item)
            self.ui.plugins.takeTopLevelItem(idx)

    def restore_defaults(self):
        self._user_interaction(False)
        self.set_current_item(self.ui.plugins.topLevelItem(0), scroll=True)
        self._remove_all()
        super().restore_defaults()

    def load(self):
        self._populate()
        self.restore_state()

    def _preserve_plugins_states(self):
        self._preserve = {}
        self._preserve_selected = None
        for item, plugin in self.items():
            self._preserve[plugin.module_name] = plugin.states
        selected = self.selected_plugin()
        if selected:
            self._preserve_selected = selected.module_name
        else:
            self._preserve_selected = None

    def _restore_plugins_states(self):
        found_selected = False
        current = None
        for item, plugin in self.items():
            if plugin.module_name in self._preserve:
                plugin.states = self._preserve[plugin.module_name]
                if self._preserve_selected == plugin.module_name:
                    current = item

        if not current:
            current = self.ui.plugins.topLevelItem(0)
        if current:
            self.set_current_item(current, scroll=True)

    def _reload(self):
        self._populate()
        self._restore_plugins_states()

    def _user_interaction(self, enabled):
        self.ui.plugins.blockSignals(not enabled)
        self.ui.plugins_container.setEnabled(enabled)

    def reload_list_of_plugins(self):
        self.ui.details.setText("")
        self._user_interaction(False)
        self._preserve_plugins_states()
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
        item, _unused_ = self.find_by_name(plugin.module_name)
        self.update_plugin_item(item, plugin,
                                make_current=True,
                                enabled=True,
                                can_be_downloaded=False,
                                can_be_updated=False,
                               )

    def plugin_updated(self, plugin_name):
        item, plugin = self.find_by_name(plugin_name)
        if item:
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setText(
                _("The plugin '%s' will be upgraded to version %s on next run of Picard.")
                % (plugin.name, item.new_version))
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.setDefaultButton(QtWidgets.QMessageBox.Ok)
            msgbox.exec_()

            self.update_plugin_item(item, plugin, make_current=True,
                                    can_be_downloaded=False,
                                    can_be_updated=False,
                                    marked_for_update=True)

    def uninstall_plugin(self, item):
        plugin = self.item_plugin(item)
        buttonReply = QtWidgets.QMessageBox.question(
            self,
            _("Uninstall plugin?"),
            _("Do you really want to uninstall the plugin '%s' ?") % plugin.name,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if buttonReply == QtWidgets.QMessageBox.Yes:
            self.manager.remove_plugin(plugin.module_name)
            self.update_plugin_item(item, plugin, make_current=True,
                                    enabled=False, is_uninstalled=True)

    def update_plugin_item(self, item, plugin,
                           make_current=False,
                           enabled=None,
                           can_be_downloaded=False,
                           can_be_updated=False,
                           marked_for_update=False,
                           is_uninstalled=False,
                           new_version=''
                          ):
        if item is None:
            item = PluginTreeWidgetItem(self.ui.plugins)
        item.setData(COLUMN_NAME, QtCore.Qt.UserRole, plugin)
        item.setText(COLUMN_NAME, plugin.name)
        item.setSortData(COLUMN_NAME, plugin.name.lower())
        item.can_be_downloaded = can_be_downloaded
        item.can_be_updated = can_be_updated
        item.marked_for_update = marked_for_update
        item.is_uninstalled = is_uninstalled
        item.new_version = new_version
        if enabled is not None:
            item.enable(enabled)
            if enabled:
                item.checkable(True)

        if item.marked_for_update:
            version = item.new_version
        else:
            version = plugin.version
        item.setText(COLUMN_VERSION, version)

        def download_processor(action):
            self.download_plugin(item, action)

        def uninstall_processor():
            self.uninstall_plugin(item)

        bt_action = PLUGIN_ACTION_NONE
        if item.is_uninstalled:
            item.enable(False)
            item.checkable(False)

        if item.can_be_downloaded:
            bt_action = PLUGIN_ACTION_INSTALL
            item.checkable(False)
        else:
            bt_action = PLUGIN_ACTION_UNINSTALL

        if bt_action != PLUGIN_ACTION_NONE:
            labels = {
                PLUGIN_ACTION_INSTALL: N_("Install"),
                PLUGIN_ACTION_UNINSTALL: N_("Uninstall"),
            }
            label = _(labels[bt_action])
            if item.is_uninstalled:
                label = _("Uninstalled")
            button = QtWidgets.QPushButton(label)
            button.setMaximumHeight(button.fontMetrics().boundingRect(label).height() + 7)
            self.ui.plugins.setItemWidget(item, COLUMN_ACTION, button)
            if item.is_uninstalled:
                button.setEnabled(False)

            if bt_action == PLUGIN_ACTION_INSTALL:
                button.released.connect(partial(download_processor, bt_action))
            else:
                button.released.connect(uninstall_processor)

        if item.can_be_updated or item.marked_for_update:
            label = _("Upgrade from %s to %s" % (plugin.version, item.new_version))
            if item.marked_for_update:
                label = _("Updated")
            button = QtWidgets.QPushButton(label)
            button.setMaximumHeight(button.fontMetrics().boundingRect(label).height() + 7)
            self.ui.plugins.setItemWidget(item, COLUMN_VERSION, button)
            if item.is_uninstalled or item.marked_for_update:
                button.setEnabled(False)

            button.released.connect(partial(download_processor, PLUGIN_ACTION_UPDATE))

        self.ui.plugins.header().resizeSections(QtWidgets.QHeaderView.ResizeToContents)

        if make_current:
            self.set_current_item(item)

        return item

    def save(self):
        enabled_plugins = []
        for item, plugin in self.items():
            if item.is_enabled():
                enabled_plugins.append(plugin.module_name)
        config.setting["enabled_plugins"] = enabled_plugins
        self.save_state()

    def refresh_details(self, item):
        plugin = self.item_plugin(item)
        text = []
        if item.new_version:
            if item.marked_for_update:
                text.append("<b>" + _("Restart Picard to upgrade to new version") + ": " + item.new_version + "</b>")
            else:
                text.append("<b>" + _("New version available") + ": " + item.new_version + "</b>")
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

    def change_details(self):
        item = self.selected_item()
        if item:
            self.refresh_details(item)

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

    def download_plugin(self, item, action):
        plugin = self.item_plugin(item)

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
