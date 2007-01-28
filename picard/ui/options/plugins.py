# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
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

from PyQt4 import QtCore, QtGui
from picard.config import TextOption
from picard.plugin import plugin_name_from_module
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_plugins import Ui_PluginsOptionsPage


class PluginsOptionsPage(OptionsPage):

    NAME = "plugins"
    TITLE = N_("Plugins")
    PARENT = None
    SORT_ORDER = 70
    ACTIVE = True

    options = [
        TextOption("setting", "enabled_plugins", ""),
    ]

    def __init__(self, parent=None):
        super(PluginsOptionsPage, self).__init__(parent)
        self.ui = Ui_PluginsOptionsPage()
        self.ui.setupUi(self)
        self.connect(self.ui.plugins, QtCore.SIGNAL("itemSelectionChanged()"), self.change_details)

    def load(self):
        enabled_plugins = self.config.setting["enabled_plugins"].split()
        self.items = {}
        firstitem = None
        for plugin in self.tagger.pluginmanager.plugins:
            item = QtGui.QTreeWidgetItem(self.ui.plugins)
            item.setText(0, plugin.name)
            if plugin_name_from_module(plugin.module) in enabled_plugins:
                item.setCheckState(0, QtCore.Qt.Checked)
            else:
                item.setCheckState(0, QtCore.Qt.Unchecked)
            item.setText(1, plugin.author)
            if not firstitem:
                firstitem = item
            self.items[item] = plugin
        self.ui.plugins.setCurrentItem(firstitem)

    def save(self):
        enabled_plugins = []
        for item, plugin in self.items.iteritems():
            if item.checkState(0) == QtCore.Qt.Checked:
                enabled_plugins.append(plugin_name_from_module(plugin.module))
        self.config.setting["enabled_plugins"] = " ".join(enabled_plugins)

    def change_details(self):
        plugin = self.items[self.ui.plugins.selectedItems()[0]]
        text = []
        name = plugin.name
        if name:
            text.append("<b>" + _("Name") + "</b>: " + name)
        author = plugin.author
        if author:
            text.append("<b>" + _("Author") + "</b>: " + author)
        text.append("<b>" + _("File") + "</b>: " + plugin.file)
        descr = plugin.description
        if descr:
            text.append(descr)
        self.ui.details.setText("<br/>\n".join(text))


register_options_page(PluginsOptionsPage)
