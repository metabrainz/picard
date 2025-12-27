# Form implementation generated from reading ui file 'ui/options.ui'
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


class Ui_OptionsDialog(object):
    def setupUi(self, OptionsDialog):
        OptionsDialog.setObjectName("OptionsDialog")
        OptionsDialog.resize(800, 450)
        self.vboxlayout = QtWidgets.QVBoxLayout(OptionsDialog)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.dialog_splitter = QtWidgets.QSplitter(parent=OptionsDialog)
        self.dialog_splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.dialog_splitter.setChildrenCollapsible(False)
        self.dialog_splitter.setObjectName("dialog_splitter")
        self.pages_tree = QtWidgets.QTreeWidget(parent=self.dialog_splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pages_tree.sizePolicy().hasHeightForWidth())
        self.pages_tree.setSizePolicy(sizePolicy)
        self.pages_tree.setMinimumSize(QtCore.QSize(140, 0))
        self.pages_tree.setObjectName("pages_tree")
        self.frame = QtWidgets.QFrame(parent=self.dialog_splitter)
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.frame.setLineWidth(0)
        self.frame.setObjectName("frame")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.pages_stack = QtWidgets.QStackedWidget(parent=self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pages_stack.sizePolicy().hasHeightForWidth())
        self.pages_stack.setSizePolicy(sizePolicy)
        self.pages_stack.setMinimumSize(QtCore.QSize(280, 0))
        self.pages_stack.setObjectName("pages_stack")
        self.verticalLayout_2.addWidget(self.pages_stack)
        self.profile_warning = QtWidgets.QFrame(parent=self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.profile_warning.sizePolicy().hasHeightForWidth())
        self.profile_warning.setSizePolicy(sizePolicy)
        self.profile_warning.setObjectName("profile_warning")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.profile_warning)
        self.horizontalLayout.setContentsMargins(-1, 10, -1, -1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_2.addWidget(self.profile_warning)
        self.vboxlayout.addWidget(self.dialog_splitter)
        self.buttonbox = QtWidgets.QDialogButtonBox(parent=OptionsDialog)
        self.buttonbox.setMinimumSize(QtCore.QSize(0, 0))
        self.buttonbox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonbox.setObjectName("buttonbox")
        self.vboxlayout.addWidget(self.buttonbox)

        self.retranslateUi(OptionsDialog)
        QtCore.QMetaObject.connectSlotsByName(OptionsDialog)

    def retranslateUi(self, OptionsDialog):
        OptionsDialog.setWindowTitle(_("Options"))
