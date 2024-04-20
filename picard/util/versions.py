# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2014 Lukáš Lalinský
# Copyright (C) 2014-2015, 2017-2018, 2020-2021, 2023-2024 Laurent Monin
# Copyright (C) 2016 Sambhav Kothari
# Copyright (C) 2018-2019, 2021-2023 Philipp Wolfer
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
from platform import python_version

from mutagen import version_string as mutagen_version

from PyQt6.QtCore import (
    PYQT_VERSION_STR as pyqt_version,
    qVersion,
)
from PyQt6.QtNetwork import QSslSocket

from picard import PICARD_FANCY_VERSION_STR
from picard.disc import discid_version
from picard.i18n import (
    N_,
    _,
)
from picard.util.astrcmp import astrcmp_implementation


_versions = None

_names = {
    'version': "Picard",
    'python-version': "Python",
    'pyqt-version': "PyQt",
    'qt-version': "Qt",
    'mutagen-version': "Mutagen",
    'discid-version': "Discid",
    'astrcmp': "astrcmp",
    'ssl-version': "SSL",
}


def _load_versions():
    global _versions
    _versions = OrderedDict((
        ('version', PICARD_FANCY_VERSION_STR),
        ('python-version', python_version()),
        ('pyqt-version', pyqt_version),
        ('qt-version', qVersion()),
        ('mutagen-version', mutagen_version),
        ('discid-version', discid_version),
        ('astrcmp', astrcmp_implementation),
        ('ssl-version', QSslSocket.sslLibraryVersionString())
    ))


def _value_as_text(value, i18n=False):
    if not value:
        value = N_("is not installed")
        if i18n:
            return _(value)
    return value


def version_name(key):
    return _names[key]


def as_dict(i18n=False):
    if not _versions:
        _load_versions()
    return OrderedDict((key, _value_as_text(value, i18n))
                        for key, value in _versions.items())


def as_string(i18n=False, separator=", "):
    values = as_dict(i18n)
    return separator.join(_names[key] + " " + value
                          for key, value in values.items())
