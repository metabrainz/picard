# Form implementation generated from reading ui file 'ui/options_cdlookup.ui'
#
# Created by: PyQt6 UI code generator 6.11.0
#
# Automatically generated - do not edit.
# Use `python setup.py build_ui` to update it.

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import gettext as _


class Ui_CDLookupOptionsPage(object):
    def setupUi(self, CDLookupOptionsPage):
        CDLookupOptionsPage.setObjectName("CDLookupOptionsPage")
        CDLookupOptionsPage.resize(224, 176)
        self.vboxlayout = QtWidgets.QVBoxLayout(CDLookupOptionsPage)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.rename_files = QtWidgets.QGroupBox(parent=CDLookupOptionsPage)
        self.rename_files.setObjectName("rename_files")
        self.gridlayout = QtWidgets.QGridLayout(self.rename_files)
        self.gridlayout.setContentsMargins(9, 9, 9, 9)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName("gridlayout")
        self.cd_lookup_device = QtWidgets.QLineEdit(parent=self.rename_files)
        self.cd_lookup_device.setObjectName("cd_lookup_device")
        self.gridlayout.addWidget(self.cd_lookup_device, 1, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(parent=self.rename_files)
        self.label_3.setObjectName("label_3")
        self.gridlayout.addWidget(self.label_3, 0, 0, 1, 1)
        self.read_isrcs_from_disc = QtWidgets.QCheckBox(parent=self.rename_files)
        self.read_isrcs_from_disc.setObjectName("read_isrcs_from_disc")
        self.gridlayout.addWidget(self.read_isrcs_from_disc, 2, 0, 1, 1)
        self.vboxlayout.addWidget(self.rename_files)
        spacerItem = QtWidgets.QSpacerItem(161, 81, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_3.setBuddy(self.cd_lookup_device)

        self.retranslateUi(CDLookupOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(CDLookupOptionsPage)
        CDLookupOptionsPage.setTabOrder(self.cd_lookup_device, self.read_isrcs_from_disc)

    def retranslateUi(self, CDLookupOptionsPage):
        self.rename_files.setTitle(_("CD Lookup"))
        self.label_3.setText(_("CD-ROM device to use for lookups:"))
        self.read_isrcs_from_disc.setToolTip(_("When enabled, ISRCs will be read from the CD during disc lookup. This may significantly slow down the disc read on some drives."))
        self.read_isrcs_from_disc.setText(_("Read ISRCs from CD"))
