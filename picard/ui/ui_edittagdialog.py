# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_EditTagDialog(object):
    def setupUi(self, EditTagDialog):
        EditTagDialog.setObjectName("EditTagDialog")
        EditTagDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        EditTagDialog.resize(400, 250)
        EditTagDialog.setFocusPolicy(QtCore.Qt.StrongFocus)
        EditTagDialog.setModal(True)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(EditTagDialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tag_names = QtWidgets.QComboBox(EditTagDialog)
        self.tag_names.setEditable(True)
        self.tag_names.setObjectName("tag_names")
        self.verticalLayout_2.addWidget(self.tag_names)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.value_list = QtWidgets.QListWidget(EditTagDialog)
        self.value_list.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.value_list.setTabKeyNavigation(False)
        self.value_list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.value_list.setMovement(QtWidgets.QListView.Free)
        self.value_list.setObjectName("value_list")
        self.horizontalLayout.addWidget(self.value_list)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.edit_value = QtWidgets.QPushButton(EditTagDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(100)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edit_value.sizePolicy().hasHeightForWidth())
        self.edit_value.setSizePolicy(sizePolicy)
        self.edit_value.setMinimumSize(QtCore.QSize(100, 0))
        self.edit_value.setAutoDefault(False)
        self.edit_value.setObjectName("edit_value")
        self.verticalLayout.addWidget(self.edit_value)
        self.add_value = QtWidgets.QPushButton(EditTagDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(100)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.add_value.sizePolicy().hasHeightForWidth())
        self.add_value.setSizePolicy(sizePolicy)
        self.add_value.setMinimumSize(QtCore.QSize(100, 0))
        self.add_value.setAutoDefault(False)
        self.add_value.setObjectName("add_value")
        self.verticalLayout.addWidget(self.add_value)
        self.remove_value = QtWidgets.QPushButton(EditTagDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(120)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.remove_value.sizePolicy().hasHeightForWidth())
        self.remove_value.setSizePolicy(sizePolicy)
        self.remove_value.setMinimumSize(QtCore.QSize(120, 0))
        self.remove_value.setAutoDefault(False)
        self.remove_value.setObjectName("remove_value")
        self.verticalLayout.addWidget(self.remove_value)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        self.verticalLayout.addItem(spacerItem)
        self.move_value_up = QtWidgets.QPushButton(EditTagDialog)
        self.move_value_up.setText("")
        icon = QtGui.QIcon.fromTheme(":/images/16x16/go-up.png")
        self.move_value_up.setIcon(icon)
        self.move_value_up.setObjectName("move_value_up")
        self.verticalLayout.addWidget(self.move_value_up)
        self.move_value_down = QtWidgets.QPushButton(EditTagDialog)
        self.move_value_down.setText("")
        icon = QtGui.QIcon.fromTheme(":/images/16x16/go-down.png")
        self.move_value_down.setIcon(icon)
        self.move_value_down.setObjectName("move_value_down")
        self.verticalLayout.addWidget(self.move_value_down)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.buttonbox = QtWidgets.QDialogButtonBox(EditTagDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(150)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonbox.sizePolicy().hasHeightForWidth())
        self.buttonbox.setSizePolicy(sizePolicy)
        self.buttonbox.setMinimumSize(QtCore.QSize(150, 0))
        self.buttonbox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonbox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonbox.setObjectName("buttonbox")
        self.verticalLayout_2.addWidget(self.buttonbox)

        self.retranslateUi(EditTagDialog)
        self.buttonbox.accepted.connect(EditTagDialog.accept) # type: ignore
        self.buttonbox.rejected.connect(EditTagDialog.reject) # type: ignore
        self.move_value_up.clicked.connect(EditTagDialog.move_row_up) # type: ignore
        self.move_value_down.clicked.connect(EditTagDialog.move_row_down) # type: ignore
        self.edit_value.clicked.connect(EditTagDialog.edit_value) # type: ignore
        self.add_value.clicked.connect(EditTagDialog.add_value) # type: ignore
        self.value_list.itemChanged['QListWidgetItem*'].connect(EditTagDialog.value_edited) # type: ignore
        self.remove_value.clicked.connect(EditTagDialog.remove_value) # type: ignore
        self.value_list.itemSelectionChanged.connect(EditTagDialog.value_selection_changed) # type: ignore
        self.tag_names.editTextChanged['QString'].connect(EditTagDialog.tag_changed) # type: ignore
        self.tag_names.activated['QString'].connect(EditTagDialog.tag_selected) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(EditTagDialog)
        EditTagDialog.setTabOrder(self.tag_names, self.value_list)
        EditTagDialog.setTabOrder(self.value_list, self.edit_value)
        EditTagDialog.setTabOrder(self.edit_value, self.add_value)
        EditTagDialog.setTabOrder(self.add_value, self.remove_value)
        EditTagDialog.setTabOrder(self.remove_value, self.buttonbox)

    def retranslateUi(self, EditTagDialog):
        _translate = QtCore.QCoreApplication.translate
        EditTagDialog.setWindowTitle(_("Edit Tag"))
        self.edit_value.setText(_("Edit value"))
        self.add_value.setText(_("Add value"))
        self.remove_value.setText(_("Remove value"))
        self.move_value_up.setToolTip(_("Move selected value up"))
        self.move_value_up.setAccessibleDescription(_("Move selected value up"))
        self.move_value_down.setToolTip(_("Move selected value down"))
        self.move_value_down.setAccessibleDescription(_("Move selected value down"))
