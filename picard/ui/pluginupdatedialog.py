# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2023 Bob Swift
# Copyright (C) 2023 Philipp Wolfer
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

from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QCheckBox,
    QMessageBox,
)


UPDATE_LINES_TO_SHOW = 3


class PluginUpdatesDialog():

    def __init__(self, parent, plugin_names):
        self._plugin_names = sorted(plugin_names)

        self.show_again = True
        show_again_text = _("Perform this check again the next time you start Picard.")

        self.msg = QMessageBox(parent)
        self.msg.setIcon(QMessageBox.Icon.Information)
        self.msg.setText(self._dialog_text)
        self.msg.setWindowTitle(_("Picard Plugins Update"))
        self.msg.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)

        self.cb = QCheckBox(show_again_text)
        self.cb.setChecked(self.show_again)
        self.cb.toggled.connect(self._set_state)

        self.msg.setCheckBox(self.cb)
        self.msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        self.msg.setDefaultButton(QMessageBox.StandardButton.Cancel)

    def _set_state(self):
        self.show_again = not self.show_again

    @property
    def _dialog_text(self):
        file_count = len(self._plugin_names)
        header = '<p>' + ngettext(
            "There is an update available for one of your currently installed plugins:",
            "There are updates available for your currently installed plugins:",
            file_count
        ) + '</p>'
        footer = '<p>' + ngettext(
            "Do you want to update the plugin now?",
            "Do you want to update the plugins now?",
            file_count
        ) + '</p>'

        extra_file_count = file_count - UPDATE_LINES_TO_SHOW
        if extra_file_count > 0:
            extra_plugins = '<p>' + ngettext(
                "plus {extra_file_count:,d} other plugin.",
                "plus {extra_file_count:,d} other plugins.",
                extra_file_count).format(extra_file_count=extra_file_count) + '</p>'
        else:
            extra_plugins = ''

        plugin_list = ''
        for plugin_name in self._plugin_names[:UPDATE_LINES_TO_SHOW]:
            plugin_list += f"<li>{plugin_name}</li>"

        return f'{header}<ul>{plugin_list}</ul>{extra_plugins}{footer}'

    def show(self):
        show_plugins_page = self.msg.exec() == QMessageBox.StandardButton.Yes
        return show_plugins_page, self.show_again
