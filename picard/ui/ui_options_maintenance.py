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
        self.label = QtWidgets.QLabel(MaintenanceOptionsPage)
        self.label.setObjectName("label")
        self.vboxlayout.addWidget(self.label)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(-1, -1, -1, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.config_file = QtWidgets.QLineEdit(MaintenanceOptionsPage)
        self.config_file.setReadOnly(True)
        self.config_file.setObjectName("config_file")
        self.horizontalLayout.addWidget(self.config_file)
        self.open_folder_button = QtWidgets.QToolButton(MaintenanceOptionsPage)
        self.open_folder_button.setObjectName("open_folder_button")
        self.horizontalLayout.addWidget(self.open_folder_button)
        self.vboxlayout.addLayout(self.horizontalLayout)
        self.option_counts = QtWidgets.QLabel(MaintenanceOptionsPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.option_counts.sizePolicy().hasHeightForWidth())
        self.option_counts.setSizePolicy(sizePolicy)
        self.option_counts.setText("")
        self.option_counts.setObjectName("option_counts")
        self.vboxlayout.addWidget(self.option_counts)
        self.enable_cleanup = QtWidgets.QCheckBox(MaintenanceOptionsPage)
        self.enable_cleanup.setObjectName("enable_cleanup")
        self.vboxlayout.addWidget(self.enable_cleanup)
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
        self.label.setText(_("Configuration File:"))
        self.open_folder_button.setText(_("Open folder"))
        self.enable_cleanup.setText(_("Remove selected options"))
        self.select_all.setText(_("Select all"))
