# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006-2014 Lukáš Lalinský
# Copyright (C) 2014 Laurent Monin
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

from collections import OrderedDict
from mutagen import version_string as mutagen_version
from PyQt5.QtCore import PYQT_VERSION_STR as pyqt_version, QT_VERSION_STR
from picard import PICARD_FANCY_VERSION_STR
from picard.disc import discid_version
from picard.util.astrcmp import astrcmp_implementation
from PyQt5.QtNetwork import QSslSocket


_versions = OrderedDict([
    ("version", PICARD_FANCY_VERSION_STR),
    ("pyqt-version", pyqt_version),
    ("qt-version", QT_VERSION_STR),
    ("mutagen-version", mutagen_version),
    ("discid-version", discid_version),
    ("astrcmp", astrcmp_implementation),
    ("SSL", QSslSocket.sslLibraryVersionString())
])

_names = {
    "version": "Picard",
    "pyqt-version": "PyQt",
    "qt-version": "Qt",
    "mutagen-version": "Mutagen",
    "discid-version": "Discid",
    "astrcmp": "astrcmp",
    "SSL": "SSL",
}


def _value_as_text(value, i18n=False):
    if not value:
        value = N_("is not installed")
        if i18n:
            return _(value)
    return value


def version_name(key):
    return _names[key]


def as_dict(i18n=False):
    return OrderedDict([(key, _value_as_text(value, i18n)) for key,
                        value in
                        _versions.items()])


def as_string(i18n=False, separator=", "):
    values = as_dict(i18n)
    return separator.join([_names[key] + " " + value for key, value in
                           values.items()])
