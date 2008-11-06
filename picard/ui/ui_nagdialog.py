# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/nagdialog.ui'
#
# Created: Fri Nov  7 00:23:06 2008
#      by: PyQt4 UI code generator 4.4.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_NagDialog(object):
    def setupUi(self, NagDialog):
        NagDialog.setObjectName("NagDialog")
        NagDialog.setWindowModality(QtCore.Qt.WindowModal)
        NagDialog.resize(378, 204)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(NagDialog.sizePolicy().hasHeightForWidth())
        NagDialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QtGui.QVBoxLayout(NagDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.info_text = QtGui.QLabel(NagDialog)
        self.info_text.setWordWrap(True)
        self.info_text.setObjectName("info_text")
        self.verticalLayout.addWidget(self.info_text)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.button_box = QtGui.QDialogButtonBox(NagDialog)
        self.button_box.setStandardButtons(QtGui.QDialogButtonBox.NoButton)
        self.button_box.setObjectName("button_box")
        self.verticalLayout.addWidget(self.button_box)

        self.retranslateUi(NagDialog)
        QtCore.QMetaObject.connectSlotsByName(NagDialog)

    def retranslateUi(self, NagDialog):
        NagDialog.setWindowTitle(_("Please donate to MusicBrainz!"))
        self.info_text.setText(QtGui.QApplication.translate("NagDialog", "The Picard Tagger is a free application and you may use it as long as you wish. However, providing the MusicBrainz service does cost money and we rely on donations from the community to keep the service running.\n"
"\n"
"Please donate $10 to the MetaBrainz Foundation which operates the MusicBrainz project. All donations are tax deductible for US residents and will keep this service alive and moving forward.", None, QtGui.QApplication.UnicodeUTF8))

