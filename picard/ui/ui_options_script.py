# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_script.ui'
#
# Created: Tue May 29 19:44:14 2012
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_ScriptingOptionsPage(object):
    def setupUi(self, ScriptingOptionsPage):
        ScriptingOptionsPage.setObjectName(_fromUtf8("ScriptingOptionsPage"))
        ScriptingOptionsPage.resize(605, 377)
        self.vboxlayout = QtGui.QVBoxLayout(ScriptingOptionsPage)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.enable_tagger_script = QtGui.QGroupBox(ScriptingOptionsPage)
        self.enable_tagger_script.setCheckable(True)
        self.enable_tagger_script.setObjectName(_fromUtf8("enable_tagger_script"))
        self.verticalLayout = QtGui.QVBoxLayout(self.enable_tagger_script)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tagger_script = QtGui.QTextEdit(self.enable_tagger_script)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Monospace"))
        self.tagger_script.setFont(font)
        self.tagger_script.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self.tagger_script.setAcceptRichText(False)
        self.tagger_script.setObjectName(_fromUtf8("tagger_script"))
        self.verticalLayout.addWidget(self.tagger_script)
        self.script_error = QtGui.QLabel(self.enable_tagger_script)
        self.script_error.setText(_fromUtf8(""))
        self.script_error.setAlignment(QtCore.Qt.AlignCenter)
        self.script_error.setObjectName(_fromUtf8("script_error"))
        self.verticalLayout.addWidget(self.script_error)
        self.vboxlayout.addWidget(self.enable_tagger_script)

        self.retranslateUi(ScriptingOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(ScriptingOptionsPage)

    def retranslateUi(self, ScriptingOptionsPage):
        self.enable_tagger_script.setTitle(_("Tagger Script"))

