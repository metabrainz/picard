# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_ratings.ui'
#
# Created: Mon Nov  3 20:50:52 2008
#      by: PyQt4 UI code generator 4.3.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_RatingsOptionsPage(object):
    def setupUi(self, RatingsOptionsPage):
        RatingsOptionsPage.setObjectName("RatingsOptionsPage")
        RatingsOptionsPage.resize(QtCore.QSize(QtCore.QRect(0,0,397,267).size()).expandedTo(RatingsOptionsPage.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(RatingsOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")

        self.enable_ratings = QtGui.QGroupBox(RatingsOptionsPage)
        self.enable_ratings.setCheckable(True)
        self.enable_ratings.setChecked(True)
        self.enable_ratings.setObjectName("enable_ratings")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.enable_ratings)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.ignore_tags_2 = QtGui.QLabel(self.enable_ratings)
        self.ignore_tags_2.setEnabled(True)
        self.ignore_tags_2.setWordWrap(True)
        self.ignore_tags_2.setObjectName("ignore_tags_2")
        self.vboxlayout1.addWidget(self.ignore_tags_2)

        self.rating_user_email = QtGui.QLineEdit(self.enable_ratings)
        self.rating_user_email.setReadOnly(False)
        self.rating_user_email.setObjectName("rating_user_email")
        self.vboxlayout1.addWidget(self.rating_user_email)
        self.vboxlayout.addWidget(self.enable_ratings)

        spacerItem = QtGui.QSpacerItem(181,31,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(RatingsOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(RatingsOptionsPage)

    def retranslateUi(self, RatingsOptionsPage):
        self.enable_ratings.setTitle(_("Enable track ratings"))
        self.ignore_tags_2.setText(_("E-mail:"))

