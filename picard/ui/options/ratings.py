# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2008-2009, 2020-2021, 2025 Philipp Wolfer
# Copyright (C) 2012-2013 Michael Wiencek
# Copyright (C) 2018, 2020-2021, 2023-2024 Laurent Monin
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


import logging
from picard.config import get_config
from picard.extension_points.options_pages import register_options_page
from picard.i18n import N_

from picard.ui.forms.ui_options_ratings import Ui_RatingsOptionsPage
from picard.ui.options import OptionsPage


class RatingsOptionsPage(OptionsPage):
    """
    Options page for configuring ratings in Picard.
    Provides UI and logic for rating-related settings.
    """

    NAME: str = 'ratings'
    TITLE: str = N_("Ratings")
    PARENT: str = 'metadata'
    SORT_ORDER: int = 20
    ACTIVE: bool = True
    HELP_URL: str = "/config/options_ratings.html"

    OPTIONS: tuple[tuple[str, list[str]], ...] = (
        ('enable_ratings', ['enable_ratings']),
        ('rating_user_email', ['rating_user_email']),
        ('submit_ratings', ['submit_ratings']),
    )

    ui: Ui_RatingsOptionsPage
    logger: logging.Logger

    def __init__(self, parent: object = None) -> None:
        """
        Initialize the RatingsOptionsPage, set up the UI and connect logic.
        :param parent: The parent widget.
        Sets up logging for this options page.
        """
        super().__init__(parent=parent)
        self.ui = Ui_RatingsOptionsPage()
        self.ui.setupUi(self)
        self.logger = logging.getLogger("picard.ui.options.ratings")

    def load(self: "RatingsOptionsPage") -> None:
        """
        Load current ratings settings from the configuration and update the UI accordingly. Logs errors.
        """
        try:
            config = get_config()
            self.ui.enable_ratings.setChecked(config.setting.get('enable_ratings', False))
            self.ui.rating_user_email.setText(config.setting.get('rating_user_email', ""))
            self.ui.submit_ratings.setChecked(config.setting.get('submit_ratings', False))
        except Exception as e:
            self.logger.error(f"Error loading ratings options: {e}")

    def save(self: "RatingsOptionsPage") -> None:
        """
        Save the current ratings settings from the UI to the configuration. Logs errors.
        """
        try:
            config = get_config()
            config.setting['enable_ratings'] = self.ui.enable_ratings.isChecked()
            config.setting['rating_user_email'] = self.ui.rating_user_email.text()
            config.setting['submit_ratings'] = self.ui.submit_ratings.isChecked()
        except Exception as e:
            self.logger.error(f"Error saving ratings options: {e}")


register_options_page(RatingsOptionsPage)
