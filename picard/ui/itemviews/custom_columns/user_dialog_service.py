# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
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

"""User dialog service for common dialog interactions."""

from typing import Literal

from PyQt6 import QtWidgets  # type: ignore[unresolved-import]

from picard.i18n import gettext as _


UnsavedAction = Literal["save", "discard", "cancel"]


class UserDialogService:
    """Provides common dialog interactions for user prompts."""

    def __init__(self, parent_widget: QtWidgets.QWidget) -> None:
        """Initialize the service with a parent widget."""
        self._parent_widget = parent_widget

    def ask_unsaved_changes(self, message: str) -> QtWidgets.QMessageBox.StandardButton:
        """Prompt user to handle unsaved changes.

        Returns
        -------
        QtWidgets.QMessageBox.StandardButton
            User's choice: "save", "discard", or "cancel".
        """
        return QtWidgets.QMessageBox.question(
            self._parent_widget,
            _("Unsaved Changes"),
            message,
            QtWidgets.QMessageBox.StandardButton.Save
            | QtWidgets.QMessageBox.StandardButton.Discard
            | QtWidgets.QMessageBox.StandardButton.Cancel,
            QtWidgets.QMessageBox.StandardButton.Save,
        )

    def confirm_discard_changes(self) -> bool:
        """Prompt user to confirm discarding changes.

        Returns
        -------
        bool
            True if user confirms discard, False otherwise.
        """
        reply: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.question(
            self._parent_widget,
            _("Confirm Discard"),
            _("You have unsaved changes that will be lost. Do you want to continue without saving?"),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        return reply == QtWidgets.QMessageBox.StandardButton.Yes

    def can_change_selection(self, has_uncommitted_changes: bool) -> bool:
        """Check if selection can be changed, prompting user if there are unsaved changes.

        Parameters
        ----------
        has_uncommitted_changes : bool
            Indicates if there are unsaved changes.

        Returns
        -------
        bool
            True if selection change is allowed, False otherwise.
        """
        if not has_uncommitted_changes:
            return True

        return self.confirm_discard_changes()

    def confirm_delete_column(self, title: str) -> bool:
        """Prompt user to confirm deletion of a custom column.

        Parameters
        ----------
        title : str
            Title of the column to be deleted.

        Returns
        -------
        bool
            True if user confirms deletion, False otherwise.
        """
        reply: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.question(
            self._parent_widget,
            _("Confirm Delete"),
            _("Are you sure you want to delete the custom column '{title}'?").format(title=title),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        return reply == QtWidgets.QMessageBox.StandardButton.Yes

    def confirm_delete_columns(self, count: int) -> bool:
        """Prompt user to confirm deletion of multiple custom columns.

        Parameters
        ----------
        count : int
            Number of columns to be deleted.

        Returns
        -------
        bool
            True if user confirms deletion, False otherwise.
        """
        reply: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.question(
            self._parent_widget,
            _("Confirm Delete"),
            _("Are you sure you want to delete {n} selected custom columns?").format(n=count),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        return reply == QtWidgets.QMessageBox.StandardButton.Yes

    def show_invalid_spec_errors(self, messages: list[str], spec_title: str | None = None) -> None:
        """Show validation errors for an invalid specification.

        Parameters
        ----------
        messages : list[str]
            Error messages to show, one per validation error.
        spec_title : str | None
            The column title, used in title and message if provided.
        """
        # Use spec_title if provided and non-empty, otherwise use default
        title = _("Invalid column: %s") % spec_title if spec_title and spec_title.strip() else _("Invalid column")

        # Build the complete message
        dialog_message = title + "\n" + "\n".join(messages)

        # Show the warning dialog
        QtWidgets.QMessageBox.warning(
            self._parent_widget,
            title,
            dialog_message,
        )
