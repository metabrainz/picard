# Form implementation generated from reading ui file 'ui/options_interface_toolbar.ui'
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


class Ui_InterfaceToolbarOptionsPage(object):
    def setupUi(self, InterfaceToolbarOptionsPage):
        InterfaceToolbarOptionsPage.setObjectName("InterfaceToolbarOptionsPage")
        InterfaceToolbarOptionsPage.resize(466, 317)
        self.vboxlayout = QtWidgets.QVBoxLayout(InterfaceToolbarOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")
        self.customize_toolbar_box = QtWidgets.QGroupBox(parent=InterfaceToolbarOptionsPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.customize_toolbar_box.sizePolicy().hasHeightForWidth())
        self.customize_toolbar_box.setSizePolicy(sizePolicy)
        self.customize_toolbar_box.setObjectName("customize_toolbar_box")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.customize_toolbar_box)
        self.verticalLayout.setObjectName("verticalLayout")
        self.toolbar_layout_list = QtWidgets.QListWidget(parent=self.customize_toolbar_box)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolbar_layout_list.sizePolicy().hasHeightForWidth())
        self.toolbar_layout_list.setSizePolicy(sizePolicy)
        self.toolbar_layout_list.setObjectName("toolbar_layout_list")
        self.verticalLayout.addWidget(self.toolbar_layout_list)
        self.edit_button_box = QtWidgets.QWidget(parent=self.customize_toolbar_box)
        self.edit_button_box.setObjectName("edit_button_box")
        self.edit_box_layout = QtWidgets.QHBoxLayout(self.edit_button_box)
        self.edit_box_layout.setContentsMargins(0, 0, 0, 0)
        self.edit_box_layout.setObjectName("edit_box_layout")
        self.add_button = QtWidgets.QToolButton(parent=self.edit_button_box)
        self.add_button.setObjectName("add_button")
        self.edit_box_layout.addWidget(self.add_button)
        self.insert_separator_button = QtWidgets.QToolButton(parent=self.edit_button_box)
        self.insert_separator_button.setObjectName("insert_separator_button")
        self.edit_box_layout.addWidget(self.insert_separator_button)
        spacerItem = QtWidgets.QSpacerItem(50, 20, QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.edit_box_layout.addItem(spacerItem)
        self.up_button = QtWidgets.QToolButton(parent=self.edit_button_box)
        icon = QtGui.QIcon.fromTheme(":/images/16x16/go-up.png")
        self.up_button.setIcon(icon)
        self.up_button.setObjectName("up_button")
        self.edit_box_layout.addWidget(self.up_button)
        self.down_button = QtWidgets.QToolButton(parent=self.edit_button_box)
        icon = QtGui.QIcon.fromTheme(":/images/16x16/go-down.png")
        self.down_button.setIcon(icon)
        self.down_button.setObjectName("down_button")
        self.edit_box_layout.addWidget(self.down_button)
        self.remove_button = QtWidgets.QToolButton(parent=self.edit_button_box)
        self.remove_button.setObjectName("remove_button")
        self.edit_box_layout.addWidget(self.remove_button)
        self.verticalLayout.addWidget(self.edit_button_box)
        self.vboxlayout.addWidget(self.customize_toolbar_box)

        self.retranslateUi(InterfaceToolbarOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(InterfaceToolbarOptionsPage)
        InterfaceToolbarOptionsPage.setTabOrder(self.toolbar_layout_list, self.add_button)
        InterfaceToolbarOptionsPage.setTabOrder(self.add_button, self.insert_separator_button)
        InterfaceToolbarOptionsPage.setTabOrder(self.insert_separator_button, self.up_button)
        InterfaceToolbarOptionsPage.setTabOrder(self.up_button, self.down_button)
        InterfaceToolbarOptionsPage.setTabOrder(self.down_button, self.remove_button)

    def retranslateUi(self, InterfaceToolbarOptionsPage):
        self.customize_toolbar_box.setTitle(_("Customize Action Toolbar"))
        self.add_button.setToolTip(_("Add a new button to Toolbar"))
        self.add_button.setText(_("Add Action"))
        self.insert_separator_button.setToolTip(_("Insert a separator"))
        self.insert_separator_button.setText(_("Add Separator"))
        self.up_button.setToolTip(_("Move selected item up"))
        self.down_button.setToolTip(_("Move selected item down"))
        self.remove_button.setToolTip(_("Remove button from toolbar"))
        self.remove_button.setText(_("Remove"))
