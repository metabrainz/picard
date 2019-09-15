# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2019 Laurent Monin
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

from PyQt5 import QtGui

from picard import config


class DefaultColor:

    def __init__(self, value, description):
        self.value = value
        self.description = description


_DEFAULT_COLORS = {
    'entity_error': DefaultColor('#C80000', N_("Errored entity")),
    'entity_pending': DefaultColor('#808080', N_("Pending entity")),
    'entity_saved': DefaultColor('#00AA00', N_("Saved entity")),
    'log_debug': DefaultColor('purple', N_('Log view text (debug)')),
    'log_error': DefaultColor('red', N_('Log view text (error)')),
    'log_info': DefaultColor('black', N_('Log view text (info)')),
    'log_warning': DefaultColor('darkorange', N_('Log view text (warning)')),
    'tagstatus_added': DefaultColor('green', N_("Tag added")),
    'tagstatus_changed': DefaultColor('darkgoldenrod', N_("Tag changed")),
    'tagstatus_removed': DefaultColor('red', N_("Tag removed")),
}


class InterfaceColors:

    def __init__(self):
        self.default_colors()

    def default_colors(self):
        self._colors = dict()
        for color_key in _DEFAULT_COLORS:
            color_value = _DEFAULT_COLORS[color_key].value
            self.set_color(color_key, color_value)

    def set_colors(self, colors_dict):
        for color_key in _DEFAULT_COLORS:
            if color_key in colors_dict:
                color_value = colors_dict[color_key]
            else:
                color_value = _DEFAULT_COLORS[color_key].value
            self.set_color(color_key, color_value)

    def load_from_config(self):
        self.set_colors(config.setting['interface_colors'])

    def get_colors(self):
        return self._colors

    def get_color(self, color_key):
        try:
            return self._colors[color_key]
        except KeyError:
            if color_key in _DEFAULT_COLORS:
                return _DEFAULT_COLORS[color_key].value
            raise Exception("Unknown color key: %s" % color_key)

    def get_qcolor(self, color_key):
        return QtGui.QColor(self.get_color(color_key))

    @staticmethod
    def get_color_description(color_key):
        return _(_DEFAULT_COLORS[color_key].description)

    def set_color(self, color_key, color_value):
        if color_key in _DEFAULT_COLORS:
            qcolor = QtGui.QColor(color_value)
            if qcolor.isValid():
                color = qcolor.name()
            else:
                color = _DEFAULT_COLORS[color_key].value
            self._colors[color_key] = color
        else:
            raise Exception("Unknown color key: %s" % color_key)


interface_colors = InterfaceColors()
