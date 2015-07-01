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

class Ui_CoverOptionsPage(object):
    def setupUi(self, CoverOptionsPage):
        CoverOptionsPage.setObjectName(_fromUtf8("CoverOptionsPage"))
        CoverOptionsPage.resize(632, 560)
        self.verticalLayout = QtGui.QVBoxLayout(CoverOptionsPage)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.rename_files = QtGui.QGroupBox(CoverOptionsPage)
        self.rename_files.setObjectName(_fromUtf8("rename_files"))
        self.vboxlayout = QtGui.QVBoxLayout(self.rename_files)
        self.vboxlayout.setSpacing(2)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.save_images_to_tags = QtGui.QCheckBox(self.rename_files)
        self.save_images_to_tags.setObjectName(_fromUtf8("save_images_to_tags"))
        self.vboxlayout.addWidget(self.save_images_to_tags)
        self.cb_embed_front_only = QtGui.QCheckBox(self.rename_files)
        self.cb_embed_front_only.setObjectName(_fromUtf8("cb_embed_front_only"))
        self.vboxlayout.addWidget(self.cb_embed_front_only)
        self.save_images_to_files = QtGui.QCheckBox(self.rename_files)
        self.save_images_to_files.setObjectName(_fromUtf8("save_images_to_files"))
        self.vboxlayout.addWidget(self.save_images_to_files)
        self.label_3 = QtGui.QLabel(self.rename_files)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.vboxlayout.addWidget(self.label_3)
        self.cover_image_filename = QtGui.QLineEdit(self.rename_files)
        self.cover_image_filename.setObjectName(_fromUtf8("cover_image_filename"))
        self.vboxlayout.addWidget(self.cover_image_filename)
        self.save_images_overwrite = QtGui.QCheckBox(self.rename_files)
        self.save_images_overwrite.setObjectName(_fromUtf8("save_images_overwrite"))
        self.vboxlayout.addWidget(self.save_images_overwrite)
        self.verticalLayout.addWidget(self.rename_files)
        self.ca_providers_groupbox = QtGui.QGroupBox(CoverOptionsPage)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ca_providers_groupbox.sizePolicy().hasHeightForWidth())
        self.ca_providers_groupbox.setSizePolicy(sizePolicy)
        self.ca_providers_groupbox.setObjectName(_fromUtf8("ca_providers_groupbox"))
        self.ca_providers_layout = QtGui.QVBoxLayout(self.ca_providers_groupbox)
        self.ca_providers_layout.setObjectName(_fromUtf8("ca_providers_layout"))
        self.tab_cover_art_providers = QtGui.QTabWidget(self.ca_providers_groupbox)
        self.tab_cover_art_providers.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tab_cover_art_providers.sizePolicy().hasHeightForWidth())
        self.tab_cover_art_providers.setSizePolicy(sizePolicy)
        self.tab_cover_art_providers.setTabPosition(QtGui.QTabWidget.North)
        self.tab_cover_art_providers.setMovable(True)
        self.tab_cover_art_providers.setObjectName(_fromUtf8("tab_cover_art_providers"))
        self.ca_providers_layout.addWidget(self.tab_cover_art_providers)
        self.reordertabs = QtGui.QHBoxLayout()
        self.reordertabs.setObjectName(_fromUtf8("reordertabs"))
        self.movetabnote = QtGui.QLabel(self.ca_providers_groupbox)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setItalic(True)
        self.movetabnote.setFont(font)
        self.movetabnote.setWordWrap(True)
        self.movetabnote.setObjectName(_fromUtf8("movetabnote"))
        self.reordertabs.addWidget(self.movetabnote)
        self.moveleft = QtGui.QToolButton(self.ca_providers_groupbox)
        self.moveleft.setArrowType(QtCore.Qt.LeftArrow)
        self.moveleft.setObjectName(_fromUtf8("moveleft"))
        self.reordertabs.addWidget(self.moveleft)
        self.moveright = QtGui.QToolButton(self.ca_providers_groupbox)
        self.moveright.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.moveright.setArrowType(QtCore.Qt.RightArrow)
        self.moveright.setObjectName(_fromUtf8("moveright"))
        self.reordertabs.addWidget(self.moveright)
        self.ca_providers_layout.addLayout(self.reordertabs)
        self.verticalLayout.addWidget(self.ca_providers_groupbox)

        self.retranslateUi(CoverOptionsPage)
        self.tab_cover_art_providers.setCurrentIndex(-1)
        QtCore.QObject.connect(self.save_images_to_tags, QtCore.SIGNAL(_fromUtf8("clicked(bool)")), self.cb_embed_front_only.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(CoverOptionsPage)
        CoverOptionsPage.setTabOrder(self.save_images_to_tags, self.cb_embed_front_only)
        CoverOptionsPage.setTabOrder(self.cb_embed_front_only, self.save_images_to_files)
        CoverOptionsPage.setTabOrder(self.save_images_to_files, self.cover_image_filename)
        CoverOptionsPage.setTabOrder(self.cover_image_filename, self.save_images_overwrite)

    def retranslateUi(self, CoverOptionsPage):
        self.rename_files.setTitle(_("Location"))
        self.save_images_to_tags.setText(_("Embed cover images into tags"))
        self.cb_embed_front_only.setText(_("Only embed a front image"))
        self.save_images_to_files.setText(_("Save cover images as separate files"))
        self.label_3.setText(_("Use the following file name for images:"))
        self.save_images_overwrite.setText(_("Overwrite the file if it already exists"))
        self.ca_providers_groupbox.setTitle(_("Cover Art Providers"))
        self.movetabnote.setText(_("Providers will be run in the order of the tabs, starting from left. Use those buttons or drag\'n\'drop to change order."))
        self.moveleft.setText(_("Move to left"))
        self.moveright.setText(_("Move to right"))

