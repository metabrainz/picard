# -*- coding: utf-8 -*-
#
# Built in Player for Picard
# Copyright (C) 2007 Gary van der Merwe
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

from PyQt4 import QtCore, QtGui

try:
    from PyQt4.phonon import Phonon
except ImportError, e:
    Phonon = None
    phonon_import_error = e
            
from picard.util import icontheme
from picard.file import File
from picard.track import Track

nano_to_milli = 1000000L
slider_acc = 100 #1/10 of a sec

class PlayerBox(QtGui.QToolBar):

    def __init__(self, parent):
        QtGui.QToolBar.__init__(self,"&Preview Bar", parent)
        
        self.setObjectName("picard.plugin.player")
        
        if Phonon:
            
            self.auto_play_action = QtGui.QAction(
                icontheme.lookup('media-playback-start',icontheme.ICON_SIZE_ALL),
                u"Play/Stop", self)
            self.auto_play_action.setCheckable(True)
            #if self.config.persist["view_cover_art"]:
            #   self.show_cover_art_action.setChecked(True)
            self.connect(self.auto_play_action, QtCore.SIGNAL("triggered()"),
                         self.onAutoPlayClicked)
            self.addAction(self.auto_play_action)
            
            self.volume_slider = Phonon.VolumeSlider(self)
            self.seek_slider = Phonon.SeekSlider(self)
            self.addWidget(self.seek_slider)
            
            self.addWidget(self.volume_slider)
            self.selection = None
            
            sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
            self.volume_slider.setSizePolicy(sizePolicy)
            self.volume_slider.setMaximumSize(QtCore.QSize(125, 48))

            sizePolicy2 = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
            self.seek_slider.setSizePolicy(sizePolicy2)
            self.seek_slider.setMinimumSize(QtCore.QSize(250, 8))
            
            self.media_object = Phonon.MediaObject(self)
            self.audio_output = Phonon.AudioOutput(self)
            Phonon.createPath(self.media_object, self.audio_output)
            self.seek_slider.setMediaObject(self.media_object)
            self.volume_slider.setAudioOutput(self.audio_output)
            
        else:
            self.addWidget(QtGui.QLabel(("Could not load Phonon. (%s)" %
                                         phonon_import_error), self))
    
    def updateSelection(self, objects):
        new_selection = None
        if len(objects)>0:
            objects = objects[0]
        
        if isinstance(objects, Track):
            if len(objects.linked_files) == 1:
                new_selection = objects.linked_files[0]
        
        if isinstance(objects, File):
            new_selection = objects
        
        if new_selection is not None and not new_selection==self.selection:
            self.selection = new_selection
            self.AutoPlay()

    def file_save(self): 
        if self.selection:
            self.media_object.clear()

    def file_changed(self): 
        if self.selection and self.selection.state==File.REMOVED:
            self.media_object.clear() 

    def AutoPlay(self):
        if self.auto_play_action.isChecked():
            if isinstance(self.selection, File) and self.selection.state!=File.PENDING:
                source = Phonon.MediaSource(self.selection.filename)
                self.media_object.setCurrentSource(source)
                self.media_object.play()

    def onAutoPlayClicked(self):
        if self.auto_play_action.isChecked() :
            self.AutoPlay()
        else:
            self.media_object.stop()
        self.updateAutoPlayIcon()

    def updateAutoPlayIcon(self):
        if self.auto_play_action.isChecked():
            self.auto_play_action.setIcon(icontheme.lookup('media-playback-stop',
                                                     icontheme.ICON_SIZE_ALL))
        else:
            self.auto_play_action.setIcon(icontheme.lookup('media-playback-start',
                                                     icontheme.ICON_SIZE_ALL))
