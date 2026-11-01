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


from PyQt6 import QtGui

# The default color values are UI-independent and live in picard.colors so
# that core modules (e.g. picard.options) can obtain them without importing
# the GUI layer. The human-readable descriptions stay here because they are
# only meaningful in the UI.
from picard.colors import DEFAULT_INTERFACE_COLORS
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


class DefaultColor:
    def __init__(self, value, description):
        self.value = value
        self.description = description


def _build_default_colors():
    colors: dict[str, dict] = {}
    for theme_name, values in DEFAULT_INTERFACE_COLORS.items():
        colors[theme_name] = {
            name: DefaultColor(value, _COLOR_DESCRIPTIONS.get(name, "FIXME: color desc for %s" % name))
            for name, value in values.items()
        }
    return colors


_DEFAULT_COLORS = _build_default_colors()


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
        Emits colors_changed to notify all consumers.
        """
        self.set_default_colors()
        self.load_from_config()
        theme.colors_changed.emit()

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
theme.theme_changed.connect(interface_colors.reload)


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
