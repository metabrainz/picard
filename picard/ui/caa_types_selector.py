# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007 Oliver Charles
# Copyright (C) 2007, 2010-2011 Lukáš Lalinský
# Copyright (C) 2007-2011, 2015, 2018-2023 Philipp Wolfer
# Copyright (C) 2011 Michael Wiencek
# Copyright (C) 2011-2012 Wieland Hoffmann
# Copyright (C) 2013-2015, 2018-2023 Laurent Monin
# Copyright (C) 2015-2016 Rahul Raturi
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Frederik “Freso” S. Olesen
# Copyright (C) 2018 Bob Swift
# Copyright (C) 2018 Vishal Choudhary
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


from functools import partial

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.ui import PicardDialog
from picard.ui.util import (
    StandardButton,
    qlistwidget_items,
)


class ArrowButton(QtWidgets.QPushButton):
    """Standard arrow button for CAA image type selection dialog.

    Keyword Arguments:
        label {string} -- Label to display on the button
        command {command} -- Command to execute when the button is clicked (default: {None})
        parent {[type]} -- Parent of the QPushButton object being created (default: {None})
    """

    def __init__(self, icon_name, command=None, parent=None):
        icon = QtGui.QIcon(":/images/16x16/" + icon_name + '.png')
        super().__init__(icon, "", parent=parent)
        if command is not None:
            self.clicked.connect(command)


class ArrowsColumn(QtWidgets.QWidget):
    """Standard arrow buttons column for CAA image type selection dialog.

    Keyword Arguments:
        selection_list {ListBox} -- ListBox of selected items associated with this arrow column
        ignore_list {ListBox} -- ListBox of unselected items associated with this arrow column
        callback {command} -- Command to execute after items are moved between lists (default: {None})
        reverse {bool} -- Determines whether the arrow directions should be reversed (default: {False})
        parent {[type]} -- Parent of the QWidget object being created (default: {None})
    """

    def __init__(self, selection_list, ignore_list, callback=None, reverse=False, parent=None):
        super().__init__(parent=parent)
        self.selection_list = selection_list
        self.ignore_list = ignore_list
        self.callback = callback
        spacer_item = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        arrows_layout = QtWidgets.QVBoxLayout()
        arrows_layout.addItem(QtWidgets.QSpacerItem(spacer_item))
        self.button_add = ArrowButton('go-next' if reverse else 'go-previous', self.move_from_ignore)
        arrows_layout.addWidget(self.button_add)
        self.button_add_all = ArrowButton('move-all-right' if reverse else 'move-all-left', self.move_all_from_ignore)
        arrows_layout.addWidget(self.button_add_all)
        self.button_remove = ArrowButton('go-previous' if reverse else 'go-next', self.move_to_ignore)
        arrows_layout.addWidget(self.button_remove)
        self.button_remove_all = ArrowButton('move-all-left' if reverse else 'move-all-right', self.move_all_to_ignore)
        arrows_layout.addWidget(self.button_remove_all)
        arrows_layout.addItem(QtWidgets.QSpacerItem(spacer_item))
        self.setLayout(arrows_layout)

    def move_from_ignore(self):
        self.ignore_list.move_selected_items(self.selection_list, callback=self.callback)

    def move_all_from_ignore(self):
        self.ignore_list.move_all_items(self.selection_list, callback=self.callback)

    def move_to_ignore(self):
        self.selection_list.move_selected_items(self.ignore_list, callback=self.callback)

    def move_all_to_ignore(self):
        self.selection_list.move_all_items(self.ignore_list, callback=self.callback)


class ListBox(QtWidgets.QListWidget):
    """Standard list box for CAA image type selection dialog.

    Keyword Arguments:
        parent {[type]} -- Parent of the QListWidget object being created (default: {None})
    """

    LISTBOX_WIDTH = 100
    LISTBOX_HEIGHT = 250

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setMinimumSize(QtCore.QSize(self.LISTBOX_WIDTH, self.LISTBOX_HEIGHT))
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.setSortingEnabled(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)

    def move_item(self, item, target_list):
        """Move the specified item to another listbox."""
        self.takeItem(self.row(item))
        target_list.addItem(item)

    def move_selected_items(self, target_list, callback=None):
        """Move the selected item to another listbox."""
        for item in self.selectedItems():
            self.move_item(item, target_list)
        if callback:
            callback()

    def move_all_items(self, target_list, callback=None):
        """Move all items to another listbox."""
        while self.count():
            self.move_item(self.item(0), target_list)
        if callback:
            callback()

    def all_items_data(self, role=QtCore.Qt.ItemDataRole.UserRole):
        for item in qlistwidget_items(self):
            yield item.data(role)


class CAATypesSelectorDialog(PicardDialog):
    """Display dialog box to select the CAA image types to include and exclude from download and use.

    Keyword Arguments:
        parent {[type]} -- Parent of the QDialog object being created (default: {None})
        types_include {[string]} -- List of CAA image types to include (default: {None})
        types_exclude {[string]} -- List of CAA image types to exclude (default: {None})
        default_include {[string]} -- List of CAA image types to include by default (default: {None})
        default_exclude {[string]} -- List of CAA image types to exclude by default (default: {None})
        known_types {{string: string}} -- Dict. of all known CAA image types, unique name as key, translated title as value (default: {None})
    """

    help_url = 'doc_cover_art_types'

    def __init__(
        self, parent=None, types_include=None, types_exclude=None,
        default_include=None, default_exclude=None, known_types=None
    ):
        super().__init__(parent)
        if types_include is None:
            types_include = []
        if types_exclude is None:
            types_exclude = []
        self._default_include = default_include or []
        self._default_exclude = default_exclude or []
        self._known_types = known_types or []

        self.setWindowTitle(_("Cover art types"))
        self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetFixedSize)

        # Create list boxes for dialog
        self.list_include = ListBox()
        self.list_exclude = ListBox()
        self.list_ignore = ListBox()

        # Populate list boxes from current settings
        self.fill_lists(types_include, types_exclude)

        # Set triggers when the lists receive the current focus
        self.list_include.clicked.connect(partial(self.clear_focus, [self.list_ignore, self.list_exclude]))
        self.list_exclude.clicked.connect(partial(self.clear_focus, [self.list_ignore, self.list_include]))
        self.list_ignore.clicked.connect(partial(self.clear_focus, [self.list_include, self.list_exclude]))

        # Add instructions to the dialog box
        instructions = QtWidgets.QLabel()
        instructions.setText(_("Please select the contents of the image type 'Include' and 'Exclude' lists."))
        instructions.setWordWrap(True)
        instructions.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.layout.addWidget(instructions)

        self.arrows_include = ArrowsColumn(
            self.list_include,
            self.list_ignore,
            callback=self.set_buttons_enabled_state,
        )

        self.arrows_exclude = ArrowsColumn(
            self.list_exclude,
            self.list_ignore,
            callback=self.set_buttons_enabled_state,
            reverse=True
        )

        lists_layout = QtWidgets.QHBoxLayout()

        include_list_layout = QtWidgets.QVBoxLayout()
        include_list_layout.addWidget(QtWidgets.QLabel(_("Include types list")))
        include_list_layout.addWidget(self.list_include)
        lists_layout.addLayout(include_list_layout)

        lists_layout.addWidget(self.arrows_include)

        ignore_list_layout = QtWidgets.QVBoxLayout()
        ignore_list_layout.addWidget(QtWidgets.QLabel(""))
        ignore_list_layout.addWidget(self.list_ignore)
        lists_layout.addLayout(ignore_list_layout)

        lists_layout.addWidget(self.arrows_exclude)

        exclude_list_layout = QtWidgets.QVBoxLayout()
        exclude_list_layout.addWidget(QtWidgets.QLabel(_("Exclude types list")))
        exclude_list_layout.addWidget(self.list_exclude)
        lists_layout.addLayout(exclude_list_layout)

        self.layout.addLayout(lists_layout)

        # Add usage explanation to the dialog box
        instructions = QtWidgets.QLabel()
        instructions.setText(_(
            "CAA images with an image type found in the 'Include' list will be downloaded and used "
            "UNLESS they also have an image type found in the 'Exclude' list. Images with types "
            "found in the 'Exclude' list will NEVER be used. Image types not appearing in the 'Include' "
            "or 'Exclude' lists will not be considered when determining whether or not to download and "
            "use a CAA image.\n")
        )
        instructions.setWordWrap(True)
        instructions.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.layout.addWidget(instructions)

        self.buttonbox = QtWidgets.QDialogButtonBox(self)
        self.buttonbox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonbox.addButton(
            StandardButton(StandardButton.OK), QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self.buttonbox.addButton(StandardButton(StandardButton.CANCEL),
                                 QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        self.buttonbox.addButton(
            StandardButton(StandardButton.HELP), QtWidgets.QDialogButtonBox.ButtonRole.HelpRole)

        extrabuttons = [
            (N_("I&nclude all"), self.move_all_to_include_list),
            (N_("E&xclude all"), self.move_all_to_exclude_list),
            (N_("C&lear all"), self.move_all_to_ignore_list),
            (N_("Restore &Defaults"), self.reset_to_defaults),
        ]
        for label, callback in extrabuttons:
            button = QtWidgets.QPushButton(_(label))
            self.buttonbox.addButton(button, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
            button.clicked.connect(callback)

        self.layout.addWidget(self.buttonbox)

        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        self.buttonbox.helpRequested.connect(self.show_help)

        self.set_buttons_enabled_state()

    def move_all_to_include_list(self):
        self.list_ignore.move_all_items(self.list_include)
        self.list_exclude.move_all_items(self.list_include)
        self.set_buttons_enabled_state()

    def move_all_to_exclude_list(self):
        self.list_ignore.move_all_items(self.list_exclude)
        self.list_include.move_all_items(self.list_exclude)
        self.set_buttons_enabled_state()

    def move_all_to_ignore_list(self):
        self.list_include.move_all_items(self.list_ignore)
        self.list_exclude.move_all_items(self.list_ignore)
        self.set_buttons_enabled_state()

    def fill_lists(self, includes, excludes):
        """Fill dialog listboxes.

        First clears the contents of the three listboxes, and then populates the listboxes
        from the dictionary of standard CAA types, using the provided 'includes' and
        'excludes' lists to determine the appropriate list for each type.

        Arguments:
            includes -- list of standard image types to place in the "Include" listbox
            excludes -- list of standard image types to place in the "Exclude" listbox
        """
        self.list_include.clear()
        self.list_exclude.clear()
        self.list_ignore.clear()
        for name, title in self._known_types.items():
            item = QtWidgets.QListWidgetItem(title)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, name)
            if name in includes:
                self.list_include.addItem(item)
            elif name in excludes:
                self.list_exclude.addItem(item)
            else:
                self.list_ignore.addItem(item)

    def get_selected_types_include(self):
        return list(self.list_include.all_items_data()) or ['front']

    def get_selected_types_exclude(self):
        return list(self.list_exclude.all_items_data()) or ['none']

    def clear_focus(self, lists):
        for temp_list in lists:
            temp_list.clearSelection()
        self.set_buttons_enabled_state()

    def reset_to_defaults(self):
        self.fill_lists(self._default_include, self._default_exclude)
        self.set_buttons_enabled_state()

    def set_buttons_enabled_state(self):
        has_items_include = self.list_include.count()
        has_items_exclude = self.list_exclude.count()
        has_items_ignore = self.list_ignore.count()

        has_selected_include = bool(self.list_include.selectedItems())
        has_selected_exclude = bool(self.list_exclude.selectedItems())
        has_selected_ignore = bool(self.list_ignore.selectedItems())

        # "Include" list buttons
        self.arrows_include.button_add.setEnabled(has_items_ignore and has_selected_ignore)
        self.arrows_include.button_add_all.setEnabled(has_items_ignore)
        self.arrows_include.button_remove.setEnabled(has_items_include and has_selected_include)
        self.arrows_include.button_remove_all.setEnabled(has_items_include)

        # "Exclude" list buttons
        self.arrows_exclude.button_add.setEnabled(has_items_ignore and has_selected_ignore)
        self.arrows_exclude.button_add_all.setEnabled(has_items_ignore)
        self.arrows_exclude.button_remove.setEnabled(has_items_exclude and has_selected_exclude)
        self.arrows_exclude.button_remove_all.setEnabled(has_items_exclude)

    @staticmethod
    def run(
            parent=None,
            types_include=None, types_exclude=None,
            default_include=None, default_exclude=None,
            known_types=None):
        dialog = CAATypesSelectorDialog(
            parent,
            types_include=types_include, types_exclude=types_exclude,
            default_include=default_include, default_exclude=default_exclude,
            known_types=known_types
        )
        result = dialog.exec_()
        return (dialog.get_selected_types_include(), dialog.get_selected_types_exclude(), result == QtWidgets.QDialog.DialogCode.Accepted)
