# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_InterfaceTopTagsOptionsPage(object):
    def setupUi(self, InterfaceTopTagsOptionsPage):
        InterfaceTopTagsOptionsPage.setObjectName("InterfaceTopTagsOptionsPage")
        InterfaceTopTagsOptionsPage.resize(893, 698)
        self.vboxlayout = QtWidgets.QVBoxLayout(InterfaceTopTagsOptionsPage)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.label = QtWidgets.QLabel(InterfaceTopTagsOptionsPage)
        self.label.setObjectName("label")
        self.vboxlayout.addWidget(self.label)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.top_tags_list = EditableTagListView(InterfaceTopTagsOptionsPage)
        self.top_tags_list.setDragEnabled(True)
        self.top_tags_list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.top_tags_list.setObjectName("top_tags_list")
        self.verticalLayout_2.addWidget(self.top_tags_list)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.tags_remove_btn = QtWidgets.QPushButton(InterfaceTopTagsOptionsPage)
        self.tags_remove_btn.setObjectName("tags_remove_btn")
        self.horizontalLayout_2.addWidget(self.tags_remove_btn)
        self.tags_add_btn = QtWidgets.QPushButton(InterfaceTopTagsOptionsPage)
        self.tags_add_btn.setAccessibleName("")
        self.tags_add_btn.setObjectName("tags_add_btn")
        self.horizontalLayout_2.addWidget(self.tags_add_btn)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.tags_move_up_btn = QtWidgets.QPushButton(InterfaceTopTagsOptionsPage)
        self.tags_move_up_btn.setText("")
        icon = QtGui.QIcon.fromTheme("go-up")
        self.tags_move_up_btn.setIcon(icon)
        self.tags_move_up_btn.setObjectName("tags_move_up_btn")
        self.verticalLayout.addWidget(self.tags_move_up_btn)
        self.tags_move_down_btn = QtWidgets.QPushButton(InterfaceTopTagsOptionsPage)
        self.tags_move_down_btn.setText("")
        icon = QtGui.QIcon.fromTheme("go-down")
        self.tags_move_down_btn.setIcon(icon)
        self.tags_move_down_btn.setObjectName("tags_move_down_btn")
        self.verticalLayout.addWidget(self.tags_move_down_btn)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem2)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.vboxlayout.addLayout(self.horizontalLayout)

        self.retranslateUi(InterfaceTopTagsOptionsPage)
        self.tags_add_btn.clicked.connect(self.top_tags_list.add_empty_row)
        self.tags_remove_btn.clicked.connect(self.top_tags_list.remove_selected_rows)
        self.tags_move_up_btn.clicked.connect(self.top_tags_list.move_selected_rows_up)
        self.tags_move_down_btn.clicked.connect(self.top_tags_list.move_selected_rows_down)
        QtCore.QMetaObject.connectSlotsByName(InterfaceTopTagsOptionsPage)

    def retranslateUi(self, InterfaceTopTagsOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.label.setText(_("Show the below tags above all other tags in the metadata view"))
        self.tags_remove_btn.setToolTip(_("Remove selected tags"))
        self.tags_remove_btn.setAccessibleName(_("Remove selected tags"))
        self.tags_remove_btn.setText(_("Remove tags"))
        self.tags_add_btn.setText(_("Add new tag"))
        self.tags_move_up_btn.setToolTip(_("Move tag up"))
        self.tags_move_up_btn.setAccessibleName(_("Move tag up"))
        self.tags_move_down_btn.setToolTip(_("Move tag down"))
        self.tags_move_down_btn.setAccessibleName(_("Move tag down"))
from picard.ui.taglistview import EditableTagListView
