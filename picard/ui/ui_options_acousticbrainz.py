# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_AcousticBrainzOptionsPage(object):
    def setupUi(self, AcousticBrainzOptionsPage):
        AcousticBrainzOptionsPage.setObjectName("AcousticBrainzOptionsPage")
        AcousticBrainzOptionsPage.resize(515, 503)
        self.verticalLayout = QtWidgets.QVBoxLayout(AcousticBrainzOptionsPage)
        self.verticalLayout.setObjectName("verticalLayout")
        self.use_acousticbrainz = QtWidgets.QGroupBox(AcousticBrainzOptionsPage)
        self.use_acousticbrainz.setCheckable(True)
        self.use_acousticbrainz.setChecked(False)
        self.use_acousticbrainz.setObjectName("use_acousticbrainz")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.use_acousticbrainz)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label = QtWidgets.QLabel(self.use_acousticbrainz)
        self.label.setObjectName("label")
        self.verticalLayout_3.addWidget(self.label)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.acousticbrainz_extractor = QtWidgets.QLineEdit(self.use_acousticbrainz)
        self.acousticbrainz_extractor.setObjectName("acousticbrainz_extractor")
        self.horizontalLayout_2.addWidget(self.acousticbrainz_extractor)
        self.acousticbrainz_extractor_browse = QtWidgets.QPushButton(self.use_acousticbrainz)
        self.acousticbrainz_extractor_browse.setObjectName("acousticbrainz_extractor_browse")
        self.horizontalLayout_2.addWidget(self.acousticbrainz_extractor_browse)
        self.acousticbrainz_extractor_download = QtWidgets.QPushButton(self.use_acousticbrainz)
        self.acousticbrainz_extractor_download.setObjectName("acousticbrainz_extractor_download")
        self.horizontalLayout_2.addWidget(self.acousticbrainz_extractor_download)
        self.verticalLayout_3.addLayout(self.horizontalLayout_2)
        self.acousticbrainz_extractor_info = QtWidgets.QLabel(self.use_acousticbrainz)
        self.acousticbrainz_extractor_info.setText("")
        self.acousticbrainz_extractor_info.setObjectName("acousticbrainz_extractor_info")
        self.verticalLayout_3.addWidget(self.acousticbrainz_extractor_info)
        self.verticalLayout.addWidget(self.use_acousticbrainz)
        spacerItem = QtWidgets.QSpacerItem(181, 21, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(AcousticBrainzOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(AcousticBrainzOptionsPage)

    def retranslateUi(self, AcousticBrainzOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.use_acousticbrainz.setTitle(_("AcousticBrainz features extraction"))
        self.label.setText(_("AcousticBrainz/Essentia feature extractor:"))
        self.acousticbrainz_extractor_browse.setText(_("Browse..."))
        self.acousticbrainz_extractor_download.setText(_("Download..."))
