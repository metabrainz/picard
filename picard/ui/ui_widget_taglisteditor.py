# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_TagListEditor(object):
    def setupUi(self, TagListEditor):
        TagListEditor.setObjectName("TagListEditor")
        TagListEditor.resize(400, 300)
        self.horizontalLayout = QtWidgets.QHBoxLayout(TagListEditor)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.tag_list_view = EditableListView(TagListEditor)
        self.tag_list_view.setObjectName("tag_list_view")
        self.verticalLayout.addWidget(self.tag_list_view)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.tags_remove_btn = QtWidgets.QPushButton(TagListEditor)
        self.tags_remove_btn.setObjectName("tags_remove_btn")
        self.horizontalLayout_2.addWidget(self.tags_remove_btn)
        self.tags_add_btn = QtWidgets.QPushButton(TagListEditor)
        self.tags_add_btn.setObjectName("tags_add_btn")
        self.horizontalLayout_2.addWidget(self.tags_add_btn)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem1)
        self.tags_move_up_btn = QtWidgets.QPushButton(TagListEditor)
        self.tags_move_up_btn.setText("")
        icon = QtGui.QIcon.fromTheme("go-up")
        self.tags_move_up_btn.setIcon(icon)
        self.tags_move_up_btn.setObjectName("tags_move_up_btn")
        self.verticalLayout_2.addWidget(self.tags_move_up_btn)
        self.tags_move_down_btn = QtWidgets.QPushButton(TagListEditor)
        self.tags_move_down_btn.setText("")
        icon = QtGui.QIcon.fromTheme("go-down")
        self.tags_move_down_btn.setIcon(icon)
        self.tags_move_down_btn.setObjectName("tags_move_down_btn")
        self.verticalLayout_2.addWidget(self.tags_move_down_btn)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem2)
        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.retranslateUi(TagListEditor)
        self.tags_remove_btn.clicked.connect(self.tag_list_view.remove_selected_rows)
        self.tags_add_btn.clicked.connect(self.tag_list_view.add_empty_row)
        self.tags_move_up_btn.clicked.connect(self.tag_list_view.move_selected_rows_up)
        self.tags_move_down_btn.clicked.connect(self.tag_list_view.move_selected_rows_down)
        QtCore.QMetaObject.connectSlotsByName(TagListEditor)

    def retranslateUi(self, TagListEditor):
        _translate = QtCore.QCoreApplication.translate
        TagListEditor.setWindowTitle(_("Form"))
        self.tags_remove_btn.setToolTip(_("Remove selected tags"))
        self.tags_remove_btn.setAccessibleName(_("Remove selected tags"))
        self.tags_remove_btn.setText(_("Remove tags"))
        self.tags_add_btn.setText(_("Add new tag"))
        self.tags_move_up_btn.setToolTip(_("Move tag up"))
        self.tags_move_up_btn.setAccessibleName(_("Move tag up"))
        self.tags_move_down_btn.setToolTip(_("Move tag down"))
        self.tags_move_down_btn.setAccessibleName(_("Move tag down"))
from picard.ui.widgets.editablelistview import EditableListView
