# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ScriptItem(object):
    def setupUi(self, ScriptItem):
        ScriptItem.setObjectName("ScriptItem")
        ScriptItem.resize(120, 20)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(ScriptItem)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.checkbox = QtWidgets.QCheckBox(ScriptItem)
        self.checkbox.setMinimumSize(QtCore.QSize(22, 0))
        self.checkbox.setStyleSheet("QCheckBox { border-width: 0px; margin-left: 3px; }")
        self.checkbox.setText("")
        self.checkbox.setObjectName("checkbox")
        self.horizontalLayout_2.addWidget(self.checkbox)
        self.name_label = ElidedLabel(ScriptItem)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.name_label.sizePolicy().hasHeightForWidth())
        self.name_label.setSizePolicy(sizePolicy)
        self.name_label.setMinimumSize(QtCore.QSize(30, 0))
        self.name_label.setText("")
        self.name_label.setObjectName("name_label")
        self.horizontalLayout_2.addWidget(self.name_label)
        self.up_button = QtWidgets.QToolButton(ScriptItem)
        self.up_button.setMaximumSize(QtCore.QSize(16, 16))
        self.up_button.setArrowType(QtCore.Qt.UpArrow)
        self.up_button.setObjectName("up_button")
        self.horizontalLayout_2.addWidget(self.up_button)
        self.down_button = QtWidgets.QToolButton(ScriptItem)
        self.down_button.setMaximumSize(QtCore.QSize(16, 16))
        self.down_button.setArrowType(QtCore.Qt.DownArrow)
        self.down_button.setObjectName("down_button")
        self.horizontalLayout_2.addWidget(self.down_button)
        self.other_button = QtWidgets.QToolButton(ScriptItem)
        self.other_button.setMaximumSize(QtCore.QSize(16, 16))
        self.other_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        self.other_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.other_button.setAutoRaise(True)
        self.other_button.setObjectName("other_button")
        self.horizontalLayout_2.addWidget(self.other_button)

        self.retranslateUi(ScriptItem)
        QtCore.QMetaObject.connectSlotsByName(ScriptItem)

    def retranslateUi(self, ScriptItem):
        _translate = QtCore.QCoreApplication.translate
        self.checkbox.setAccessibleDescription(_("Enable this script"))
        self.up_button.setToolTip(_("Move script up"))
        self.up_button.setText(_("..."))
        self.down_button.setToolTip(_("Move script down"))
        self.down_button.setText(_("..."))
        self.other_button.setToolTip(_("Other options"))
        self.other_button.setText(_("..."))
from picard.ui.widgets import ElidedLabel
