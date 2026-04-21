# Form implementation generated from reading ui file 'ui/options_player.ui'
#
# Created by: PyQt6 UI code generator 6.11.0
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
        self.listenbrainz_enabled = QtWidgets.QGroupBox(parent=PlayerOptionsPage)
        self.listenbrainz_enabled.setCheckable(True)
        self.listenbrainz_enabled.setObjectName("listenbrainz_enabled")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.listenbrainz_enabled)
        self.verticalLayout.setObjectName("verticalLayout")
        self.listenbrainz_submit_only_tagged = QtWidgets.QCheckBox(parent=self.listenbrainz_enabled)
        self.listenbrainz_submit_only_tagged.setChecked(True)
        self.listenbrainz_submit_only_tagged.setObjectName("listenbrainz_submit_only_tagged")
        self.verticalLayout.addWidget(self.listenbrainz_submit_only_tagged)
        self.listenbrainz_user_label = QtWidgets.QLabel(parent=self.listenbrainz_enabled)
        self.listenbrainz_user_label.setObjectName("listenbrainz_user_label")
        self.verticalLayout.addWidget(self.listenbrainz_user_label)
        self.listenbrainz_user = QtWidgets.QLineEdit(parent=self.listenbrainz_enabled)
        self.listenbrainz_user.setObjectName("listenbrainz_user")
        self.verticalLayout.addWidget(self.listenbrainz_user)
        self.listenbrainz_token_label = QtWidgets.QLabel(parent=self.listenbrainz_enabled)
        self.listenbrainz_token_label.setObjectName("listenbrainz_token_label")
        self.verticalLayout.addWidget(self.listenbrainz_token_label)
        self.listenbrainz_token = QtWidgets.QLineEdit(parent=self.listenbrainz_enabled)
        self.listenbrainz_token.setObjectName("listenbrainz_token")
        self.verticalLayout.addWidget(self.listenbrainz_token)
        self.vboxlayout.addWidget(self.listenbrainz_enabled)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.listenbrainz_user_label.setBuddy(self.listenbrainz_user)
        self.listenbrainz_token_label.setBuddy(self.listenbrainz_token)

        self.retranslateUi(PlayerOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(PlayerOptionsPage)
        PlayerOptionsPage.setTabOrder(self.player_now_playing, self.listenbrainz_enabled)
        PlayerOptionsPage.setTabOrder(self.listenbrainz_enabled, self.listenbrainz_submit_only_tagged)
        PlayerOptionsPage.setTabOrder(self.listenbrainz_submit_only_tagged, self.listenbrainz_user)
        PlayerOptionsPage.setTabOrder(self.listenbrainz_user, self.listenbrainz_token)

    def retranslateUi(self, PlayerOptionsPage):
        PlayerOptionsPage.setAccessibleName(_("ListenBrainz user name"))
        self.player_now_playing.setText(_("Enable audio player \"now playing\" notifications"))
        self.listenbrainz_enabled.setTitle(_("Submit listens to ListenBrainz"))
        self.listenbrainz_submit_only_tagged.setText(_("Submit only tagged files"))
        self.listenbrainz_user_label.setText(_("ListenBrainz username:"))
        self.listenbrainz_user.setAccessibleName(_("ListenBrainz username"))
        self.listenbrainz_token_label.setText(_("ListenBrainz user token:"))
        self.listenbrainz_token.setAccessibleDescription(_("ListenBrainz user token"))
