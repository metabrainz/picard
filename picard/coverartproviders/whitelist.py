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

import traceback

from picard import config, log
from picard.coverartproviders import CoverArtProvider
from picard.coverartimage import CoverArtImage


class CoverArtProviderWhitelist(CoverArtProvider):

    """Use cover art link and has_cover_art_at MusicBrainz relationships to get
    cover art"""

    NAME = "Whitelist"

    def enabled(self):
        if not config.setting['ca_provider_use_whitelist']:
            log.debug("Cover art from white list disabled by user")
            return False
        return not self.coverart.front_image_found

    def queue_downloads(self):
        try:
            if 'relation_list' in self.release.children:
                for relation_list in self.release.relation_list:
                    if relation_list.target_type == 'url':
                        for relation in relation_list.relation:
                            # Use the URL of a cover art link directly
                            if (relation.type == 'cover art link' or
                                relation.type == 'has_cover_art_at'):
                                log.debug("Found cover art link in whitelist")
                                self.queue_put(CoverArtImage(url=relation.target[0].text))
        except AttributeError:
            self.error(traceback.format_exc())
        return CoverArtProvider.FINISHED
