# Form implementation generated from reading ui file 'ui/options_startup.ui'
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


class Ui_StartupOptionsPage(object):
    def setupUi(self, StartupOptionsPage):
        StartupOptionsPage.setObjectName("StartupOptionsPage")
        StartupOptionsPage.resize(403, 373)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(StartupOptionsPage.sizePolicy().hasHeightForWidth())
        StartupOptionsPage.setSizePolicy(sizePolicy)
        self.vboxlayout = QtWidgets.QVBoxLayout(StartupOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")
        self.update_check_group = QtWidgets.QGroupBox(parent=StartupOptionsPage)
        self.update_check_group.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.update_check_group.sizePolicy().hasHeightForWidth())
        self.update_check_group.setSizePolicy(sizePolicy)
        self.update_check_group.setObjectName("update_check_group")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.update_check_group)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.check_rtd_updates = QtWidgets.QCheckBox(parent=self.update_check_group)
        self.check_rtd_updates.setObjectName("check_rtd_updates")
        self.verticalLayout_2.addWidget(self.check_rtd_updates)
        self.check_plugin_updates = QtWidgets.QCheckBox(parent=self.update_check_group)
        self.check_plugin_updates.setObjectName("check_plugin_updates")
        self.verticalLayout_2.addWidget(self.check_plugin_updates)
        self.program_update_check_group = QtWidgets.QFrame(parent=self.update_check_group)
        self.program_update_check_group.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.program_update_check_group.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.program_update_check_group.setObjectName("program_update_check_group")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.program_update_check_group)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.check_for_updates = QtWidgets.QCheckBox(parent=self.program_update_check_group)
        self.check_for_updates.setObjectName("check_for_updates")
        self.verticalLayout.addWidget(self.check_for_updates)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(parent=self.program_update_check_group)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.update_check_days = QtWidgets.QSpinBox(parent=self.program_update_check_group)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.update_check_days.sizePolicy().hasHeightForWidth())
        self.update_check_days.setSizePolicy(sizePolicy)
        self.update_check_days.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeading
            | QtCore.Qt.AlignmentFlag.AlignLeft
            | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.update_check_days.setMinimum(1)
        self.update_check_days.setObjectName("update_check_days")
        self.horizontalLayout_2.addWidget(self.update_check_days)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.verticalLayout_2.addWidget(self.program_update_check_group)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_3 = QtWidgets.QLabel(parent=self.update_check_group)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_3.addWidget(self.label_3)
        self.update_level = QtWidgets.QComboBox(parent=self.update_check_group)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.update_level.sizePolicy().hasHeightForWidth())
        self.update_level.setSizePolicy(sizePolicy)
        self.update_level.setEditable(False)
        self.update_level.setObjectName("update_level")
        self.horizontalLayout_3.addWidget(self.update_level)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        self.vboxlayout.addWidget(self.update_check_group)
        self.groupBox_3 = QtWidgets.QGroupBox(parent=StartupOptionsPage)
        self.groupBox_3.setObjectName("groupBox_3")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.groupBox_3)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.log_verbosity_label = QtWidgets.QLabel(parent=self.groupBox_3)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.log_verbosity_label.sizePolicy().hasHeightForWidth())
        self.log_verbosity_label.setSizePolicy(sizePolicy)
        self.log_verbosity_label.setObjectName("log_verbosity_label")
        self.horizontalLayout_4.addWidget(self.log_verbosity_label)
        self.starting_log_level = QtWidgets.QComboBox(parent=self.groupBox_3)
        self.starting_log_level.setObjectName("starting_log_level")
        self.horizontalLayout_4.addWidget(self.starting_log_level)
        self.vboxlayout.addWidget(self.groupBox_3)
        spacerItem = QtWidgets.QSpacerItem(
            181, 21, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding
        )
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(StartupOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(StartupOptionsPage)
        StartupOptionsPage.setTabOrder(self.check_rtd_updates, self.check_plugin_updates)
        StartupOptionsPage.setTabOrder(self.check_plugin_updates, self.check_for_updates)
        StartupOptionsPage.setTabOrder(self.check_for_updates, self.update_check_days)
        StartupOptionsPage.setTabOrder(self.update_check_days, self.update_level)
        StartupOptionsPage.setTabOrder(self.update_level, self.starting_log_level)

    def retranslateUi(self, StartupOptionsPage):
        self.update_check_group.setTitle(_("Update Checking"))
        self.check_rtd_updates.setText(_("Check for documentation updates during startup"))
        self.check_plugin_updates.setText(_("Check for plugin updates during startup"))
        self.check_for_updates.setText(_("Check for program updates during startup"))
        self.label_2.setText(_("Days between checks:"))
        self.label_3.setText(_("Updates to check:"))
        self.groupBox_3.setTitle(_("Logging"))
        self.log_verbosity_label.setText(_("Default log level:"))
