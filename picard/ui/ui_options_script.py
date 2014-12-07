# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ScriptingOptionsPage(object):
    def setupUi(self, ScriptingOptionsPage):
        ScriptingOptionsPage.setObjectName("ScriptingOptionsPage")
        ScriptingOptionsPage.resize(605, 377)
        self.vboxlayout = QtWidgets.QVBoxLayout(ScriptingOptionsPage)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.enable_tagger_script = QtWidgets.QGroupBox(ScriptingOptionsPage)
        self.enable_tagger_script.setCheckable(True)
        self.enable_tagger_script.setObjectName("enable_tagger_script")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.enable_tagger_script)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tagger_script = QtWidgets.QTextEdit(self.enable_tagger_script)
        font = QtGui.QFont()
        font.setFamily("Monospace")
        self.tagger_script.setFont(font)
        self.tagger_script.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.tagger_script.setAcceptRichText(False)
        self.tagger_script.setObjectName("tagger_script")
        self.verticalLayout.addWidget(self.tagger_script)
        self.script_error = QtWidgets.QLabel(self.enable_tagger_script)
        self.script_error.setText("")
        self.script_error.setAlignment(QtCore.Qt.AlignCenter)
        self.script_error.setObjectName("script_error")
        self.verticalLayout.addWidget(self.script_error)
        self.vboxlayout.addWidget(self.enable_tagger_script)
        self.scripting_doc_link = QtWidgets.QLabel(ScriptingOptionsPage)
        self.scripting_doc_link.setText("")
        self.scripting_doc_link.setWordWrap(True)
        self.scripting_doc_link.setOpenExternalLinks(True)
        self.scripting_doc_link.setObjectName("scripting_doc_link")
        self.vboxlayout.addWidget(self.scripting_doc_link)

        self.retranslateUi(ScriptingOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(ScriptingOptionsPage)

    def retranslateUi(self, ScriptingOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.enable_tagger_script.setTitle(_("Tagger Script"))

