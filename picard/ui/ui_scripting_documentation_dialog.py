# Form implementation generated from reading ui file 'ui/scripting_documentation_dialog.ui'
#
# Created by: PyQt6 UI code generator 6.6.1
#
# Automatically generated - do not edit.
# Use `python setup.py build_ui` to update it.

from picard.i18n import _


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_ScriptingDocumentationDialog(object):
    def setupUi(self, ScriptingDocumentationDialog):
        ScriptingDocumentationDialog.setObjectName("ScriptingDocumentationDialog")
        ScriptingDocumentationDialog.resize(725, 457)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(ScriptingDocumentationDialog.sizePolicy().hasHeightForWidth())
        ScriptingDocumentationDialog.setSizePolicy(sizePolicy)
        ScriptingDocumentationDialog.setModal(False)
        self.verticalLayout = QtWidgets.QVBoxLayout(ScriptingDocumentationDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.documentation_layout = QtWidgets.QVBoxLayout()
        self.documentation_layout.setObjectName("documentation_layout")
        self.verticalLayout.addLayout(self.documentation_layout)
        self.buttonBox = QtWidgets.QDialogButtonBox(parent=ScriptingDocumentationDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Close)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(ScriptingDocumentationDialog)
        QtCore.QMetaObject.connectSlotsByName(ScriptingDocumentationDialog)

    def retranslateUi(self, ScriptingDocumentationDialog):
        _translate = QtCore.QCoreApplication.translate
        ScriptingDocumentationDialog.setWindowTitle(_("Scripting Documentation"))
