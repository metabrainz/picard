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
from picard.api import IOptionsPage
from picard.component import Component, implements
from picard.ui.ui_options_plugins import Ui_PluginsPage

class PluginsOptionsPage(Component):

    implements(IOptionsPage)

    def get_page_info(self):
        return _(u"Plugins"), "plugins", None, 50

    def get_page_widget(self, parent=None):
        self.widget = QtGui.QWidget(parent)
        self.ui = Ui_PluginsPage()
        self.ui.setupUi(self.widget)
        self.connect(self.ui.plugins, QtCore.SIGNAL("itemSelectionChanged()"), self.change_details)
        return self.widget

    def check(self):
        pass

    def load_options(self):
        self.items = {}
        firstitem = None
        for plugin in self.tagger.pluginmanager.plugins:
            item = QtGui.QTreeWidgetItem(self.ui.plugins)
            item.setText(0, plugin.name)
            item.setText(1, plugin.author)
            if not firstitem:
                firstitem = item
            self.items[item] = plugin
        self.ui.plugins.setCurrentItem(firstitem)

    def save_options(self):
        pass

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
