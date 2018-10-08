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

from sys import version_info
import webbrowser

from PyQt5 import QtWidgets

from picard import log
from picard.const import PICARD_URLS


"""
A webbrowser extension for Picard. It handles and displays errors
in PyQt and also adds a utility function for opening Picard URLS.
"""


def open(url):
    try:
        webbrowser.open(url)
    except webbrowser.Error as e:
        QtWidgets.QMessageBox.critical(None, _("Web Browser Error"), _("Error while launching a web browser:\n\n%s") % (e,))
    except TypeError as e:
        if version_info.major == 3 and version_info.minor == 7 and version_info.micro == 0:
            # See https://bugs.python.org/issue31014, webbrowser.open doesn't
            # work on 3.7.0 the first time it's called. The initialization code
            # in it will be skipped after the first call, making it possibly to
            # use it, although it might not accurately identify the users
            # preferred browser.
            log.info("Working around https://bugs.python.org/issue31014 - URLs might not be opened in the correct browser")
            webbrowser.open(url)


def goto(url_id):
    open(PICARD_URLS[url_id])
