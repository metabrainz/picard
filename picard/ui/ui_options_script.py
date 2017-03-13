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
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.groupBox)
        self.verticalLayout_3.setMargin(0)
        self.verticalLayout_3.setSpacing(6)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.add_script = QtGui.QPushButton(self.groupBox)
        self.add_script.setObjectName(_fromUtf8("add_script"))
        self.horizontalLayout.addWidget(self.add_script)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.splitter = QtGui.QSplitter(self.groupBox)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.script_list = QtGui.QListWidget(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.script_list.sizePolicy().hasHeightForWidth())
        self.script_list.setSizePolicy(sizePolicy)
        self.script_list.setObjectName(_fromUtf8("script_list"))
        self.formWidget = QtGui.QWidget(self.splitter)
        self.formWidget.setObjectName(_fromUtf8("formWidget"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.formWidget)
        self.verticalLayout_2.setMargin(0)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.script_name = QtGui.QLineEdit(self.formWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.script_name.sizePolicy().hasHeightForWidth())
        self.script_name.setSizePolicy(sizePolicy)
        self.script_name.setObjectName(_fromUtf8("script_name"))
        self.verticalLayout_2.addWidget(self.script_name)
        self.tagger_script = QtGui.QTextEdit(self.formWidget)
        self.tagger_script.setObjectName(_fromUtf8("tagger_script"))
        self.verticalLayout_2.addWidget(self.tagger_script)
        self.verticalLayout_3.addWidget(self.splitter)
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
        self.add_script.setToolTip(_("Add new script"))
        self.add_script.setText(_("Add new script"))
        self.script_name.setPlaceholderText(_("Display Name"))

