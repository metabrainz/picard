# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Stevil Knevil
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


from collections import namedtuple


class MimeDataHelper:
    """
    A registry for encoding and decoding functions based on MIME types.

    This class allows users to register custom encode and decode functions
    for specific MIME types. These functions can then be used to handle
    data serialization and deserialization for those MIME types.
    """

    MimeConverters = namedtuple('MimeConverters', ('encode_func', 'decode_func'))

    def __init__(self):
        self._registry = {}

    def register(self, mimetype, encode_func=None, decode_func=None):
        """
        Registers encode and decode functions for a specific MIME type.

        Args:
            mimetype (str): The MIME type to register.
            encode_func (callable or None): A function that encodes data for the MIME type, or None.
            decode_func (callable or None): A function that decodes data for the MIME type, or None.
        """
        if encode_func is not None and not callable(encode_func):
            raise ValueError("encode_func must be callable or None.")
        if decode_func is not None and not callable(decode_func):
            raise ValueError("decode_func must be callable or None.")
        if self.is_registered(mimetype):
            raise ValueError(f"MIME type '{mimetype}' is already registered.")

        self._registry[mimetype] = self.MimeConverters(encode_func=encode_func, decode_func=decode_func)

    def is_registered(self, mimetype):
        return mimetype in self._registry

    def encode_func(self, mimetype):
        return self._registry[mimetype].encode_func

    def decode_func(self, mimetype):
        return self._registry[mimetype].decode_func

    def encode_funcs(self):
        """
        Return a generator of registered MIMETYPES and their handling encoding functions.
        """
        for mimetype, converters in self._registry.items():
            if converters.encode_func:
                yield mimetype, self._registry[mimetype].encode_func

    def decode_funcs(self, mimedata):
        """
        Return a generator of decoding functions that can handle mimetypes in the given mimedata.
        Args:
            mimedata (QMimeData): The MIME data to check.
        """
        for mimetype, converters in self._registry.items():
            if mimedata.hasFormat(mimetype) and converters.decode_func:
                yield self._registry[mimetype].decode_func
