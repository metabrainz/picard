# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2014 Lukáš Lalinský
# Copyright (C) 2008, 2013, 2018-2024 Philipp Wolfer
# Copyright (C) 2011 Pavan Chander
# Copyright (C) 2011, 2013 Wieland Hoffmann
# Copyright (C) 2013 Michael Wiencek
# Copyright (C) 2013-2015, 2018, 2020-2026 Laurent Monin
# Copyright (C) 2014 Ismael Olea
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2021 Bob Swift
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


from PyQt6 import (
    QtCore,
    QtGui,
)

from picard import tagger_instance
from picard.config import get_config
from picard.const import PICARD_URLS
from picard.i18n import gettext as _
from picard.util import (
    get_url,
    webbrowser2,
)
from picard.util.versions import (
    as_dict,
    version_name,
)

from picard.ui import (
    PicardDialog,
    SingletonDialog,
)
from picard.ui.forms.ui_aboutdialog import Ui_AboutDialog
from picard.ui.theme import theme


class AboutDialog(PicardDialog, SingletonDialog):
    modality = QtCore.Qt.WindowModality.NonModal

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.ui = Ui_AboutDialog()
        self.ui.setupUi(self)
        self._apply_styling()
        self._update_content()

    def _apply_styling(self):
        """Apply accent color and visual styling to the dialog."""
        accent_color = theme.accent_color
        if accent_color:
            accent_css = accent_color.name()
            # Style section headings with accent color
            heading_style = f"color: {accent_css};"
            self.ui.formats_heading.setStyleSheet(heading_style)
            self.ui.donate_heading.setStyleSheet(heading_style)
            self.ui.credits_heading.setStyleSheet(heading_style)
            self.ui.website_heading.setStyleSheet(heading_style)

            # Style the donate button with accent color
            text_color = 'white' if accent_color.lightness() < 160 else 'black'
            hover_color = accent_color.lighter(120).name()
            button_style = f"""
                QPushButton {{
                    background-color: {accent_css};
                    color: {text_color};
                    border: none;
                    border-radius: 4px;
                    padding: 8px 24px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                }}
                QPushButton:pressed {{
                    background-color: {accent_css};
                }}
            """
            self.ui.donate_button.setStyleSheet(button_style)
            self.ui.translate_button.setStyleSheet(button_style)

        # Bold version label
        font = self.ui.version_label.font()
        font.setBold(True)
        self.ui.version_label.setFont(font)

        # Inset separators with margin
        separator_style = "margin-left: 40px; margin-right: 40px;"
        self.ui.separator_1.setStyleSheet(separator_style)
        self.ui.separator_2.setStyleSheet(separator_style)
        self.ui.separator_3.setStyleSheet(separator_style)
        self.ui.separator_4.setStyleSheet(separator_style)

        # Muted color for version details and formats
        palette = self.palette()
        muted_color = palette.color(QtGui.QPalette.ColorRole.Text)
        muted_color.setAlpha(160)
        muted_css = f"color: {muted_color.name(QtGui.QColor.NameFormat.HexArgb)};"
        self.ui.versions_detail_label.setStyleSheet(muted_css)
        self.ui.formats_label.setStyleSheet(muted_css)

    def _update_content(self):
        versions_dict = as_dict(i18n=True)

        # Version label
        version_text = _("Version %s") % versions_dict['version']
        self.ui.version_label.setText(version_text)

        # Third-party versions detail
        third_parties = ', '.join(
            f"{version_name(name)} {value}" for name, value in versions_dict.items() if name != 'version'
        )
        self.ui.versions_detail_label.setText(third_parties)

        # Supported formats
        tagger = tagger_instance()
        formats = ", ".join(ext[1:] for ext in tagger.format_registry.supported_extensions())
        self.ui.formats_label.setText(formats)

        # Donate section
        self.ui.donate_button.clicked.connect(self._open_donate_url)

        # Credits section
        # Project credit with links
        self.ui.project_credit_label.linkHovered.connect(self.ui.project_credit_label.setToolTip)

        authors_credits = ", ".join(
            [
                'Robert Kaye',
                'Lukáš Lalinský',
                'Laurent Monin',
                'Sambhav Kothari',
                'Philipp Wolfer',
                'Bob Swift',
            ]
        )
        copyright_text = _("Copyright © %(copyright_years)s %(authors_credits)s and others") % {
            'copyright_years': '2004-2026',
            'authors_credits': authors_credits,
        }
        self.ui.copyright_label.setText(copyright_text)

        # Translator credits
        config = get_config()
        ui_language = config.setting['ui_language']
        if ui_language != 'en':
            self.ui.translator_credits.setVisible(True)
            self.ui.translate_button.clicked.connect(self._open_translate_url)
        else:
            self.ui.translator_credits.setVisible(False)

        # Icons credits (contains HTML links)
        icons_credits = _(
            'Icons made by Sambhav Kothari '
            'and <a href="http://www.flaticon.com/authors/madebyoliver">Madebyoliver</a>, '
            '<a href="http://www.flaticon.com/authors/pixel-buddha">Pixel Buddha</a>, '
            '<a href="http://www.flaticon.com/authors/nikita-golubev">Nikita Golubev</a>, '
            '<a href="http://www.flaticon.com/authors/maxim-basinski">Maxim Basinski</a>, '
            '<a href="https://www.flaticon.com/authors/smashicons">Smashicons</a> '
            'from <a href="https://www.flaticon.com">www.flaticon.com</a>'
        )
        self.ui.icons_credits_label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.ui.icons_credits_label.setText(icons_credits)
        self.ui.icons_credits_label.linkHovered.connect(self.ui.icons_credits_label.setToolTip)

        # Links section
        self.ui.website_heading.setText(_("Links"))
        links = [
            (PICARD_URLS['home'], _("Official website")),
            (get_url('documentation_server'), _("Documentation")),
            (PICARD_URLS['forum'], _("Community forum")),
            (PICARD_URLS['license'], _("License")),
        ]
        links_html = " · ".join(f'<a href="{url}">{label}</a>' for url, label in links)
        self.ui.website_link_label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.ui.website_link_label.setText(links_html)
        self.ui.website_link_label.linkHovered.connect(self.ui.website_link_label.setToolTip)

    def _open_donate_url(self):
        webbrowser2.open('donate')

    def _open_translate_url(self):
        webbrowser2.open('translate')
