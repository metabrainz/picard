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
import webbrowser

"""
A webbrowser extension that respects user's preferred browser on each
platform. Python 2.5 already has *some* support for this, but it's not
enough, in my opinion. See also:
http://sourceforge.net/tracker/index.php?func=detail&aid=1681228&group_id=5470&atid=105470
"""

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
    webbrowser._tryorder.remove('windows-default')
    webbrowser._tryorder.insert(0, 'windows-default')

open = webbrowser.open
