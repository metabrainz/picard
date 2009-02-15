# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/tageditor.ui'
#
# Created: Sun Feb 15 17:17:13 2009
#      by: PyQt4 UI code generator 4.3.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_TagEditorDialog(object):
    def setupUi(self, TagEditorDialog):
        TagEditorDialog.setObjectName("TagEditorDialog")
        TagEditorDialog.resize(QtCore.QSize(QtCore.QRect(0,0,535,436).size()).expandedTo(TagEditorDialog.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(TagEditorDialog)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setObjectName("vboxlayout")

        self.tabWidget = QtGui.QTabWidget(TagEditorDialog)
        self.tabWidget.setObjectName("tabWidget")

        self.tab_4 = QtGui.QWidget()
        self.tab_4.setObjectName("tab_4")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.tab_4)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.tags = QtGui.QTreeWidget(self.tab_4)
        self.tags.setRootIsDecorated(False)
        self.tags.setObjectName("tags")
        self.vboxlayout1.addWidget(self.tags)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setObjectName("hboxlayout")

        self.ratingLabel = QtGui.QLabel(self.tab_4)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ratingLabel.sizePolicy().hasHeightForWidth())
        self.ratingLabel.setSizePolicy(sizePolicy)
        self.ratingLabel.setMinimumSize(QtCore.QSize(0,0))
        self.ratingLabel.setObjectName("ratingLabel")
        self.hboxlayout.addWidget(self.ratingLabel)

        self.rating = RatingWidget(self.tab_4)
        self.rating.setEnabled(True)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.rating.sizePolicy().hasHeightForWidth())
        self.rating.setSizePolicy(sizePolicy)
        self.rating.setMinimumSize(QtCore.QSize(0,0))
        self.rating.setObjectName("rating")
        self.hboxlayout.addWidget(self.rating)
        self.vboxlayout1.addLayout(self.hboxlayout)

        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setObjectName("hboxlayout1")

        self.tags_add = QtGui.QPushButton(self.tab_4)
        self.tags_add.setObjectName("tags_add")
        self.hboxlayout1.addWidget(self.tags_add)

        self.tags_edit = QtGui.QPushButton(self.tab_4)
        self.tags_edit.setObjectName("tags_edit")
        self.hboxlayout1.addWidget(self.tags_edit)

        self.tags_delete = QtGui.QPushButton(self.tab_4)
        self.tags_delete.setObjectName("tags_delete")
        self.hboxlayout1.addWidget(self.tags_delete)

        spacerItem = QtGui.QSpacerItem(151,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout1.addItem(spacerItem)
        self.vboxlayout1.addLayout(self.hboxlayout1)
        self.tabWidget.addTab(self.tab_4,"")

        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName("tab_2")

        self.vboxlayout2 = QtGui.QVBoxLayout(self.tab_2)
        self.vboxlayout2.setSpacing(6)
        self.vboxlayout2.setMargin(9)
        self.vboxlayout2.setObjectName("vboxlayout2")

        self.artwork_list = QtGui.QListWidget(self.tab_2)
        self.artwork_list.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.artwork_list.setIconSize(QtCore.QSize(170,170))
        self.artwork_list.setMovement(QtGui.QListView.Static)
        self.artwork_list.setFlow(QtGui.QListView.LeftToRight)
        self.artwork_list.setProperty("isWrapping",QtCore.QVariant(False))
        self.artwork_list.setResizeMode(QtGui.QListView.Fixed)
        self.artwork_list.setSpacing(10)
        self.artwork_list.setViewMode(QtGui.QListView.IconMode)
        self.artwork_list.setObjectName("artwork_list")
        self.vboxlayout2.addWidget(self.artwork_list)
        self.tabWidget.addTab(self.tab_2,"")

        self.tab_5 = QtGui.QWidget()
        self.tab_5.setObjectName("tab_5")

        self.vboxlayout3 = QtGui.QVBoxLayout(self.tab_5)
        self.vboxlayout3.setSpacing(6)
        self.vboxlayout3.setMargin(9)
        self.vboxlayout3.setObjectName("vboxlayout3")

        self.info = QtGui.QLabel(self.tab_5)
        self.info.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.info.setWordWrap(True)
        self.info.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.info.setObjectName("info")
        self.vboxlayout3.addWidget(self.info)
        self.tabWidget.addTab(self.tab_5,"")
        self.vboxlayout.addWidget(self.tabWidget)

        self.buttonbox = QtGui.QDialogButtonBox(TagEditorDialog)
        self.buttonbox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonbox.setObjectName("buttonbox")
        self.vboxlayout.addWidget(self.buttonbox)

        self.retranslateUi(TagEditorDialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(TagEditorDialog)
        TagEditorDialog.setTabOrder(self.tags,self.tags_add)
        TagEditorDialog.setTabOrder(self.tags_add,self.tags_delete)
        TagEditorDialog.setTabOrder(self.tags_delete,self.tabWidget)
        TagEditorDialog.setTabOrder(self.tabWidget,self.artwork_list)

    def retranslateUi(self, TagEditorDialog):
        self.tags.headerItem().setText(0,_("Name"))
        self.tags.headerItem().setText(1,_("Value"))
        self.ratingLabel.setText(_("Rating:"))
        self.tags_add.setText(_("&Add..."))
        self.tags_edit.setText(_("&Edit..."))
        self.tags_delete.setText(_("&Delete"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), _("&Metadata"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _("A&rtwork"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), _("&Info"))

from picard.ui.ratingwidget import RatingWidget
