# Form implementation generated from reading ui file 'ui/options_cover_processing.ui'
#
# Created by: PyQt6 UI code generator 6.6.1
#
# Automatically generated - do not edit.
# Use `python setup.py build_ui` to update it.

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import gettext as _


class Ui_CoverProcessingOptionsPage(object):
    def setupUi(self, CoverProcessingOptionsPage):
        CoverProcessingOptionsPage.setObjectName("CoverProcessingOptionsPage")
        CoverProcessingOptionsPage.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(CoverProcessingOptionsPage)
        self.verticalLayout.setObjectName("verticalLayout")
        self.filtering = QtWidgets.QGroupBox(parent=CoverProcessingOptionsPage)
        self.filtering.setCheckable(True)
        self.filtering.setChecked(False)
        self.filtering.setObjectName("filtering")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.filtering)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.width_widget = QtWidgets.QWidget(parent=self.filtering)
        self.width_widget.setObjectName("width_widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.width_widget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.width_label = QtWidgets.QLabel(parent=self.width_widget)
        self.width_label.setObjectName("width_label")
        self.horizontalLayout.addWidget(self.width_label)
        self.width_value = QtWidgets.QSpinBox(parent=self.width_widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.width_value.sizePolicy().hasHeightForWidth())
        self.width_value.setSizePolicy(sizePolicy)
        self.width_value.setMaximum(1000)
        self.width_value.setProperty("value", 250)
        self.width_value.setObjectName("width_value")
        self.horizontalLayout.addWidget(self.width_value)
        self.px_label2 = QtWidgets.QLabel(parent=self.width_widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.px_label2.sizePolicy().hasHeightForWidth())
        self.px_label2.setSizePolicy(sizePolicy)
        self.px_label2.setObjectName("px_label2")
        self.horizontalLayout.addWidget(self.px_label2)
        self.verticalLayout_2.addWidget(self.width_widget)
        self.height_widget = QtWidgets.QWidget(parent=self.filtering)
        self.height_widget.setObjectName("height_widget")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.height_widget)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.height_label = QtWidgets.QLabel(parent=self.height_widget)
        self.height_label.setObjectName("height_label")
        self.horizontalLayout_2.addWidget(self.height_label)
        self.height_value = QtWidgets.QSpinBox(parent=self.height_widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.height_value.sizePolicy().hasHeightForWidth())
        self.height_value.setSizePolicy(sizePolicy)
        self.height_value.setMaximum(1000)
        self.height_value.setProperty("value", 250)
        self.height_value.setObjectName("height_value")
        self.horizontalLayout_2.addWidget(self.height_value)
        self.px_label1 = QtWidgets.QLabel(parent=self.height_widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.px_label1.sizePolicy().hasHeightForWidth())
        self.px_label1.setSizePolicy(sizePolicy)
        self.px_label1.setObjectName("px_label1")
        self.horizontalLayout_2.addWidget(self.px_label1)
        self.verticalLayout_2.addWidget(self.height_widget)
        self.verticalLayout.addWidget(self.filtering)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(CoverProcessingOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(CoverProcessingOptionsPage)

    def retranslateUi(self, CoverProcessingOptionsPage):
        CoverProcessingOptionsPage.setWindowTitle(_("Form"))
        self.filtering.setTitle(_("Discard images if below the given size"))
        self.width_label.setText(_("Width:"))
        self.px_label2.setText(_("px"))
        self.height_label.setText(_("Height:"))
        self.px_label1.setText(_("px"))
