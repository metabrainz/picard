# Form implementation generated from reading ui file 'ui/options_interface_colors.ui'
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


class Ui_InterfaceColorsOptionsPage(object):
    def setupUi(self, InterfaceColorsOptionsPage):
        InterfaceColorsOptionsPage.setObjectName("InterfaceColorsOptionsPage")
        InterfaceColorsOptionsPage.resize(171, 137)
        self.verticalLayout = QtWidgets.QVBoxLayout(InterfaceColorsOptionsPage)
        self.verticalLayout.setObjectName("verticalLayout")
        self.colors = QtWidgets.QGroupBox(parent=InterfaceColorsOptionsPage)
        self.colors.setObjectName("colors")
        self.verticalLayout.addWidget(self.colors)

        self.retranslateUi(InterfaceColorsOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(InterfaceColorsOptionsPage)

    def retranslateUi(self, InterfaceColorsOptionsPage):
        self.colors.setTitle(_("Colors"))
