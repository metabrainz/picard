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
    error_label: object

    def __init__(self, parent: object = None) -> None:
        """
        Initialize the RatingsOptionsPage, set up the UI and connect logic.
        :param parent: The parent widget.
        Sets up logging for this options page.
        Adds tooltips to all fields.
        Adds error label for UI error messages.
        Sets tab order for main fields to improve accessibility (Tab navigation).
        """
        super().__init__(parent=parent)
        self.ui = Ui_RatingsOptionsPage()
        self.ui.setupUi(self)
        self.logger = logging.getLogger("picard.ui.options.ratings")

        # Tooltips for main fields (internationalized)
        self.ui.enable_ratings.setToolTip(N_(
            "Enable ratings for tracks and albums. This allows you to rate your music and store ratings in MusicBrainz and your local files."
        ))
        self.ui.rating_user_email.setToolTip(N_(
            "Enter your e-mail address for submitting ratings to MusicBrainz. Example: user@example.com"
        ))
        self.ui.submit_ratings.setToolTip(N_(
            "If enabled, ratings will be automatically submitted to MusicBrainz whenever you change them."
        ))
        # Error label for UI error messages
        from PyQt6.QtWidgets import QLabel
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setVisible(False)
        self.ui.verticalLayout.addWidget(self.error_label)
        # Visual focus feedback for input fields
        focus_style = "QLineEdit:focus { border: 2px solid #0078d7; }"  # Blue border on focus
        self.ui.rating_user_email.setStyleSheet(focus_style)
        # Accessibility: Set tab order for main fields
        # This ensures logical navigation using the Tab key (enable_ratings → rating_user_email → submit_ratings)
        try:
            self.setTabOrder(self.ui.enable_ratings, self.ui.rating_user_email)
            self.setTabOrder(self.ui.rating_user_email, self.ui.submit_ratings)
        except Exception:
            pass  # If fields do not exist, do not raise exception

    def load(self: "RatingsOptionsPage") -> None:
        """
        Load current ratings settings from the configuration and update the UI accordingly. Logs errors.
        """
        try:
            config = get_config()
            self.ui.enable_ratings.setChecked(config.setting.get('enable_ratings', False))
            self.ui.rating_user_email.setText(config.setting.get('rating_user_email', ""))
            self.ui.submit_ratings.setChecked(config.setting.get('submit_ratings', False))
            self.error_label.setVisible(False)
        except Exception as e:
            self.logger.error(f"Error loading ratings options: {e}")
            self.error_label.setText(f"Error loading ratings options: {e}")
            self.error_label.setVisible(True)

    def save(self: "RatingsOptionsPage") -> None:
        """
        Save the current ratings settings from the UI to the configuration. Logs errors.
        """
        import re
        from PyQt6.QtCore import QTimer
        email = self.ui.rating_user_email.text()
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$"
        if email and not re.match(email_pattern, email):
            self.error_label.setText("Invalid e-mail address format. Please enter a valid e-mail (e.g. user@example.com).")
            self.error_label.setStyleSheet("color: red;")
            self.error_label.setVisible(True)
            return
        try:
            config = get_config()
            config.setting['enable_ratings'] = self.ui.enable_ratings.isChecked()
            config.setting['rating_user_email'] = email
            config.setting['submit_ratings'] = self.ui.submit_ratings.isChecked()
            self.error_label.setText("Settings saved successfully.")
            self.error_label.setStyleSheet("color: green;")
            self.error_label.setVisible(True)
            QTimer.singleShot(2000, lambda: self.error_label.setVisible(False))
        except Exception as e:
            self.logger.error(f"Error saving ratings options: {e}")
            self.error_label.setText(f"Error saving ratings options: {e}")
            self.error_label.setStyleSheet("color: red;")
            self.error_label.setVisible(True)


register_options_page(RatingsOptionsPage)
