# Form implementation generated from reading ui file 'ui/options.ui'
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


class Ui_OptionsDialog(object):
    def setupUi(self, OptionsDialog):
        OptionsDialog.setObjectName("OptionsDialog")
        OptionsDialog.resize(800, 450)
        OptionsDialog.setToolTip(_("Edit Picard's settings here. Use the categories on the left to find specific options."))
        self.vboxlayout = QtWidgets.QVBoxLayout(OptionsDialog)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.vboxlayout.setToolTip(_("This area contains all controls for editing Picard's options."))
        self.vboxlayout.setWhatsThis(_("This layout arranges all controls and widgets for editing Picard's options."))
        self.dialog_splitter = QtWidgets.QSplitter(parent=OptionsDialog)
        self.dialog_splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.dialog_splitter.setChildrenCollapsible(False)
        self.dialog_splitter.setObjectName("dialog_splitter")
        self.dialog_splitter.setToolTip(_("Drag to resize the categories and settings areas"))
        self.pages_tree = QtWidgets.QTreeWidget(parent=self.dialog_splitter)
        self.pages_tree.setToolTip(_("Select a category to view and edit its options. You can use the search bar above to quickly find settings."))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pages_tree.sizePolicy().hasHeightForWidth())
        self.pages_tree.setSizePolicy(sizePolicy)
        self.pages_tree.setMinimumSize(QtCore.QSize(140, 0))
        self.pages_tree.setWhatsThis(_("This widget has a minimum width to ensure all categories are visible."))
        self.pages_tree.setObjectName("pages_tree")
        self.pages_stack = QtWidgets.QStackedWidget(parent=self.dialog_splitter)
        self.pages_stack.setToolTip(_("Settings for the selected category are shown here. You can edit values directly in this area."))
        self.pages_stack.setWhatsThis(_("This area displays the settings for the selected category. You can change values here and save them with the OK button."))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pages_stack.sizePolicy().hasHeightForWidth())
        self.pages_stack.setSizePolicy(sizePolicy)
        self.pages_stack.setMinimumSize(QtCore.QSize(280, 0))
        self.pages_stack.setObjectName("pages_stack")
        self.vboxlayout.addWidget(self.dialog_splitter)
        self.buttonbox = QtWidgets.QDialogButtonBox(parent=OptionsDialog)
        self.buttonbox.setMinimumSize(QtCore.QSize(0, 0))
        self.buttonbox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonbox.setObjectName("buttonbox")
        self.buttonbox.setToolTip(_("Use these buttons to save or discard your changes."))
        self.buttonbox.setWhatsThis(_("Click OK to save your changes or Cancel to discard them and close the dialog."))
        self.vboxlayout.addWidget(self.buttonbox)

        self.retranslateUi(OptionsDialog)
        # Add tooltips for OK and Cancel buttons
        ok_button = self.buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            ok_button.setToolTip(_("Accept and save changes"))
        cancel_button = self.buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        if cancel_button:
            cancel_button.setToolTip(_("Cancel and discard changes"))
        QtCore.QMetaObject.connectSlotsByName(OptionsDialog)

    def retranslateUi(self, OptionsDialog):
        OptionsDialog.setWindowTitle(_("Options"))
