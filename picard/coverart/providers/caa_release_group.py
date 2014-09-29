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
from picard.coverart.providers import CoverArtProvider
from picard.coverart.providers.caa import CoverArtProviderCaa
from picard.coverart.image import CaaCoverArtImage, CaaThumbnailCoverArtImage


class CaaCoverArtImageRg(CaaCoverArtImage):
    pass


class CaaThumbnailCoverArtImageRg(CaaThumbnailCoverArtImage):
    pass


class CoverArtProviderCaaReleaseGroup(CoverArtProviderCaa):

    """Use cover art from album release group"""

    NAME = "CaaReleaseGroup"

    ignore_json_not_found_error = True
    coverartimage_class = CaaCoverArtImageRg
    coverartimage_thumbnail_class = CaaThumbnailCoverArtImageRg

    @property
    def _has_suitable_artwork(self):
        if not config.setting['ca_provider_use_caa_release_group_fallback']:
            log.debug("Release group cover art fallback disabled by user")
            return False
        return not self.coverart.front_image_found

    @property
    def _caa_path(self):
        return "/release-group/%s/" % self.metadata["musicbrainz_releasegroupid"]
