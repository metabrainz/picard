# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_script.ui'
#
# Created: Fri Apr  4 14:52:10 2014
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

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
        font.setFamily(_fromUtf8("Courier"))
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

