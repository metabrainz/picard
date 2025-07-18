# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2008 Lukáš Lalinský
# Copyright (C) 2018, 2020-2023, 2025 Philipp Wolfer
# Copyright (C) 2019 Wieland Hoffmann
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


import logging
from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QTextBlockFormat,
    QTextCursor,
)

from picard.config import get_config
from picard.extension_points.options_pages import register_options_page
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.track import TagGenreFilter

from picard.ui.forms.ui_options_genres import Ui_GenresOptionsPage
from picard.ui.options import OptionsPage


TOOLTIP_GENRES_FILTER = N_("""<html><head/><body>
<p>Lines not starting with <b>-</b> or <b>+</b> are ignored.</p>
<p>One expression per line, case-insensitive</p>
<p>Examples:</p>
<p><b>
#comment<br/>
!comment<br/>
comment
</b></p>
<p><u>Strict filtering:</u></p>
<p>
<b>-word</b>: exclude <i>word</i><br/>
<b>+word</b>: include <i>word</i>
</p>
<p><u>Wildcard filtering:</u></p>
<p>
<b>-*word</b>: exclude all genres ending with <i>word</i><br/>
<b>+word*</b>: include all genres starting with <i>word</i><br/>
<b>+wor?</b>: include all genres starting with <i>wor</i> and ending with an arbitrary character<br/>
<b>+wor[dk]</b>: include all genres starting with <i>wor</i> and ending with <i>d</i> or <i>k</i><br/>
<b>-w*rd</b>: exclude all genres starting with <i>w</i> and ending with <i>rd</i>
</p>
<p><u>Regular expressions filtering (Python re syntax):</u></p>
<p><b>-/^w.rd+/</b>: exclude genres starting with <i>w</i> followed by any character, then <i>r</i> followed by at least one <i>d</i>
</p>
</body></html>""")

TOOLTIP_TEST_GENRES_FILTER = N_("""<html><head/><body>
<p>You can add genres to test filters against, one per line.<br/>
This playground will not be preserved on Options exit.
</p>
<p>
Red background means the tag will be skipped.<br/>
Green background means the tag will be kept.
</p>
</body></html>""")


class GenresOptionsPage(OptionsPage):
    """
    Options page for configuring genre handling in Picard.
    Provides UI and logic for genre-related settings and filtering.
    """

    NAME: str = 'genres'
    TITLE: str = N_("Genres")
    PARENT: str = 'metadata'
    SORT_ORDER: int = 20
    ACTIVE: bool = True
    HELP_URL: str = "/config/options_genres.html"

    OPTIONS: tuple[tuple[str, list[str] | None], ...] = (
        ('use_genres', None),
        ('only_my_genres', ['only_my_genres']),
        ('artists_genres', ['artists_genres']),
        ('folksonomy_tags', ['folksonomy_tags']),
        ('min_genre_usage', ['min_genre_usage']),
        ('max_genres', ['max_genres']),
        ('join_genres', ['join_genres']),
        ('genres_filter', ['genres_filter']),
    )

    ui: Ui_GenresOptionsPage
    fmt_keep: QTextBlockFormat
    fmt_skip: QTextBlockFormat
    fmt_clear: QTextBlockFormat
    logger: logging.Logger

    def __init__(self, parent: object = None) -> None:
        """
        Initialize the GenresOptionsPage, set up the UI and connect logic.
        :param parent: The parent widget.
        Sets up logging for this options page.
        """
        super().__init__(parent=parent)
        self.ui = Ui_GenresOptionsPage()
        self.ui.setupUi(self)
        self.logger = logging.getLogger("picard.ui.options.genres")

        # Tooltips for main fields (English)
        self.ui.use_genres.setToolTip("Enable genres for tags.")
        self.ui.only_my_genres.setToolTip("Use only your own genres, not those from MusicBrainz.")
        self.ui.artists_genres.setToolTip("Use genres from artists if available.")
        self.ui.folksonomy_tags.setToolTip("Use folksonomy tags as genres.")
        self.ui.min_genre_usage.setToolTip("Minimum usage for a genre to be included.")
        self.ui.max_genres.setToolTip("Maximum number of genres per release.")
        self.ui.join_genres.setToolTip("Separator for joined genres.")
        self.ui.genres_filter.setToolTip(_(TOOLTIP_GENRES_FILTER))
        self.ui.genres_filter.textChanged.connect(self.update_test_genres_filter)

        self.ui.test_genres_filter.setToolTip(_(TOOLTIP_TEST_GENRES_FILTER))
        self.ui.test_genres_filter.textChanged.connect(self.update_test_genres_filter)

        # Accessibility: color feedback for filter results
        self.fmt_keep = QTextBlockFormat()
        self.fmt_keep.setBackground(Qt.GlobalColor.green)

        self.fmt_skip = QTextBlockFormat()
        self.fmt_skip.setBackground(Qt.GlobalColor.red)

        self.fmt_clear = QTextBlockFormat()
        self.fmt_clear.clearBackground()

    def load(self: "GenresOptionsPage") -> None:
        """
        Load current genre settings from the configuration and update the UI accordingly. Logs errors.
        """
        try:
            config = get_config()
            self.ui.use_genres.setChecked(config.setting.get('use_genres', False))
            self.ui.max_genres.setValue(config.setting.get("max_genres", 0))
            self.ui.min_genre_usage.setValue(config.setting.get("min_genre_usage", 0))
            self.ui.join_genres.setEditText(config.setting.get("join_genres", ""))
            self.ui.genres_filter.setPlainText(config.setting.get("genres_filter", ""))
            self.ui.only_my_genres.setChecked(config.setting.get("only_my_genres", False))
            self.ui.artists_genres.setChecked(config.setting.get("artists_genres", False))
            self.ui.folksonomy_tags.setChecked(config.setting.get("folksonomy_tags", False))
        except Exception as e:
            self.logger.error(f"Error loading genre options: {e}")

    def save(self: "GenresOptionsPage") -> None:
        """
        Save the current genre settings from the UI to the configuration. Logs errors.
        """
        try:
            config = get_config()
            config.setting['use_genres'] = self.ui.use_genres.isChecked()
            config.setting['max_genres'] = self.ui.max_genres.value()
            config.setting['min_genre_usage'] = self.ui.min_genre_usage.value()
            config.setting['join_genres'] = self.ui.join_genres.currentText()
            config.setting['genres_filter'] = self.ui.genres_filter.toPlainText()
            config.setting['only_my_genres'] = self.ui.only_my_genres.isChecked()
            config.setting['artists_genres'] = self.ui.artists_genres.isChecked()
            config.setting['folksonomy_tags'] = self.ui.folksonomy_tags.isChecked()
        except Exception as e:
            self.logger.error(f"Error saving genre options: {e}")

    def update_test_genres_filter(self: "GenresOptionsPage") -> None:
        """
        Update the test genres filter UI, providing color feedback for each test genre line. Logs errors.
        """
        try:
            test_text = self.ui.test_genres_filter.toPlainText()

            filters = self.ui.genres_filter.toPlainText()
            tagfilter = TagGenreFilter(filters)

            # Simple error reporting for filter syntax
            self.ui.label_test_genres_filter_error.setText(
                "\n".join(tagfilter.format_errors())
            )

            def set_line_fmt(lineno: int, textformat: QTextBlockFormat) -> None:
                """
                Set the background color for a line in the test genres filter UI.
                :param lineno: Line number to format, or -1 for current cursor.
                :param textformat: QTextBlockFormat to apply.
                """
                obj = self.ui.test_genres_filter
                if lineno < 0:
                    # use current cursor position
                    cursor = obj.textCursor()
                else:
                    cursor = QTextCursor(obj.document().findBlockByNumber(lineno))
                obj.blockSignals(True)
                cursor.setBlockFormat(textformat)
                obj.blockSignals(False)

            set_line_fmt(-1, self.fmt_clear)
            for lineno, line in enumerate(test_text.splitlines()):
                line = line.strip()
                fmt = self.fmt_clear
                if line:
                    if tagfilter.skip(line):
                        fmt = self.fmt_skip
                    else:
                        fmt = self.fmt_keep
                set_line_fmt(lineno, fmt)
        except Exception as e:
            self.logger.error(f"Error updating test genres filter: {e}")


register_options_page(GenresOptionsPage)
