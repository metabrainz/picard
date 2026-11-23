# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022-2023 Philipp Wolfer
# Copyright (C) 2023 Bob Swift
# Copyright (C) 2024-2026 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from PyQt6 import QtWidgets

from picard.config import get_config
from picard.i18n import (
    N_,
    gettext as _,
    ngettext,
)

from picard.ui.dialogs.donotshowagainmessagebox import DoNotShowAgainMessageBox


class SaveWarningDialog(DoNotShowAgainMessageBox):
    KEY = 'save_warning'
    TITLE = N_("File Save Warning")

    def __init__(self, parent, file_count):
        actions = []
        config = get_config()

        if config.setting['enable_tag_saving']:
            actions.append(
                ngettext(
                    "overwrite existing metadata (tags) within the file",
                    "overwrite existing metadata (tags) within the files",
                    file_count,
                )
            )
        if config.setting['rename_files']:
            actions.append(ngettext("rename the file", "rename the files", file_count))
        if config.setting['move_files']:
            actions.append(
                ngettext("move the file to a different location", "move the files to a different location", file_count)
            )

        if actions:
            header = ngettext(
                "You are about to save {file_count:,d} file and this will:",
                "You are about to save {file_count:,d} files and this will:",
                file_count,
            ).format(file_count=file_count)
            footer = _("<strong>This action cannot be undone.</strong> Do you want to continue?")
            list_of_actions = ''
            for action in actions:
                list_of_actions += _('<li>{action}</li>').format(action=action)
            warning_text = _('<p>{header}</p><ul>{list_of_actions}</ul><p>{footer}</p>').format(
                header=header, list_of_actions=list_of_actions, footer=footer
            )
        else:
            warning_text = _("There are no actions selected. No changes will be saved.")

        super().__init__(
            parent,
            text=warning_text,
            icon=QtWidgets.QMessageBox.Icon.Warning,
            buttons=QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel,
            default_button=QtWidgets.QMessageBox.StandardButton.Cancel,
        )
