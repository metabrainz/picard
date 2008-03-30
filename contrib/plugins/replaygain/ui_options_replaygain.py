# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'options_replaygain.ui'
#
# Created: Thu Mar 13 23:07:48 2008
#      by: PyQt4 UI code generator 4.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_ReplayGainOptionsPage(object):
    def setupUi(self, ReplayGainOptionsPage):
        ReplayGainOptionsPage.setObjectName("ReplayGainOptionsPage")
        ReplayGainOptionsPage.resize(QtCore.QSize(QtCore.QRect(0,0,305,317).size()).expandedTo(ReplayGainOptionsPage.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(ReplayGainOptionsPage)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setObjectName("vboxlayout")

        self.replay_gain = QtGui.QGroupBox(ReplayGainOptionsPage)
        self.replay_gain.setObjectName("replay_gain")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.replay_gain)
        self.vboxlayout1.setSpacing(2)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.label = QtGui.QLabel(self.replay_gain)
        self.label.setObjectName("label")
        self.vboxlayout1.addWidget(self.label)

        self.vorbisgain_command = QtGui.QLineEdit(self.replay_gain)
        self.vorbisgain_command.setObjectName("vorbisgain_command")
        self.vboxlayout1.addWidget(self.vorbisgain_command)

        self.label_2 = QtGui.QLabel(self.replay_gain)
        self.label_2.setObjectName("label_2")
        self.vboxlayout1.addWidget(self.label_2)

        self.mp3gain_command = QtGui.QLineEdit(self.replay_gain)
        self.mp3gain_command.setObjectName("mp3gain_command")
        self.vboxlayout1.addWidget(self.mp3gain_command)

        self.label_3 = QtGui.QLabel(self.replay_gain)
        self.label_3.setObjectName("label_3")
        self.vboxlayout1.addWidget(self.label_3)

        self.metaflac_command = QtGui.QLineEdit(self.replay_gain)
        self.metaflac_command.setObjectName("metaflac_command")
        self.vboxlayout1.addWidget(self.metaflac_command)
        self.vboxlayout.addWidget(self.replay_gain)

        spacerItem = QtGui.QSpacerItem(263,21,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(ReplayGainOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(ReplayGainOptionsPage)

    def retranslateUi(self, ReplayGainOptionsPage):
        self.replay_gain.setTitle(QtGui.QApplication.translate("ReplayGainOptionsPage", "Replay Gain", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("ReplayGainOptionsPage", "Path to VorbisGain:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("ReplayGainOptionsPage", "Path to MP3Gain:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("ReplayGainOptionsPage", "Path to metaflac:", None, QtGui.QApplication.UnicodeUTF8))

