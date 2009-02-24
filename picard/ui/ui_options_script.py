# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_script.ui'
#
# Created: Tue Feb 24 22:56:42 2009
#      by: PyQt4 UI code generator 4.4.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_ScriptingOptionsPage(object):
    def setupUi(self, ScriptingOptionsPage):
        ScriptingOptionsPage.setObjectName("ScriptingOptionsPage")
        ScriptingOptionsPage.resize(605, 377)
        self.vboxlayout = QtGui.QVBoxLayout(ScriptingOptionsPage)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setObjectName("vboxlayout")
        self.enable_tagger_script = QtGui.QGroupBox(ScriptingOptionsPage)
        self.enable_tagger_script.setCheckable(True)
        self.enable_tagger_script.setObjectName("enable_tagger_script")
        self.verticalLayout = QtGui.QVBoxLayout(self.enable_tagger_script)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tagger_script = QtGui.QTextEdit(self.enable_tagger_script)
        font = QtGui.QFont()
        font.setFamily("Monospace")
        self.tagger_script.setFont(font)
        self.tagger_script.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self.tagger_script.setAcceptRichText(False)
        self.tagger_script.setObjectName("tagger_script")
        self.verticalLayout.addWidget(self.tagger_script)
        self.script_error = QtGui.QLabel(self.enable_tagger_script)
        self.script_error.setAlignment(QtCore.Qt.AlignCenter)
        self.script_error.setObjectName("script_error")
        self.verticalLayout.addWidget(self.script_error)
        self.vboxlayout.addWidget(self.enable_tagger_script)

        self.retranslateUi(ScriptingOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(ScriptingOptionsPage)

    def retranslateUi(self, ScriptingOptionsPage):
        self.enable_tagger_script.setTitle(_("Tagger Script"))

