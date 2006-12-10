# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/advtageditor.ui'
#
# Created: Sun Dec 10 12:18:41 2006
#      by: PyQt4 UI code generator 4.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(QtCore.QSize(QtCore.QRect(0,0,453,388).size()).expandedTo(Dialog.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(Dialog)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.tabWidget = QtGui.QTabWidget(Dialog)
        self.tabWidget.setObjectName("tabWidget")

        self.tab = QtGui.QWidget()
        self.tab.setObjectName("tab")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.tab)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.tags = QtGui.QTreeWidget(self.tab)
        self.tags.setRootIsDecorated(False)
        self.tags.setObjectName("tags")
        self.vboxlayout1.addWidget(self.tags)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        self.artwork_add_2 = QtGui.QPushButton(self.tab)
        self.artwork_add_2.setObjectName("artwork_add_2")
        self.hboxlayout.addWidget(self.artwork_add_2)

        self.artwork_delete_2 = QtGui.QPushButton(self.tab)
        self.artwork_delete_2.setObjectName("artwork_delete_2")
        self.hboxlayout.addWidget(self.artwork_delete_2)

        spacerItem = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)
        self.vboxlayout1.addLayout(self.hboxlayout)
        self.tabWidget.addTab(self.tab, "")

        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName("tab_2")

        self.vboxlayout2 = QtGui.QVBoxLayout(self.tab_2)
        self.vboxlayout2.setMargin(9)
        self.vboxlayout2.setSpacing(6)
        self.vboxlayout2.setObjectName("vboxlayout2")

        self.artwork_list = QtGui.QListWidget(self.tab_2)
        self.artwork_list.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.artwork_list.setIconSize(QtCore.QSize(170,170))
        self.artwork_list.setMovement(QtGui.QListView.Static)
        self.artwork_list.setFlow(QtGui.QListView.LeftToRight)
        self.artwork_list.setWrapping(False)
        self.artwork_list.setResizeMode(QtGui.QListView.Fixed)
        self.artwork_list.setSpacing(10)
        self.artwork_list.setViewMode(QtGui.QListView.IconMode)
        self.artwork_list.setObjectName("artwork_list")
        self.vboxlayout2.addWidget(self.artwork_list)

        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setObjectName("hboxlayout1")

        self.artwork_add = QtGui.QPushButton(self.tab_2)
        self.artwork_add.setObjectName("artwork_add")
        self.hboxlayout1.addWidget(self.artwork_add)

        self.artwork_delete = QtGui.QPushButton(self.tab_2)
        self.artwork_delete.setObjectName("artwork_delete")
        self.hboxlayout1.addWidget(self.artwork_delete)

        spacerItem1 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout1.addItem(spacerItem1)
        self.vboxlayout2.addLayout(self.hboxlayout1)
        self.tabWidget.addTab(self.tab_2, "")

        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName("tab_3")

        self.vboxlayout3 = QtGui.QVBoxLayout(self.tab_3)
        self.vboxlayout3.setMargin(9)
        self.vboxlayout3.setSpacing(6)
        self.vboxlayout3.setObjectName("vboxlayout3")

        self.info = QtGui.QLabel(self.tab_3)
        self.info.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.info.setWordWrap(True)
        self.info.setObjectName("info")
        self.vboxlayout3.addWidget(self.info)
        self.tabWidget.addTab(self.tab_3, "")
        self.vboxlayout.addWidget(self.tabWidget)

        self.hboxlayout2 = QtGui.QHBoxLayout()
        self.hboxlayout2.setMargin(0)
        self.hboxlayout2.setSpacing(6)
        self.hboxlayout2.setObjectName("hboxlayout2")

        spacerItem2 = QtGui.QSpacerItem(131,31,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout2.addItem(spacerItem2)

        self.okButton = QtGui.QPushButton(Dialog)
        self.okButton.setObjectName("okButton")
        self.hboxlayout2.addWidget(self.okButton)

        self.cancelButton = QtGui.QPushButton(Dialog)
        self.cancelButton.setObjectName("cancelButton")
        self.hboxlayout2.addWidget(self.cancelButton)
        self.vboxlayout.addLayout(self.hboxlayout2)

        self.retranslateUi(Dialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.okButton,QtCore.SIGNAL("clicked()"),Dialog.accept)
        QtCore.QObject.connect(self.cancelButton,QtCore.SIGNAL("clicked()"),Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.artwork_list,self.artwork_add)
        Dialog.setTabOrder(self.artwork_add,self.artwork_delete)
        Dialog.setTabOrder(self.artwork_delete,self.okButton)
        Dialog.setTabOrder(self.okButton,self.cancelButton)
        Dialog.setTabOrder(self.cancelButton,self.tabWidget)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_(u"Tag Editor"))
        self.artwork_add_2.setText(_(u"&Add..."))
        self.artwork_delete_2.setText(_(u"Delete"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _(u"&Tags"))
        self.artwork_add.setText(_(u"&Add..."))
        self.artwork_delete.setText(_(u"Delete"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _(u"A&rtwork"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _(u"&Info"))
        self.okButton.setText(_(u"OK"))
        self.cancelButton.setText(_(u"Cancel"))
