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
        self.script_tools = QtGui.QGroupBox(self.enable_tagger_scripts)
        self.script_tools.setTitle(_fromUtf8(""))
        self.script_tools.setObjectName(_fromUtf8("script_tools"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.script_tools)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.add_script = QtGui.QToolButton(self.script_tools)
        self.add_script.setAutoRaise(False)
        self.add_script.setObjectName(_fromUtf8("add_script"))
        self.horizontalLayout.addWidget(self.add_script, QtCore.Qt.AlignLeft)
        self.remove_script = QtGui.QToolButton(self.script_tools)
        self.remove_script.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.remove_script.setAutoRaise(False)
        self.remove_script.setObjectName(_fromUtf8("remove_script"))
        self.horizontalLayout.addWidget(self.remove_script)
        self.up_script = QtGui.QToolButton(self.script_tools)
        self.up_script.setArrowType(QtCore.Qt.UpArrow)
        self.up_script.setObjectName(_fromUtf8("up_script"))
        self.horizontalLayout.addWidget(self.up_script, QtCore.Qt.AlignLeft)
        self.down_script = QtGui.QToolButton(self.script_tools)
        self.down_script.setArrowType(QtCore.Qt.DownArrow)
        self.down_script.setObjectName(_fromUtf8("down_script"))
        self.horizontalLayout.addWidget(self.down_script, QtCore.Qt.AlignLeft)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addWidget(self.script_tools)
        self.groupBox = QtGui.QGroupBox(self.enable_tagger_scripts)
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
        self.gridLayout.addWidget(self.script_list, 0, 0, 1, 1)
        self.tagger_script = QtGui.QTextEdit(self.groupBox)
        self.tagger_script.setObjectName(_fromUtf8("tagger_script"))
        self.gridLayout.addWidget(self.tagger_script, 0, 1, 1, 1)
        self.verticalLayout.addWidget(self.groupBox)
        self.script_error = QtGui.QLabel(self.enable_tagger_scripts)
        self.script_error.setText(_fromUtf8(""))
        self.script_error.setAlignment(QtCore.Qt.AlignCenter)
        self.script_error.setObjectName(_fromUtf8("script_error"))
        self.verticalLayout.addWidget(self.script_error)
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

