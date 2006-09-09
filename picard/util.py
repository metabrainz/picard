# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2004 Robert Kaye
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

import sys
import os.path

_ioEncoding = sys.getfilesystemencoding() 

def setIoEncoding(encoding):
    _ioEncoding = encoding

def encode_filename(filename):
    if isinstance(filename, unicode):
        if os.path.supports_unicode_filenames:
            return filename
        else:
            return filename.encode(_ioEncoding, 'replace')
    else:
        return filename

def decode_filename(filename):
    if isinstance(filename, unicode):
        return filename
    else:
        return filename.decode(_ioEncoding)
        
def formatTime(ms):
    if ms == 0:
        return u"?:??"
    else:
        return u"%d:%02d" % (ms / 60000, (ms / 1000) % 60)

