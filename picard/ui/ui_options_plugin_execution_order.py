# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_PluginExecutionOrderOptionsPage(object):
    def setupUi(self, PluginExecutionOrderOptionsPage):
        PluginExecutionOrderOptionsPage.setObjectName("PluginExecutionOrderOptionsPage")
        PluginExecutionOrderOptionsPage.resize(413, 612)
        self.vboxlayout = QtWidgets.QVBoxLayout(PluginExecutionOrderOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")
        self.label = QtWidgets.QLabel(PluginExecutionOrderOptionsPage)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.vboxlayout.addWidget(self.label)
        self.description = QtWidgets.QLabel(PluginExecutionOrderOptionsPage)
        self.description.setWordWrap(True)
        self.description.setObjectName("description")
        self.vboxlayout.addWidget(self.description)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.edit_plugin_order = QtWidgets.QPushButton(PluginExecutionOrderOptionsPage)
        self.edit_plugin_order.setObjectName("edit_plugin_order")
        self.horizontalLayout.addWidget(self.edit_plugin_order)
        self.vboxlayout.addLayout(self.horizontalLayout)
        spacerItem1 = QtWidgets.QSpacerItem(20, 41, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem1)

        self.retranslateUi(PluginExecutionOrderOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(PluginExecutionOrderOptionsPage)

    def retranslateUi(self, PluginExecutionOrderOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.label.setText(_("Plugin Execution Order"))
        self.description.setText(_("TextLabel"))
        self.edit_plugin_order.setText(_("Edit Execution Order…"))
