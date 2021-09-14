# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2014 Lukáš Lalinský
# Copyright (C) 2008, 2013, 2018-2021 Philipp Wolfer
# Copyright (C) 2011 Pavan Chander
# Copyright (C) 2011, 2013 Wieland Hoffmann
# Copyright (C) 2013 Michael Wiencek
# Copyright (C) 2013-2015, 2018, 2020 Laurent Monin
# Copyright (C) 2014 Ismael Olea
# Copyright (C) 2017 Sambhav Kothari
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


from PyQt5 import QtCore

from picard.config import get_config
from picard.const import PICARD_URLS
from picard.formats import supported_extensions
from picard.util import versions

from picard.ui import (
    PicardDialog,
    SingletonDialog,
)
from picard.ui.ui_aboutdialog import Ui_AboutDialog


class AboutDialog(PicardDialog, SingletonDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.ui = Ui_AboutDialog()
        self.ui.setupUi(self)
        self._update_content()

    def _update_content(self):
        args = versions.as_dict(i18n=True)

        args['third_parties_versions'] = ', '.join([
            ("%s %s" % (versions.version_name(name), value))
            .replace(' ', '&nbsp;')
            .replace('-', '&#8209;')  # non-breaking hyphen
            for name, value
            in versions.as_dict(i18n=True).items()
            if name != 'version'])

        config = get_config()
        args['ini_file'] = config.fileName()

        args['formats'] = ", ".join(map(lambda x: x[1:], supported_extensions()))
        args['copyright_years'] = '2004-2021'
        args['authors_credits'] = ", ".join([
            'Robert Kaye',
            'Lukáš Lalinský',
            'Laurent Monin',
            'Sambhav Kothari',
            'Philipp Wolfer',
        ])

        # TR: Replace this with your name to have it appear in the "About" dialog.
        args["translator_credits"] = _("translator-credits")
        if args["translator_credits"] != "translator-credits":
            # TR: Replace LANG with language you are translating to.
            args["translator_credits"] = _("<br/>Translated to LANG by %s") % args["translator_credits"].replace("\n", "<br/>")
        else:
            args["translator_credits"] = ""
        args['icons_credits'] = _(
            'Icons made by Sambhav Kothari <sambhavs.email@gmail.com> '
            'and <a href="http://www.flaticon.com/authors/madebyoliver">Madebyoliver</a>, '
            '<a href="http://www.flaticon.com/authors/pixel-buddha">Pixel Buddha</a>, '
            '<a href="http://www.flaticon.com/authors/nikita-golubev">Nikita Golubev</a>, '
            '<a href="http://www.flaticon.com/authors/maxim-basinski">Maxim Basinski</a>, '
            '<a href="https://www.flaticon.com/authors/smashicons">Smashicons</a> '
            'from <a href="https://www.flaticon.com">www.flaticon.com</a>')

        def strong(s):
            return '<strong>' + s + '</strong>'

        def small(s):
            return '<small>' + s + '</small>'

        def url(url, s=None):
            if s is None:
                s = url
            return '<a href="%s">%s</a>' % (url, s)

        text_paragraphs = [
            strong(_("Version %(version)s")),
            small('%(third_parties_versions)s'),
            small(_('Configuration File: %(ini_file)s')),
            strong(_("Supported formats")),
            '%(formats)s',
            strong(_("Please donate")),
            _("Thank you for using Picard. Picard relies on the MusicBrainz database, which is operated by the "
              "MetaBrainz Foundation with the help of thousands of volunteers. If you like this application please "
              "consider donating to the MetaBrainz Foundation to keep the service running."),
            url(PICARD_URLS['donate'], _("Donate now!")),
            strong(_("Credits")),
            small(_("Copyright © %(copyright_years)s %(authors_credits)s and others") + "%(translator_credits)s"),
            small('%(icons_credits)s'),
            strong(_("Official website")),
            url(PICARD_URLS['home'])
        ]
        self.ui.label.setOpenExternalLinks(True)
        self.ui.label.setText("".join(['<p align="center">' + p + "</p>" for p in text_paragraphs]) % args)
