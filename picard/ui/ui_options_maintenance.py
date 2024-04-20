# Form implementation generated from reading ui file 'ui/options_maintenance.ui'
#
# Created by: PyQt6 UI code generator 6.6.1
#
# Automatically generated - do not edit.
# Use `python setup.py build_ui` to update it.

from picard.i18n import _


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MaintenanceOptionsPage(object):
    def setupUi(self, MaintenanceOptionsPage):
        MaintenanceOptionsPage.setObjectName("MaintenanceOptionsPage")
        MaintenanceOptionsPage.resize(334, 397)
        self.vboxlayout = QtWidgets.QVBoxLayout(MaintenanceOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")
        self.label = QtWidgets.QLabel(parent=MaintenanceOptionsPage)
        self.label.setObjectName("label")
        self.vboxlayout.addWidget(self.label)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setContentsMargins(-1, -1, -1, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.config_file = QtWidgets.QLineEdit(parent=MaintenanceOptionsPage)
        self.config_file.setReadOnly(True)
        self.config_file.setObjectName("config_file")
        self.horizontalLayout_3.addWidget(self.config_file)
        self.open_folder_button = QtWidgets.QToolButton(parent=MaintenanceOptionsPage)
        self.open_folder_button.setObjectName("open_folder_button")
        self.horizontalLayout_3.addWidget(self.open_folder_button)
        self.vboxlayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(-1, -1, -1, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.load_backup_button = QtWidgets.QToolButton(parent=MaintenanceOptionsPage)
        self.load_backup_button.setObjectName("load_backup_button")
        self.horizontalLayout.addWidget(self.load_backup_button)
        self.save_backup_button = QtWidgets.QToolButton(parent=MaintenanceOptionsPage)
        self.save_backup_button.setObjectName("save_backup_button")
        self.horizontalLayout.addWidget(self.save_backup_button)
        self.vboxlayout.addLayout(self.horizontalLayout)
        self.option_counts = QtWidgets.QLabel(parent=MaintenanceOptionsPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.option_counts.sizePolicy().hasHeightForWidth())
        self.option_counts.setSizePolicy(sizePolicy)
        self.option_counts.setText("")
        self.option_counts.setObjectName("option_counts")
        self.vboxlayout.addWidget(self.option_counts)
        self.enable_cleanup = QtWidgets.QCheckBox(parent=MaintenanceOptionsPage)
        self.enable_cleanup.setObjectName("enable_cleanup")
        self.vboxlayout.addWidget(self.enable_cleanup)
        self.description = QtWidgets.QLabel(parent=MaintenanceOptionsPage)
        self.description.setText("")
        self.description.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeading|QtCore.Qt.AlignmentFlag.AlignLeft|QtCore.Qt.AlignmentFlag.AlignTop)
        self.description.setWordWrap(True)
        self.description.setIndent(0)
        self.description.setObjectName("description")
        self.vboxlayout.addWidget(self.description)
        spacerItem1 = QtWidgets.QSpacerItem(20, 8, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        self.vboxlayout.addItem(spacerItem1)
        self.line = QtWidgets.QFrame(parent=MaintenanceOptionsPage)
        self.line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line.setObjectName("line")
        self.vboxlayout.addWidget(self.line)
        self.select_all = QtWidgets.QCheckBox(parent=MaintenanceOptionsPage)
        self.select_all.setObjectName("select_all")
        self.vboxlayout.addWidget(self.select_all)
        self.tableWidget = QtWidgets.QTableWidget(parent=MaintenanceOptionsPage)
        self.tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
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
        self.load_backup_button.setText(_("Load Backup"))
        self.save_backup_button.setText(_("Save Backup"))
        self.enable_cleanup.setText(_("Remove selected options"))
        self.select_all.setText(_("Select all"))
