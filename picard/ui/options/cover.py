# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2010, 2018-2021, 2024-2025 Philipp Wolfer
# Copyright (C) 2012, 2014 Wieland Hoffmann
# Copyright (C) 2012-2014 Michael Wiencek
# Copyright (C) 2013-2015, 2018-2021, 2023-2024 Laurent Monin
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Suhas
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2024 Giorgio Fontanive
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


from PyQt6.QtCore import Qt

from picard.config import (
    Option,
    get_config,
)
from picard.const.defaults import (
    DEFAULT_CA_NEVER_REPLACE_TYPE_EXCLUDE,
    DEFAULT_CA_NEVER_REPLACE_TYPE_INCLUDE,
)
from picard.coverart.providers import cover_art_providers
from picard.extension_points.options_pages import register_options_page
from picard.i18n import (
    N_,
    gettext as _,
)

from picard.ui.caa_types_selector import CAATypesSelectorDialog
from picard.ui.forms.ui_options_cover import Ui_CoverOptionsPage
from picard.ui.moveable_list_view import MoveableListView
from picard.ui.options import OptionsPage
from picard.ui.util import qlistwidget_items
from picard.ui.widgets.checkbox_list_item import CheckboxListItem



class CoverOptionsPage(OptionsPage):
    """
    Options page for cover art settings in Picard.
    Provides UI and logic for configuring cover art download, embedding, and provider selection.
    """

    NAME: str = 'cover'
    TITLE: str = N_("Cover Art")
    PARENT: None = None
    SORT_ORDER: int = 35
    ACTIVE: bool = True
    HELP_URL: str = "/config/options_cover.html"

    OPTIONS: tuple[tuple[str, list[str]], ...] = (
        ('save_images_to_tags', ['save_images_to_tags']),
        ('embed_only_one_front_image', ['cb_embed_front_only']),
        ('dont_replace_with_smaller_cover', ['cb_dont_replace_with_smaller']),
        ('dont_replace_cover_of_types', ['cb_never_replace_types']),
        ('dont_replace_included_types', ['dont_replace_included_types']),
        ('dont_replace_excluded_types', ['dont_replace_excluded_types']),
        ('save_images_to_files', ['save_images_to_files']),
        ('cover_image_filename', ['cover_image_filename']),
        ('save_images_overwrite', ['save_images_overwrite']),
        ('save_only_one_front_image', ['save_only_one_front_image']),
        ('image_type_as_filename', ['image_type_as_filename']),
        ('ca_providers', ['ca_providers_list']),
    )

    ui: Ui_CoverOptionsPage
    move_view: MoveableListView
    dont_replace_included_types: list[str] | None
    dont_replace_excluded_types: list[str] | None

    def __init__(self, parent: object = None) -> None:
        """
        Initialisiert die CoverOptionsPage und verbindet UI-Elemente mit der Logik.
        :param parent: Das übergeordnete Widget.
        """
        super().__init__(parent=parent)
        self.ui = Ui_CoverOptionsPage()
        self.ui.setupUi(self)
        self.ui.cover_image_filename.setPlaceholderText(Option.get('setting', 'cover_image_filename').default)
        self.ui.save_images_to_files.clicked.connect(self.update_ca_providers_groupbox_state)
        self.ui.save_images_to_tags.clicked.connect(self.update_ca_providers_groupbox_state)
        self.ui.save_only_one_front_image.toggled.connect(self.ui.image_type_as_filename.setDisabled)
        self.ui.cb_never_replace_types.toggled.connect(self.ui.select_types_button.setEnabled)
        self.ui.select_types_button.clicked.connect(self.select_never_replace_image_types)
        self.move_view = MoveableListView(self.ui.ca_providers_list, self.ui.up_button, self.ui.down_button)


    def restore_defaults(self) -> None:
        """
        Setzt die Einstellungen für Cover Art auf die Standardwerte zurück.
        """
        self.ui.ca_providers_list.clear()
        self.dont_replace_included_types = DEFAULT_CA_NEVER_REPLACE_TYPE_INCLUDE.copy()
        self.dont_replace_excluded_types = DEFAULT_CA_NEVER_REPLACE_TYPE_EXCLUDE.copy()
        super().restore_defaults()


    def _load_cover_art_providers(self) -> None:
        """
        Lädt verfügbare Cover-Art-Provider und initialisiert die zugehörigen Optionen.
        """
        self.ui.ca_providers_list.clear()
        for provider in cover_art_providers():
            try:
                item = CheckboxListItem(_(provider.title), checked=provider.enabled)
                item.setData(Qt.ItemDataRole.UserRole, provider.name)
                self.ui.ca_providers_list.addItem(item)
            except Exception as e:
                import logging
                logging.error(f"Fehler beim Laden des Cover-Art-Providers '{getattr(provider, 'name', repr(provider))}': {e}")


    def load(self) -> None:
        """
        Lädt die aktuellen Cover-Art-Einstellungen aus der Konfiguration und aktualisiert die UI.
        """
        import logging
        try:
            config = get_config()
            self.ui.save_images_to_tags.setChecked(config.setting['save_images_to_tags'])
            self.ui.cb_embed_front_only.setChecked(config.setting['embed_only_one_front_image'])
            self.ui.cb_dont_replace_with_smaller.setChecked(config.setting['dont_replace_with_smaller_cover'])
            self.ui.cb_never_replace_types.setChecked(config.setting['dont_replace_cover_of_types'])
            self.ui.select_types_button.setEnabled(config.setting['dont_replace_cover_of_types'])
            self.dont_replace_included_types = config.setting['dont_replace_included_types']
            self.dont_replace_excluded_types = config.setting['dont_replace_excluded_types']
            self.ui.save_images_to_files.setChecked(config.setting['save_images_to_files'])
            self.ui.cover_image_filename.setText(config.setting['cover_image_filename'])
            self.ui.save_images_overwrite.setChecked(config.setting['save_images_overwrite'])
            self.ui.save_only_one_front_image.setChecked(config.setting['save_only_one_front_image'])
            self.ui.image_type_as_filename.setChecked(config.setting['image_type_as_filename'])
            self._load_cover_art_providers()
            self.ui.ca_providers_list.setCurrentRow(0)
            self.update_ca_providers_groupbox_state()
        except Exception as e:
            logging.error(f"Fehler beim Laden der Cover-Art-Einstellungen: {e}")


    def _ca_providers(self) -> list[tuple[str, bool]]:
        """
        Gibt eine Liste von Tupeln mit Provider-Namen und aktiviertem Status zurück.
        """
        return [
            (str(item.data(Qt.ItemDataRole.UserRole)), bool(item.checked))
            for item in qlistwidget_items(self.ui.ca_providers_list)
        ]


    def save(self) -> None:
        """
        Speichert die aktuellen Cover-Art-Einstellungen aus der UI in die Konfiguration.
        """
        import logging
        try:
            config = get_config()
            config.setting['save_images_to_tags'] = self.ui.save_images_to_tags.isChecked()
            config.setting['embed_only_one_front_image'] = self.ui.cb_embed_front_only.isChecked()
            config.setting['dont_replace_with_smaller_cover'] = self.ui.cb_dont_replace_with_smaller.isChecked()
            config.setting['dont_replace_cover_of_types'] = self.ui.cb_never_replace_types.isChecked()
            config.setting['dont_replace_included_types'] = self.dont_replace_included_types
            config.setting['dont_replace_excluded_types'] = self.dont_replace_excluded_types
            config.setting['save_images_to_files'] = self.ui.save_images_to_files.isChecked()
            config.setting['cover_image_filename'] = self.ui.cover_image_filename.text()
            config.setting['save_images_overwrite'] = self.ui.save_images_overwrite.isChecked()
            config.setting['save_only_one_front_image'] = self.ui.save_only_one_front_image.isChecked()
            config.setting['image_type_as_filename'] = self.ui.image_type_as_filename.isChecked()
            config.setting['ca_providers'] = self._ca_providers()
        except Exception as e:
            logging.error(f"Fehler beim Speichern der Cover-Art-Einstellungen: {e}")


    def update_ca_providers_groupbox_state(self) -> None:
        """
        Aktiviert oder deaktiviert die Cover-Art-Provider-Groupbox basierend auf den Einstellungen.
        """
        files_enabled = self.ui.save_images_to_files.isChecked()
        tags_enabled = self.ui.save_images_to_tags.isChecked()
        self.ui.ca_providers_groupbox.setEnabled(files_enabled or tags_enabled)


    def select_never_replace_image_types(self) -> None:
        """
        Öffnet den Dialog zur Auswahl von Bildtypen, die niemals ersetzt werden sollen.
        """
        instructions_bottom = N_(
            "Eingebettete Cover-Art-Bilder mit einem Typ aus der 'Include'-Liste werden niemals durch ein neu heruntergeladenes Bild ersetzt, "
            "AUSSER sie haben auch einen Bildtyp aus der 'Exclude'-Liste. Bilder mit Typen aus der 'Exclude'-Liste werden immer durch "
            "heruntergeladene Bilder desselben Typs ersetzt. Bildtypen, die weder in der 'Include'- noch in der 'Exclude'-Liste erscheinen, "
            "werden bei der Entscheidung, ob ein eingebettetes Cover-Art-Bild ersetzt wird, nicht berücksichtigt.\n"
        )
        try:
            included_types, excluded_types, ok = CAATypesSelectorDialog.display(
                types_include=self.dont_replace_included_types,
                types_exclude=self.dont_replace_excluded_types,
                parent=self,
                instructions_bottom=instructions_bottom,
            )
            if ok:
                self.dont_replace_included_types = included_types
                self.dont_replace_excluded_types = excluded_types
        except Exception as e:
            import logging
            logging.error(f"Fehler beim Auswählen der Bildtypen: {e}")


register_options_page(CoverOptionsPage)
