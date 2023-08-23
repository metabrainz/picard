# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2008 Lukáš Lalinský
# Copyright (C) 2018, 2020-2023 Philipp Wolfer
# Copyright (C) 2019 Wieland Hoffmann
# Copyright (C) 2019-2022 Laurent Monin
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


from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QTextBlockFormat,
    QTextCursor,
)

from picard.config import (
    BoolOption,
    IntOption,
    TextOption,
    get_config,
)
from picard.track import TagGenreFilter

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_genres import Ui_GenresOptionsPage


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

    NAME = "genres"
    TITLE = N_("Genres")
    PARENT = "metadata"
    SORT_ORDER = 20
    ACTIVE = True
    HELP_URL = '/config/options_genres.html'

    options = [
        BoolOption("setting", "use_genres", False),
        IntOption("setting", "max_genres", 5),
        IntOption("setting", "min_genre_usage", 90),
        TextOption("setting", "genres_filter", "-seen live\n-favorites\n-fixme\n-owned"),
        TextOption("setting", "join_genres", ""),
        BoolOption("setting", "only_my_genres", False),
        BoolOption("setting", "artists_genres", False),
        BoolOption("setting", "folksonomy_tags", False),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_GenresOptionsPage()
        self.ui.setupUi(self)

        self.ui.genres_filter.setToolTip(_(TOOLTIP_GENRES_FILTER))
        self.ui.genres_filter.textChanged.connect(self.update_test_genres_filter)

        self.ui.test_genres_filter.setToolTip(_(TOOLTIP_TEST_GENRES_FILTER))
        self.ui.test_genres_filter.textChanged.connect(self.update_test_genres_filter)

        # FIXME: colors aren't great from accessibility POV
        self.fmt_keep = QTextBlockFormat()
        self.fmt_keep.setBackground(Qt.GlobalColor.green)

        self.fmt_skip = QTextBlockFormat()
        self.fmt_skip.setBackground(Qt.GlobalColor.red)

        self.fmt_clear = QTextBlockFormat()
        self.fmt_clear.clearBackground()

    def load(self):
        config = get_config()
        self.ui.use_genres.setChecked(config.setting["use_genres"])
        self.ui.max_genres.setValue(config.setting["max_genres"])
        self.ui.min_genre_usage.setValue(config.setting["min_genre_usage"])
        self.ui.join_genres.setEditText(config.setting["join_genres"])
        self.ui.genres_filter.setPlainText(config.setting["genres_filter"])
        self.ui.only_my_genres.setChecked(config.setting["only_my_genres"])
        self.ui.artists_genres.setChecked(config.setting["artists_genres"])
        self.ui.folksonomy_tags.setChecked(config.setting["folksonomy_tags"])

    def save(self):
        config = get_config()
        config.setting["use_genres"] = self.ui.use_genres.isChecked()
        config.setting["max_genres"] = self.ui.max_genres.value()
        config.setting["min_genre_usage"] = self.ui.min_genre_usage.value()
        config.setting["join_genres"] = self.ui.join_genres.currentText()
        config.setting["genres_filter"] = self.ui.genres_filter.toPlainText()
        config.setting["only_my_genres"] = self.ui.only_my_genres.isChecked()
        config.setting["artists_genres"] = self.ui.artists_genres.isChecked()
        config.setting["folksonomy_tags"] = self.ui.folksonomy_tags.isChecked()

    def update_test_genres_filter(self):
        test_text = self.ui.test_genres_filter.toPlainText()

        filters = self.ui.genres_filter.toPlainText()
        tagfilter = TagGenreFilter(filters)

        # FIXME: very simple error reporting, improve
        self.ui.label_test_genres_filter_error.setText(
            "\n".join(
                _("Error line %(lineno)d: %(error)s") % {'lineno': lineno + 1, 'error': error}
                for lineno, error in tagfilter.errors.items()
            )
        )

        def set_line_fmt(lineno, textformat):
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


register_options_page(GenresOptionsPage)
