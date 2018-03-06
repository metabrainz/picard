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

from collections import OrderedDict, namedtuple
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtNetwork import QNetworkReply
from picard import config, log
from picard.const import CAA_HOST, CAA_PORT
from picard.coverart.providers import CoverArtProvider, ProviderOptions
from picard.coverart.image import CaaCoverArtImage, CaaThumbnailCoverArtImage
from picard.coverart.utils import CAA_TYPES, translate_caa_type
from picard.ui.ui_provider_options_caa import Ui_CaaOptions
from picard.ui.util import StandardButton
from picard.util import webbrowser2, load_json


CaaSizeItem = namedtuple('CaaSizeItem', ['thumbnail', 'label'])

_CAA_THUMBNAIL_SIZE_MAP = OrderedDict([
    (250, CaaSizeItem('small', N_('250 px'))),
    (500, CaaSizeItem('large', N_('500 px'))),
    (1200, CaaSizeItem('1200', N_('1200 px'))),
    (-1, CaaSizeItem(None, N_('Full size'))),
])

_CAA_IMAGE_SIZE_DEFAULT = 500


def caa_url_fallback_list(desired_size, thumbnails):
    """List of thumbnail urls equal or smaller than size, in size decreasing order
    It is used for find the "best" thumbnail according to:
        - user choice
        - thumbnail availability
    If user choice isn't matching an available thumbnail size, a fallback to
    smaller thumbnails is possible
    This function returns the list of possible urls, ordered from the biggest
    matching the user choice to the smallest one.
    Of course, if none are possible, the returned list may be empty.
    """
    reversed_map = OrderedDict(reversed(list(_CAA_THUMBNAIL_SIZE_MAP.items())))
    urls = []
    for item_id, item in reversed_map.items():
        if item_id == -1 or item_id > desired_size:
            continue
        if item.thumbnail in thumbnails:
            urls.append(thumbnails[item.thumbnail])
    return urls


class CAATypesSelectorDialog(QtWidgets.QDialog):
    _columns = 4

    def __init__(self, parent=None, types=None):
        if types is None:
            types = []
        super().__init__(parent)

        self.setWindowTitle(_("Cover art types"))
        self._items = {}
        self.layout = QtWidgets.QVBoxLayout(self)

        grid = QtWidgets.QWidget()
        gridlayout = QtWidgets.QGridLayout()
        grid.setLayout(gridlayout)

        for index, caa_type in enumerate(CAA_TYPES):
            row = index // self._columns
            column = index % self._columns
            name = caa_type["name"]
            text = translate_caa_type(name)
            item = QtWidgets.QCheckBox(text)
            item.setChecked(name in types)
            self._items[item] = caa_type
            gridlayout.addWidget(item, row, column)

        self.layout.addWidget(grid)

        self.buttonbox = QtWidgets.QDialogButtonBox(self)
        self.buttonbox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonbox.addButton(
            StandardButton(StandardButton.OK), QtWidgets.QDialogButtonBox.AcceptRole)
        self.buttonbox.addButton(StandardButton(StandardButton.CANCEL),
                                 QtWidgets.QDialogButtonBox.RejectRole)
        self.buttonbox.addButton(
            StandardButton(StandardButton.HELP), QtWidgets.QDialogButtonBox.HelpRole)

        extrabuttons = [
            (N_("Chec&k all"), self.checkall),
            (N_("&Uncheck all"), self.uncheckall),
        ]
        for label, callback in extrabuttons:
            button = QtWidgets.QPushButton(_(label))
            button.setSizePolicy(
                QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
            self.buttonbox.addButton(button, QtWidgets.QDialogButtonBox.ActionRole)
            button.clicked.connect(callback)

        self.layout.addWidget(self.buttonbox)

        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        self.buttonbox.helpRequested.connect(self.help)

    def help(self):
        webbrowser2.goto('doc_cover_art_types')

    def uncheckall(self):
        self._set_checked_all(False)

    def checkall(self):
        self._set_checked_all(True)

    def _set_checked_all(self, value):
        for item in self._items.keys():
            item.setChecked(value)

    def get_selected_types(self):
        return [typ['name'] for item, typ in self._items.items() if
                item.isChecked()] or ['front']

    @staticmethod
    def run(parent=None, types=None):
        if types is None:
                types = []
        dialog = CAATypesSelectorDialog(parent, types)
        result = dialog.exec_()
        return (dialog.get_selected_types(), result == QtWidgets.QDialog.Accepted)


class ProviderOptionsCaa(ProviderOptions):
    """
        Options for Cover Art Archive cover art provider
    """

    options = [
        config.BoolOption("setting", "caa_save_single_front_image", False),
        config.BoolOption("setting", "caa_approved_only", False),
        config.BoolOption("setting", "caa_image_type_as_filename", False),
        config.IntOption("setting", "caa_image_size",
                         _CAA_IMAGE_SIZE_DEFAULT),
        config.ListOption("setting", "caa_image_types", ["front"]),
        config.BoolOption("setting", "caa_restrict_image_types", True),
    ]

    _options_ui = Ui_CaaOptions

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui.restrict_images_types.clicked.connect(self.update_caa_types)
        self.ui.select_caa_types.clicked.connect(self.select_caa_types)

    def load(self):
        self.ui.cb_image_size.clear()
        for item_id, item in _CAA_THUMBNAIL_SIZE_MAP.items():
            self.ui.cb_image_size.addItem(_(item.label), userData=item_id)

        size = config.setting["caa_image_size"]
        index = self.ui.cb_image_size.findData(size)
        if index < 0:
            index = self.ui.cb_image_size.findData(_CAA_IMAGE_SIZE_DEFAULT)
        self.ui.cb_image_size.setCurrentIndex(index)

        self.ui.cb_save_single_front_image.setChecked(config.setting["caa_save_single_front_image"])
        self.ui.cb_approved_only.setChecked(config.setting["caa_approved_only"])
        self.ui.cb_type_as_filename.setChecked(config.setting["caa_image_type_as_filename"])
        self.ui.restrict_images_types.setChecked(
            config.setting["caa_restrict_image_types"])
        self.update_caa_types()

    def save(self):
        size = self.ui.cb_image_size.currentData()
        config.setting["caa_image_size"] = size
        config.setting["caa_save_single_front_image"] = \
            self.ui.cb_save_single_front_image.isChecked()
        config.setting["caa_approved_only"] = \
            self.ui.cb_approved_only.isChecked()
        config.setting["caa_image_type_as_filename"] = \
            self.ui.cb_type_as_filename.isChecked()
        config.setting["caa_restrict_image_types"] = \
            self.ui.restrict_images_types.isChecked()

    def update_caa_types(self):
        enabled = self.ui.restrict_images_types.isChecked()
        self.ui.select_caa_types.setEnabled(enabled)

    def select_caa_types(self):
        (types, ok) = CAATypesSelectorDialog.run(
            self, config.setting["caa_image_types"])
        if ok:
            config.setting["caa_image_types"] = types



class CoverArtProviderCaa(CoverArtProvider):

    """Get cover art from Cover Art Archive using release mbid"""

    NAME = "Cover Art Archive"
    TITLE = N_('Cover Art Archive')
    OPTIONS = ProviderOptionsCaa

    ignore_json_not_found_error = False
    coverartimage_class = CaaCoverArtImage
    coverartimage_thumbnail_class = CaaThumbnailCoverArtImage

    def __init__(self, coverart):
        super().__init__(coverart)
        self.caa_types = list(map(str.lower, config.setting["caa_image_types"]))
        self.len_caa_types = len(self.caa_types)
        self.restrict_types = config.setting["caa_restrict_image_types"]

    @property
    def _has_suitable_artwork(self):
        # MB web service indicates if CAA has artwork
        # https://tickets.metabrainz.org/browse/MBS-4536
        if 'cover-art-archive' not in self.release:
            log.debug("No Cover Art Archive information for %s"
                      % self.release['id'])
            return False

        caa_node = self.release['cover-art-archive']
        caa_has_suitable_artwork = caa_node['artwork']

        if not caa_has_suitable_artwork:
            log.debug("There are no images in the Cover Art Archive for %s"
                      % self.release['id'])
            return False

        if self.restrict_types:
            want_front = 'front' in self.caa_types
            want_back = 'back' in self.caa_types
            caa_has_front = caa_node['front']
            caa_has_back = caa_node['back']

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
                      % self.release['id'])
        else:
            log.debug("There are suitable images in the Cover Art Archive for %s"
                      % self.release['id'])

        return caa_has_suitable_artwork

    def enabled(self):
        """Check if CAA artwork has to be downloaded"""
        if not super().enabled() or \
                self.coverart.front_image_found:
            return False
        if self.restrict_types and not self.len_caa_types:
            log.debug("User disabled all Cover Art Archive types")
            return False
        return self._has_suitable_artwork

    @property
    def _caa_path(self):
        return "/release/%s/" % self.metadata["musicbrainz_albumid"]

    def queue_images(self):
        self.album.tagger.webservice.download(
            CAA_HOST,
            CAA_PORT,
            self._caa_path,
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
            if not (error == QNetworkReply.ContentNotFoundError and self.ignore_json_not_found_error):
                self.error('CAA JSON error: %s' % (http.errorString()))
        else:
            try:
                caa_data = load_json(data)
            except ValueError:
                self.error("Invalid JSON: %s" % (http.url().toString()))
            else:
                for image in caa_data["images"]:
                    if config.setting["caa_approved_only"] and not image["approved"]:
                        continue
                    is_pdf = image["image"].endswith('.pdf')
                    if is_pdf and not config.setting["save_images_to_files"]:
                        log.debug("Skipping pdf cover art : %s" %
                                  image["image"])
                        continue
                    # if image has no type set, we still want it to match
                    # pseudo type 'unknown'
                    if not image["types"]:
                        image["types"] = ["unknown"]
                    else:
                        image["types"] = list(map(str.lower, image["types"]))
                    if self.restrict_types:
                        # only keep enabled caa types
                        types = set(image["types"]).intersection(
                            set(self.caa_types))
                    else:
                        types = True
                    if types:
                        urls = caa_url_fallback_list(config.setting["caa_image_size"],
                                                     image["thumbnails"])
                        if not urls or is_pdf:
                            url = image["image"]
                        else:
                            #FIXME: try other urls in case of 404
                            url = urls[0]
                        coverartimage = self.coverartimage_class(
                            url,
                            types=image["types"],
                            is_front=image['front'],
                            comment=image["comment"],
                        )
                        if urls and is_pdf:
                            # thumbnail will be used to "display" PDF in info
                            # dialog
                            thumbnail = self.coverartimage_thumbnail_class(
                                url=url[0],
                                types=image["types"],
                                is_front=image['front'],
                                comment=image["comment"],
                            )
                            self.queue_put(thumbnail)
                            coverartimage.thumbnail = thumbnail
                            # PDFs cannot be saved to tags (as 2014/05/29)
                            coverartimage.can_be_saved_to_tags = False
                        self.queue_put(coverartimage)
                        if config.setting["caa_save_single_front_image"] and \
                                config.setting["save_images_to_files"] and \
                                image["front"]:
                                    break

        self.next_in_queue()
