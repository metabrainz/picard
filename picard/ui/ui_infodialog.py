# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_InfoDialog(object):
    def setupUi(self, InfoDialog):
        InfoDialog.setObjectName("InfoDialog")
        InfoDialog.resize(535, 436)
        self.verticalLayout = QtWidgets.QVBoxLayout(InfoDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(InfoDialog)
        self.tabWidget.setObjectName("tabWidget")
        self.info_tab = QtWidgets.QWidget()
        self.info_tab.setObjectName("info_tab")
        self.vboxlayout = QtWidgets.QVBoxLayout(self.info_tab)
        self.vboxlayout.setObjectName("vboxlayout")
        self.info_scroll = QtWidgets.QScrollArea(self.info_tab)
        self.info_scroll.setWidgetResizable(True)
        self.info_scroll.setObjectName("info_scroll")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setEnabled(True)
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 493, 358))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayoutLabel = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayoutLabel.setContentsMargins(0, 0, 0, 0)
        self.verticalLayoutLabel.setObjectName("verticalLayoutLabel")
        self.info = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.info.setText("")
        self.info.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.info.setWordWrap(True)
        self.info.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.info.setObjectName("info")
        self.verticalLayoutLabel.addWidget(self.info)
        self.info_scroll.setWidget(self.scrollAreaWidgetContents)
        self.vboxlayout.addWidget(self.info_scroll)
        self.tabWidget.addTab(self.info_tab, "")
        self.artwork_tab = QtWidgets.QWidget()
        self.artwork_tab.setObjectName("artwork_tab")
        self.vboxlayout1 = QtWidgets.QVBoxLayout(self.artwork_tab)
        self.vboxlayout1.setObjectName("vboxlayout1")
        self.tabWidget.addTab(self.artwork_tab, "")
        self.verticalLayout.addWidget(self.tabWidget)
        self.buttonBox = QtWidgets.QDialogButtonBox(InfoDialog)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.NoButton)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(InfoDialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(InfoDialog)
        InfoDialog.setTabOrder(self.tabWidget, self.buttonBox)

    def retranslateUi(self, InfoDialog):
        _translate = QtCore.QCoreApplication.translate
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.info_tab), _("&Info"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.artwork_tab), _("A&rtwork"))

