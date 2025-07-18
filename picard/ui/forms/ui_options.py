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
        # Connect search bar to filter categories in pages_tree
        self.no_results_label = QtWidgets.QLabel(parent=OptionsDialog)
        self.no_results_label.setObjectName("no_results_label")
        self.no_results_label.setText(_("No results found."))
        self.no_results_label.setStyleSheet("color: #a00; font-style: italic;")
        self.no_results_label.setVisible(False)
        self.vboxlayout.addWidget(self.no_results_label)

        def filter_tree():
            query = self.search_bar.text().lower()
            def match_item(item):
                # Prüfe, ob das Item oder eines seiner Kinder passt
                if query == "":
                    return True
                if query in item.text(0).lower():
                    return True
                for j in range(item.childCount()):
                    if match_item(item.child(j)):
                        return True
                return False
            any_visible = False
            for i in range(self.pages_tree.topLevelItemCount()):
                item = self.pages_tree.topLevelItem(i)
                visible = match_item(item)
                item.setHidden(not visible)
                if visible:
                    any_visible = True
                # Auch alle Child-Items entsprechend setzen
                def set_children_hidden(parent):
                    for j in range(parent.childCount()):
                        child = parent.child(j)
                        child_visible = match_item(child)
                        child.setHidden(not child_visible)
                        if child_visible:
                            nonlocal any_visible
                            any_visible = True
                        set_children_hidden(child)
                set_children_hidden(item)
            # Label nur bei Suchtext und keinen Ergebnissen anzeigen
            self.no_results_label.setVisible(query != "" and not any_visible)

        self.search_bar.textChanged.connect(lambda: filter_tree())
        # Setze Fokus auf die Suchleiste beim Öffnen
        self.search_bar.setFocus()

        def select_first_visible():
            # Wähle die erste sichtbare Kategorie im Baum
            for i in range(self.pages_tree.topLevelItemCount()):
                item = self.pages_tree.topLevelItem(i)
                if not item.isHidden():
                    self.pages_tree.setCurrentItem(item)
                    self.pages_tree.scrollToItem(item)
                    return
                def select_child(parent):
                    for j in range(parent.childCount()):
                        child = parent.child(j)
                        if not child.isHidden():
                            self.pages_tree.setCurrentItem(child)
                            self.pages_tree.scrollToItem(child)
                            return True
                        if select_child(child):
                            return True
                    return False
                if select_child(item):
                    return

        def handle_search_key(event):
            if event.key() == QtCore.Qt.Key.Key_Return or event.key() == QtCore.Qt.Key.Key_Enter:
                select_first_visible()
            elif event.key() == QtCore.Qt.Key.Key_Escape:
                self.search_bar.clear()
            else:
                QtWidgets.QLineEdit.keyPressEvent(self.search_bar, event)
        self.search_bar.keyPressEvent = handle_search_key
        OptionsDialog.setObjectName("OptionsDialog")
        OptionsDialog.resize(800, 450)
        OptionsDialog.setToolTip(_("Edit Picard's settings here. Use the categories on the left to find specific options."))
        OptionsDialog.setWhatsThis(_("This dialog allows you to configure all settings for Picard. Use the categories on the left to navigate and the area on the right to edit options."))
        self.vboxlayout = QtWidgets.QVBoxLayout(OptionsDialog)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.vboxlayout.setToolTip(_("This area contains all controls for editing Picard's options."))
        self.vboxlayout.setWhatsThis(_("This layout arranges all controls and widgets for editing Picard's options."))
        self.search_bar = QtWidgets.QLineEdit(parent=OptionsDialog)
        self.search_bar.setObjectName("search_bar")
        self.search_bar.setPlaceholderText(_("Search settings..."))
        self.search_bar.setToolTip(_("Type here to search for settings or categories."))
        self.search_bar.setWhatsThis(_("Enter keywords to quickly find specific settings or categories in the options dialog."))
        self.vboxlayout.addWidget(self.search_bar)
        self.dialog_splitter = QtWidgets.QSplitter(parent=OptionsDialog)
        self.dialog_splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.dialog_splitter.setChildrenCollapsible(False)
        self.dialog_splitter.setObjectName("dialog_splitter")
        self.dialog_splitter.setToolTip(_("Drag the divider to resize the categories and settings areas."))
        self.dialog_splitter.setWhatsThis(_("You can adjust the width of the categories and settings areas by dragging the divider."))
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
        self.buttonbox.setWhatsThis(_("The OK button saves your changes and closes the dialog. The Cancel button discards any changes and closes the dialog."))
        self.vboxlayout.addWidget(self.buttonbox)

        self.retranslateUi(OptionsDialog)
        # Add tooltips for OK and Cancel buttons
        ok_button = self.buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            ok_button.setToolTip(_("Accept and save changes"))
            ok_button.setWhatsThis(_("Click to save all changes and close the dialog."))
        cancel_button = self.buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        if cancel_button:
            cancel_button.setToolTip(_("Cancel and discard changes"))
            cancel_button.setWhatsThis(_("Click to discard all changes and close the dialog."))
        QtCore.QMetaObject.connectSlotsByName(OptionsDialog)

    def retranslateUi(self, OptionsDialog):
        OptionsDialog.setWindowTitle(_("Options"))
