# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_general.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_GeneralOptionsPage(object):
    def setupUi(self, GeneralOptionsPage):
        if not GeneralOptionsPage.objectName():
            GeneralOptionsPage.setObjectName(u"GeneralOptionsPage")
        GeneralOptionsPage.resize(403, 640)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(GeneralOptionsPage.sizePolicy().hasHeightForWidth())
        GeneralOptionsPage.setSizePolicy(sizePolicy)
        self.vboxLayout = QVBoxLayout(GeneralOptionsPage)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.groupBox = QGroupBox(GeneralOptionsPage)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout = QGridLayout(self.groupBox)
        self.gridLayout.setSpacing(2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.server_port = QSpinBox(self.groupBox)
        self.server_port.setObjectName(u"server_port")
        self.server_port.setMinimum(1)
        self.server_port.setMaximum(65535)
        self.server_port.setValue(80)

        self.gridLayout.addWidget(self.server_port, 1, 1, 1, 1)

        self.server_host_primary_warning = QFrame(self.groupBox)
        self.server_host_primary_warning.setObjectName(u"server_host_primary_warning")
        self.server_host_primary_warning.setStyleSheet(u"QFrame { background-color: #ffc107; color: black }\n"
"QCheckBox { color: black }")
        self.server_host_primary_warning.setFrameShape(QFrame.NoFrame)
        self.verticalLayout_4 = QVBoxLayout(self.server_host_primary_warning)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label_4 = QLabel(self.server_host_primary_warning)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setWordWrap(True)

        self.verticalLayout_4.addWidget(self.label_4)

        self.use_server_for_submission = QCheckBox(self.server_host_primary_warning)
        self.use_server_for_submission.setObjectName(u"use_server_for_submission")

        self.verticalLayout_4.addWidget(self.use_server_for_submission)


        self.gridLayout.addWidget(self.server_host_primary_warning, 3, 0, 1, 2)

        self.server_host = QComboBox(self.groupBox)
        self.server_host.setObjectName(u"server_host")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.server_host.sizePolicy().hasHeightForWidth())
        self.server_host.setSizePolicy(sizePolicy1)
        self.server_host.setEditable(True)

        self.gridLayout.addWidget(self.server_host, 1, 0, 1, 1)

        self.label_7 = QLabel(self.groupBox)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout.addWidget(self.label_7, 0, 1, 1, 1)

        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.spacer = QSpacerItem(1, 4, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout.addItem(self.spacer, 2, 0, 1, 1)


        self.vboxLayout.addWidget(self.groupBox)

        self.rename_files_2 = QGroupBox(GeneralOptionsPage)
        self.rename_files_2.setObjectName(u"rename_files_2")
        self.verticalLayout_3 = QVBoxLayout(self.rename_files_2)
        self.verticalLayout_3.setSpacing(2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.login_error = QLabel(self.rename_files_2)
        self.login_error.setObjectName(u"login_error")

        self.verticalLayout_3.addWidget(self.login_error)

        self.logged_in = QLabel(self.rename_files_2)
        self.logged_in.setObjectName(u"logged_in")

        self.verticalLayout_3.addWidget(self.logged_in)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.login = QPushButton(self.rename_files_2)
        self.login.setObjectName(u"login")

        self.horizontalLayout.addWidget(self.login)

        self.logout = QPushButton(self.rename_files_2)
        self.logout.setObjectName(u"logout")

        self.horizontalLayout.addWidget(self.logout)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout_3.addLayout(self.horizontalLayout)


        self.vboxLayout.addWidget(self.rename_files_2)

        self.groupBox_2 = QGroupBox(GeneralOptionsPage)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout = QVBoxLayout(self.groupBox_2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.analyze_new_files = QCheckBox(self.groupBox_2)
        self.analyze_new_files.setObjectName(u"analyze_new_files")

        self.verticalLayout.addWidget(self.analyze_new_files)

        self.cluster_new_files = QCheckBox(self.groupBox_2)
        self.cluster_new_files.setObjectName(u"cluster_new_files")

        self.verticalLayout.addWidget(self.cluster_new_files)

        self.ignore_file_mbids = QCheckBox(self.groupBox_2)
        self.ignore_file_mbids.setObjectName(u"ignore_file_mbids")

        self.verticalLayout.addWidget(self.ignore_file_mbids)


        self.vboxLayout.addWidget(self.groupBox_2)

        self.update_check_groupbox = QGroupBox(GeneralOptionsPage)
        self.update_check_groupbox.setObjectName(u"update_check_groupbox")
        self.update_check_groupbox.setEnabled(True)
        sizePolicy.setHeightForWidth(self.update_check_groupbox.sizePolicy().hasHeightForWidth())
        self.update_check_groupbox.setSizePolicy(sizePolicy)
        self.verticalLayout_2 = QVBoxLayout(self.update_check_groupbox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.check_for_plugin_updates = QCheckBox(self.update_check_groupbox)
        self.check_for_plugin_updates.setObjectName(u"check_for_plugin_updates")

        self.verticalLayout_2.addWidget(self.check_for_plugin_updates)

        self.program_update_check_group = QWidget(self.update_check_groupbox)
        self.program_update_check_group.setObjectName(u"program_update_check_group")
        self.program_update_check_group.setMinimumSize(QSize(0, 0))
        self.verticalLayout_6 = QVBoxLayout(self.program_update_check_group)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.check_for_updates = QCheckBox(self.program_update_check_group)
        self.check_for_updates.setObjectName(u"check_for_updates")

        self.verticalLayout_6.addWidget(self.check_for_updates)

        self.gridLayout1 = QGridLayout()
        self.gridLayout1.setObjectName(u"gridLayout1")
        self.gridLayout1.setContentsMargins(-1, -1, -1, 0)
        self.label_2 = QLabel(self.program_update_check_group)
        self.label_2.setObjectName(u"label_2")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy2)

        self.gridLayout1.addWidget(self.label_2, 0, 0, 1, 1)

        self.update_check_days = QSpinBox(self.program_update_check_group)
        self.update_check_days.setObjectName(u"update_check_days")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.update_check_days.sizePolicy().hasHeightForWidth())
        self.update_check_days.setSizePolicy(sizePolicy3)
        self.update_check_days.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.update_check_days.setMinimum(1)

        self.gridLayout1.addWidget(self.update_check_days, 0, 1, 1, 1)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(-1, -1, -1, 0)
        self.label_3 = QLabel(self.program_update_check_group)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_2.addWidget(self.label_3, 0, 0, 1, 1)

        self.update_level = QComboBox(self.program_update_check_group)
        self.update_level.setObjectName(u"update_level")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.update_level.sizePolicy().hasHeightForWidth())
        self.update_level.setSizePolicy(sizePolicy4)
        self.update_level.setEditable(False)

        self.gridLayout_2.addWidget(self.update_level, 0, 1, 1, 1)


        self.gridLayout1.addLayout(self.gridLayout_2, 1, 0, 1, 1)


        self.verticalLayout_6.addLayout(self.gridLayout1)


        self.verticalLayout_2.addWidget(self.program_update_check_group)

        self.program_update_check_frame = QFrame(self.update_check_groupbox)
        self.program_update_check_frame.setObjectName(u"program_update_check_frame")
        sizePolicy.setHeightForWidth(self.program_update_check_frame.sizePolicy().hasHeightForWidth())
        self.program_update_check_frame.setSizePolicy(sizePolicy)
        self.program_update_check_frame.setFrameShape(QFrame.NoFrame)
        self.program_update_check_frame.setFrameShadow(QFrame.Plain)
        self.verticalLayout_5 = QVBoxLayout(self.program_update_check_frame)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout_2.addWidget(self.program_update_check_frame)


        self.vboxLayout.addWidget(self.update_check_groupbox)

        self.spacerItem = QSpacerItem(181, 21, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vboxLayout.addItem(self.spacerItem)

        QWidget.setTabOrder(self.server_host, self.server_port)
        QWidget.setTabOrder(self.server_port, self.use_server_for_submission)
        QWidget.setTabOrder(self.use_server_for_submission, self.login)
        QWidget.setTabOrder(self.login, self.logout)
        QWidget.setTabOrder(self.logout, self.analyze_new_files)
        QWidget.setTabOrder(self.analyze_new_files, self.cluster_new_files)
        QWidget.setTabOrder(self.cluster_new_files, self.ignore_file_mbids)
        QWidget.setTabOrder(self.ignore_file_mbids, self.check_for_plugin_updates)
        QWidget.setTabOrder(self.check_for_plugin_updates, self.check_for_updates)
        QWidget.setTabOrder(self.check_for_updates, self.update_check_days)
        QWidget.setTabOrder(self.update_check_days, self.update_level)

        self.retranslateUi(GeneralOptionsPage)

        QMetaObject.connectSlotsByName(GeneralOptionsPage)
    # setupUi

    def retranslateUi(self, GeneralOptionsPage):
        self.groupBox.setTitle(_(u"MusicBrainz Server"))
        self.label_4.setText(_(u"You have configured an unofficial MusicBrainz server. By default submissions of releases, recordings and disc IDs will go to the primary database on musicbrainz.org."))
        self.use_server_for_submission.setText(_(u"Submit data to the configured server"))
        self.label_7.setText(_(u"Port:"))
        self.label.setText(_(u"Server address:"))
        self.rename_files_2.setTitle(_(u"MusicBrainz Account"))
        self.login_error.setText("")
        self.logged_in.setText("")
        self.login.setText(_(u"Log in"))
        self.logout.setText(_(u"Log out"))
        self.groupBox_2.setTitle(_(u"General"))
        self.analyze_new_files.setText(_(u"Automatically scan all new files"))
        self.cluster_new_files.setText(_(u"Automatically cluster all new files"))
        self.ignore_file_mbids.setText(_(u"Ignore MBIDs when loading new files"))
        self.update_check_groupbox.setTitle(_(u"Update Checking"))
        self.check_for_plugin_updates.setText(_(u"Check for plugin updates during startup"))
        self.check_for_updates.setText(_(u"Check for program updates during startup"))
        self.label_2.setText(_(u"Days between checks:"))
        self.label_3.setText(_(u"Updates to check:"))
        pass
    # retranslateUi

