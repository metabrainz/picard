# Form implementation generated from reading ui file 'ui/options_interface_colors.ui'
#
# Created by: PyQt6 UI code generator 6.6.1
#
# Automatically generated - do not edit.
# Use `python setup.py build_ui` to update it.

from PySide6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import gettext as _


class Ui_InterfaceColorsOptionsPage(object):
    def setupUi(self, InterfaceColorsOptionsPage):
        InterfaceColorsOptionsPage.setObjectName("InterfaceColorsOptionsPage")
        InterfaceColorsOptionsPage.resize(171, 137)
        self.vboxlayout = QtWidgets.QVBoxLayout(InterfaceColorsOptionsPage)
        self.vboxlayout.setContentsMargins(0, 0, 0, 0)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.scrollArea = QtWidgets.QScrollArea(parent=InterfaceColorsOptionsPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.scrollArea.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.scrollArea.setLineWidth(0)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeading|QtCore.Qt.AlignmentFlag.AlignLeft|QtCore.Qt.AlignmentFlag.AlignTop)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 199, 137))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setContentsMargins(9, 9, 9, 9)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.colors = QtWidgets.QGroupBox(parent=self.scrollAreaWidgetContents)
        self.colors.setObjectName("colors")
        self.verticalLayout.addWidget(self.colors)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.vboxlayout.addWidget(self.scrollArea)

        self.retranslateUi(InterfaceColorsOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(InterfaceColorsOptionsPage)

    def retranslateUi(self, InterfaceColorsOptionsPage):
        self.colors.setTitle(_("Colors"))
