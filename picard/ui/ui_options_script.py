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
        self.script_error = QtGui.QLabel(self.enable_tagger_scripts)
        self.script_error.setText(_fromUtf8(""))
        self.script_error.setAlignment(QtCore.Qt.AlignCenter)
        self.script_error.setObjectName(_fromUtf8("script_error"))
        self.verticalLayout.addWidget(self.script_error)
        self.script_list = QtGui.QListWidget(self.enable_tagger_scripts)
        self.script_list.setObjectName(_fromUtf8("script_list"))
        self.verticalLayout.addWidget(self.script_list)
        self.tagger_script = QtGui.QTextEdit(self.enable_tagger_scripts)
        self.tagger_script.setObjectName(_fromUtf8("tagger_script"))
        self.verticalLayout.addWidget(self.tagger_script)
        self.script_tools = QtGui.QGroupBox(self.enable_tagger_scripts)
        self.script_tools.setTitle(_fromUtf8(""))
        self.script_tools.setObjectName(_fromUtf8("script_tools"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.script_tools)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.add_script = QtGui.QToolButton(self.script_tools)
        icon = QtGui.QIcon.fromTheme(_fromUtf8("add"))
        self.add_script.setIcon(icon)
        self.add_script.setObjectName(_fromUtf8("add_script"))
        self.horizontalLayout.addWidget(self.add_script, QtCore.Qt.AlignLeft)
        self.remove_script = QtGui.QToolButton(self.script_tools)
        icon = QtGui.QIcon.fromTheme(_fromUtf8("remove"))
        self.remove_script.setIcon(icon)
        self.remove_script.setObjectName(_fromUtf8("remove_script"))
        self.horizontalLayout.addWidget(self.remove_script)
        self.up_script = QtGui.QToolButton(self.script_tools)
        icon = QtGui.QIcon.fromTheme(_fromUtf8("up"))
        self.up_script.setIcon(icon)
        self.up_script.setObjectName(_fromUtf8("up_script"))
        self.horizontalLayout.addWidget(self.up_script, QtCore.Qt.AlignLeft)
        self.down_script = QtGui.QToolButton(self.script_tools)
        icon = QtGui.QIcon.fromTheme(_fromUtf8("down"))
        self.down_script.setIcon(icon)
        self.down_script.setObjectName(_fromUtf8("down_script"))
        self.horizontalLayout.addWidget(self.down_script, QtCore.Qt.AlignLeft)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addWidget(self.script_tools)
        self.vboxlayout.addWidget(self.enable_tagger_scripts)
        self.scripting_doc_link = QtGui.QLabel(ScriptingOptionsPage)
        self.scripting_doc_link.setText(_fromUtf8(""))
        self.scripting_doc_link.setWordWrap(True)
        self.scripting_doc_link.setOpenExternalLinks(True)
        self.scripting_doc_link.setObjectName(_fromUtf8("scripting_doc_link"))
        self.vboxlayout.addWidget(self.scripting_doc_link)

        self.retranslateUi(ScriptingOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(ScriptingOptionsPage)

    def retranslateUi(self, ScriptingOptionsPage):
        self.enable_tagger_scripts.setTitle(_("Tagger Script(s)"))
        self.add_script.setToolTip(_("Add script"))
        self.add_script.setText(_("..."))
        self.remove_script.setToolTip(_("Remove script"))
        self.remove_script.setText(_("..."))
        self.up_script.setToolTip(_("Move script up"))
        self.up_script.setText(_("..."))
        self.down_script.setToolTip(_("Move script down"))
        self.down_script.setText(_("..."))

