# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019, 2021 Philipp Wolfer
# Copyright (C) 2020, 2023 Laurent Monin
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
import os.path
import sys

from picard import (
    PICARD_APP_NAME,
    PICARD_ORG_NAME,
)


# The portable version stores all data in a folder beside the executable
configdir = '{}-{}'.format(PICARD_ORG_NAME, PICARD_APP_NAME)
basedir = os.path.join(os.path.dirname(sys.executable), configdir)
os.makedirs(basedir, exist_ok=True)

# Setup config file if not specified as command line argument
if '--config-file' not in sys.argv and '-c' not in sys.argv:
    sys.argv.append('--config-file')
    sys.argv.append(os.path.join(basedir, 'Config.ini'))

plugindir = os.path.normpath(os.path.join(basedir, 'Plugins'))
cachedir = os.path.normpath(os.path.join(basedir, 'Cache'))

os.environ['PICARD_CONFIG_DIR'] = basedir
os.environ['PICARD_CACHE_DIR'] = cachedir
os.environ['PICARD_PLUGIN_DIR'] = plugindir
