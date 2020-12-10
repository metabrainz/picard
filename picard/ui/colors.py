# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019 Laurent Monin
# Copyright (C) 2019-2020 Philipp Wolfer
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

from picard.ui.theme import theme


class UnknownColorException(Exception):
    pass


class DefaultColor:

    def __init__(self, value, description):
        qcolor = QtGui.QColor(value)
        self.value = qcolor.name()
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

_DEFAULT_COLORS_DARK = {
    'entity_error': DefaultColor('#C80000', N_("Errored entity")),
    'entity_pending': DefaultColor('#808080', N_("Pending entity")),
    'entity_saved': DefaultColor('#00AA00', N_("Saved entity")),
    'log_debug': DefaultColor('plum', N_('Log view text (debug)')),
    'log_error': DefaultColor('red', N_('Log view text (error)')),
    'log_info': DefaultColor('white', N_('Log view text (info)')),
    'log_warning': DefaultColor('darkorange', N_('Log view text (warning)')),
    'tagstatus_added': DefaultColor('green', N_("Tag added")),
    'tagstatus_changed': DefaultColor('darkgoldenrod', N_("Tag changed")),
    'tagstatus_removed': DefaultColor('red', N_("Tag removed")),
}


class InterfaceColors:

    def __init__(self, dark_theme=None):
        self._dark_theme = dark_theme
        self.set_default_colors()

    @property
    def dark_theme(self):
        if self._dark_theme is None:
            return theme.is_dark_theme
        else:
            return self._dark_theme

    @property
    def default_colors(self):
        if self.dark_theme:
            return _DEFAULT_COLORS_DARK
        else:
            return _DEFAULT_COLORS

    @property
    def _config_key(self):
        if self.dark_theme:
            return 'interface_colors_dark'
        else:
            return 'interface_colors'

    def set_default_colors(self):
        self._colors = dict()
        for color_key in self.default_colors:
            color_value = self.default_colors[color_key].value
            self.set_color(color_key, color_value)

    def set_colors(self, colors_dict):
        for color_key in self.default_colors:
            if color_key in colors_dict:
                color_value = colors_dict[color_key]
            else:
                color_value = self.default_colors[color_key].value
            self.set_color(color_key, color_value)

    def load_from_config(self):
        self.set_colors(config.setting[self._config_key])

    def get_colors(self):
        return self._colors

    def get_color(self, color_key):
        try:
            return self._colors[color_key]
        except KeyError:
            if color_key in self.default_colors:
                return self.default_colors[color_key].value
            raise UnknownColorException("Unknown color key: %s" % color_key)

    def get_qcolor(self, color_key):
        return QtGui.QColor(self.get_color(color_key))

    def get_color_description(self, color_key):
        return _(self.default_colors[color_key].description)

    def set_color(self, color_key, color_value):
        if color_key in self.default_colors:
            qcolor = QtGui.QColor(color_value)
            if not qcolor.isValid():
                qcolor = QtGui.QColor(self.default_colors[color_key].value)
            self._colors[color_key] = qcolor.name()
        else:
            raise UnknownColorException("Unknown color key: %s" % color_key)

    def save_to_config(self):
        # returns True if user has to be warned about color changes
        changed = False
        conf = config.setting[self._config_key]
        for key, color in self._colors.items():
            if key not in conf:
                # new color key, not need to warn user
                conf[key] = color
            elif color != conf[key]:
                # color changed
                conf[key] = color
                changed = True
        for key in set(conf) - set(self.default_colors):
            # old color key, remove
            del conf[key]
        return changed


interface_colors = InterfaceColors()
