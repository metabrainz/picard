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

import json
import traceback
from picard import config, log
from picard.const import CAA_HOST, CAA_PORT
from picard.coverartproviders import CoverArtProvider
from picard.coverartimage import CaaCoverArtImage


_CAA_THUMBNAIL_SIZE_MAP = {
    0: "small",
    1: "large",
}


class CoverArtProviderCaa(CoverArtProvider):

    """Get cover art from Cover Art Archive using release mbid"""

    NAME = "Cover Art Archive"

    def __init__(self, coverart):
        CoverArtProvider.__init__(self, coverart)
        self.caa_types = map(unicode.lower, config.setting["caa_image_types"])
        self.len_caa_types = len(self.caa_types)

    def enabled(self):
        """Check if CAA artwork has to be downloaded"""
        if not config.setting['ca_provider_use_caa']:
            log.debug("Cover Art Archive disabled by user")
            return False
        if not self.len_caa_types:
            log.debug("User disabled all Cover Art Archive types")
            return False

        # MB web service indicates if CAA has artwork
        # http://tickets.musicbrainz.org/browse/MBS-4536
        if 'cover_art_archive' not in self.release.children:
            log.debug("No Cover Art Archive information for %s"
                      % self.release.id)
            return False

        caa_node = self.release.children['cover_art_archive'][0]
        caa_has_suitable_artwork = caa_node.artwork[0].text == 'true'

        if not caa_has_suitable_artwork:
            log.debug("There are no images in the Cover Art Archive for %s"
                      % self.release.id)
            return False

        want_front = 'front' in self.caa_types
        want_back = 'back' in self.caa_types
        caa_has_front = caa_node.front[0].text == 'true'
        caa_has_back = caa_node.back[0].text == 'true'

        if self.len_caa_types == 2 and (want_front or want_back):
            # The OR cases are there to still download and process the CAA
            # JSON file if front or back is enabled but not in the CAA and
            # another type (that's neither front nor back) is enabled.
            # For example, if both front and booklet are enabled and the
            # CAA only has booklet images, the front element in the XML
            # from the webservice will be false (thus front_in_caa is False
            # as well) but it's still necessary to download the booklet
            # images by using the fact that back is enabled but there are
            # no back images in the CAA.
            front_in_caa = caa_has_front or not want_front
            back_in_caa = caa_has_back or not want_back
            caa_has_suitable_artwork = front_in_caa or back_in_caa

        elif self.len_caa_types == 1 and (want_front or want_back):
            front_in_caa = caa_has_front and want_front
            back_in_caa = caa_has_back and want_back
            caa_has_suitable_artwork = front_in_caa or back_in_caa

        if not caa_has_suitable_artwork:
            log.debug("There are no suitable images in the Cover Art Archive for %s"
                      % self.release.id)
        else:
            log.debug("There are suitable images in the Cover Art Archive for %s"
                      % self.release.id)

        return caa_has_suitable_artwork

    def queue_downloads(self):
        self.album.tagger.xmlws.download(
            CAA_HOST,
            CAA_PORT,
            "/release/%s/" % self.metadata["musicbrainz_albumid"],
            self._caa_json_downloaded,
            priority=True,
            important=False
        )
        self.album._requests += 1
        # we will call next_in_queue() after json parsing
        return CoverArtProvider.WAIT

    def _caa_json_downloaded(self, data, http, error):
        """Parse CAA JSON file and queue CAA cover art images for download"""
        self.album._requests -= 1
        if error:
            self.error(u'CAA JSON error: %s' % (unicode(http.errorString())))
        else:
            try:
                caa_data = json.loads(data)
            except ValueError:
                self.error("Invalid JSON: %s", http.url().toString())
            else:
                for image in caa_data["images"]:
                    if config.setting["caa_approved_only"] and not image["approved"]:
                        continue
                    # if image has no type set, we still want it to match
                    # pseudo type 'unknown'
                    if not image["types"]:
                        image["types"] = [u"unknown"]
                    else:
                        image["types"] = map(unicode.lower, image["types"])
                    # only keep enabled caa types
                    types = set(image["types"]).intersection(
                        set(self.caa_types))
                    if types:
                        self._queue_from_caa(image)

        self.next_in_queue()

    def _queue_from_caa(self, image):
        """Queue images depending on the CAA image size settings."""
        imagesize = config.setting["caa_image_size"]
        thumbsize = _CAA_THUMBNAIL_SIZE_MAP.get(imagesize, None)
        if thumbsize is None:
            url = image["image"]
        else:
            url = image["thumbnails"][thumbsize]
        coverartimage = CaaCoverArtImage(
            url,
            types=image["types"],
            comment=image["comment"],
        )
        # front image indicator from CAA
        coverartimage.is_front = bool(image['front'])
        self.queue_put(coverartimage)
