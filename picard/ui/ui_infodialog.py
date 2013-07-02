# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/infodialog.ui'
#
# Created: Sat Jun 15 12:58:18 2013
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

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
        self.artwork_list = QtGui.QListWidget(self.artwork_tab)
        self.artwork_list.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.artwork_list.setIconSize(QtCore.QSize(170, 170))
        self.artwork_list.setMovement(QtGui.QListView.Static)
        self.artwork_list.setFlow(QtGui.QListView.LeftToRight)
        self.artwork_list.setProperty("isWrapping", False)
        self.artwork_list.setResizeMode(QtGui.QListView.Fixed)
        self.artwork_list.setSpacing(10)
        self.artwork_list.setViewMode(QtGui.QListView.IconMode)
        self.artwork_list.setObjectName(_fromUtf8("artwork_list"))
        self.vboxlayout1.addWidget(self.artwork_list)
        self.tabWidget.addTab(self.artwork_tab, _fromUtf8(""))
        self.verticalLayout.addWidget(self.tabWidget)
        self.buttonBox = QtGui.QDialogButtonBox(InfoDialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(InfoDialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(InfoDialog)
        InfoDialog.setTabOrder(self.tabWidget, self.artwork_list)
        InfoDialog.setTabOrder(self.artwork_list, self.buttonBox)

    def retranslateUi(self, InfoDialog):
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.info_tab), _("&Info"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.artwork_tab), _("A&rtwork"))

