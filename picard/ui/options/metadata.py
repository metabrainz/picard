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

from PyQt4 import QtCore, QtGui
from picard.api import IOptionsPage
from picard.component import Component, implements
from picard.config import BoolOption, TextOption

class MetadataOptionsPage(Component):

    implements(IOptionsPage)

    options = [
        BoolOption("setting", "translate_artist_names", False),
    ]

    def get_page_info(self):
        return _("Metadata"), "metadata", None, 20

    def get_page_widget(self, parent=None):
        self.widget = QtGui.QWidget(parent)
        from picard.ui.ui_options_metadata import Ui_Form
        self.ui = Ui_Form()
        self.ui.setupUi(self.widget)
        self.ui.translate_artist_names.setChecked(
            self.config.setting["translate_artist_names"])
        return self.widget

    def save_options(self):
        self.config.setting["translate_artist_names"] = \
            self.ui.translate_artist_names.isChecked()
