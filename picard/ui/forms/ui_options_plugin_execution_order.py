# Form implementation generated from reading ui file 'ui/options_plugin_execution_order.ui'
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


class Ui_PluginExecutionOrderOptionsPage(object):
    def setupUi(self, PluginExecutionOrderOptionsPage):
        PluginExecutionOrderOptionsPage.setObjectName("PluginExecutionOrderOptionsPage")
        PluginExecutionOrderOptionsPage.resize(413, 612)
        self.vboxlayout = QtWidgets.QVBoxLayout(PluginExecutionOrderOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")
        self.page_header_label = QtWidgets.QLabel(parent=PluginExecutionOrderOptionsPage)
        font = QtGui.QFont()
        font.setBold(True)
        self.page_header_label.setFont(font)
        self.page_header_label.setObjectName("page_header_label")
        self.vboxlayout.addWidget(self.page_header_label)
        self.description = QtWidgets.QLabel(parent=PluginExecutionOrderOptionsPage)
        self.description.setWordWrap(True)
        self.description.setObjectName("description")
        self.vboxlayout.addWidget(self.description)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.edit_plugin_order = QtWidgets.QPushButton(parent=PluginExecutionOrderOptionsPage)
        self.edit_plugin_order.setObjectName("edit_plugin_order")
        self.horizontalLayout.addWidget(self.edit_plugin_order)
        self.vboxlayout.addLayout(self.horizontalLayout)
        spacerItem1 = QtWidgets.QSpacerItem(20, 41, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.vboxlayout.addItem(spacerItem1)

        self.retranslateUi(PluginExecutionOrderOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(PluginExecutionOrderOptionsPage)

    def retranslateUi(self, PluginExecutionOrderOptionsPage):
        self.page_header_label.setText(_("Plugin Execution Order"))
        self.description.setText(_("TextLabel"))
        self.edit_plugin_order.setText(_("Edit Execution Order…"))
