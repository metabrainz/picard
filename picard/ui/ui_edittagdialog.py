# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/edittagdialog.ui'
#
# Created: Fri Dec 16 23:07:11 2011
#      by: PyQt4 UI code generator 4.8.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_EditTagDialog(object):
    def setupUi(self, EditTagDialog):
        EditTagDialog.setObjectName(_fromUtf8("EditTagDialog"))
        EditTagDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        EditTagDialog.resize(436, 240)
        EditTagDialog.setFocusPolicy(QtCore.Qt.StrongFocus)
        EditTagDialog.setWindowTitle(_("Edit tag"))
        EditTagDialog.setModal(True)
        self.verticalLayout = QtGui.QVBoxLayout(EditTagDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.value_list = QtGui.QListWidget(EditTagDialog)
        self.value_list.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.value_list.setTabKeyNavigation(False)
        self.value_list.setProperty("showDropIndicator", False)
        self.value_list.setObjectName(_fromUtf8("value_list"))
        self.verticalLayout.addWidget(self.value_list)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.add_value = QtGui.QPushButton(EditTagDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(100)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.add_value.sizePolicy().hasHeightForWidth())
        self.add_value.setSizePolicy(sizePolicy)
        self.add_value.setMinimumSize(QtCore.QSize(100, 0))
        self.add_value.setText(_("Add value"))
        self.add_value.setAutoDefault(False)
        self.add_value.setObjectName(_fromUtf8("add_value"))
        self.horizontalLayout.addWidget(self.add_value)
        self.remove_value = QtGui.QPushButton(EditTagDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(120)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.remove_value.sizePolicy().hasHeightForWidth())
        self.remove_value.setSizePolicy(sizePolicy)
        self.remove_value.setMinimumSize(QtCore.QSize(120, 0))
        self.remove_value.setText(_("Remove value"))
        self.remove_value.setAutoDefault(False)
        self.remove_value.setObjectName(_fromUtf8("remove_value"))
        self.horizontalLayout.addWidget(self.remove_value)
        spacerItem = QtGui.QSpacerItem(33, 17, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.buttonbox = QtGui.QDialogButtonBox(EditTagDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(150)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonbox.sizePolicy().hasHeightForWidth())
        self.buttonbox.setSizePolicy(sizePolicy)
        self.buttonbox.setMinimumSize(QtCore.QSize(150, 0))
        self.buttonbox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonbox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Save)
        self.buttonbox.setObjectName(_fromUtf8("buttonbox"))
        self.horizontalLayout.addWidget(self.buttonbox)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(EditTagDialog)
        QtCore.QObject.connect(self.buttonbox, QtCore.SIGNAL(_fromUtf8("accepted()")), EditTagDialog.accept)
        QtCore.QObject.connect(self.buttonbox, QtCore.SIGNAL(_fromUtf8("rejected()")), EditTagDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(EditTagDialog)

    def retranslateUi(self, EditTagDialog):
        pass

