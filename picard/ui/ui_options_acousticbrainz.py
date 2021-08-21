# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_AcousticBrainzOptionsPage(object):
    def setupUi(self, AcousticBrainzOptionsPage):
        AcousticBrainzOptionsPage.setObjectName("AcousticBrainzOptionsPage")
        AcousticBrainzOptionsPage.resize(371, 408)
        self.verticalLayout = QtWidgets.QVBoxLayout(AcousticBrainzOptionsPage)
        self.verticalLayout.setObjectName("verticalLayout")
        self.acoustic_features = QtWidgets.QGroupBox(AcousticBrainzOptionsPage)
        self.acoustic_features.setCheckable(False)
        self.acoustic_features.setObjectName("acoustic_features")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.acoustic_features)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.disable_acoustic_features = QtWidgets.QRadioButton(self.acoustic_features)
        self.disable_acoustic_features.setObjectName("disable_acoustic_features")
        self.verticalLayout_3.addWidget(self.disable_acoustic_features)
        self.use_acoustic_features = QtWidgets.QRadioButton(self.acoustic_features)
        self.use_acoustic_features.setObjectName("use_acoustic_features")
        self.verticalLayout_3.addWidget(self.use_acoustic_features)
        self.verticalLayout.addWidget(self.acoustic_features)
        self.acousticbrainz_settings = QtWidgets.QGroupBox(AcousticBrainzOptionsPage)
        self.acousticbrainz_settings.setObjectName("acousticbrainz_settings")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.acousticbrainz_settings)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label = QtWidgets.QLabel(self.acousticbrainz_settings)
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.acousticbrainz_extractor = QtWidgets.QLineEdit(self.acousticbrainz_settings)
        self.acousticbrainz_extractor.setObjectName("acousticbrainz_extractor")
        self.horizontalLayout_2.addWidget(self.acousticbrainz_extractor)
        self.acousticbrainz_extractor_browse = QtWidgets.QPushButton(self.acousticbrainz_settings)
        self.acousticbrainz_extractor_browse.setObjectName("acousticbrainz_extractor_browse")
        self.horizontalLayout_2.addWidget(self.acousticbrainz_extractor_browse)
        self.acousticbrainz_extractor_download = QtWidgets.QPushButton(self.acousticbrainz_settings)
        self.acousticbrainz_extractor_download.setObjectName("acousticbrainz_extractor_download")
        self.horizontalLayout_2.addWidget(self.acousticbrainz_extractor_download)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.acousticbrainz_extractor_info = QtWidgets.QLabel(self.acousticbrainz_settings)
        self.acousticbrainz_extractor_info.setText("")
        self.acousticbrainz_extractor_info.setObjectName("acousticbrainz_extractor_info")
        self.verticalLayout_2.addWidget(self.acousticbrainz_extractor_info)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.verticalLayout.addWidget(self.acousticbrainz_settings)
        spacerItem = QtWidgets.QSpacerItem(181, 21, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(AcousticBrainzOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(AcousticBrainzOptionsPage)

    def retranslateUi(self, AcousticBrainzOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.acoustic_features.setTitle(_("AcousticBrainz features extraction"))
        self.disable_acoustic_features.setText(_("Do not use acoustic feature extraction"))
        self.use_acoustic_features.setText(_("Use acoustic feature extraction"))
        self.acousticbrainz_settings.setTitle(_("AcousticBrainz Settings"))
        self.label.setText(_("AcousticBrainz/Essentia feature extractor:"))
        self.acousticbrainz_extractor_browse.setText(_("Browse..."))
        self.acousticbrainz_extractor_download.setText(_("Download..."))
