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
        self.tag_list_view.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.tag_list_view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tag_list_view.setObjectName("tag_list_view")
        self.verticalLayout.addWidget(self.tag_list_view)
        self.edit_buttons = QtWidgets.QWidget(TagListEditor)
        self.edit_buttons.setObjectName("edit_buttons")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.edit_buttons)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.tags_add_btn = QtWidgets.QToolButton(self.edit_buttons)
        self.tags_add_btn.setObjectName("tags_add_btn")
        self.horizontalLayout_2.addWidget(self.tags_add_btn)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.sort_buttons = QtWidgets.QWidget(self.edit_buttons)
        self.sort_buttons.setObjectName("sort_buttons")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.sort_buttons)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.tags_move_up_btn = QtWidgets.QToolButton(self.sort_buttons)
        self.tags_move_up_btn.setText("")
        icon = QtGui.QIcon.fromTheme(":/images/16x16/go-up.png")
        self.tags_move_up_btn.setIcon(icon)
        self.tags_move_up_btn.setObjectName("tags_move_up_btn")
        self.horizontalLayout_3.addWidget(self.tags_move_up_btn)
        self.tags_move_down_btn = QtWidgets.QToolButton(self.sort_buttons)
        self.tags_move_down_btn.setText("")
        icon = QtGui.QIcon.fromTheme(":/images/16x16/go-down.png")
        self.tags_move_down_btn.setIcon(icon)
        self.tags_move_down_btn.setObjectName("tags_move_down_btn")
        self.horizontalLayout_3.addWidget(self.tags_move_down_btn)
        self.horizontalLayout_2.addWidget(self.sort_buttons)
        self.tags_remove_btn = QtWidgets.QToolButton(self.edit_buttons)
        self.tags_remove_btn.setObjectName("tags_remove_btn")
        self.horizontalLayout_2.addWidget(self.tags_remove_btn)
        self.verticalLayout.addWidget(self.edit_buttons)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.retranslateUi(TagListEditor)
        self.tags_add_btn.clicked.connect(self.tag_list_view.add_empty_row)
        self.tags_remove_btn.clicked.connect(self.tag_list_view.remove_selected_rows)
        self.tags_move_up_btn.clicked.connect(self.tag_list_view.move_selected_rows_up)
        self.tags_move_down_btn.clicked.connect(self.tag_list_view.move_selected_rows_down)
        QtCore.QMetaObject.connectSlotsByName(TagListEditor)

    def retranslateUi(self, TagListEditor):
        _translate = QtCore.QCoreApplication.translate
        TagListEditor.setWindowTitle(_("Form"))
        self.tags_add_btn.setText(_("Add new tag"))
        self.tags_move_up_btn.setToolTip(_("Move tag up"))
        self.tags_move_up_btn.setAccessibleName(_("Move tag up"))
        self.tags_move_down_btn.setToolTip(_("Move tag down"))
        self.tags_move_down_btn.setAccessibleName(_("Move tag down"))
        self.tags_remove_btn.setToolTip(_("Remove selected tags"))
        self.tags_remove_btn.setAccessibleName(_("Remove selected tags"))
        self.tags_remove_btn.setText(_("Remove tags"))
from picard.ui.widgets.editablelistview import EditableListView
