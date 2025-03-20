# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2012-2014, 2017, 2019 Wieland Hoffmann
# Copyright (C) 2013-2014, 2018-2025 Laurent Monin
# Copyright (C) 2014, 2017, 2020 Sophist-UK
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017-2019 Antonio Larrosa
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2018-2024 Philipp Wolfer
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 Suryansh Shakya
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

from picard.i18n import (
    gettext as _,
    ngettext,
)

from .dialog import InfoDialog
from .utils import (
    format_file_info,
    format_tracklist,
)


class FileInfoDialog(InfoDialog):

    def __init__(self, file_, parent=None):
        super().__init__(file_, parent=parent)
        self.setWindowTitle(_("Info") + " - " + file_.base_filename)

    def _display_info_tab(self):
        file_ = self.obj
        text = format_file_info(file_)
        self.ui.info.setText(text)


class AlbumInfoDialog(InfoDialog):

    def __init__(self, album, parent=None):
        super().__init__(album, parent=parent)
        self.setWindowTitle(_("Album Info"))

    def _display_info_tab(self):
        album = self.obj
        if album._tracks_loaded:
            self.ui.info.setText(format_tracklist(album))
        else:
            self.tab_hide(self.ui.info_tab)


class TrackInfoDialog(InfoDialog):

    def __init__(self, track, parent=None):
        super().__init__(track, parent=parent)
        self.setWindowTitle(_("Track Info"))

    def _display_info_tab(self):
        track = self.obj
        tab = self.ui.info_tab
        tabWidget = self.ui.tabWidget
        tab_index = tabWidget.indexOf(tab)
        if track.num_linked_files == 0:
            tabWidget.setTabText(tab_index, _("&Info"))
            self.tab_hide(tab)
            return

        tabWidget.setTabText(tab_index, _("&Info"))
        text = ngettext("%i file in this track", "%i files in this track",
                        track.num_linked_files) % track.num_linked_files
        info_files = [format_file_info(file_) for file_ in track.files]
        text += '<hr />' + '<hr />'.join(info_files)
        self.ui.info.setText(text)


class ClusterInfoDialog(InfoDialog):

    def __init__(self, cluster, parent=None):
        super().__init__(cluster, parent=parent)
        self.setWindowTitle(_("Cluster Info"))

    def _display_info_tab(self):
        tab = self.ui.info_tab
        tabWidget = self.ui.tabWidget
        tab_index = tabWidget.indexOf(tab)
        tabWidget.setTabText(tab_index, _("&Info"))
        self.ui.info.setText(format_tracklist(self.obj))
