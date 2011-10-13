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

import os
import sys
import webbrowser
from PyQt4 import QtGui

"""
A webbrowser extension that respects user's preferred browser on each
platform. Python 2.5 already has *some* support for this, but it's not
enough, in my opinion. See also:
http://sourceforge.net/tracker/index.php?func=detail&aid=1681228&group_id=5470&atid=105470
"""

if sys.version_info >= (2, 5):
    # Cross-platform default tool
    if webbrowser._iscommand('xdg-open'):
        webbrowser.register('xdg-open', None, webbrowser.BackgroundBrowser(["xdg-open", "%s"]), update_tryorder=-1)
    else:
        # KDE default browser
        if 'KDE_FULL_SESSION' in os.environ and os.environ['KDE_FULL_SESSION'] == 'true' and webbrowser._iscommand('kfmclient'):
            webbrowser.register('kfmclient', None, webbrowser.BackgroundBrowser(["kfmclient", "exec", "%s"]), update_tryorder=-1)
        # GNOME default browser
        if 'GNOME_DESKTOP_SESSION_ID' in os.environ and webbrowser._iscommand('gnome-open'):
            webbrowser.register('gnome-open', None, webbrowser.BackgroundBrowser(["gnome-open", "%s"]), update_tryorder=-1)


else:
    # KDE default browser
    if 'KDE_FULL_SESSION' in os.environ and os.environ['KDE_FULL_SESSION'] == 'true' and webbrowser._iscommand('kfmclient'):
        webbrowser.register('kfmclient', None, webbrowser.GenericBrowser("kfmclient exec '%s' &"))
        if 'BROWSER' in os.environ:
            webbrowser._tryorder.insert(len(os.environ['BROWSER'].split(os.pathsep)), 'kfmclient')
        else:
            webbrowser._tryorder.insert(0, 'kfmclient')
    # GNOME default browser
    if 'GNOME_DESKTOP_SESSION_ID' in os.environ and webbrowser._iscommand('gnome-open'):
        webbrowser.register('gnome-open', None, webbrowser.GenericBrowser("gnome-open '%s' &"))
        if 'BROWSER' in os.environ:
            webbrowser._tryorder.insert(len(os.environ['BROWSER'].split(os.pathsep)), 'gnome-open')
        else:
            webbrowser._tryorder.insert(0, 'gnome-open')


if 'windows-default' in webbrowser._tryorder:
    class WindowsDefault2(webbrowser.BaseBrowser):
        def open(self, url, new=0, autoraise=1):
            try:
                os.startfile(url)
            except WindowsError:
                # [Error 22] No application is associated with the specified
                # file for this operation: '<URL>'
                return False
            else:
                return True

    webbrowser._tryorder.remove('windows-default')
    webbrowser.register('windows-default-2', WindowsDefault2,
                        update_tryorder=-1)

    iexplore = webbrowser.BackgroundBrowser(
        os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
                     'Internet Explorer\\IEXPLORE.EXE'))
    webbrowser.register('iexplore', None, iexplore)


def open(url):
    try:
        webbrowser.open(url)
    except webbrowser.Error, e:
        QtGui.QMessageBox.critical(None, _("Web Browser Error"), _("Error while launching a web browser:\n\n%s") % (e,))
