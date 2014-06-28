# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2009 Carlin Mangar
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
import json
from PyQt4 import QtCore, QtGui
from picard import config
from picard.const import USER_DIR, USER_PLUGIN_DIR
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

    def load(self):
        try:
            with open(os.path.join(USER_DIR, "Plugins.json"), "r") as pluginfile:
                plugins = json.load(pluginfile)['plugins']
        except IOError as e:
                plugins = []
        for plugin in plugins:
            item = self.add_plugin_item(plugin)
            if not firstitem:
                firstitem = item
        self.ui.plugins.setCurrentItem(firstitem)
        self.ui.plugins.header().resizeSections(QtGui.QHeaderView.ResizeToContents)

    def add_plugin_item(self, plugin, enabled=False, item=None):
        if item is None:
            item = QtGui.QTreeWidgetItem(self.ui.plugins)
        item.setText(0, plugin['name'])
        item.setCheckState(0, QtCore.Qt.Unchecked)
        item.setText(1, plugin['ver'])
        item.setText(2, str(plugin['downloads']))
        item.setText(3, plugin['author'])
        self.ui.plugins.header().resizeSections(QtGui.QHeaderView.ResizeToContents)
        self.items[item] = plugin
        return item

    def change_details(self):
        plugin = self.items[self.ui.plugins.selectedItems()[0]]
        text = []
        name = plugin['name']
        descr = plugin['desc']
        if descr:
            text.append(descr + "<br/>")
            text.append('______________________________')
        if name:
            text.append("<b>" + _("Name") + "</b>: " + name)
        author = plugin['author']
        if author:
            text.append("<b>" + _("Author") + "</b>: " + author)
        text.append("<b>" + _("File") + "</b>: " + ", ".join(plugin['files'].keys()))
        self.ui.details.setText("<p>%s</p>" % "<br/>\n".join(text))

    def install_plugin(self, path):
        pass

    def open_plugin_site(self):
        webbrowser2.goto('https://github.com/musicbrainz/picard-plugins')

    def mimeTypes(self):
        return ["text/uri-list"]


register_options_page(PluginsDownloadPage)
