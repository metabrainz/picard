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

import os
import sys
import zipfile
from functools import partial
from PyQt4 import QtCore, QtGui
from picard import config, log
from picard.const import (USER_DIR, USER_PLUGIN_DIR,
                          USER_DOWNLOADS_DIR, PICARD_URLS, PLUGINS_API)
from picard.util import encode_filename, webbrowser2
from picard.webservice import XmlWebService
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_plugins_download import Ui_PluginsDownloadPage


class PluginsDownloadPage(OptionsPage):

    NAME = "plugins_download"
    TITLE = N_("Download")
    PARENT = "plugins"
    SORT_ORDER = 70
    ACTIVE = True

    options = [
        config.ListOption("setting", "enabled_plugins", []),
    ]

    def __init__(self, parent=None):
        super(PluginsDownloadPage, self).__init__(parent)
        self.ui = Ui_PluginsDownloadPage()
        self.ui.setupUi(self)
        self.items = {}
        self.ui.plugins.itemSelectionChanged.connect(self.change_details)
        self.ui.plugins.setSortingEnabled(True)
        self.ui.plugins.mimeTypes = self.mimeTypes
        if sys.platform == "win32":
            self.loader = "file:///%s"
        else:
            self.loader = "file://%s"
        self.ui.install_plugin.clicked.connect(self.download_plugin)
        self.ui.install_plugin.setEnabled(False)
        self.ui.open_repo.clicked.connect(self.open_repo)
        self.tagger.pluginmanager.plugin_installed.connect(self.plugin_installed)
        self.installed = [p.module_name for p in self.tagger.pluginmanager.plugins]
        self.plugins_available = self.tagger.plugins_available

    def load(self):
        self.ui.plugins.clear()
        self.ui.details.setText("<b>"+ _("No new plugins available.") + "</b>")
        for module_name, data in self.plugins_available.items():
            data['module_name'] = module_name
            if module_name not in self.installed:
                item = self.add_plugin_item(data)
        self.ui.plugins.setCurrentItem(self.ui.plugins.topLevelItem(0))

    def add_plugin_item(self, plugin, enabled=False, item=None):
        if item is None:
            item = QtGui.QTreeWidgetItem(self.ui.plugins)
        item.setText(0, plugin['name'])
        item.setText(1, plugin['version'])
        item.setText(2, str(plugin['downloads']))
        item.setText(3, plugin['author'])
        self.ui.plugins.header().resizeSections(QtGui.QHeaderView.ResizeToContents)
        self.items[item] = plugin
        return item

    def change_details(self):
        if not self.ui.plugins.selectedItems():
            return

        plugin = self.items[self.ui.plugins.selectedItems()[0]]
        installed = bool(plugin['module_name'] in self.installed)

        text = []
        if installed:
            self.ui.install_plugin.setEnabled(False)
            text.append("<b>"+ _("Installed version") + ": " + plugin["version"] + "</b><br/>")
        else:
            self.ui.install_plugin.setEnabled(True)

        name = plugin['name']
        desc = plugin['description']
        if desc:
            text.append(desc + "<br/>")
            text.append('______________________________')
        if name:
            text.append("<b>" + _("Name") + "</b>: " + name)
        author = plugin['author']
        if author:
            text.append("<b>" + _("Author") + "</b>: " + author)
        text.append("<b>" + _("File") + "</b>: " + ", ".join(plugin['files'].keys()))
        self.ui.details.setText("<p>%s</p>" % "<br/>\n".join(text))

    def download_plugin(self, selected=None):
        if not selected:
            selected = self.items[self.ui.plugins.selectedItems()[0]]
        module_name = selected['module_name']

        self.tagger.xmlws.get(
            PLUGINS_API['host'],
            PLUGINS_API['port'],
            PLUGINS_API['endpoint']['download'] + "?id=" + module_name,
            partial(self.download_handler, selected=selected, module_name=module_name),
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
            msgbox.setText(u"The plugin ‘%s’ could not be downloaded." % selected["name"])
            msgbox.setInformativeText("Please try again later.")
            msgbox.setStandardButtons(QtGui.QMessageBox.Ok)
            msgbox.setDefaultButton(QtGui.QMessageBox.Ok)
            msgbox.exec_()
        else:
            # Extract and remove zip
            downloadzip = zipfile.ZipFile(zippath)
            downloadzip.extractall(downloadpath)
            downloadzip.close()
            os.remove(zippath)

            self.install_plugin(module_name, selected)

    def install_plugin(self, module_name, selected):
        if len(selected["files"]) == 1:
            source = os.path.join(USER_DOWNLOADS_DIR, module_name, selected["files"].keys()[0])
            dest = os.path.join(USER_PLUGIN_DIR, selected["files"].keys()[0])
        else:
            source = os.path.join(USER_DOWNLOADS_DIR, module_name)
            dest = os.path.join(USER_PLUGIN_DIR, module_name)

        self.tagger.pluginmanager.install_plugin(source, dest)

    def plugin_installed(self, plugin):
        if not plugin.compatible:
            msgbox = QtGui.QMessageBox(self)
            msgbox.setText(u"The plugin ‘%s’ is not compatible with this version of Picard." % plugin.name)
            msgbox.setStandardButtons(QtGui.QMessageBox.Ok)
            msgbox.setDefaultButton(QtGui.QMessageBox.Ok)
            msgbox.exec_()
            return

        self.installed.append(plugin.module_name)

        #Remove the installed plugin from the list
        root = self.ui.plugins.invisibleRootItem()
        for i in range(root.childCount()):
            item = self.items[root.child(i)]
            if item['module_name'] == plugin.module_name:
                root.removeChild(root.child(i))
                break

        self.ui.plugins.setCurrentItem(self.ui.plugins.topLevelItem(0))

        msgbox = QtGui.QMessageBox(self)
        msgbox.setText(u"The plugin ‘%s’ has been installed." % plugin.name)
        msgbox.setInformativeText("You can now activate it from the Installed Plugins panel.")
        msgbox.setStandardButtons(QtGui.QMessageBox.Ok)
        msgbox.setDefaultButton(QtGui.QMessageBox.Ok)
        msgbox.exec_()

    def open_repo(self):
        webbrowser2.goto('plugins_repo')

    def mimeTypes(self):
        return ["text/uri-list"]


register_options_page(PluginsDownloadPage)
