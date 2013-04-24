# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2006 Matthias Friedrich
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

import ctypes
import sys
import traceback
from PyQt4 import QtCore
from picard.ui.cdlookup import CDLookupDialog


_libdiscid = None


class DiscError(IOError):
    pass


class Disc(QtCore.QObject):

    def __init__(self):
        QtCore.QObject.__init__(self)
        self.id = None
        self.submission_url = None

    def read(self, device):
        global _libdiscid
        if _libdiscid is None:
            _libdiscid = _openLibrary()
        handle = _libdiscid.discid_new()
        assert handle != 0, "libdiscid: discid_new() returned NULL"
        try:
            res = _libdiscid.discid_read_sparse(handle, device or None, 0)
        except AttributeError:
            res = _libdiscid.discid_read(handle, device or None)
        if res == 0:
            raise DiscError(_libdiscid.discid_get_error_msg(handle))
        self.id = _libdiscid.discid_get_id(handle)
        self.submission_url = _libdiscid.discid_get_submission_url(handle)
        _libdiscid.discid_free(handle)

    def lookup(self):
        self.tagger.xmlws.lookup_discid(self.id, self._lookup_finished)

    def _lookup_finished(self, document, http, error):
        self.tagger.restore_cursor()
        releases = []
        if error:
            self.log.error("%r", unicode(http.errorString()))
        else:
            try:
                releases = document.metadata[0].disc[0].release_list[0].release
            except (AttributeError, IndexError):
                self.log.error(traceback.format_exc())

        dialog = CDLookupDialog(releases, self, parent=self.tagger.window)
        dialog.exec_()


def libdiscid_version():
    global _libdiscid
    try:
        if _libdiscid is None:
            _libdiscid = _openLibrary()
    except NotImplementedError:
        return ""
    try:
        return _libdiscid.discid_get_version_string()
    except AttributeError:
        return "libdiscid"


def _openLibrary():
    """Tries to open libdiscid.

    @return: a C{ctypes.CDLL} object, representing the opened library

    @raise NotImplementedError: if the library can't be opened
    """

    # Check to see if we're running in a Mac OS X bundle.
    if sys.platform == 'darwin':
        try:
            libDiscId = ctypes.cdll.LoadLibrary('../Frameworks/libdiscid.0.dylib')
            _setPrototypes(libDiscId)
            return libDiscId
        except OSError, e:
            pass

    # This only works for ctypes >= 0.9.9.3. Any libdiscid is found,
    # no matter how it's called on this platform.
    try:
        if hasattr(ctypes.cdll, 'find'):
            libDiscId = ctypes.cdll.find('discid')
            _setPrototypes(libDiscId)
            return libDiscId
    except OSError, e:
        raise NotImplementedError(str(e))

    # For compatibility with ctypes < 0.9.9.3 try to figure out the library
    # name without the help of ctypes. We use cdll.LoadLibrary() below,
    # which isn't available for ctypes == 0.9.9.3.
    #
    if sys.platform == 'linux2':
        libName = 'libdiscid.so.0'
    elif sys.platform == 'darwin':
        libName = 'libdiscid.0.dylib'
    elif sys.platform == 'win32':
        libName = 'discid.dll'
    else:
        # This should at least work for Un*x-style operating systems
        libName = 'libdiscid.so.0'

    try:
        libDiscId = ctypes.cdll.LoadLibrary(libName)
        _setPrototypes(libDiscId)
        return libDiscId
    except OSError, e:
        raise NotImplementedError('Error opening library: ' + str(e))

    assert False # not reached


def _setPrototypes(libDiscId):
    ct = ctypes
    libDiscId.discid_new.argtypes = ( )
    libDiscId.discid_new.restype = ct.c_void_p

    libDiscId.discid_free.argtypes = (ct.c_void_p, )

    libDiscId.discid_read.argtypes = (ct.c_void_p, ct.c_char_p)
    try:
        libDiscId.discid_read_sparse.argtypes = (ct.c_void_p, ct.c_char_p,
                                                 ct.c_uint)
    except AttributeError:
        pass

    libDiscId.discid_get_error_msg.argtypes = (ct.c_void_p, )
    libDiscId.discid_get_error_msg.restype = ct.c_char_p

    libDiscId.discid_get_id.argtypes = (ct.c_void_p, )
    libDiscId.discid_get_id.restype = ct.c_char_p

    libDiscId.discid_get_submission_url.argtypes = (ct.c_void_p, )
    libDiscId.discid_get_submission_url.restype = ct.c_char_p

    try:
        libDiscId.discid_get_version_string.restype = ct.c_char_p
    except AttributeError:
        pass
