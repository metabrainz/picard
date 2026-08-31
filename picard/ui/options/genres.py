# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2008 Lukáš Lalinský
# Copyright (C) 2018, 2020-2023, 2025-2026 Philipp Wolfer
# Copyright (C) 2019 Wieland Hoffmann
# Copyright (C) 2019-2026 Laurent Monin
# Copyright (C) 2026 Bob Swift
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


from typing import ClassVar

from picard.config import get_config
from picard.extension_points.options_pages import register_options_page
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.track import TagGenreFilter

from picard.ui.forms.ui_options_genres import Ui_GenresOptionsPage
from picard.ui.options import (
    OptionsPage,
    PageOptionConfigs,
)
from picard.ui.playground import Playground


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


class GenresOptionsPage(OptionsPage):
    NAME = 'genres'
    TITLE = N_("Genres")
    PARENT = 'metadata'
    SORT_ORDER = 20
    ACTIVE = True
    HELP_URL = "/config/options_genres.html"

    OPTIONS: ClassVar[PageOptionConfigs] = {
        'use_genres': {'widgets': ['use_genres']},
        'only_my_genres': {'widgets': ['only_my_genres']},
        'artists_genres': {'widgets': ['artists_genres']},
        'folksonomy_tags': {'widgets': ['folksonomy_tags']},
        'min_genre_usage': {'widgets': ['min_genre_usage']},
        'max_genres': {'widgets': ['max_genres']},
        'join_genres': {'widgets': ['join_genres']},
        'genres_filter': {'widgets': ['genres_filter']},
    }

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_GenresOptionsPage()
        self.ui.setupUi(self)
        self.apply_option_bounds(self.ui.min_genre_usage, 'min_genre_usage')
        self.apply_option_bounds(self.ui.max_genres, 'max_genres')

        self.ui.genres_filter.setToolTip(_(TOOLTIP_GENRES_FILTER))
        self.ui.genres_filter.textChanged.connect(self.update_test_genres_filter)

        self.playground = Playground(_("Test genres filter:"), parent=self)
        self.playground.set_description(
            description=_("Enter genres or folksonomy tags to test, one per line."),
            match_meaning=_("the tag will be kept"),
            skip_meaning=_("the tag will be skipped"),
        )
        self.ui.verticalLayout.addWidget(self.playground)
        self.playground.textChanged.connect(self.update_test_genres_filter)

    def load(self):
        config = get_config()
        self.ui.use_genres.setChecked(config.setting['use_genres'])
        self.ui.max_genres.setValue(config.setting["max_genres"])
        self.ui.min_genre_usage.setValue(config.setting["min_genre_usage"])
        self.ui.join_genres.setEditText(config.setting["join_genres"])
        self.ui.genres_filter.setPlainText(config.setting["genres_filter"])
        self.ui.only_my_genres.setChecked(config.setting["only_my_genres"])
        self.ui.artists_genres.setChecked(config.setting["artists_genres"])
        self.ui.folksonomy_tags.setChecked(config.setting["folksonomy_tags"])

    def save(self):
        config = get_config()
        config.setting['use_genres'] = self.ui.use_genres.isChecked()
        config.setting['max_genres'] = self.ui.max_genres.value()
        config.setting['min_genre_usage'] = self.ui.min_genre_usage.value()
        config.setting['join_genres'] = self.ui.join_genres.currentText()
        config.setting['genres_filter'] = self.ui.genres_filter.toPlainText()
        config.setting['only_my_genres'] = self.ui.only_my_genres.isChecked()
        config.setting['artists_genres'] = self.ui.artists_genres.isChecked()
        config.setting['folksonomy_tags'] = self.ui.folksonomy_tags.isChecked()

    def update_test_genres_filter(self):
        filters = self.ui.genres_filter.toPlainText()
        tagfilter = TagGenreFilter(filters)

        errors = list(tagfilter.format_errors())
        if errors:
            self.playground.set_error("\n".join(errors))
        else:
            self.playground.clear_error()

        def check_line(line: str) -> bool:
            return not tagfilter.skip(line)

        self.playground.update(check_line)


register_options_page(GenresOptionsPage)
