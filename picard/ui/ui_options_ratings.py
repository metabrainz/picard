# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_RatingsOptionsPage(object):
    def setupUi(self, RatingsOptionsPage):
        RatingsOptionsPage.setObjectName("RatingsOptionsPage")
        RatingsOptionsPage.resize(397, 267)
        self.vboxlayout = QtWidgets.QVBoxLayout(RatingsOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")
        self.enable_ratings = QtWidgets.QGroupBox(RatingsOptionsPage)
        self.enable_ratings.setCheckable(True)
        self.enable_ratings.setChecked(True)
        self.enable_ratings.setObjectName("enable_ratings")
        self.vboxlayout1 = QtWidgets.QVBoxLayout(self.enable_ratings)
        self.vboxlayout1.setObjectName("vboxlayout1")
        self.label = QtWidgets.QLabel(self.enable_ratings)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.vboxlayout1.addWidget(self.label)
        self.ignore_tags_2 = QtWidgets.QLabel(self.enable_ratings)
        self.ignore_tags_2.setEnabled(True)
        self.ignore_tags_2.setWordWrap(True)
        self.ignore_tags_2.setObjectName("ignore_tags_2")
        self.vboxlayout1.addWidget(self.ignore_tags_2)
        self.rating_user_email = QtWidgets.QLineEdit(self.enable_ratings)
        self.rating_user_email.setReadOnly(False)
        self.rating_user_email.setObjectName("rating_user_email")
        self.vboxlayout1.addWidget(self.rating_user_email)
        self.submit_ratings = QtWidgets.QCheckBox(self.enable_ratings)
        self.submit_ratings.setObjectName("submit_ratings")
        self.vboxlayout1.addWidget(self.submit_ratings)
        self.vboxlayout.addWidget(self.enable_ratings)
        spacerItem = QtWidgets.QSpacerItem(181, 31, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(RatingsOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(RatingsOptionsPage)

    def retranslateUi(self, RatingsOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.enable_ratings.setTitle(_("Enable track ratings"))
        self.label.setText(_("Picard saves the ratings together with an e-mail address identifying the user who did the rating. That way different ratings for different users can be stored in the files. Please specify the e-mail you want to use to save your ratings."))
        self.ignore_tags_2.setText(_("E-mail:"))
        self.submit_ratings.setText(_("Submit ratings to MusicBrainz"))

