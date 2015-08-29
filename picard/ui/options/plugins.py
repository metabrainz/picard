# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2014 Shadab Zafar
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
import zipfile
from hashlib import md5
from functools import partial
from PyQt4 import QtCore, QtGui
from picard import config, log
from picard.const import (USER_DIR, USER_PLUGIN_DIR,
                          USER_DOWNLOADS_DIR, PICARD_URLS, PLUGINS_API)
from picard.util import encode_filename, webbrowser2
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_plugins import Ui_PluginsOptionsPage


def cmp_plugins(a, b):
    return cmp(a.name, b.name)


class PluginsOptionsPage(OptionsPage):

    NAME = "plugins"
    TITLE = N_("Plugins")
    PARENT = None
    SORT_ORDER = 70
    ACTIVE = True

    options = [
        config.ListOption("setting", "enabled_plugins", []),
    ]

    def __init__(self, parent=None):
        super(PluginsOptionsPage, self).__init__(parent)
        self.ui = Ui_PluginsOptionsPage()
        self.ui.setupUi(self)
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
        self.ui.update_plugin.clicked.connect(self.update_plugin)
        self.ui.update_plugin.setEnabled(False)
        self.tagger.pluginmanager.plugin_installed.connect(self.plugin_installed)
        self.ui.plugins.header().setStretchLastSection(False)

    def load(self):
        self.ui.details.setText("<b>"+ _("No plugins installed.") + "</b>")
        plugins = sorted(self.tagger.pluginmanager.plugins, cmp=cmp_plugins)
        enabled_plugins = config.setting["enabled_plugins"]
        installed = []
        for plugin in plugins:
            enabled = plugin.module_name in enabled_plugins
            if plugin.module_name in self.tagger.pluginmanager.available_plugins:
                latest = self.tagger.pluginmanager.available_plugins[plugin.module_name]["version"]
                if latest > plugin.version: # FIXME : better way to compare
                    plugin.new_version = latest
            plugin.files_list = plugin.file[len(plugin.dir)+1:] # FIXME
            item = self.add_plugin_item(plugin, enabled=enabled, update=bool(plugin.new_version))
            installed.append(plugin.module_name)

        # FIXME: a bit hacky here
        class objectview(object):
            def __init__(self, d):
                self.__dict__ = d

        for module_name, data in self.tagger.pluginmanager.available_plugins.items():
            data['module_name'] = module_name
            data['new_version'] = False
            if module_name not in installed:
                plugin = objectview(data)
                plugin.files_list = ", ".join(plugin.files.keys())
                item = self.add_plugin_item(plugin, download=True)

        self.ui.plugins.setCurrentItem(self.ui.plugins.topLevelItem(0))

    def plugin_installed(self, plugin):
        if not plugin.compatible:
            msgbox = QtGui.QMessageBox(self)
            msgbox.setText(_(u"The plugin ‘%s’ is not compatible with this version of Picard.") % plugin.name)
            msgbox.setStandardButtons(QtGui.QMessageBox.Ok)
            msgbox.setDefaultButton(QtGui.QMessageBox.Ok)
            msgbox.exec_()
            return
        for i, p in self.items.items():
            if plugin.module_name == p.module_name:
                enabled = i.checkState(0) == QtCore.Qt.Checked
                self.add_plugin_item(plugin, enabled=enabled, item=i)
                break
        else:
            self.add_plugin_item(plugin)

    def add_plugin_item(self, plugin, enabled=False, item=None, update=False,
                        download=False):
        if item is None:
            item = QtGui.QTreeWidgetItem(self.ui.plugins)
        item.setText(0, plugin.name)
        if enabled:
            item.setCheckState(0, QtCore.Qt.Checked)
        else:
            item.setCheckState(0, QtCore.Qt.Unchecked)
        item.setText(1, plugin.version)

        if update:
            button = QtGui.QPushButton(_("Update"))
            self.ui.plugins.setItemWidget(item, 2, button)
            def update_button_process():
                 self.ui.plugins.setCurrentItem(item)
                 self.update_plugin()
            button.released.connect(update_button_process)
        elif download:
            button = QtGui.QPushButton(_("Download"))
            self.ui.plugins.setItemWidget(item, 2, button)
            def download_button_process():
                 self.ui.plugins.setCurrentItem(item)
                 self.download_plugin()
            button.released.connect(download_button_process)
        else:
            # Note: setText() don't work after it was set to a button
            self.ui.plugins.setItemWidget(item, 2, QtGui.QLabel(_("Installed")))

        self.ui.plugins.header().resizeSections(QtGui.QHeaderView.ResizeToContents)
        self.items[item] = plugin
        return item

    def save(self):
        enabled_plugins = []
        for item, plugin in self.items.iteritems():
            if item.checkState(0) == QtCore.Qt.Checked:
                enabled_plugins.append(plugin.module_name)
        config.setting["enabled_plugins"] = enabled_plugins

    def change_details(self):
        selected = self.ui.plugins.selectedItems()[0]
        plugin = self.items[selected]

        text = []
        if plugin.new_version:
            text.append("<b>" + _("New version available") + ": " + plugin.new_version + "</b><br/>")
            self.ui.update_plugin.setEnabled(True)
        else:
            self.ui.update_plugin.setEnabled(False)

        if plugin.description:
            text.append(plugin.description + "<br/>")
            text.append('______________________________')
        if plugin.name:
            text.append("<b>" + _("Name") + "</b>: " + plugin.name)
        if plugin.author:
            text.append("<b>" + _("Author") + "</b>: " + plugin.author)
        if plugin.license:
            text.append("<b>" + _("License") + "</b>: " + plugin.license)
        text.append("<b>" + _("Files") + "</b>: " + plugin.files_list)
        self.ui.details.setText("<p>%s</p>" % "<br/>\n".join(text))

    def open_plugins(self):
        files = QtGui.QFileDialog.getOpenFileNames(self, "",
                                                   QtCore.QDir.homePath(),
                                                   "Picard plugin (*.py *.pyc *.zip)")
        if files:
            files = map(unicode, files)
            for path in files:
                self.install_plugin(path)

    def overwrite_confirm(self, name):
        msgbox = QtGui.QMessageBox(self)
        msgbox.setText(_("A plugin named '%s' is already installed.") % name)
        msgbox.setInformativeText(_("Do you want to overwrite the existing plugin?"))
        msgbox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        msgbox.setDefaultButton(QtGui.QMessageBox.No)
        return (msgbox.exec_() == QtGui.QMessageBox.Yes)

    def install_plugin(self, path):
        self.tagger.pluginmanager.install_plugin(path,
                                                 overwrite_confirm=self.overwrite_confirm)

    def update_plugin(self):
        if not self.tagger.pluginmanager.available_plugins:
            return
        self.download_plugin()

    def download_plugin(self):
        selected = self.ui.plugins.selectedItems()[0]
        plugin = self.items[selected]

        plugin_data = self.tagger.pluginmanager.available_plugins[plugin.module_name]

        self.tagger.xmlws.get(
            PLUGINS_API['host'],
            PLUGINS_API['port'],
            PLUGINS_API['endpoint']['download'] + "?id=" + plugin.module_name,
            partial(self.download_handler, plugin_data=plugin_data, module_name=plugin.module_name),
            xml=False,
            priority=True,
            important=True
        )

    def download_handler(self, response, reply, error, plugin_data, module_name):
        if error:
            msgbox = QtGui.QMessageBox(self)
            msgbox.setText(_(u"The plugin '%s' could not be downloaded.") % plugin_data["name"])
            msgbox.setInformativeText(_("Please try again later."))
            msgbox.setStandardButtons(QtGui.QMessageBox.Ok)
            msgbox.setDefaultButton(QtGui.QMessageBox.Ok)
            msgbox.exec_()
            log.error("Error occurred while trying to download the plugin: '%s'" % plugin_data["name"])
            return

        if not os.path.exists(USER_DOWNLOADS_DIR):
            os.makedirs(USER_DOWNLOADS_DIR)

        zippath = os.path.join(USER_DOWNLOADS_DIR, module_name + ".zip")
        with open(zippath, "wb") as downloadzip:
            downloadzip.write(response)
        self.install_plugin(zippath)

    def open_plugin_dir(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.loader % USER_PLUGIN_DIR, QtCore.QUrl.TolerantMode))

    def open_plugin_site(self):
        webbrowser2.goto('plugins_repo')

    def mimeTypes(self):
        return ["text/uri-list"]

    def dragEnterEvent(self, event):
        event.setDropAction(QtCore.Qt.CopyAction)
        event.accept()

    def dropEvent(self, event):
        for path in [os.path.normpath(unicode(u.toLocalFile())) for u in event.mimeData().urls()]:
            self.install_plugin(path)


register_options_page(PluginsOptionsPage)
