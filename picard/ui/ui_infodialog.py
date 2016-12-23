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

class Ui_InfoDialog(object):
    def setupUi(self, InfoDialog):
        InfoDialog.setObjectName(_fromUtf8("InfoDialog"))
        InfoDialog.resize(535, 436)
        self.verticalLayout = QtGui.QVBoxLayout(InfoDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tabWidget = QtGui.QTabWidget(InfoDialog)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.info_tab = QtGui.QWidget()
        self.info_tab.setObjectName(_fromUtf8("info_tab"))
        self.vboxlayout = QtGui.QVBoxLayout(self.info_tab)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.info_scroll = QtGui.QScrollArea(self.info_tab)
        self.info_scroll.setWidgetResizable(True)
        self.info_scroll.setObjectName(_fromUtf8("info_scroll"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setEnabled(True)
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 493, 334))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.verticalLayoutLabel = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayoutLabel.setObjectName(_fromUtf8("verticalLayoutLabel"))
        self.info = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.info.setText(_fromUtf8(""))
        self.info.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.info.setWordWrap(True)
        self.info.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.info.setObjectName(_fromUtf8("info"))
        self.verticalLayoutLabel.addWidget(self.info)
        self.info_scroll.setWidget(self.scrollAreaWidgetContents)
        self.vboxlayout.addWidget(self.info_scroll)
        self.tabWidget.addTab(self.info_tab, _fromUtf8(""))
        self.artwork_tab = QtGui.QWidget()
        self.artwork_tab.setObjectName(_fromUtf8("artwork_tab"))
        self.vboxlayout1 = QtGui.QVBoxLayout(self.artwork_tab)
        self.vboxlayout1.setObjectName(_fromUtf8("vboxlayout1"))
        self.tabWidget.addTab(self.artwork_tab, _fromUtf8(""))
        self.verticalLayout.addWidget(self.tabWidget)
        self.buttonBox = QtGui.QDialogButtonBox(InfoDialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(InfoDialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(InfoDialog)
        InfoDialog.setTabOrder(self.tabWidget, self.buttonBox)

    def retranslateUi(self, InfoDialog):
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.info_tab), _("&Info"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.artwork_tab), _("A&rtwork"))

