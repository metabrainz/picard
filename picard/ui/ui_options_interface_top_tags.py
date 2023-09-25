# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_InterfaceTopTagsOptionsPage(object):
    def setupUi(self, InterfaceTopTagsOptionsPage):
        InterfaceTopTagsOptionsPage.setObjectName("InterfaceTopTagsOptionsPage")
        InterfaceTopTagsOptionsPage.resize(418, 310)
        self.vboxlayout = QtWidgets.QVBoxLayout(InterfaceTopTagsOptionsPage)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.top_tags_groupBox = QtWidgets.QGroupBox(InterfaceTopTagsOptionsPage)
        self.top_tags_groupBox.setObjectName("top_tags_groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.top_tags_groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.top_tags_list = TagListEditor(self.top_tags_groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.top_tags_list.sizePolicy().hasHeightForWidth())
        self.top_tags_list.setSizePolicy(sizePolicy)
        self.top_tags_list.setObjectName("top_tags_list")
        self.verticalLayout.addWidget(self.top_tags_list)
        self.vboxlayout.addWidget(self.top_tags_groupBox)

        self.retranslateUi(InterfaceTopTagsOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(InterfaceTopTagsOptionsPage)

    def retranslateUi(self, InterfaceTopTagsOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.top_tags_groupBox.setTitle(_("Show the below tags above all other tags in the metadata view"))
from picard.ui.widgets.taglisteditor import TagListEditor
