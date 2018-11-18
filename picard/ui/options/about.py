# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006-2014 Lukáš Lalinský
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

from picard.const import PICARD_URLS
from picard.formats import supported_extensions
from picard.util import versions

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_about import Ui_AboutOptionsPage


class AboutOptionsPage(OptionsPage):

    NAME = "about"
    TITLE = N_("About")
    PARENT = None
    SORT_ORDER = 100
    ACTIVE = True

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_AboutOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        args = {
            "picard-doc-url": PICARD_URLS['home'],
            "picard-donate-url": PICARD_URLS['donate'],
        }
        args.update(versions.as_dict(i18n=True))

        args["formats"] = ", ".join(map(lambda x: x[1:], supported_extensions()))

        # TR: Replace this with your name to have it appear in the "About" dialog.
        args["translator-credits"] = _("translator-credits")
        if args["translator-credits"] != "translator-credits":
            # TR: Replace LANG with language you are translating to.
            args["translator-credits"] = _("<br/>Translated to LANG by %s") % args["translator-credits"].replace("\n", "<br/>")
        else:
            args["translator-credits"] = ""

        args['third_parties_versions'] = '<br />'.join(["%s %s" %
                                                        (versions.version_name(name), value) for name, value
                                                        in versions.as_dict(i18n=True).items()
                                                        if name != 'version'])
        args['authors-credits'] = ", ".join([
            'Robert Kaye',
            'Lukáš Lalinský',
            'Laurent Monin',
            'Sambhav Kothari',
            'Philipp Wolfer',
        ])
        args['copyright-years'] = '2004-2018'
        args['icons-credits'] = _("""Icons made by Sambhav Kothari <sambhavs.email@gmail.com>
and <a href="http://www.flaticon.com/authors/madebyoliver">Madebyoliver</a>,
<a href="http://www.flaticon.com/authors/pixel-buddha">Pixel Buddha</a>,
<a href="http://www.flaticon.com/authors/nikita-golubev">Nikita Golubev</a>,
<a href="http://www.flaticon.com/authors/maxim-basinski">Maxim Basinski</a>
from <a href="www.flaticon.com">www.flaticon.com</a>""")

        text = _("""<p align="center"><span style="font-size:15px;font-weight:bold;">MusicBrainz Picard</span><br/>
Version %(version)s</p>
<p align="center"><small>
%(third_parties_versions)s
</small></p>
<p align="center"><strong>Supported formats</strong><br/>%(formats)s</p>
<p align="center"><strong>Please donate</strong><br/>
Thank you for using Picard. Picard relies on the MusicBrainz database, which is operated by the MetaBrainz Foundation with the help of thousands of volunteers. If you like this application please consider donating to the MetaBrainz Foundation to keep the service running.</p>
<p align="center"><a href="%(picard-donate-url)s">Donate now!</a></p>
<p align="center"><strong>Credits</strong><br/>
<small>Copyright © %(copyright-years)s %(authors-credits)s and others%(translator-credits)s</small></p>
<p align="center"><small>%(icons-credits)s</small></p>
<p align="center"><strong>Official website</strong><br/><a href="%(picard-doc-url)s">%(picard-doc-url)s</a></p>
""") % args
        self.ui.label.setOpenExternalLinks(True)
        self.ui.label.setText(text)


register_options_page(AboutOptionsPage)
