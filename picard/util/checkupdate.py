# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2018 Bob Swift
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

from picard import (PICARD_VERSION_STR_SHORT, log)
from picard.const import PICARD_URLS
import picard.util.webbrowser2 as wb2
from PyQt5.QtWidgets import QMessageBox
#from PyQt5 import QtCore, QtGui, QtWidgets
#from PyQt5.QtGui import QIcon
import urllib.request
import re

_RE_TEST = r'.*infoText\s*=\s*\"v([0-9\.]*)'

_NOTICE_TEXT = '''
A new version of Picard is available.

Your version: v%s
New version: v%s

Would you like to download the new version?
'''

latest_version = ""
''' Use a module-level variable to store the latest release information
    to avoid multiple calls to the web site in a single Picard session. '''


def get_latest_version_number():
    '''Scrapes the Picard home page to extract the latest release version number.'''
    global latest_version
    if not latest_version:
        try:
            page = urllib.request.urlopen(PICARD_URLS['home'])
            matches = re.findall(_RE_TEST, page.read().decode('utf-8'), re.M | re.I)
            if matches:
                latest_version = matches[0]
            else:
                log.warning("Unable to get the latest version information from %s" % PICARD_URLS['home'])
        except Exception as e:
            log.error("Exception while getting the latest version information from %s: %s" % (PICARD_URLS['home'], e,))
    return latest_version


def check_update(show_always=False):
    '''Checks if an update is available.

    Compares the version number of the currently running instance of Picard
    and displays a dialog box informing the user  if an update is available,
    with an option of opening the Picard site in the browser to download the
    update.  If there is no update available, no dialog will be shown unless
    the "show_always" parameter has been set to True.  This allows for silent
    checking during startup if so configured.
    '''
    latest_version = get_latest_version_number()
    msg_title = "Picard Update"
    if latest_version > PICARD_VERSION_STR_SHORT:
        msg_text = _NOTICE_TEXT % (PICARD_VERSION_STR_SHORT, latest_version)
        if QMessageBox.information(None, msg_title, msg_text, QMessageBox.Ok | QMessageBox.Cancel,
                                   QMessageBox.Cancel) == QMessageBox.Ok:
            wb2.goto("home")
    else:
        if show_always:
            msg_text = "There is no update currently available.  The latest release is %s." % (
                'v' + latest_version if latest_version else 'Unknown',)
            QMessageBox.information(None, msg_title, msg_text, QMessageBox.Ok, QMessageBox.Ok)
