# -*- coding: utf-8 -*-
#
# Built in Player for Picard
# Copyright (C) 2007 Gary van der Merwe
# Copyright (C) 2013 Laurent Monin
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

try:
    from PyQt4.phonon import Phonon
except ImportError, e:
    Phonon = None
    phonon_import_error = e

from picard.util import icontheme
from picard.file import File
from picard.track import Track
from picard import log


class PlayerBox(QtGui.QToolBar):

    def __init__(self, parent):
        QtGui.QToolBar.__init__(self, "&Player", parent)

        self.name = "picard.plugin.player"
        self.setObjectName(self.name)

        self.selection = None

        if Phonon:
            icon = icontheme.lookup('media-playback-start',icontheme.ICON_SIZE_ALL)
            self.auto_play_action = QtGui.QAction(icon, u"Play/Stop", self)
            self.auto_play_action.setCheckable(True)
            self.auto_play_action.triggered.connect(self.onAutoPlayClicked)
            self.addAction(self.auto_play_action)

            self.seek_slider = Phonon.SeekSlider(self)
            self.addWidget(self.seek_slider)

            self.player = Phonon.MediaObject(self)
            Phonon.createPath(self.player, Phonon.AudioOutput(self))
            self.seek_slider.setMediaObject(self.player)
            log.debug(self.me("initialized"))
        else:
            errmsg = self.me("could not load Phonon. (%s)" % (phonon_import_error))
            self.addWidget(QtGui.QLabel(errmsg, self))
            log.error(errmsg)

    def me(self, msg):
        return "%s: %s" % (self.name, msg)

    def updateSelection(self, objects):
        if not objects:
            return

        new_selection = None
        obj = objects[0]

        if isinstance(obj, Track):
            if len(obj.linked_files) == 1:
                obj = obj.linked_files[0]

        if isinstance(obj, File):
            new_selection = obj

        if new_selection is not None and not new_selection == self.selection:
            self.selection = new_selection
            log.debug(self.me("new selection: %s" % self.selection))
            self.AutoPlay()

    def file_state_changed(self):
        obj = self.selection
        if not obj:
            return
        if not isinstance(obj, File) or obj.state != File.NORMAL:
            self.stop()

    def play(self):
        obj = self.selection
        if not isinstance(obj, File):
            return

        source = Phonon.MediaSource(obj.filename)
        log.debug(self.me("playing %s" % obj.filename))
        self.player.setCurrentSource(source)
        self.player.play()

    def stop(self):
        log.debug(self.me("stop"))
        self.player.stop()

    def AutoPlay(self):
        if self.auto_play_action.isChecked():
            self.play()

    def onAutoPlayClicked(self):
        if self.auto_play_action.isChecked():
            self.AutoPlay()
        else:
            self.stop()
        self.updateAutoPlayIcon()

    def updateAutoPlayIcon(self):
        if self.auto_play_action.isChecked():
            icon = 'media-playback-stop'
        else:
            icon = 'media-playback-start'
        self.auto_play_action.setIcon(icontheme.lookup(icon,
                                                       icontheme.ICON_SIZE_ALL))
