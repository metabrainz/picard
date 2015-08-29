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

    def load(self):
        self.ui.details.setText("<b>"+ _("No plugins installed.") + "</b>")
        plugins = sorted(self.tagger.pluginmanager.plugins, cmp=cmp_plugins)
        enabled_plugins = config.setting["enabled_plugins"]
        for plugin in plugins:
            enabled = plugin.module_name in enabled_plugins
            if plugin.module_name in self.tagger.pluginmanager.available_plugins:
                latest = self.tagger.pluginmanager.available_plugins[plugin.module_name]["version"]
                if latest > plugin.version: # FIXME : better way to compare
                    plugin.new_version = latest
            item = self.add_plugin_item(plugin, enabled=enabled, bold=bool(plugin.new_version))
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

    def add_plugin_item(self, plugin, enabled=False, item=None, bold=False):
        if item is None:
            item = QtGui.QTreeWidgetItem(self.ui.plugins)
        item.setText(0, plugin.name)
        if enabled:
            item.setCheckState(0, QtCore.Qt.Checked)
        else:
            item.setCheckState(0, QtCore.Qt.Unchecked)
        if bold:
            font = QtGui.QFont()
            font.setBold(True)
            item.setFont(0, font)
        item.setText(1, plugin.version)
        item.setText(2, plugin.author)
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
        text.append("<b>" + _("Files") + "</b>: " + plugin.file[len(plugin.dir)+1:])
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

        selected = self.ui.plugins.selectedItems()[0]
        plugin = self.items[selected]

        plugin_data = self.tagger.pluginmanager.available_plugins[plugin.module_name]
        files_modified = False

        if (len(plugin_data['files']) == 1):
            with open(plugin.file, "rb") as md5file:
                md5Hash = md5(md5file.read()).hexdigest()

            if md5Hash != plugin_data['files'].values()[0]:
                files_modified = True
        else:
            for fname in plugin_data['files'].keys():
                filepath = os.path.join(plugin.file, fname)
                with open(filepath, "rb") as md5file:
                    md5Hash = md5(md5file.read()).hexdigest()

                if md5Hash != plugin_data['files'][fname]:
                    files_modified = True

        if files_modified:
            msgbox = QtGui.QMessageBox(self)
            msgbox.setText(_(u"Updating ‘%s’ plugin will overwrite any changes that you might have made.") % plugin.name)
            msgbox.setInformativeText(_(u"Are you sure you want to continue?"))
            msgbox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            msgbox.setDefaultButton(QtGui.QMessageBox.No)
            if msgbox.exec_() == QtGui.QMessageBox.No:
                return

        self.tagger.xmlws.get(
            PLUGINS_API['host'],
            PLUGINS_API['port'],
            PLUGINS_API['endpoint']['download'] + "?id=" + plugin.module_name,
            partial(self.download_handler, selected=plugin_data, module_name=plugin.module_name),
            xml=False,
            priority=True,
            important=True
        )

    def download_handler(self, response, reply, error, selected, module_name):
        if error:
            log.error("Error occurred while trying to download the plugin")
            return

        if not os.path.exists(USER_DOWNLOADS_DIR):
            os.makedirs(USER_DOWNLOADS_DIR)

        downloadpath = os.path.join(USER_DOWNLOADS_DIR, module_name)
        zippath = downloadpath+".zip"

        try:
            with open(zippath, "wb") as downloadzip:
                downloadzip.write(response)
        except:
            msgbox = QtGui.QMessageBox(self)
            msgbox.setText(_(u"The plugin ‘%s’ could not be updated.") % selected["name"])
            msgbox.setInformativeText(_("Please try again later."))
            msgbox.setStandardButtons(QtGui.QMessageBox.Ok)
            msgbox.setDefaultButton(QtGui.QMessageBox.Ok)
            msgbox.exec_()
        else:
            # Extract and remove zip
            downloadzip = zipfile.ZipFile(zippath)
            downloadzip.extractall(downloadpath)
            downloadzip.close()
            os.remove(zippath)

            self.install_downloaded_plugin(module_name, selected)

    def install_downloaded_plugin(self, module_name, selected):
        if len(selected["files"]) == 1:
            source = os.path.join(USER_DOWNLOADS_DIR, module_name, selected["files"].keys()[0])
        else:
            source = os.path.join(USER_DOWNLOADS_DIR, module_name)

        self.install_plugin(source)

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
