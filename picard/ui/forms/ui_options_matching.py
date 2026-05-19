# Form implementation generated from reading ui file 'ui/options_matching.ui'
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


class Ui_MatchingOptionsPage(object):
    def setupUi(self, MatchingOptionsPage):
        MatchingOptionsPage.setObjectName("MatchingOptionsPage")
        MatchingOptionsPage.resize(413, 612)
        self.vboxlayout = QtWidgets.QVBoxLayout(MatchingOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")
        self.matching_group = QtWidgets.QGroupBox(parent=MatchingOptionsPage)
        self.matching_group.setObjectName("matching_group")
        self.gridlayout = QtWidgets.QGridLayout(self.matching_group)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName("gridlayout")
        self.label_min_similarity = QtWidgets.QLabel(parent=self.matching_group)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_min_similarity.sizePolicy().hasHeightForWidth())
        self.label_min_similarity.setSizePolicy(sizePolicy)
        self.label_min_similarity.setObjectName("label_min_similarity")
        self.gridlayout.addWidget(self.label_min_similarity, 0, 0, 1, 1)
        self.match_min_similarity = QtWidgets.QSpinBox(parent=self.matching_group)
        self.match_min_similarity.setMaximum(100)
        self.match_min_similarity.setObjectName("match_min_similarity")
        self.gridlayout.addWidget(self.match_min_similarity, 0, 1, 1, 1)
        self.label_min_margin = QtWidgets.QLabel(parent=self.matching_group)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_min_margin.sizePolicy().hasHeightForWidth())
        self.label_min_margin.setSizePolicy(sizePolicy)
        self.label_min_margin.setObjectName("label_min_margin")
        self.gridlayout.addWidget(self.label_min_margin, 1, 0, 1, 1)
        self.match_min_margin = QtWidgets.QSpinBox(parent=self.matching_group)
        self.match_min_margin.setMaximum(100)
        self.match_min_margin.setObjectName("match_min_margin")
        self.gridlayout.addWidget(self.match_min_margin, 1, 1, 1, 1)
        self.label_track_matching = QtWidgets.QLabel(parent=self.matching_group)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_track_matching.sizePolicy().hasHeightForWidth())
        self.label_track_matching.setSizePolicy(sizePolicy)
        self.label_track_matching.setObjectName("label_track_matching")
        self.gridlayout.addWidget(self.label_track_matching, 2, 0, 1, 1)
        self.track_matching_threshold = QtWidgets.QSpinBox(parent=self.matching_group)
        self.track_matching_threshold.setMaximum(100)
        self.track_matching_threshold.setObjectName("track_matching_threshold")
        self.gridlayout.addWidget(self.track_matching_threshold, 2, 1, 1, 1)
        self.vboxlayout.addWidget(self.matching_group)
        spacerItem = QtWidgets.QSpacerItem(20, 41, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_min_similarity.setBuddy(self.match_min_similarity)
        self.label_min_margin.setBuddy(self.match_min_margin)
        self.label_track_matching.setBuddy(self.track_matching_threshold)

        self.retranslateUi(MatchingOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(MatchingOptionsPage)
        MatchingOptionsPage.setTabOrder(self.match_min_similarity, self.match_min_margin)
        MatchingOptionsPage.setTabOrder(self.match_min_margin, self.track_matching_threshold)

    def retranslateUi(self, MatchingOptionsPage):
        self.matching_group.setTitle(_("Matching"))
        self.label_min_similarity.setText(_("Minimum similarity:"))
        self.match_min_similarity.setSuffix(_(" %"))
        self.label_min_margin.setText(_("Minimum margin between best and second-best match:"))
        self.match_min_margin.setSuffix(_(" %"))
        self.label_track_matching.setText(_("Minimal similarity for matching files to tracks:"))
        self.track_matching_threshold.setSuffix(_(" %"))
