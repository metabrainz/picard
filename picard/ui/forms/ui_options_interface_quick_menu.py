# Form implementation generated from reading ui file 'ui/options_interface_quick_menu.ui'
#
# Created by: PyQt6 UI code generator 6.9.1
#
# Automatically generated - do not edit.
# Use `python setup.py build_ui` to update it.

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import gettext as _


class Ui_InterfaceQuickMenuOptionsPage(object):
    def setupUi(self, InterfaceQuickMenuOptionsPage):
        InterfaceQuickMenuOptionsPage.setObjectName("InterfaceQuickMenuOptionsPage")
        InterfaceQuickMenuOptionsPage.resize(418, 310)
        self.vboxlayout = QtWidgets.QVBoxLayout(InterfaceQuickMenuOptionsPage)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.quick_menu_groupBox = QtWidgets.QGroupBox(parent=InterfaceQuickMenuOptionsPage)
        self.quick_menu_groupBox.setObjectName("quick_menu_groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.quick_menu_groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.quick_menu_instructions = QtWidgets.QLabel(parent=self.quick_menu_groupBox)
        self.quick_menu_instructions.setWordWrap(True)
        self.quick_menu_instructions.setObjectName("quick_menu_instructions")
        self.verticalLayout.addWidget(self.quick_menu_instructions)
        self.quick_menu_items = QtWidgets.QTreeWidget(parent=self.quick_menu_groupBox)
        self.quick_menu_items.setObjectName("quick_menu_items")
        self.quick_menu_items.headerItem().setText(0, "1")
        self.verticalLayout.addWidget(self.quick_menu_items)
        self.vboxlayout.addWidget(self.quick_menu_groupBox)

        self.retranslateUi(InterfaceQuickMenuOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(InterfaceQuickMenuOptionsPage)

    def retranslateUi(self, InterfaceQuickMenuOptionsPage):
        self.quick_menu_groupBox.setTitle(_("Quick Settings Menu"))
        self.quick_menu_instructions.setText(_("TextLabel"))
