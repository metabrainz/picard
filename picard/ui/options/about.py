# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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

from mutagen import version_string as mutagen_version
from PyQt4.QtCore import PYQT_VERSION_STR as pyqt_version
from picard import __version__ as picard_version
from picard.formats import supported_formats
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_about import Ui_AboutOptionsPage
from picard.disc import libdiscid_version


class AboutOptionsPage(OptionsPage):

    NAME = "about"
    TITLE = N_("About")
    PARENT = None
    SORT_ORDER = 100
    ACTIVE = True

    def __init__(self, parent=None):
        super(AboutOptionsPage, self).__init__(parent)
        self.ui = Ui_AboutOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        args = {
            "version": picard_version,
            "mutagen-version": mutagen_version,
            "pyqt-version": pyqt_version,
            "libdiscid-version": libdiscid_version()
            }

        formats = []
        for exts, name in supported_formats():
            formats.extend(exts)
        args["formats"] = ", ".join(formats)

        # TR: Replace this with your name to have it appear in the "About" dialog.
        args["translator-credits"] = _("translator-credits")
        if args["translator-credits"] != "translator-credits":
            # TR: Replace LANG with language you are translatig to.
            args["translator-credits"] = _("<br/>Translated to LANG by %s") % args["translator-credits"].replace("\n", "<br/>")
        else:
            args["translator-credits"] = ""

        text = _(u"""<p align="center"><span style="font-size:15px;font-weight:bold;">MusicBrainz Picard</span><br/>
Version %(version)s</p>
<p align="center"><small>
PyQt %(pyqt-version)s<br/>
Mutagen %(mutagen-version)s<br/>
%(libdiscid-version)s
</small></p>
<p align="center"><strong>Supported formats</strong><br/>%(formats)s</p>
<p align="center"><strong>Please donate</strong><br/>
Thank you for using Picard. Picard relies on the MusicBrainz database, which is operated by the MetaBrainz Foundation with the help of thousands of volunteers. If you like this application please consider donating to the MetaBrainz Foundation to keep the service running.</p>
<p align="center"><a href="http://metabrainz.org/donate">Donate now!</a></p>
<p align="center"><strong>Credits</strong><br/>
<small>Copyright © 2004-2011 Robert Kaye, Lukáš Lalinský and others%(translator-credits)s</small></p>
<p align="center"><a href="http://musicbrainz.org/doc/MusicBrainz_Picard">http://musicbrainz.org/doc/MusicBrainz_Picard</a></p>
""") % args
        self.ui.label.setOpenExternalLinks(True)
        self.ui.label.setText(text)


register_options_page(AboutOptionsPage)
