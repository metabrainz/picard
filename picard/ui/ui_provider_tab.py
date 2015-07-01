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

class Ui_ProviderTab(object):
    def setupUi(self, ProviderTab):
        ProviderTab.setObjectName(_fromUtf8("ProviderTab"))
        ProviderTab.resize(400, 300)
        self.verticalLayout = QtGui.QVBoxLayout(ProviderTab)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(6, 6, 0, 0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.enabled = QtGui.QGroupBox(ProviderTab)
        self.enabled.setCheckable(True)
        self.enabled.setChecked(False)
        self.enabled.setObjectName(_fromUtf8("enabled"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.enabled)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.scrollArea = QtGui.QScrollArea(self.enabled)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setAutoFillBackground(False)
        self.scrollArea.setFrameShape(QtGui.QFrame.NoFrame)
        self.scrollArea.setFrameShadow(QtGui.QFrame.Plain)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName(_fromUtf8("scrollArea"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setEnabled(False)
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 368, 258))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_2.addWidget(self.scrollArea)
        self.verticalLayout.addWidget(self.enabled)

        self.retranslateUi(ProviderTab)
        QtCore.QMetaObject.connectSlotsByName(ProviderTab)

    def retranslateUi(self, ProviderTab):
        ProviderTab.setWindowTitle(_("Form"))
        self.enabled.setTitle(_("Enabled"))

