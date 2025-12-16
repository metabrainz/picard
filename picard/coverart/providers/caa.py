# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007 Oliver Charles
# Copyright (C) 2007, 2010-2011 Lukáš Lalinský
# Copyright (C) 2007-2011, 2015, 2018-2024 Philipp Wolfer
# Copyright (C) 2011 Michael Wiencek
# Copyright (C) 2011-2012 Wieland Hoffmann
# Copyright (C) 2013-2015, 2018-2024 Laurent Monin
# Copyright (C) 2015-2016 Rahul Raturi
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Frederik “Freso” S. Olesen
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2018, 2024 Bob Swift
# Copyright (C) 2024 Giorgio Fontanive
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


from collections import (
    OrderedDict,
    namedtuple,
)

from PyQt6.QtNetwork import (
    QNetworkReply,
    QNetworkRequest,
)

from picard import log
from picard.album_requests import TaskType
from picard.config import get_config
from picard.const import CAA_URL
from picard.const.defaults import (
    DEFAULT_CAA_IMAGE_SIZE,
    DEFAULT_CAA_IMAGE_TYPE_EXCLUDE,
    DEFAULT_CAA_IMAGE_TYPE_INCLUDE,
)
from picard.coverart.image import (
    CaaCoverArtImage,
    CaaThumbnailCoverArtImage,
)
from picard.coverart.processing import run_image_metadata_filters
from picard.coverart.providers.provider import (
    CoverArtProvider,
    ProviderOptions,
)
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.webservice import ratecontrol

from picard.ui.caa_types_selector import CAATypesSelectorDialog
from picard.ui.forms.ui_provider_options_caa import Ui_CaaOptions


CaaSizeItem = namedtuple('CaaSizeItem', ['thumbnail', 'label'])
CaaThumbnailListItem = namedtuple('CAAThumbnailListItem', ['url', 'width'])

_CAA_THUMBNAIL_SIZE_MAP = OrderedDict(
    [
        (250, CaaSizeItem('250', N_('250 px'))),
        (500, CaaSizeItem('500', N_('500 px'))),
        (1200, CaaSizeItem('1200', N_('1200 px'))),
        (-1, CaaSizeItem(None, N_('Full size'))),
    ]
)
_CAA_THUMBNAIL_SIZE_ALIASES = {
    '500': 'large',
    '250': 'small',
}

ratecontrol.set_minimum_delay_for_url(CAA_URL, 0)
ratecontrol.set_minimum_delay_for_url("https://archive.org", 0)


def caa_url_fallback_list(desired_size, thumbnails):
    """List of thumbnail urls equal or smaller than size, in size decreasing order
    It is used for find the "best" thumbnail according to:
        - user choice
        - thumbnail availability
    If user choice isn't matching an available thumbnail size, a fallback to
    smaller thumbnails is possible
    This function returns the list of possible urls, ordered from the biggest
    matching the user choice to the smallest one, together with its thumbnail's size.
    Of course, if none are possible, the returned list may be empty.
    """
    reversed_map = OrderedDict(reversed(list(_CAA_THUMBNAIL_SIZE_MAP.items())))
    thumbnail_list = []
    for thumbnail_width, item in reversed_map.items():
        if thumbnail_width == -1 or thumbnail_width > desired_size:
            continue
        url = thumbnails.get(item.thumbnail, None)
        if url is None:
            size_alias = _CAA_THUMBNAIL_SIZE_ALIASES.get(item.thumbnail, None)
            if size_alias is not None:
                url = thumbnails.get(size_alias, None)
        if url is not None:
            thumbnail_list.append(CaaThumbnailListItem(url, thumbnail_width))
    return thumbnail_list


class ProviderOptionsCaa(ProviderOptions):
    """
    Options for Cover Art Archive cover art provider
    """

    TITLE = N_("Cover Art Archive")
    HELP_URL = "/config/options_cover_art_archive.html"

    _options_ui = Ui_CaaOptions

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui.restrict_images_types.clicked.connect(self.update_caa_types)
        self.ui.select_caa_types.clicked.connect(self.select_caa_types)

    def restore_defaults(self):
        self.caa_image_types = DEFAULT_CAA_IMAGE_TYPE_INCLUDE
        self.caa_image_types_to_omit = DEFAULT_CAA_IMAGE_TYPE_EXCLUDE
        super().restore_defaults()

    def load(self):
        self.ui.cb_image_size.clear()
        for item_id, item in _CAA_THUMBNAIL_SIZE_MAP.items():
            self.ui.cb_image_size.addItem(_(item.label), userData=item_id)

        config = get_config()
        size = config.setting['caa_image_size']
        index = self.ui.cb_image_size.findData(size)
        if index < 0:
            index = self.ui.cb_image_size.findData(DEFAULT_CAA_IMAGE_SIZE)
        self.ui.cb_image_size.setCurrentIndex(index)

        self.ui.cb_approved_only.setChecked(config.setting['caa_approved_only'])
        self.ui.restrict_images_types.setChecked(config.setting['caa_restrict_image_types'])
        self.caa_image_types = config.setting['caa_image_types']
        self.caa_image_types_to_omit = config.setting['caa_image_types_to_omit']
        self.update_caa_types()

    def save(self):
        config = get_config()
        size = self.ui.cb_image_size.currentData()
        config.setting['caa_image_size'] = size
        config.setting['caa_approved_only'] = self.ui.cb_approved_only.isChecked()
        config.setting['caa_restrict_image_types'] = self.ui.restrict_images_types.isChecked()
        config.setting['caa_image_types'] = self.caa_image_types
        config.setting['caa_image_types_to_omit'] = self.caa_image_types_to_omit

    def update_caa_types(self):
        enabled = self.ui.restrict_images_types.isChecked()
        self.ui.select_caa_types.setEnabled(enabled)

    def select_caa_types(self):
        (types, types_to_omit, ok) = CAATypesSelectorDialog.display(
            types_include=self.caa_image_types,
            types_exclude=self.caa_image_types_to_omit,
            parent=self,
            instructions_top=None,
            instructions_bottom=None,
        )
        if ok:
            self.caa_image_types = types
            self.caa_image_types_to_omit = types_to_omit


class CoverArtProviderCaa(CoverArtProvider):
    """Get cover art from Cover Art Archive using release mbid"""

    NAME = "Cover Art Archive"
    TITLE = N_("Cover Art Archive: Release")
    OPTIONS = ProviderOptionsCaa

    ignore_json_not_found_error = False
    coverartimage_class = CaaCoverArtImage
    coverartimage_thumbnail_class = CaaThumbnailCoverArtImage

    def __init__(self, coverart):
        super().__init__(coverart)
        config = get_config()
        self.restrict_types = config.setting['caa_restrict_image_types']
        if self.restrict_types:
            self.included_types = {t.lower() for t in config.setting['caa_image_types']}
            self.excluded_types = {t.lower() for t in config.setting['caa_image_types_to_omit']}
            self.included_types_count = len(self.included_types)

    @property
    def _has_suitable_artwork(self):
        # MB web service indicates if CAA has artwork
        # https://tickets.metabrainz.org/browse/MBS-4536
        if 'cover-art-archive' not in self.release:
            log.debug("No Cover Art Archive information for %s", self.release['id'])
            return False

        caa_node = self.release['cover-art-archive']
        caa_has_suitable_artwork = caa_node['artwork']

        if not caa_has_suitable_artwork:
            log.debug("There are no images in the Cover Art Archive for %s", self.release['id'])
            return False

        if self.restrict_types:
            want_front = 'front' in self.included_types
            want_back = 'back' in self.included_types
            caa_has_front = caa_node['front']
            caa_has_back = caa_node['back']

            if self.included_types_count == 2 and (want_front or want_back):
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

            elif self.included_types_count == 1 and (want_front or want_back):
                front_in_caa = caa_has_front and want_front
                back_in_caa = caa_has_back and want_back
                caa_has_suitable_artwork = front_in_caa or back_in_caa

        if not caa_has_suitable_artwork:
            log.debug("There are no suitable images in the Cover Art Archive for %s", self.release['id'])
        else:
            log.debug("There are suitable images in the Cover Art Archive for %s", self.release['id'])

        return caa_has_suitable_artwork

    def enabled(self):
        """Check if CAA artwork has to be downloaded"""
        if not super().enabled():
            return False
        if self.restrict_types and not self.included_types_count:
            log.debug("User disabled all Cover Art Archive types")
            return False
        return self._has_suitable_artwork

    @property
    def _caa_path(self):
        return "/release/%s/" % self.metadata['musicbrainz_albumid']

    def queue_images(self):
        task_id = f'caa_json_{self.metadata["musicbrainz_albumid"]}'

        def create_request():
            return self.album.tagger.webservice.get_url(
                url=CAA_URL + self._caa_path,
                handler=self._caa_json_downloaded,
                priority=True,
                important=False,
                cacheloadcontrol=QNetworkRequest.CacheLoadControl.PreferNetwork,
            )

        self.album.add_task(
            task_id,
            TaskType.OPTIONAL,
            f'CAA JSON metadata for {self.metadata["musicbrainz_albumid"]}',
            request_factory=create_request,
        )
        # we will call next_in_queue() after json parsing
        return CoverArtProvider.QueueState.WAIT

    def _caa_json_downloaded(self, data, http, error):
        """Parse CAA JSON file and queue CAA cover art images for download"""
        task_id = f'caa_json_{self.metadata["musicbrainz_albumid"]}'
        self.album.complete_task(task_id)
        if error:
            if not (error == QNetworkReply.NetworkError.ContentNotFoundError and self.ignore_json_not_found_error):
                self.error("CAA JSON error: %s" % (http.errorString()))
        else:
            if self.restrict_types:
                log.debug("CAA types: included: %s, excluded: %s", list(self.included_types), list(self.excluded_types))
            try:
                config = get_config()
                for image in data['images']:
                    if config.setting['caa_approved_only'] and not image['approved']:
                        continue
                    is_pdf = image['image'].endswith('.pdf')
                    if is_pdf and not config.setting['save_images_to_files']:
                        log.debug("Skipping pdf cover art : %s", image['image'])
                        continue
                    # if image has no type set, we still want it to match
                    # pseudo type 'unknown'
                    if not image['types']:
                        image['types'] = ['unknown']
                    else:
                        image['types'] = [t.lower() for t in image['types']]

                    if self.restrict_types:
                        # accept only if image types matches according to included/excluded types
                        accepted = bool(
                            set(image['types']).intersection(self.included_types).difference(self.excluded_types)
                        )
                        log.debug(
                            "CAA image %s: %s  %s",
                            ('accepted' if accepted else 'rejected'),
                            image['image'],
                            image['types'],
                        )
                    else:
                        accepted = True

                    if accepted:
                        thumbnail_list = caa_url_fallback_list(config.setting['caa_image_size'], image['thumbnails'])
                        if not thumbnail_list or is_pdf:
                            url = image['image']
                        else:
                            image_data = {'width': thumbnail_list[0].width, 'height': -1}
                            filters_result = run_image_metadata_filters(image_data)
                            if not filters_result:
                                continue
                            # FIXME: try other urls in case of 404
                            url = thumbnail_list[0].url
                        coverartimage = self.coverartimage_class(
                            url,
                            types=image['types'],
                            is_front=image['front'],
                            comment=image['comment'],
                        )
                        if thumbnail_list and is_pdf:
                            # thumbnail will be used to "display" PDF in info
                            # dialog
                            thumbnail = self.coverartimage_thumbnail_class(
                                url=thumbnail_list[0].url,
                                types=image['types'],
                                is_front=image['front'],
                                comment=image['comment'],
                            )
                            self.queue_put(thumbnail)
                            coverartimage.thumbnail = thumbnail
                            # PDFs cannot be saved to tags (as 2014/05/29)
                            coverartimage.can_be_saved_to_tags = False
                        self.queue_put(coverartimage)
                        if (
                            config.setting['save_only_one_front_image']
                            and config.setting['save_images_to_files']
                            and image['front']
                        ):
                            break
            except (AttributeError, KeyError, TypeError) as e:
                self.error("CAA JSON error: %s" % e)

        self.next_in_queue()
