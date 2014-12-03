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

from mutagen import version_string as mutagen_version
from PyQt4.QtCore import PYQT_VERSION_STR as pyqt_version
from picard import PICARD_FANCY_VERSION_STR
from picard.disc import discid_version


_versions = {
    "version": PICARD_FANCY_VERSION_STR,
    "pyqt-version": pyqt_version,
    "mutagen-version": mutagen_version,
    "discid-version": discid_version,
}

_names = {
    "version": "Picard",
    "pyqt-version": "PyQt",
    "mutagen-version": "Mutagen",
    "discid-version": "Discid",
}


def _value_as_text(value, i18n=False):
    if not value:
        value = N_("is not installed")
        if i18n:
            return _(value)
    return value


def as_dict(i18n=False):
    return dict([(key, _value_as_text(value, i18n)) for key, value in
                 _versions.iteritems()])


def as_string(i18n=False, separator=", "):
    return separator.join([_names[key] + " " + value for key, value in
                           as_dict(i18n).items()])
