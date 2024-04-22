# Form implementation generated from reading ui file 'ui/widget_taglisteditor.ui'
#
# Created by: PyQt6 UI code generator 6.6.1
#
# Automatically generated - do not edit.
# Use `python setup.py build_ui` to update it.

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import gettext as _


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
        self.tag_list_view = UniqueEditableListView(parent=TagListEditor)
        self.tag_list_view.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.tag_list_view.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tag_list_view.setObjectName("tag_list_view")
        self.verticalLayout.addWidget(self.tag_list_view)
        self.edit_buttons = QtWidgets.QWidget(parent=TagListEditor)
        self.edit_buttons.setObjectName("edit_buttons")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.edit_buttons)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.tags_add_btn = QtWidgets.QToolButton(parent=self.edit_buttons)
        self.tags_add_btn.setObjectName("tags_add_btn")
        self.horizontalLayout_2.addWidget(self.tags_add_btn)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.sort_buttons = QtWidgets.QWidget(parent=self.edit_buttons)
        self.sort_buttons.setObjectName("sort_buttons")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.sort_buttons)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.tags_move_up_btn = QtWidgets.QToolButton(parent=self.sort_buttons)
        self.tags_move_up_btn.setText("")
        icon = QtGui.QIcon.fromTheme(":/images/16x16/go-up.png")
        self.tags_move_up_btn.setIcon(icon)
        self.tags_move_up_btn.setObjectName("tags_move_up_btn")
        self.horizontalLayout_3.addWidget(self.tags_move_up_btn)
        self.tags_move_down_btn = QtWidgets.QToolButton(parent=self.sort_buttons)
        self.tags_move_down_btn.setText("")
        icon = QtGui.QIcon.fromTheme(":/images/16x16/go-down.png")
        self.tags_move_down_btn.setIcon(icon)
        self.tags_move_down_btn.setObjectName("tags_move_down_btn")
        self.horizontalLayout_3.addWidget(self.tags_move_down_btn)
        self.horizontalLayout_2.addWidget(self.sort_buttons)
        self.tags_remove_btn = QtWidgets.QToolButton(parent=self.edit_buttons)
        self.tags_remove_btn.setObjectName("tags_remove_btn")
        self.horizontalLayout_2.addWidget(self.tags_remove_btn)
        self.verticalLayout.addWidget(self.edit_buttons)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.retranslateUi(TagListEditor)
        self.tags_add_btn.clicked.connect(self.tag_list_view.add_empty_row) # type: ignore
        self.tags_remove_btn.clicked.connect(self.tag_list_view.remove_selected_rows) # type: ignore
        self.tags_move_up_btn.clicked.connect(self.tag_list_view.move_selected_rows_up) # type: ignore
        self.tags_move_down_btn.clicked.connect(self.tag_list_view.move_selected_rows_down) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(TagListEditor)

    def retranslateUi(self, TagListEditor):
        TagListEditor.setWindowTitle(_("Form"))
        self.tags_add_btn.setText(_("Add new tag"))
        self.tags_move_up_btn.setToolTip(_("Move tag up"))
        self.tags_move_up_btn.setAccessibleName(_("Move tag up"))
        self.tags_move_down_btn.setToolTip(_("Move tag down"))
        self.tags_move_down_btn.setAccessibleName(_("Move tag down"))
        self.tags_remove_btn.setToolTip(_("Remove selected tags"))
        self.tags_remove_btn.setAccessibleName(_("Remove selected tags"))
        self.tags_remove_btn.setText(_("Remove tags"))
from picard.ui.widgets.editablelistview import UniqueEditableListView
