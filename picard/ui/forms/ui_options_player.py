# Form implementation generated from reading ui file 'ui/options_player.ui'
#
# Created by: PyQt6 UI code generator 6.10.2
#
# Automatically generated - do not edit.
# Use `python setup.py build_ui` to update it.

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import gettext as _


class Ui_PlayerOptionsPage(object):
    def setupUi(self, PlayerOptionsPage):
        PlayerOptionsPage.setObjectName("PlayerOptionsPage")
        PlayerOptionsPage.resize(466, 360)
        self.vboxlayout = QtWidgets.QVBoxLayout(PlayerOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")
        self.player_now_playing = QtWidgets.QCheckBox(parent=PlayerOptionsPage)
        self.player_now_playing.setObjectName("player_now_playing")
        self.vboxlayout.addWidget(self.player_now_playing)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(PlayerOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(PlayerOptionsPage)

    def retranslateUi(self, PlayerOptionsPage):
        self.player_now_playing.setText(_("Enable audio player \"now playing\" notifications"))
