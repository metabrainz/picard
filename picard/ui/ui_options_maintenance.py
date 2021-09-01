# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MaintenanceOptionsPage(object):
    def setupUi(self, MaintenanceOptionsPage):
        MaintenanceOptionsPage.setObjectName("MaintenanceOptionsPage")
        MaintenanceOptionsPage.resize(334, 397)
        self.vboxlayout = QtWidgets.QVBoxLayout(MaintenanceOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")
        self.description = QtWidgets.QLabel(MaintenanceOptionsPage)
        self.description.setText("")
        self.description.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.description.setWordWrap(True)
        self.description.setIndent(0)
        self.description.setObjectName("description")
        self.vboxlayout.addWidget(self.description)
        spacerItem = QtWidgets.QSpacerItem(20, 8, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.vboxlayout.addItem(spacerItem)
        self.line = QtWidgets.QFrame(MaintenanceOptionsPage)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.vboxlayout.addWidget(self.line)
        spacerItem1 = QtWidgets.QSpacerItem(20, 8, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.vboxlayout.addItem(spacerItem1)
        self.enable_cleanup = QtWidgets.QCheckBox(MaintenanceOptionsPage)
        self.enable_cleanup.setObjectName("enable_cleanup")
        self.vboxlayout.addWidget(self.enable_cleanup)
        self.select_all = QtWidgets.QCheckBox(MaintenanceOptionsPage)
        self.select_all.setObjectName("select_all")
        self.vboxlayout.addWidget(self.select_all)
        self.tableWidget = QtWidgets.QTableWidget(MaintenanceOptionsPage)
        self.tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setRowCount(0)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.verticalHeader().setVisible(False)
        self.vboxlayout.addWidget(self.tableWidget)

        self.retranslateUi(MaintenanceOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(MaintenanceOptionsPage)

    def retranslateUi(self, MaintenanceOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.enable_cleanup.setText(_("Remove selected options"))
        self.select_all.setText(_("Select all"))
