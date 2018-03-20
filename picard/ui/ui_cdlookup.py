# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(640, 240)
        self.vboxlayout = QtWidgets.QVBoxLayout(Dialog)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.vboxlayout.addWidget(self.label)
        self.release_list = QtWidgets.QTreeWidget(Dialog)
        self.release_list.setObjectName("release_list")
        self.release_list.headerItem().setText(0, "1")
        self.vboxlayout.addWidget(self.release_list)
        self.hboxlayout = QtWidgets.QHBoxLayout()
        self.hboxlayout.setContentsMargins(0, 0, 0, 0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")
        spacerItem = QtWidgets.QSpacerItem(111, 31, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)
        self.ok_button = QtWidgets.QPushButton(Dialog)
        self.ok_button.setEnabled(False)
        self.ok_button.setObjectName("ok_button")
        self.hboxlayout.addWidget(self.ok_button)
        self.lookup_button = QtWidgets.QPushButton(Dialog)
        self.lookup_button.setObjectName("lookup_button")
        self.hboxlayout.addWidget(self.lookup_button)
        self.cancel_button = QtWidgets.QPushButton(Dialog)
        self.cancel_button.setObjectName("cancel_button")
        self.hboxlayout.addWidget(self.cancel_button)
        self.vboxlayout.addLayout(self.hboxlayout)

        self.retranslateUi(Dialog)
        self.ok_button.clicked.connect(Dialog.accept)
        self.cancel_button.clicked.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.release_list, self.ok_button)
        Dialog.setTabOrder(self.ok_button, self.lookup_button)
        Dialog.setTabOrder(self.lookup_button, self.cancel_button)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_("CD Lookup"))
        self.label.setText(_("The following releases on MusicBrainz match the CD:"))
        self.ok_button.setText(_("&Load into Picard"))
        self.lookup_button.setText(_("Lookup in &Browser"))
        self.cancel_button.setText(_("&Cancel"))

