# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Bob Swift
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

from picard.i18n import (
    N_,
    gettext as _,
)

from picard.ui.dialogs.donotshowagainmessagebox import DoNotShowAgainMessageBox
from picard.ui.dialogs.installconfirm import PLUGIN_TRUST_WARNING


class PluginNotesDialog(DoNotShowAgainMessageBox):
    """Dialog for displaying notes specific to the plugins options page."""

    KEY = 'plugin_page_notes'
    TITLE = N_("Plugin Page Notes")

    def __init__(self, parent):
        # One translatable string per paragraph, markup stays out of the msgids
        paragraphs = (
            _("Plugins extend Picard's functionality. Installed plugins are loaded when Picard starts."),
            _(
                "The Plugins page differs from the other option pages. Changes made and "
                "actions taken here are applied immediately, and are not reverted when "
                "the Options dialog is closed without saving."
            ),
            "<strong>%s</strong>" % _(PLUGIN_TRUST_WARNING),
        )
        text = ''.join(f"<p>{paragraph}</p>" for paragraph in paragraphs)

        super().__init__(parent, text=text, icon=QtWidgets.QMessageBox.Icon.Warning)
