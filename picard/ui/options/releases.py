# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2012 Frederik “Freso” S. Olesen
# Copyright (C) 2013-2015, 2018-2024 Laurent Monin
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Suhas
# Copyright (C) 2018-2022, 2024-2025 Philipp Wolfer
# Copyright (C) 2024 joncrall
# Copyright (C) 2026 Laurent Monin
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


from PyQt6 import QtWidgets

from picard.config import get_config
from picard.const import (
    RELEASE_FORMATS,
    RELEASE_PRIMARY_GROUPS,
    RELEASE_SECONDARY_GROUPS,
)
from picard.const.countries import RELEASE_COUNTRIES
from picard.extension_points.options_pages import register_options_page
from picard.i18n import (
    N_,
    gettext as _,
    gettext_countries,
    pgettext_attributes,
)

from picard.ui.options import (
    OptionsPage,
    PageOptionConfigs,
)
from picard.ui.widgets.preferencelistwidget import PreferenceListWidget
from picard.ui.widgets.titledgroupbox import TitledGroupBox


class ReleasesOptionsPage(OptionsPage):
    NAME = 'releases'
    TITLE = N_("Preferred Releases")
    PARENT = 'metadata'
    SORT_ORDER = 10
    ACTIVE = True
    HELP_URL = "/config/options_releases.html"

    OPTIONS: PageOptionConfigs = {
        'preferred_release_types': {'widgets': ['preferred_release_types_group']},
        'discouraged_release_types': {'widgets': ['discouraged_release_types_group']},
        'preferred_release_countries': {'widgets': ['preferred_release_countries_group']},
        'preferred_release_formats': {'widgets': ['preferred_release_formats_group']},
    }

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Release types available items (primary + secondary, translated)
        self._preferred_release_type_items = {}
        for name in RELEASE_PRIMARY_GROUPS:
            self._preferred_release_type_items[name] = pgettext_attributes('release_group_primary_type', name)
        for name in RELEASE_SECONDARY_GROUPS:
            self._preferred_release_type_items[name] = pgettext_attributes('release_group_secondary_type', name)

        # Preferred release types
        self._preferred_release_types = self._create_preference_group(
            title=N_("Preferred release types (higher priority first)"),
            object_name='preferred_release_types_group',
            tooltip=_(
                "When multiple releases match a file, types listed here are scored higher.<br>"
                "The top item gets the strongest preference.<br>"
                "Unlisted types are treated neutrally."
            ),
            items=self._preferred_release_type_items,
            parent_layout=layout,
        )

        # Discouraged release types
        self._discouraged_release_types = self._create_preference_group(
            title=N_("Discouraged release types (avoided when matching)"),
            object_name='discouraged_release_types_group',
            tooltip=_(
                "Releases with these types are penalized when matching.<br>"
                "They will only be chosen if no other release matches.<br>"
                "Useful for avoiding compilations, DJ-mixes, etc."
            ),
            items=self._preferred_release_type_items,
            parent_layout=layout,
            ordered=False,
        )

        # Cross-exclusion: items in one list can't appear in the other
        self._preferred_release_types.changed.connect(self._sync_type_exclusions)
        self._discouraged_release_types.changed.connect(self._sync_type_exclusions)

        # Preferred release countries
        preferred_release_country_items = {key: gettext_countries(name) for key, name in RELEASE_COUNTRIES.items()}
        self._preferred_release_countries = self._create_preference_group(
            title=N_("Preferred release countries (higher priority first)"),
            object_name='preferred_release_countries_group',
            tooltip=_(
                "When multiple editions of a release exist, "
                "prefer those from countries listed here.<br>"
                "The top country gets the strongest preference."
            ),
            items=preferred_release_country_items,
            parent_layout=layout,
        )

        # Preferred medium formats
        preferred_release_format_items = {
            key: pgettext_attributes('medium_format', name) for key, name in RELEASE_FORMATS.items()
        }
        self._preferred_release_formats = self._create_preference_group(
            title=N_("Preferred medium formats (higher priority first)"),
            object_name='preferred_release_formats_group',
            tooltip=_(
                "When multiple editions of a release exist, "
                "prefer those in formats listed here (e.g. CD over Digital Media).<br>"
                "The top format gets the strongest preference."
            ),
            items=preferred_release_format_items,
            parent_layout=layout,
        )

    def _create_preference_group(
        self,
        title: str,
        object_name: str,
        tooltip: str,
        items: dict[str, str],
        parent_layout: QtWidgets.QVBoxLayout,
        ordered: bool = True,
    ) -> PreferenceListWidget:
        """Create a titled group box with a PreferenceListWidget inside it.

        Returns the PreferenceListWidget for further configuration.
        """
        group = TitledGroupBox(title, self)
        group.setObjectName(object_name)
        group.setToolTip(tooltip)
        group_layout = QtWidgets.QVBoxLayout(group)
        widget = PreferenceListWidget(group, ordered=ordered)
        widget.set_available_items(items)
        group_layout.addWidget(widget)
        parent_layout.addWidget(group)
        setattr(self, object_name, group)
        return widget

    def _sync_type_exclusions(self):
        """Keep preferred and discouraged type lists mutually exclusive."""
        self._preferred_release_types.set_excluded_keys(set(self._discouraged_release_types.selected_keys()))
        self._discouraged_release_types.set_excluded_keys(set(self._preferred_release_types.selected_keys()))

    def load(self):
        config = get_config()
        self._preferred_release_types.set_selected_keys(config.setting['preferred_release_types'])
        self._discouraged_release_types.set_selected_keys(config.setting['discouraged_release_types'])
        self._sync_type_exclusions()
        self._preferred_release_countries.set_selected_keys(config.setting['preferred_release_countries'])
        self._preferred_release_formats.set_selected_keys(config.setting['preferred_release_formats'])

    def save(self):
        config = get_config()
        config.setting['preferred_release_types'] = self._preferred_release_types.selected_keys()
        config.setting['discouraged_release_types'] = self._discouraged_release_types.selected_keys()
        config.setting['preferred_release_countries'] = self._preferred_release_countries.selected_keys()
        config.setting['preferred_release_formats'] = self._preferred_release_formats.selected_keys()

    def restore_defaults(self):
        self._preferred_release_types.set_selected_keys([])
        self._discouraged_release_types.set_selected_keys([])
        self._preferred_release_countries.set_selected_keys([])
        self._preferred_release_formats.set_selected_keys([])
        self._sync_type_exclusions()


register_options_page(ReleasesOptionsPage)
