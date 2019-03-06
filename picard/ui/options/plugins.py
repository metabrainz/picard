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
    PLUGINS_API,
    USER_PLUGIN_DIR,
)
from picard.const.sys import IS_WIN
from picard.util import reconnect

from picard.ui import HashableTreeWidgetItem
from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_plugins import Ui_PluginsOptionsPage

COLUMN_NAME, COLUMN_VERSION, COLUMN_ACTIONS = range(3)


class PluginActionButton(QtWidgets.QToolButton):

    def __init__(self, icon=None, tooltip=None, retain_space=False,
                 switch_method=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if tooltip is not None:
            self.setToolTip(tooltip)

        if icon is not None:
            self.set_icon(self, icon)

        if retain_space is True:
            sp_retain = self.sizePolicy()
            sp_retain.setRetainSizeWhenHidden(True)
            self.setSizePolicy(sp_retain)
        if switch_method is not None:
            self.switch_method = switch_method

    def mode(self, mode):
        if self.switch_method is not None:
            self.switch_method(self, mode)


class PluginTreeWidgetItem(HashableTreeWidgetItem):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sortData = {}
        self.upgrade_to_version = None
        self.new_version = None
        self.is_enabled = False
        self.is_installed = False
        self.installed_font = None
        self.enabled_font = None
        self.available_font = None

        self.buttons = {}
        self.buttons_widget = QtWidgets.QWidget()

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 5, 0)
        layout.addStretch(1)
        self.buttons_widget.setLayout(layout)

        def add_button(name, method):
            button = PluginActionButton(switch_method=method)
            layout.addWidget(button)
            self.buttons[name] = button
            button.mode('hide')

        add_button('update', self.show_update)
        add_button('uninstall', self.show_uninstall)
        add_button('enable', self.show_enable)
        add_button('install', self.show_install)

        self.treeWidget().setItemWidget(self, COLUMN_ACTIONS,
                                        self.buttons_widget)

    @staticmethod
    def set_icon(button, stdicon):
        button.setIcon(button.style().standardIcon(getattr(QtWidgets.QStyle, stdicon)))

    def show_install(self, button, mode):
        if mode == 'hide':
            button.hide()
        else:
            button.show()
            button.setToolTip(_("Download and install plugin"))
            self.set_icon(button, 'SP_ArrowDown')

    def show_update(self, button, mode):
        if mode == 'hide':
            button.hide()
        else:
            button.show()
            button.setToolTip(_("Download and upgrade plugin to version %s") % self.new_version)
            self.set_icon(button, 'SP_BrowserReload')

    def show_enable(self, button, mode):
        if mode == 'enabled':
            button.show()
            button.setToolTip(_("Enabled"))
            self.set_icon(button, 'SP_DialogApplyButton')
        elif mode == 'disabled':
            button.show()
            button.setToolTip(_("Disabled"))
            self.set_icon(button, 'SP_DialogCancelButton')
        else:
            button.hide()

    def show_uninstall(self, button, mode):
        if mode == 'hide':
            button.hide()
        else:
            button.show()
            button.setToolTip(_("Uninstall plugin"))
            self.set_icon(button, 'SP_TrashIcon')

    def save_state(self):
        return {
            'is_enabled': self.is_enabled,
            'upgrade_to_version': self.upgrade_to_version,
            'new_version': self.new_version,
            'is_installed': self.is_installed,
        }

    def restore_state(self, states):
        self.upgrade_to_version = states['upgrade_to_version']
        self.new_version = states['new_version']
        self.is_enabled = states['is_enabled']
        self.is_installed = states['is_installed']

    def __lt__(self, other):
        if not isinstance(other, PluginTreeWidgetItem):
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

    @property
    def plugin(self):
        return self.data(COLUMN_NAME, QtCore.Qt.UserRole)

    def enable(self, boolean, greyout=None):
        if boolean is not None:
            self.is_enabled = boolean
        if self.is_enabled:
            self.buttons['enable'].mode('enabled')
        else:
            self.buttons['enable'].mode('disabled')
        if greyout is not None:
            self.buttons['enable'].setEnabled(not greyout)


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
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_PluginsOptionsPage()
        self.ui.setupUi(self)
        plugins = self.ui.plugins

        # fix for PICARD-1226, QT bug (https://bugreports.qt.io/browse/QTBUG-22572) workaround
        plugins.setStyleSheet('')

        plugins.itemSelectionChanged.connect(self.change_details)
        plugins.mimeTypes = self.mimeTypes
        plugins.dropEvent = self.dropEvent
        plugins.dragEnterEvent = self.dragEnterEvent

        self.ui.install_plugin.clicked.connect(self.open_plugins)
        self.ui.folder_open.clicked.connect(self.open_plugin_dir)
        self.ui.reload_list_of_plugins.clicked.connect(self.reload_list_of_plugins)

        self.manager = self.tagger.pluginmanager
        self.manager.plugin_installed.connect(self.plugin_installed)
        self.manager.plugin_updated.connect(self.plugin_updated)
        self.manager.plugin_removed.connect(self.plugin_removed)
        self.manager.plugin_errored.connect(self.plugin_loading_error)

        self._preserve = {}
        self._preserve_selected = None

    def items(self):
        iterator = QTreeWidgetItemIterator(self.ui.plugins, QTreeWidgetItemIterator.All)
        while iterator.value():
            item = iterator.value()
            iterator += 1
            yield item

    def find_item_by_plugin_name(self, plugin_name):
        for item in self.items():
            if plugin_name == item.plugin.module_name:
                return item
        return None

    def selected_item(self):
        try:
            return self.ui.plugins.selectedItems()[COLUMN_NAME]
        except IndexError:
            return None

    def save_state(self):
        header = self.ui.plugins.header()
        config.persist["plugins_list_state"] = header.saveState()
        config.persist["plugins_list_sort_section"] = header.sortIndicatorSection()
        config.persist["plugins_list_sort_order"] = header.sortIndicatorOrder()

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

    @staticmethod
    def is_plugin_enabled(plugin):
        return bool(plugin.module_name in config.setting["enabled_plugins"])

    def available_plugins_name_version(self):
        return dict([(p.module_name, p.version) for p in self.manager.available_plugins])

    def installable_plugins(self):
        if self.manager.available_plugins is not None:
            installed_plugins = [plugin.module_name for plugin in
                                 self.installed_plugins()]
            for plugin in sorted(self.manager.available_plugins,
                                 key=attrgetter('name')):
                if plugin.module_name not in installed_plugins:
                    yield plugin

    def installed_plugins(self):
        return sorted(self.manager.plugins, key=attrgetter('name'))

    def enabled_plugins(self):
        return [item.plugin.module_name for item in self.items() if item.is_enabled]

    def _populate(self):
        self._user_interaction(False)
        if self.manager.available_plugins is None:
            available_plugins = {}
            self.manager.query_available_plugins(self._reload)
        else:
            available_plugins = self.available_plugins_name_version()

        self.ui.details.setText("")

        self.ui.plugins.setSortingEnabled(False)
        for plugin in self.installed_plugins():
            new_version = None
            if plugin.module_name in available_plugins:
                latest = available_plugins[plugin.module_name]
                if latest.split('.') > plugin.version.split('.'):
                    new_version = latest
            self.update_plugin_item(None, plugin,
                                    enabled=self.is_plugin_enabled(plugin),
                                    new_version=new_version,
                                    is_installed=True
                                    )

        for plugin in self.installable_plugins():
            self.update_plugin_item(None, plugin, enabled=False,
                                    is_installed=False)

        self.ui.plugins.setSortingEnabled(True)
        self._user_interaction(True)
        header = self.ui.plugins.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(COLUMN_NAME, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(COLUMN_VERSION, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COLUMN_ACTIONS, QtWidgets.QHeaderView.ResizeToContents)

    def _remove_all(self):
        for item in self.items():
            idx = self.ui.plugins.indexOfTopLevelItem(item)
            self.ui.plugins.takeTopLevelItem(idx)

    def restore_defaults(self):
        self._user_interaction(False)
        self._remove_all()
        super().restore_defaults()
        self.set_current_item(self.ui.plugins.topLevelItem(0), scroll=True)

    def load(self):
        self._populate()
        self.restore_state()

    def _preserve_plugins_states(self):
        self._preserve = {item.plugin.module_name: item.save_state() for item in self.items()}
        item = self.selected_item()
        if item:
            self._preserve_selected = item.plugin.module_name
        else:
            self._preserve_selected = None

    def _restore_plugins_states(self):
        for item in self.items():
            plugin = item.plugin
            if plugin.module_name in self._preserve:
                item.restore_state(self._preserve[plugin.module_name])
                if self._preserve_selected == plugin.module_name:
                    self.set_current_item(item, scroll=True)

    def _reload(self):
        self._remove_all()
        self._populate()
        self._restore_plugins_states()

    def _user_interaction(self, enabled):
        self.ui.plugins.blockSignals(not enabled)
        self.ui.plugins_container.setEnabled(enabled)

    def reload_list_of_plugins(self):
        self.ui.details.setText(_("Reloading list of available plugins..."))
        self._user_interaction(False)
        self._preserve_plugins_states()
        self.manager.query_available_plugins(callback=self._reload)

    def plugin_loading_error(self, plugin_name, error):
        QtWidgets.QMessageBox.critical(
            self,
            _("Plugin '%s'") % plugin_name,
            _("An error occured while loading the plugin '%s':\n\n%s") % (plugin_name, error)
        )

    def plugin_installed(self, plugin):
        log.debug("Plugin %r installed", plugin.name)
        if not plugin.compatible:
            QtWidgets.QMessageBox.warning(
                self,
                _("Plugin '%s'") % plugin.name,
                _("The plugin '%s' is not compatible with this version of Picard.") % plugin.name
            )
            return
        item = self.find_item_by_plugin_name(plugin.module_name)
        if item:
            self.update_plugin_item(item, plugin, make_current=True,
                                    enabled=True, is_installed=True)
        else:
            self._reload()
            item = self.find_item_by_plugin_name(plugin.module_name)
            if item:
                self.set_current_item(item, scroll=True)

    def plugin_updated(self, plugin_name):
        log.debug("Plugin %r updated", plugin_name)
        item = self.find_item_by_plugin_name(plugin_name)
        if item:
            plugin = item.plugin
            QtWidgets.QMessageBox.information(
                self,
                _("Plugin '%s'") % plugin_name,
                _("The plugin '%s' will be upgraded to version %s on next run of Picard.")
                % (plugin.name, item.new_version)
            )

            item.upgrade_to_version = item.new_version
            self.update_plugin_item(item, plugin, make_current=True)

    def plugin_removed(self, plugin_name):
        log.debug("Plugin %r removed", plugin_name)
        item = self.find_item_by_plugin_name(plugin_name)
        if item:
            if self.manager.is_available(plugin_name):
                self.update_plugin_item(item, None, make_current=True,
                                        is_installed=False)
            else:  # Remove local plugin
                self.ui.plugins.invisibleRootItem().removeChild(item)

    def uninstall_plugin(self, item):
        plugin = item.plugin
        buttonReply = QtWidgets.QMessageBox.question(
            self,
            _("Uninstall plugin '%s'?") % plugin.name,
            _("Do you really want to uninstall the plugin '%s' ?") % plugin.name,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if buttonReply == QtWidgets.QMessageBox.Yes:
            self.manager.remove_plugin(plugin.module_name, with_update=True)

    def update_plugin_item(self, item, plugin,
                           make_current=False,
                           enabled=None,
                           new_version=None,
                           is_installed=None
                           ):
        if item is None:
            item = PluginTreeWidgetItem(self.ui.plugins)
        if plugin is not None:
            item.setData(COLUMN_NAME, QtCore.Qt.UserRole, plugin)
        else:
            plugin = item.plugin
        if new_version is not None:
            item.new_version = new_version
        if is_installed is not None:
            item.is_installed = is_installed
        if enabled is None:
            enabled = item.is_enabled

        def update_text():
            if item.new_version is not None:
                version = "%s → %s" % (plugin.version, item.new_version)
            else:
                version = plugin.version

            if item.installed_font is None:
                item.installed_font = item.font(COLUMN_NAME)
            if item.enabled_font is None:
                item.enabled_font = QtGui.QFont(item.installed_font)
                item.enabled_font.setBold(True)
            if item.available_font is None:
                item.available_font = QtGui.QFont(item.installed_font)

            if item.is_enabled:
                item.setFont(COLUMN_NAME, item.enabled_font)
            else:
                if item.is_installed:
                    item.setFont(COLUMN_NAME, item.installed_font)
                else:
                    item.setFont(COLUMN_NAME, item.available_font)

            item.setText(COLUMN_NAME, plugin.name)
            item.setText(COLUMN_VERSION, version)

        def toggle_enable():
            item.enable(not item.is_enabled, greyout=not item.is_installed)
            log.debug("Plugin %r enabled: %r", item.plugin.name, item.is_enabled)
            update_text()

        reconnect(item.buttons['enable'].clicked, toggle_enable)

        install_enabled = not item.is_installed or bool(item.new_version)
        if item.upgrade_to_version:
            if item.upgrade_to_version != item.new_version:
                # case when a new version is known after a plugin was marked for update
                install_enabled = True
            else:
                install_enabled = False

        if install_enabled:
            if item.new_version is not None:
                def download_and_update():
                    self.download_plugin(item, update=True)

                reconnect(item.buttons['update'].clicked, download_and_update)
                item.buttons['install'].mode('hide')
                item.buttons['update'].mode('show')
            else:
                def download_and_install():
                    self.download_plugin(item)

                reconnect(item.buttons['install'].clicked, download_and_install)
                item.buttons['install'].mode('show')
                item.buttons['update'].mode('hide')

        if item.is_installed:
            item.buttons['install'].mode('hide')
            item.buttons['uninstall'].mode('show')
            item.enable(enabled, greyout=False)

            def uninstall_processor():
                self.uninstall_plugin(item)

            reconnect(item.buttons['uninstall'].clicked, uninstall_processor)
        else:
            item.buttons['uninstall'].mode('hide')
            item.enable(False)
            item.buttons['enable'].mode('hide')

        update_text()

        if make_current:
            self.set_current_item(item)

        actions_sort_score = 2
        if item.is_installed:
            if item.is_enabled:
                actions_sort_score = 0
            else:
                actions_sort_score = 1

        item.setSortData(COLUMN_ACTIONS, actions_sort_score)
        item.setSortData(COLUMN_NAME, plugin.name.lower())

        def v2int(elem):
            try:
                return int(elem)
            except ValueError:
                return 0
        item.setSortData(COLUMN_VERSION, tuple(v2int(e) for e in plugin.version.split('.')))

        return item

    def save(self):
        config.setting["enabled_plugins"] = self.enabled_plugins()
        self.save_state()

    def refresh_details(self, item):
        plugin = item.plugin
        text = []
        if item.new_version is not None:
            if item.upgrade_to_version:
                label = _("Restart Picard to upgrade to new version")
            else:
                label = _("New version available")
            text.append("<b>" + label + ": " + item.new_version + "</b>")
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
                self.manager.install_plugin(path)

    def download_plugin(self, item, update=False):
        plugin = item.plugin

        self.tagger.webservice.get(
            PLUGINS_API['host'],
            PLUGINS_API['port'],
            PLUGINS_API['endpoint']['download'],
            partial(self.download_handler, update, plugin=plugin),
            parse_response_type=None,
            priority=True,
            important=True,
            queryargs={"id": plugin.module_name}
        )

    def download_handler(self, update, response, reply, error, plugin):
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
            update=update,
            plugin_name=plugin.module_name,
            plugin_data=response,
        )

    @staticmethod
    def open_plugin_dir():
        if IS_WIN:
            url = 'file:///' + USER_PLUGIN_DIR
        else:
            url = 'file://' + USER_PLUGIN_DIR
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url, QtCore.QUrl.TolerantMode))

    def mimeTypes(self):
        return ["text/uri-list"]

    def dragEnterEvent(self, event):
        event.setDropAction(QtCore.Qt.CopyAction)
        event.accept()

    def dropEvent(self, event):
        for path in [os.path.normpath(u.toLocalFile()) for u in event.mimeData().urls()]:
            self.manager.install_plugin(path)


register_options_page(PluginsOptionsPage)
