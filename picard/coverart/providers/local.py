# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Oliver Charles
# Copyright (C) 2007-2011 Philipp Wolfer
# Copyright (C) 2007, 2010, 2011 Lukáš Lalinský
# Copyright (C) 2011 Michael Wiencek
# Copyright (C) 2011-2012 Wieland Hoffmann
# Copyright (C) 2013-2014 Laurent Monin
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
import re
import traceback

from picard import config, log
from picard.coverart.providers import CoverArtProvider
from picard.coverart.image import CoverArtImageFromFile


class CoverArtProviderLocal(CoverArtProvider):

    """Get cover art from local files"""

    NAME = "Local"

    _match_re = re.compile('^(?:cover|folder|albumart).*\.(?:jpe?g|png|gif|tiff?)$', re.IGNORECASE)

    def enabled(self):
        if not config.setting['ca_provider_use_local']:
            log.debug("Cover art from local files disabled by user")
            return False
        return not self.coverart.front_image_found

    def queue_images(self):
        dirs_done = {}
        for file in self.album.iterfiles():
            current_dir = os.path.dirname(file.filename)
            if current_dir in dirs_done:
                continue
            dirs_done[current_dir] = True
            for root, dirs, files in os.walk(current_dir):
                for filename in files:
                    if self._match_filename(filename):
                        filepath = os.path.join(current_dir, root, filename)
                        if os.path.exists(filepath):
                            self.queue_put(CoverArtImageFromFile(filepath))
        return CoverArtProvider.FINISHED

    def _match_filename(self, filename):
        return self._match_re.search(filename)

