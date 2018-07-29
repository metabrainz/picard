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


from picard import log
from picard.coverart.image import CoverArtImage
from picard.coverart.providers import CoverArtProvider


class CoverArtProviderWhitelist(CoverArtProvider):

    """Use cover art link and has_cover_art_at MusicBrainz relationships to get
    cover art"""

    NAME = "Whitelist"
    TITLE = N_('Whitelist')

    def enabled(self):
        return (super().enabled()
                and not self.coverart.front_image_found)

    def queue_images(self):
        self.match_url_relations(('cover art link', 'has_cover_art_at'),
                                 self._queue_from_whitelist)
        return CoverArtProvider.FINISHED

    def _queue_from_whitelist(self, url):
        log.debug("Found cover art link in whitelist")
        self.queue_put(CoverArtImage(url))
