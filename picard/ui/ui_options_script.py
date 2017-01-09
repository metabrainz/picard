# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_ScriptingOptionsPage(object):
    def setupUi(self, ScriptingOptionsPage):
        ScriptingOptionsPage.setObjectName(_fromUtf8("ScriptingOptionsPage"))
        ScriptingOptionsPage.resize(605, 377)
        self.vboxlayout = QtGui.QVBoxLayout(ScriptingOptionsPage)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.enable_tagger_scripts = QtGui.QGroupBox(ScriptingOptionsPage)
        self.enable_tagger_scripts.setCheckable(True)
        self.enable_tagger_scripts.setObjectName(_fromUtf8("enable_tagger_scripts"))
        self.verticalLayout = QtGui.QVBoxLayout(self.enable_tagger_scripts)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.groupBox = QtGui.QGroupBox(self.enable_tagger_scripts)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setTitle(_fromUtf8(""))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.script_list = QtGui.QListWidget(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.script_list.sizePolicy().hasHeightForWidth())
        self.script_list.setSizePolicy(sizePolicy)
        self.script_list.setObjectName(_fromUtf8("script_list"))
        self.gridLayout.addWidget(self.script_list, 2, 2, 3, 1)
        self.tagger_script = QtGui.QTextEdit(self.groupBox)
        self.tagger_script.setObjectName(_fromUtf8("tagger_script"))
        self.gridLayout.addWidget(self.tagger_script, 3, 4, 2, 2)
        self.add_script = QtGui.QToolButton(self.groupBox)
        self.add_script.setAutoRaise(False)
        self.add_script.setObjectName(_fromUtf8("add_script"))
        self.gridLayout.addWidget(self.add_script, 0, 2, 1, 1)
        self.lineEdit = QtGui.QLineEdit(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit.sizePolicy().hasHeightForWidth())
        self.lineEdit.setSizePolicy(sizePolicy)
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
        self.gridLayout.addWidget(self.lineEdit, 2, 4, 1, 2)
        self.verticalLayout.addWidget(self.groupBox)
        self.script_error = QtGui.QLabel(self.enable_tagger_scripts)
        self.script_error.setText(_fromUtf8(""))
        self.script_error.setAlignment(QtCore.Qt.AlignCenter)
        self.script_error.setObjectName(_fromUtf8("script_error"))
        self.verticalLayout.addWidget(self.script_error)
        self.scripting_doc_link = QtGui.QLabel(self.enable_tagger_scripts)
        self.scripting_doc_link.setText(_fromUtf8(""))
        self.scripting_doc_link.setWordWrap(True)
        self.scripting_doc_link.setOpenExternalLinks(True)
        self.scripting_doc_link.setObjectName(_fromUtf8("scripting_doc_link"))
        self.verticalLayout.addWidget(self.scripting_doc_link)
        self.vboxlayout.addWidget(self.enable_tagger_scripts)

        self.retranslateUi(ScriptingOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(ScriptingOptionsPage)

    def retranslateUi(self, ScriptingOptionsPage):
        self.enable_tagger_scripts.setTitle(_("Tagger Script(s)"))
        self.add_script.setToolTip(_("Add script"))
        self.add_script.setText(_("..."))

