# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2023 Philipp Wolfer
# Copyright (C) 2019-2024 Laurent Monin
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

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.const.sys import IS_MACOS
from picard.extension_points.options_pages import register_options_page
from picard.i18n import (
    N_,
    gettext as _,
    sort_key,
)
from picard.util import icontheme

from picard.ui.colors import interface_colors
from picard.ui.forms.ui_options_interface_colors import (
    Ui_InterfaceColorsOptionsPage,
)
from picard.ui.options import OptionsPage
from picard.ui.util import changes_require_restart_warning


class ColorButton(QtWidgets.QPushButton):

    color_changed = QtCore.pyqtSignal(str)

    def __init__(self, initial_color=None, parent=None):
        super().__init__('    ', parent=parent)
        # On macOS the style override in picard.ui.theme breaks styling these
        # buttons. Explicitly reset the style for this widget only.
        if IS_MACOS:
            self.setStyle(QtWidgets.QStyleFactory.create('macos'))
        color = QtGui.QColor(initial_color)
        if not color.isValid():
            color = QtGui.QColor('black')
        self.color = color
        self.clicked.connect(self.open_color_dialog)
        self.update_color()

    def update_color(self, qcolor=None):
        if qcolor is not None:
            self.color = qcolor
        self.setStyleSheet("QPushButton { background-color: %s; }" % self.color.name())

    def open_color_dialog(self):
        new_color = QtWidgets.QColorDialog.getColor(
            self.color, title=_("Choose a color"), parent=self.parent())

        if new_color.isValid():
            self.color = new_color
            self.update_color()
            self.color_changed.emit(self.color.name())


def delete_items_of_layout(layout):
    # Credits:
    # https://stackoverflow.com/a/45790404
    # https://riverbankcomputing.com/pipermail/pyqt/2009-November/025214.html
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
            else:
                delete_items_of_layout(item.layout())


class InterfaceColorsOptionsPage(OptionsPage):

    NAME = 'interface_colors'
    TITLE = N_("Colors")
    PARENT = 'interface'
    SORT_ORDER = 30
    ACTIVE = True
    HELP_URL = "/config/options_interface_colors.html"

    OPTIONS = (
        ('interface_colors', ['colors']),
        ('interface_colors_dark', ['colors']),
    )

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_InterfaceColorsOptionsPage()
        self.ui.setupUi(self)
        self.new_colors = {}
        self.colors_list = QtWidgets.QVBoxLayout()
        self.ui.colors.setLayout(self.colors_list)

    def update_color_selectors(self):
        if self.colors_list:
            delete_items_of_layout(self.colors_list)

        def color_changed(color_key, color_value):
            interface_colors.set_color(color_key, color_value)

        def restore_default_color(color_key, color_button):
            interface_colors.set_default_color(color_key)
            color_button.update_color(interface_colors.get_qcolor(color_key))

        def colors():
            for color_key, color_value in interface_colors.get_colors().items():
                group = interface_colors.get_color_group(color_key)
                title = interface_colors.get_color_title(color_key)
                yield color_key, color_value, title, group

        prev_group = None
        for color_key, color_value, title, group in sorted(colors(), key=lambda c: (sort_key(c[3]), sort_key(c[2]))):
            if prev_group != group:
                groupbox = QtWidgets.QGroupBox(group)
                self.colors_list.addWidget(groupbox)
                groupbox_layout = QtWidgets.QVBoxLayout()
                groupbox.setLayout(groupbox_layout)
                prev_group = group

            widget = QtWidgets.QWidget()

            hlayout = QtWidgets.QHBoxLayout()
            hlayout.setContentsMargins(0, 0, 0, 0)

            label = QtWidgets.QLabel(title)
            label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
            hlayout.addWidget(label)

            color_button = ColorButton(color_value)
            color_button.color_changed.connect(partial(color_changed, color_key))
            hlayout.addWidget(color_button, 0, QtCore.Qt.AlignmentFlag.AlignRight)

            refresh_button = QtWidgets.QPushButton(icontheme.lookup('view-refresh'), "")
            refresh_button.setToolTip(_("Restore default color"))
            refresh_button.clicked.connect(partial(restore_default_color, color_key, color_button))
            hlayout.addWidget(refresh_button, 0, QtCore.Qt.AlignmentFlag.AlignRight)

            widget.setLayout(hlayout)
            groupbox_layout.addWidget(widget)

        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.colors_list.addItem(spacerItem1)

    def load(self):
        interface_colors.load_from_config()
        self.update_color_selectors()

    def save(self):
        if interface_colors.save_to_config():
            changes_require_restart_warning(self, warnings=[_("You have changed the interface colors.")])

    def restore_defaults(self):
        interface_colors.set_default_colors()
        self.update_color_selectors()


register_options_page(InterfaceColorsOptionsPage)
