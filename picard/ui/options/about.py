# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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

import picard.plugins
from PyQt4 import QtCore, QtGui
from picard import __version__
from picard.api import IOptionsPage
from picard.component import Component, implements
from picard.config import BoolOption, TextOption

class AboutOptionsPage(Component):

    implements(IOptionsPage)
    
    def get_page_info(self):
        return (_(u"About"), "about", None, 100)

    def get_page_widget(self, parent=None):
        from picard.ui.ui_options_about import Ui_Form
        self.widget = QtGui.QWidget(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self.widget)

        args = {}
        args["version"] = __version__
        
        plugins = []
        for name in dir(picard.plugins):
            if not name.startswith("_"):
                plugins.append(name)
        args["plugins"] = ", ".join(plugins)

        text = _("""<p><span style="font-size:15px;font-weight:bold;">MusicBrainz Picard</span><br/>
Version %(version)s
</p>
<p>
...
</p>
<p><strong>Plugins:</strong> %(plugins)s</p>
""" % args)
        self.ui.label.setText(text)
        return self.widget

    def save_options(self):
        pass

