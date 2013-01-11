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

from picard.ui.infodialogcommon import *

class AlbumInfoDialog(InfoDialogCommon):

    def __init__(self, album, parent=None):
        InfoDialogCommon.__init__(self, album, parent)
        self.setWindowTitle(_("Album Info"))
        self.load_info()

    def load_info(self):
        self.ui.tabWidget.removeTab(0) # hide info tab for now

        self.display_images()
