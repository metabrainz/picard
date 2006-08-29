# ***** BEGIN LICENSE BLOCK *****
# Version: RCSL 1.0/RPSL 1.0/GPL 2.0
#
# Portions Copyright (c) 1995-2002 RealNetworks, Inc. All Rights Reserved.
# Portions Copyright (c) 2004 Robert Kaye. All Rights Reserved.
#
# The contents of this file, and the files included with this file, are
# subject to the current version of the RealNetworks Public Source License
# Version 1.0 (the "RPSL") available at
# http://www.helixcommunity.org/content/rpsl unless you have licensed
# the file under the RealNetworks Community Source License Version 1.0
# (the "RCSL") available at http://www.helixcommunity.org/content/rcsl,
# in which case the RCSL will apply. You may also obtain the license terms
# directly from RealNetworks.  You may not use this file except in
# compliance with the RPSL or, if you have a valid RCSL with RealNetworks
# applicable to this file, the RCSL.  Please see the applicable RPSL or
# RCSL for the rights, obligations and limitations governing use of the
# contents of the file.
#
# This file is part of the Helix DNA Technology. RealNetworks is the
# developer of the Original Code and owns the copyrights in the portions
# it created.
#
# This file, and the files included with this file, is distributed and made
# available on an 'AS IS' basis, WITHOUT WARRANTY OF ANY KIND, EITHER
# EXPRESS OR IMPLIED, AND REALNETWORKS HEREBY DISCLAIMS ALL SUCH WARRANTIES,
# INCLUDING WITHOUT LIMITATION, ANY WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE, QUIET ENJOYMENT OR NON-INFRINGEMENT.
#
# Technology Compatibility Kit Test Suite(s) Location:
#    http://www.helixcommunity.org/content/tck
#
# --------------------------------------------------------------------
#
# picard is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# picard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with picard; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Contributor(s):
#   Robert Kaye
#   Lukas Lalinsky
#
#
# ***** END LICENSE BLOCK *****

import sys, os, webbrowser, tempfile
#from picard import wpath

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

class Launch(object):

    def __init__(self, parent):
        self.parent = parent

    def getTempFile(self):
        tempDir = tempfile.gettempdir()
        return wpath.wpath().join(tempDir, "post.html")

    def cleanup(self):
        try:
            os.unlink(self.getTempFile())
        except:
            pass
        
    def launch(self, url):
        # If the browser var does not specify the %s, warn the user 
        browser = os.environ.get('BROWSER')
        if browser and browser not in webbrowser._browsers and ('%s' not in browser or '&' not in browser):
                dlg = wx.MessageDialog(self.parent, "Your BROWSER variable does not contain a %s and/or a & ."+
                       " To ensure that your browser launches correctly and doesn't lock the rest of the "+
                       " application, make sure your BROWSER environment varable includes a %s &. For example, "+
                       ' BROWSER="firefox \'%s\' &" should work to launch Firefox correctly.', style=wx.OK)
                dlg.ShowModal()

        try:
            webbrowser.open(url)
            return True
        except:
            return False


    def post(self, post):
        try:
            file = open(self.getTempFile(), "w")
            file.write(post);
            file.close()
        except IOError:
            dlg = wx.MessageDialog(self.parent, "Could not write a temporary file to launch a browser.",
                                   "HTTP POST Launch", style=wx.OK)
            dlg.ShowModal()

        self.launch("file://" + self.getTempFile())
