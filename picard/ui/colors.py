# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2021, 2024-2026 Laurent Monin
# Copyright (C) 2019-2022 Philipp Wolfer
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


from collections import defaultdict

from PyQt6 import QtGui

from picard.config import get_config
from picard.i18n import (
    N_,
    gettext as _,
)

from picard.ui.theme import theme


class UnknownColorException(Exception):
    pass


class ColorDescription:
    def __init__(self, title, group):
        self.title = title
        self.group = group


_COLOR_DESCRIPTIONS = {
    'entity_error': ColorDescription(title=N_("Errored entity"), group=N_("Entities")),
    'entity_pending': ColorDescription(title=N_("Pending entity"), group=N_("Entities")),
    'entity_saved': ColorDescription(title=N_("Saved entity"), group=N_("Entities")),
    'first_cover_hl': ColorDescription(title=N_("First cover art"), group=N_("Others")),
    'log_debug': ColorDescription(title=N_('Log view text (debug)'), group=N_("Logging")),
    'log_error': ColorDescription(title=N_('Log view text (error)'), group=N_("Logging")),
    'log_info': ColorDescription(title=N_('Log view text (info)'), group=N_("Logging")),
    'log_warning': ColorDescription(title=N_('Log view text (warning)'), group=N_("Logging")),
    'match_similarity_low': ColorDescription(title=N_("Low match similarity background"), group=N_("Others")),
    'profile_hl_bg': ColorDescription(title=N_("Profile highlight background"), group=N_("Profiles")),
    'profile_hl_fg': ColorDescription(title=N_("Profile highlight foreground"), group=N_("Profiles")),
    'tagstatus_added': ColorDescription(title=N_("Tag added"), group=N_("Tags")),
    'tagstatus_changed': ColorDescription(title=N_("Tag changed"), group=N_("Tags")),
    'tagstatus_removed': ColorDescription(title=N_("Tag removed"), group=N_("Tags")),
    'syntax_hl_error': ColorDescription(title=N_("Error syntax highlight"), group=N_("Syntax Highlighting")),
    'syntax_hl_escape': ColorDescription(title=N_("Escape syntax highlight"), group=N_("Syntax Highlighting")),
    'syntax_hl_func': ColorDescription(title=N_("Function syntax highlight"), group=N_("Syntax Highlighting")),
    'syntax_hl_noop': ColorDescription(title=N_("Noop syntax highlight"), group=N_("Syntax Highlighting")),
    'syntax_hl_special': ColorDescription(title=N_("Special syntax highlight"), group=N_("Syntax Highlighting")),
    'syntax_hl_unicode': ColorDescription(title=N_("Unicode syntax highlight"), group=N_("Syntax Highlighting")),
    'syntax_hl_var': ColorDescription(title=N_("Variable syntax highlight"), group=N_("Syntax Highlighting")),
}

_DEFAULT_COLORS: dict[str, dict] = defaultdict(dict)


class DefaultColor:
    def __init__(self, value, description):
        qcolor = QtGui.QColor(value)
        self.value = qcolor.name()
        self.description = description


def register_color(themes, name, value):
    description = _COLOR_DESCRIPTIONS.get(name, "FIXME: color desc for %s" % name)
    for theme_name in themes:
        _DEFAULT_COLORS[theme_name][name] = DefaultColor(value, description)


_DARK = ('dark',)
_LIGHT = ('light',)
_ALL = _DARK + _LIGHT

register_color(_ALL, 'entity_error', '#C80000')
register_color(_ALL, 'entity_pending', '#808080')
register_color(_ALL, 'entity_saved', '#00AA00')
register_color(_LIGHT, 'log_debug', 'purple')
register_color(_DARK, 'log_debug', 'plum')
register_color(_ALL, 'log_error', 'red')
register_color(_LIGHT, 'log_info', 'black')
register_color(_DARK, 'log_info', 'white')
register_color(_ALL, 'log_warning', 'darkorange')
register_color(_ALL, 'tagstatus_added', 'green')
register_color(_ALL, 'tagstatus_changed', 'darkgoldenrod')
register_color(_ALL, 'tagstatus_removed', 'red')
register_color(_DARK, 'profile_hl_fg', '#ffffff')
register_color(_LIGHT, 'profile_hl_fg', '#000000')
register_color(_DARK, 'profile_hl_bg', '#1c71d8')
register_color(_LIGHT, 'profile_hl_bg', '#F9F906')
register_color(_LIGHT, 'first_cover_hl', 'darkgoldenrod')
register_color(_DARK, 'first_cover_hl', 'orange')
register_color(_ALL, 'match_similarity_low', '#DF7D7D')

# syntax highlighting colors
register_color(_LIGHT, 'syntax_hl_error', 'red')
register_color(_LIGHT, 'syntax_hl_escape', 'darkRed')
register_color(_LIGHT, 'syntax_hl_func', 'blue')
register_color(_LIGHT, 'syntax_hl_noop', 'darkGray')
register_color(_LIGHT, 'syntax_hl_special', 'blue')
register_color(_LIGHT, 'syntax_hl_unicode', 'darkRed')
register_color(_LIGHT, 'syntax_hl_var', 'darkCyan')
register_color(_DARK, 'syntax_hl_error', '#F16161')
register_color(_DARK, 'syntax_hl_escape', '#4BEF1F')
register_color(_DARK, 'syntax_hl_func', '#FF57A0')
register_color(_DARK, 'syntax_hl_noop', '#04E7D5')
register_color(_DARK, 'syntax_hl_special', '#FF57A0')
register_color(_DARK, 'syntax_hl_unicode', '#4BEF1F')
register_color(_DARK, 'syntax_hl_var', '#FCBB51')


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
            return _DEFAULT_COLORS['dark']
        else:
            return _DEFAULT_COLORS['light']

    @property
    def _config_key(self):
        if self.dark_theme:
            return 'interface_colors_dark'
        else:
            return 'interface_colors'

    def set_default_colors(self):
        self._colors = {}
        for color_key in self.default_colors:
            self.set_default_color(color_key)

    def reload(self):
        """Reload colors for the current theme from config.

        Call this after a theme switch to pick up the correct color set
        (dark or light) and any user customizations.
        """
        self.set_default_colors()
        self.load_from_config()

    def set_default_color(self, color_key):
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
        config = get_config()
        self.set_colors(config.setting[self._config_key])

    def get_colors(self):
        return self._colors

    def get_color(self, color_key):
        try:
            return self._colors[color_key]
        except KeyError:
            if color_key in self.default_colors:
                return self.default_colors[color_key].value
            raise UnknownColorException("Unknown color key: %s" % color_key) from None

    def get_qcolor(self, color_key):
        return QtGui.QColor(self.get_color(color_key))

    def get_color_css_rgba(self, color_key, alpha=255):
        """Return an rgba() string for use in Qt stylesheets. Alpha is 0-255."""
        color = self.get_qcolor(color_key)
        return f'rgba({color.red()}, {color.green()}, {color.blue()}, {alpha})'

    def get_color_description(self, color_key):
        return _(self.default_colors[color_key].description)

    def get_color_title(self, color_key):
        return _(self.default_colors[color_key].description.title)

    def get_color_group(self, color_key):
        return _(self.default_colors[color_key].description.group)

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
        config = get_config()
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
        config.setting[self._config_key] = conf
        return changed


interface_colors = InterfaceColors()

# Reload colors automatically when the theme changes at runtime.
# After reload, also emit colors_changed to notify color consumers.
theme.theme_changed.connect(interface_colors.reload)
theme.theme_changed.connect(theme.colors_changed)


# Theme-aware validation indicator colors.
# These are not user-configurable; they are standard UX patterns
# (green = success, red = error) that adapt to dark/light themes.
_VALIDATION_COLORS = {
    'light': {'success_bg': '#229922', 'error_bg': '#ff5555'},
    'dark': {'success_bg': '#2d8a2d', 'error_bg': '#cc4444'},
}


def _validation_colors():
    return _VALIDATION_COLORS['dark'] if theme.is_dark_theme else _VALIDATION_COLORS['light']


def stylesheet_validation_success():
    bg = _validation_colors()['success_bg']
    return f"QWidget {{ background-color: {bg}; color: white; padding: 2px; }}"


def stylesheet_validation_error():
    bg = _validation_colors()['error_bg']
    return f"QWidget {{ background-color: {bg}; color: white; font-weight: bold; padding: 2px; }}"
