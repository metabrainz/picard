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
from PyQt4 import QtCore, QtGui
from picard import config
from picard.const import USER_PLUGIN_DIR
from picard.plugin import PluginFlags
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
        self.tagger.pluginmanager.plugin_installed.connect(self.plugin_installed)

    def load(self):
        plugins = sorted(self.tagger.pluginmanager.plugins, cmp=cmp_plugins)
        enabled_plugins = config.setting["enabled_plugins"]
        available_plugins = dict([(p.module_name, p.version) for p in
                                  self.tagger.pluginmanager.available_plugins])
        for plugin in plugins:
            plugin.flags = PluginFlags.NONE
            if plugin.module_name in enabled_plugins:
                plugin.flags |= PluginFlags.ENABLED
            if plugin.module_name in available_plugins.keys():
                latest = available_plugins[plugin.module_name]
                if latest.split('.') > plugin.version.split('.'):
                    plugin.new_version = latest
                    plugin.flags |= PluginFlags.CAN_BE_UPDATED
            item = self.add_plugin_item(plugin)
        self.ui.plugins.setCurrentItem(self.ui.plugins.topLevelItem(0))

    def plugin_installed(self, plugin):
        if not plugin.compatible:
            msgbox = QtGui.QMessageBox(self)
            msgbox.setText(_(u"The plugin '%s' is not compatible with this version of Picard.") % plugin.name)
            msgbox.setStandardButtons(QtGui.QMessageBox.Ok)
            msgbox.setDefaultButton(QtGui.QMessageBox.Ok)
            msgbox.exec_()
            return
        plugin.new_version = False
        plugin.flags = PluginFlags.NONE
        for i, p in self.items.items():
            if plugin.module_name == p.module_name:
                if i.checkState(0) == QtCore.Qt.Checked:
                    plugin.flags |= PluginFlags.ENABLED
                self.add_plugin_item(plugin, item=i)
                break
        else:
            self.add_plugin_item(plugin)

    def add_plugin_item(self, plugin, item=None):
        if item is None:
            item = QtGui.QTreeWidgetItem(self.ui.plugins)
        item.setText(0, plugin.name)
        if plugin.flags & PluginFlags.ENABLED:
            item.setCheckState(0, QtCore.Qt.Checked)
        else:
            item.setCheckState(0, QtCore.Qt.Unchecked)
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
        plugin = self.items[self.ui.plugins.selectedItems()[0]]
        text = []
        if plugin.new_version:
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
        files = QtGui.QFileDialog.getOpenFileNames(self, "",
                                                   QtCore.QDir.homePath(),
                                                   "Picard plugin (*.py *.pyc)")
        if files:
            files = map(unicode, files)
            for path in files:
                self.install_plugin(path)

    def install_plugin(self, path):
        path = encode_filename(path)
        file = os.path.basename(path)
        dest = os.path.join(USER_PLUGIN_DIR, file)
        if os.path.exists(dest):
            msgbox = QtGui.QMessageBox(self)
            msgbox.setText("A plugin named %s is already installed." % file)
            msgbox.setInformativeText("Do you want to overwrite the existing plugin?")
            msgbox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            msgbox.setDefaultButton(QtGui.QMessageBox.No)
            if msgbox.exec_() == QtGui.QMessageBox.No:
                return
        self.tagger.pluginmanager.install_plugin(path, dest)

    def open_plugin_dir(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.loader % USER_PLUGIN_DIR, QtCore.QUrl.TolerantMode))

    def mimeTypes(self):
        return ["text/uri-list"]

    def dragEnterEvent(self, event):
        event.setDropAction(QtCore.Qt.CopyAction)
        event.accept()

    def dropEvent(self, event):
        for path in [os.path.normpath(unicode(u.toLocalFile())) for u in event.mimeData().urls()]:
            self.install_plugin(path)


register_options_page(PluginsOptionsPage)
