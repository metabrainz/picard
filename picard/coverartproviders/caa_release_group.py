# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
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

import traceback

from picard import config, log
from picard.coverartproviders import CoverArtProvider
from picard.coverartproviders.caa import CoverArtProviderCaa
from picard.coverartimage import CoverArtImage


class CoverArtProviderCaaReleaseGroup(CoverArtProviderCaa):

    """Use cover art from album release group"""

    NAME = "CaaReleaseGroup"

    def enabled(self):
        if not config.setting['ca_provider_use_caa']:
            log.debug("Cover art from Cover Art Archive disabled by user")
            return False
        if not config.setting['ca_provider_use_caa_release_group_fallback']:
            log.debug("Release group cover art fallback disabled by user")
            return False
        if not self.len_caa_types:
            log.debug("User disabled all Cover Art Archive types")
            return False

        return not self.coverart.front_image_found

    def _caa_path(self):
        return "/release-group/%s/" % self.metadata["musicbrainz_releasegroupid"]
