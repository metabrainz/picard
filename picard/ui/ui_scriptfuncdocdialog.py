# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ScriptFunctionsDocDialog(object):
    def setupUi(self, ScriptFunctionsDocDialog):
        ScriptFunctionsDocDialog.setObjectName("ScriptFunctionsDocDialog")
        ScriptFunctionsDocDialog.resize(667, 451)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(ScriptFunctionsDocDialog.sizePolicy().hasHeightForWidth())
        ScriptFunctionsDocDialog.setSizePolicy(sizePolicy)
        ScriptFunctionsDocDialog.setModal(False)
        self.gridLayout = QtWidgets.QGridLayout(ScriptFunctionsDocDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.buttonBox = QtWidgets.QDialogButtonBox(ScriptFunctionsDocDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 1, 1, 1, 1)
        self.textBrowser = QtWidgets.QTextBrowser(ScriptFunctionsDocDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.textBrowser.sizePolicy().hasHeightForWidth())
        self.textBrowser.setSizePolicy(sizePolicy)
        self.textBrowser.setOpenExternalLinks(True)
        self.textBrowser.setObjectName("textBrowser")
        self.gridLayout.addWidget(self.textBrowser, 0, 0, 1, 2)

        self.retranslateUi(ScriptFunctionsDocDialog)
        QtCore.QMetaObject.connectSlotsByName(ScriptFunctionsDocDialog)

    def retranslateUi(self, ScriptFunctionsDocDialog):
        _translate = QtCore.QCoreApplication.translate
        ScriptFunctionsDocDialog.setWindowTitle(_("Script Functions Documentation"))

