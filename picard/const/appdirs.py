# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Philipp Wolfer
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

import os.path

from PyQt5.QtCore import (
    QCoreApplication,
    QStandardPaths,
)

from picard import (
    PICARD_APP_NAME,
    PICARD_ORG_NAME,
)


# Ensure the application is properly configured for the paths to work
QCoreApplication.setApplicationName(PICARD_APP_NAME)
QCoreApplication.setOrganizationName(PICARD_ORG_NAME)


def config_folder():
    return os.path.normpath(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation))


def cache_folder():
    return os.path.normpath(QStandardPaths.writableLocation(QStandardPaths.CacheLocation))


def plugin_folder():
    # FIXME: This really should be in QStandardPaths.AppDataLocation instead,
    # but this is a breaking change that requires data migration
    return os.path.normpath(os.path.join(config_folder(), 'plugins'))
