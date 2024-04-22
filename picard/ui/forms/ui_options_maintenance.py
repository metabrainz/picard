# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_maintenance.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## Use `python setup.py build_ui` to update it.
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QAbstractScrollArea, QApplication, QCheckBox,
    QFrame, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QSizePolicy, QSpacerItem, QTableWidget,
    QTableWidgetItem, QToolButton, QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_MaintenanceOptionsPage(object):
    def setupUi(self, MaintenanceOptionsPage):
        if not MaintenanceOptionsPage.objectName():
            MaintenanceOptionsPage.setObjectName(u"MaintenanceOptionsPage")
        MaintenanceOptionsPage.resize(334, 397)
        self.vboxLayout = QVBoxLayout(MaintenanceOptionsPage)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.label = QLabel(MaintenanceOptionsPage)
        self.label.setObjectName(u"label")

        self.vboxLayout.addWidget(self.label)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(-1, -1, -1, 0)
        self.config_file = QLineEdit(MaintenanceOptionsPage)
        self.config_file.setObjectName(u"config_file")
        self.config_file.setReadOnly(True)

        self.horizontalLayout_3.addWidget(self.config_file)

        self.open_folder_button = QToolButton(MaintenanceOptionsPage)
        self.open_folder_button.setObjectName(u"open_folder_button")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.open_folder_button.sizePolicy().hasHeightForWidth())
        self.open_folder_button.setSizePolicy(sizePolicy)

        self.horizontalLayout_3.addWidget(self.open_folder_button)


        self.vboxLayout.addLayout(self.horizontalLayout_3)

        self.label_2 = QLabel(MaintenanceOptionsPage)
        self.label_2.setObjectName(u"label_2")

        self.vboxLayout.addWidget(self.label_2)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.autobackup_dir = QLineEdit(MaintenanceOptionsPage)
        self.autobackup_dir.setObjectName(u"autobackup_dir")

        self.horizontalLayout_6.addWidget(self.autobackup_dir)

        self.browse_autobackup_dir = QToolButton(MaintenanceOptionsPage)
        self.browse_autobackup_dir.setObjectName(u"browse_autobackup_dir")
        sizePolicy.setHeightForWidth(self.browse_autobackup_dir.sizePolicy().hasHeightForWidth())
        self.browse_autobackup_dir.setSizePolicy(sizePolicy)

        self.horizontalLayout_6.addWidget(self.browse_autobackup_dir)


        self.vboxLayout.addLayout(self.horizontalLayout_6)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, -1, -1, 0)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.load_backup_button = QToolButton(MaintenanceOptionsPage)
        self.load_backup_button.setObjectName(u"load_backup_button")
        sizePolicy.setHeightForWidth(self.load_backup_button.sizePolicy().hasHeightForWidth())
        self.load_backup_button.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.load_backup_button)

        self.save_backup_button = QToolButton(MaintenanceOptionsPage)
        self.save_backup_button.setObjectName(u"save_backup_button")
        sizePolicy.setHeightForWidth(self.save_backup_button.sizePolicy().hasHeightForWidth())
        self.save_backup_button.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.save_backup_button)


        self.vboxLayout.addLayout(self.horizontalLayout)

        self.line_2 = QFrame(MaintenanceOptionsPage)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.vboxLayout.addWidget(self.line_2)

        self.option_counts = QLabel(MaintenanceOptionsPage)
        self.option_counts.setObjectName(u"option_counts")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.option_counts.sizePolicy().hasHeightForWidth())
        self.option_counts.setSizePolicy(sizePolicy1)

        self.vboxLayout.addWidget(self.option_counts)

        self.description = QLabel(MaintenanceOptionsPage)
        self.description.setObjectName(u"description")
        self.description.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.description.setWordWrap(True)
        self.description.setIndent(0)

        self.vboxLayout.addWidget(self.description)

        self.verticalSpacer_3 = QSpacerItem(20, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.vboxLayout.addItem(self.verticalSpacer_3)

        self.line = QFrame(MaintenanceOptionsPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.vboxLayout.addWidget(self.line)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(-1, 0, -1, -1)
        self.select_all = QCheckBox(MaintenanceOptionsPage)
        self.select_all.setObjectName(u"select_all")

        self.horizontalLayout_2.addWidget(self.select_all)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.enable_cleanup = QCheckBox(MaintenanceOptionsPage)
        self.enable_cleanup.setObjectName(u"enable_cleanup")

        self.horizontalLayout_2.addWidget(self.enable_cleanup)


        self.vboxLayout.addLayout(self.horizontalLayout_2)

        self.tableWidget = QTableWidget(MaintenanceOptionsPage)
        if (self.tableWidget.columnCount() < 2):
            self.tableWidget.setColumnCount(2)
        self.tableWidget.setObjectName(u"tableWidget")
        self.tableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.setColumnCount(2)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.verticalHeader().setVisible(False)

        self.vboxLayout.addWidget(self.tableWidget)

        QWidget.setTabOrder(self.config_file, self.open_folder_button)
        QWidget.setTabOrder(self.open_folder_button, self.autobackup_dir)
        QWidget.setTabOrder(self.autobackup_dir, self.browse_autobackup_dir)
        QWidget.setTabOrder(self.browse_autobackup_dir, self.load_backup_button)
        QWidget.setTabOrder(self.load_backup_button, self.save_backup_button)
        QWidget.setTabOrder(self.save_backup_button, self.select_all)
        QWidget.setTabOrder(self.select_all, self.enable_cleanup)
        QWidget.setTabOrder(self.enable_cleanup, self.tableWidget)

        self.retranslateUi(MaintenanceOptionsPage)

        QMetaObject.connectSlotsByName(MaintenanceOptionsPage)
    # setupUi

    def retranslateUi(self, MaintenanceOptionsPage):
        self.label.setText(_(u"Configuration file:"))
        self.open_folder_button.setText(_(u"Open folder\u2026"))
        self.label_2.setText(_(u"Automatic configuration backups directory:"))
        self.browse_autobackup_dir.setText(_(u"Browse\u2026"))
        self.load_backup_button.setText(_(u"Load backup\u2026"))
        self.save_backup_button.setText(_(u"Save backup\u2026"))
        self.option_counts.setText("")
        self.description.setText("")
        self.select_all.setText(_(u"Select all"))
        self.enable_cleanup.setText(_(u"Remove selected options"))
        pass
    # retranslateUi

