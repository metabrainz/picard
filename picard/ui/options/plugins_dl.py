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
import json
import urllib2
import zipfile
from PyQt4 import QtCore, QtGui
from picard import config, log
from picard.const import USER_DIR, USER_PLUGIN_DIR, USER_PLUGIN_DOWNLOAD_DIR
from picard.util import encode_filename, webbrowser2
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_plugins_download import Ui_PluginsDownloadPage


def cmp_plugins(a, b):
    return cmp(a.name, b.name)


class PluginsDownloadPage(OptionsPage):

    NAME = "plugins_dl"
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
        self.ui.install_plugin.clicked.connect(self.install_plugin)
        self.ui.open_repo.clicked.connect(self.open_repo)
        self.tagger.pluginmanager.plugin_installed.connect(self.plugin_installed)

    def load(self):
        try:
            with open(os.path.join(USER_DIR, "plugins.json")) as pluginfile:
                self.pluginjson = json.load(pluginfile)['plugins']
        except IOError as e:
                self.pluginjson = {}
        for module_name, data in self.pluginjson.items():
            item = self.add_plugin_item(data)
        self.ui.plugins.setCurrentItem(self.ui.plugins.topLevelItem(0))

    def add_plugin_item(self, plugin, enabled=False, item=None):
        if item is None:
            item = QtGui.QTreeWidgetItem(self.ui.plugins)
        item.setText(0, plugin['name'])
        item.setCheckState(0, QtCore.Qt.Unchecked)
        item.setText(1, plugin['version'])
        item.setText(2, str(plugin['downloads']))
        item.setText(3, plugin['author'])
        self.ui.plugins.header().resizeSections(QtGui.QHeaderView.ResizeToContents)
        self.items[item] = plugin
        return item

    def change_details(self):
        plugin = self.items[self.ui.plugins.selectedItems()[0]]
        text = []
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

    def download_plugin(self, module_name):
        """
        Downloads a plugin to USER_PLUGIN_DOWNLOAD_DIR
        """

        if not os.path.exists(USER_PLUGIN_DOWNLOAD_DIR):
            os.makedirs(USER_PLUGIN_DOWNLOAD_DIR)

        downloadpath = os.path.join(USER_PLUGIN_DOWNLOAD_DIR, module_name)
        zippath = downloadpath+".zip"

        url = "http://picard.mbsandbox.org/api/v1/download/?id="+module_name
        try:
            with open(zippath, "wb") as downloadzip:
                response = urllib2.urlopen(url).read()
                downloadzip.write(response)
            log.debug("Successfully downloaded the plugin %s from: %s",
                      module_name, url)
        except urllib2.URLError as e:
            msgbox = QtGui.QMessageBox(self)
            msgbox.setText(u"The plugin ‘%s’ could not be downloaded. Please try again later." % selected["name"])
            msgbox.setStandardButtons(QtGui.QMessageBox.Ok)
            msgbox.setDefaultButton(QtGui.QMessageBox.Ok)
            msgbox.exec_()

            return False
        else:
            # Extract and remove zip
            downloadzip = zipfile.ZipFile(zippath)
            downloadzip.extractall(downloadpath)
            downloadzip.close()
            os.remove(zippath)
            return True

    def install_plugin(self):
        """
        Installs an already downloaded plugin
        """

        selected = self.items[self.ui.plugins.selectedItems()[0]]
        for module_name, data in self.pluginjson.items():
            if data == selected:
                break

        if self.download_plugin(module_name):
            if len(selected["files"]) == 1:
                source = os.path.join(USER_PLUGIN_DOWNLOAD_DIR, module_name, selected["files"].keys()[0])
                dest = os.path.join(USER_PLUGIN_DIR, selected["files"].keys()[0])
            else:
                source = os.path.join(USER_PLUGIN_DOWNLOAD_DIR, module_name)
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

    def open_repo(self):
        webbrowser2.goto('plugins')

    def mimeTypes(self):
        return ["text/uri-list"]


register_options_page(PluginsDownloadPage)
