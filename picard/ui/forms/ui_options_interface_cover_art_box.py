# Form implementation generated from reading ui file 'ui/options_interface_cover_art_box.ui'
#
# Created by: PyQt6 UI code generator 6.9.1
#
# Automatically generated - do not edit.
# Use `python setup.py build_ui` to update it.

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import gettext as _


class Ui_InterfaceCoverArtBoxOptionsPage(object):
    def setupUi(self, InterfaceCoverArtBoxOptionsPage):
        InterfaceCoverArtBoxOptionsPage.setObjectName("InterfaceCoverArtBoxOptionsPage")
        InterfaceCoverArtBoxOptionsPage.resize(466, 200)
        self.vboxlayout = QtWidgets.QVBoxLayout(InterfaceCoverArtBoxOptionsPage)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.cb_show_cover_art_details = QtWidgets.QGroupBox(parent=InterfaceCoverArtBoxOptionsPage)
        self.cb_show_cover_art_details.setCheckable(True)
        self.cb_show_cover_art_details.setChecked(False)
        self.cb_show_cover_art_details.setObjectName("cb_show_cover_art_details")
        self.cover_art_details_layout = QtWidgets.QVBoxLayout(self.cb_show_cover_art_details)
        self.cover_art_details_layout.setObjectName("cover_art_details_layout")
        self.cb_show_cover_art_details_type = QtWidgets.QCheckBox(parent=self.cb_show_cover_art_details)
        self.cb_show_cover_art_details_type.setObjectName("cb_show_cover_art_details_type")
        self.cover_art_details_layout.addWidget(self.cb_show_cover_art_details_type)
        self.cb_show_cover_art_details_filesize = QtWidgets.QCheckBox(parent=self.cb_show_cover_art_details)
        self.cb_show_cover_art_details_filesize.setObjectName("cb_show_cover_art_details_filesize")
        self.cover_art_details_layout.addWidget(self.cb_show_cover_art_details_filesize)
        self.cb_show_cover_art_details_dimensions = QtWidgets.QCheckBox(parent=self.cb_show_cover_art_details)
        self.cb_show_cover_art_details_dimensions.setObjectName("cb_show_cover_art_details_dimensions")
        self.cover_art_details_layout.addWidget(self.cb_show_cover_art_details_dimensions)
        self.cb_show_cover_art_details_mimetype = QtWidgets.QCheckBox(parent=self.cb_show_cover_art_details)
        self.cb_show_cover_art_details_mimetype.setObjectName("cb_show_cover_art_details_mimetype")
        self.cover_art_details_layout.addWidget(self.cb_show_cover_art_details_mimetype)
        self.vboxlayout.addWidget(self.cb_show_cover_art_details)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(InterfaceCoverArtBoxOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(InterfaceCoverArtBoxOptionsPage)

    def retranslateUi(self, InterfaceCoverArtBoxOptionsPage):
        self.cb_show_cover_art_details.setTitle(_("Show cover art details in cover art view"))
        self.cb_show_cover_art_details_type.setText(_("Show type (front, back, etc.)"))
        self.cb_show_cover_art_details_filesize.setText(_("Show file size"))
        self.cb_show_cover_art_details_dimensions.setText(_("Show dimensions"))
        self.cb_show_cover_art_details_mimetype.setText(_("Show MIME type"))
