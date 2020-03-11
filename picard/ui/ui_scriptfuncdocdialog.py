# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ScriptFunctionsDocDialog(object):
    def setupUi(self, ScriptFunctionsDocDialog):
        ScriptFunctionsDocDialog.setObjectName("ScriptFunctionsDocDialog")
        ScriptFunctionsDocDialog.resize(725, 457)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(ScriptFunctionsDocDialog.sizePolicy().hasHeightForWidth())
        ScriptFunctionsDocDialog.setSizePolicy(sizePolicy)
        ScriptFunctionsDocDialog.setModal(False)
        self.gridLayout = QtWidgets.QGridLayout(ScriptFunctionsDocDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.textBrowser = QtWidgets.QTextBrowser(ScriptFunctionsDocDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.textBrowser.sizePolicy().hasHeightForWidth())
        self.textBrowser.setSizePolicy(sizePolicy)
        self.textBrowser.setOpenExternalLinks(True)
        self.textBrowser.setObjectName("textBrowser")
        self.gridLayout.addWidget(self.textBrowser, 0, 0, 1, 2)
        self.scripting_doc_link = QtWidgets.QLabel(ScriptFunctionsDocDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scripting_doc_link.sizePolicy().hasHeightForWidth())
        self.scripting_doc_link.setSizePolicy(sizePolicy)
        self.scripting_doc_link.setWordWrap(True)
        self.scripting_doc_link.setOpenExternalLinks(True)
        self.scripting_doc_link.setObjectName("scripting_doc_link")
        self.gridLayout.addWidget(self.scripting_doc_link, 1, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(ScriptFunctionsDocDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 1, 1, 1, 1)

        self.retranslateUi(ScriptFunctionsDocDialog)
        QtCore.QMetaObject.connectSlotsByName(ScriptFunctionsDocDialog)

    def retranslateUi(self, ScriptFunctionsDocDialog):
        _translate = QtCore.QCoreApplication.translate
        ScriptFunctionsDocDialog.setWindowTitle(_("Script Functions Documentation"))
        self.scripting_doc_link.setText(_("Open documentation in browser"))

