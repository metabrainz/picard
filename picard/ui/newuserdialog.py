# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022-2023 Philipp Wolfer
# Copyright (C) 2023, 2025 Bob Swift
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


from PyQt6 import (
    QtCore,
    QtGui,
)

from picard.i18n import (
    N_,
    gettext as _,
)
from picard.util import get_url

from picard.ui.dialogs.donotshowagainmessagebox import DoNotShowAgainMessageBox


class NewUserDialog(DoNotShowAgainMessageBox):
    KEY = 'new_user'
    TITLE = N_("New User Warning")

    def __init__(self, parent):
        text = _(
            "<p>"
            "<strong>Changes made by Picard are not reversible.</strong>"
            "</p><p>"
            "Picard is a very flexible music tagging tool which can rename your files and overwrite the tags. "
            "We <strong>strongly recommend</strong> that you:"
            "</p><ul>"
            "<li>read the <a href='{documentation_url}'>User Guide</a> (also available from the Help menu)</li>"
            "<li>test with copies of your music and work in small batches</li>"
            "</ul><p>"
            "Picard is open source software written by volunteers. It is provided as-is and with no warranty."
            "</p>"
        ).format(documentation_url=get_url('documentation_server'))
        super().__init__(parent, text=text)
        pixmap = QtGui.QPixmap(":/images/wizard-welcome.png")
        self.setIconPixmap(
            pixmap.scaled(
                128, 128, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation
            )
        )
