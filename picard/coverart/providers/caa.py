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

from collections import (
    OrderedDict,
    namedtuple,
)

from PyQt5 import (
    QtCore,
    QtWidgets,
)
from PyQt5.QtNetwork import QNetworkReply

from picard import (
    config,
    log,
)
from picard.const import (
    CAA_HOST,
    CAA_PORT,
)
from picard.coverart.image import (
    CaaCoverArtImage,
    CaaThumbnailCoverArtImage,
)
from picard.coverart.providers import (
    CoverArtProvider,
    ProviderOptions,
)
from picard.coverart.utils import (
    CAA_TYPES,
    translate_caa_type,
)
from picard.util import (
    load_json,
    webbrowser2,
)

from picard.ui.ui_provider_options_caa import Ui_CaaOptions
from picard.ui.util import StandardButton

CaaSizeItem = namedtuple('CaaSizeItem', ['thumbnail', 'label'])

_CAA_THUMBNAIL_SIZE_MAP = OrderedDict([
    (250, CaaSizeItem('small', N_('250 px'))),
    (500, CaaSizeItem('large', N_('500 px'))),
    (1200, CaaSizeItem('1200', N_('1200 px'))),
    (-1, CaaSizeItem(None, N_('Full size'))),
])

_CAA_IMAGE_SIZE_DEFAULT = 500

_CAA_IMAGE_TYPE_DEFAULT_INCLUDE = [ 'front', ]
_CAA_IMAGE_TYPE_DEFAULT_EXCLUDE = [ 'raw/unedited', 'watermark', ]


def make_list_box():
    """Make standard list box for CAA image type selection dialog."""
    list_box = QtWidgets.QListWidget()
    list_box.setFixedSize(QtCore.QSize(150, 250))
    list_box.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
    list_box.setSortingEnabled(True)
    list_box.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
    return list_box

def make_arrow_button(label, command):
    """Make standard arrow button for CAA image type selection dialog."""
    item = QtWidgets.QPushButton(label)
    item.clicked.connect(command)
    item.setFixedSize(QtCore.QSize(35, 20))
    return item

def make_arrows_column(list_add, list_add_all, list_remove, list_remove_all, reverse=False):
    """Make standard arrow buttons column for CAA image type selection dialog."""
    _spacer_item = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
    arrows = QtWidgets.QWidget()
    arrows_layout = QtWidgets.QVBoxLayout()
    arrows.setLayout(arrows_layout)
    arrows_layout.addItem(QtWidgets.QSpacerItem(_spacer_item))
    arrows_layout.addWidget(make_arrow_button('>' if reverse else '<', list_add))
    arrows_layout.addWidget(make_arrow_button('>>' if reverse else '<<', list_add_all))
    arrows_layout.addWidget(make_arrow_button('<' if reverse else '>', list_remove))
    arrows_layout.addWidget(make_arrow_button('<<' if reverse else '>>', list_remove_all))
    arrows_layout.addItem(QtWidgets.QSpacerItem(_spacer_item))
    return arrows

def move_item(item, list1, list2):
    """Move the specified item from one listbox to another.  Used in the CAA image type selection dialog."""
    clone = item.clone()
    list2.addItem(clone)
    list1.takeItem(list1.row(item))

def move_selected_items(list1, list2):
    """Move the selected item from one listbox to another.  Used in the CAA image type selection dialog."""
    for item in list1.selectedItems():
        move_item(item, list1, list2)

def move_all_items(list1, list2):
    """Move all items from one listbox to another.  Used in the CAA image type selection dialog."""
    while list1.count():
        item = list1.item(0)
        move_item(item, list1, list2)

def clear_listbox_focus(list_to_clear):
    """Clear all item selections in the specified listbox."""
    list_to_clear.clearSelection()


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
    """Display dialog box to select the CAA image types to include and exclude from download and use."""

    # Dictionary of standard image type names by translated image type title
    #   key:    image type title displayed in list boxes (translated by i18n)
    #   value:  standard image type name
    #
    # This is used to return the include and exclude lists containing standard image
    # type names based on the titles displayed in the list boxes in the dialog.
    image_types_by_display_title = {}

    def __init__(self, parent=None, types_include=None, types_exclude=None):
        if types_include is None:
            types_include = []
        if types_exclude is None:
            types_exclude = []
        super().__init__(parent)

        self.setWindowTitle(_("Cover art types"))
        self.layout = QtWidgets.QVBoxLayout(self)

        # Populate display title / standard name dictionary
        for caa_type in CAA_TYPES:
            name = caa_type['name']
            title = _(caa_type['title'])
            self.image_types_by_display_title[title] = name

        # Create list boxes for dialog
        self.list_include = make_list_box()
        self.list_exclude = make_list_box()
        self.list_ignore = make_list_box()

        # Populate list boxes from current settings
        self.fill_lists(types_include, types_exclude)

        self.list_include.clicked.connect(self.focus_set_include)
        self.list_exclude.clicked.connect(self.focus_set_exclude)
        self.list_ignore.clicked.connect(self.focus_set_ignore)

        # Add instructions to the dialog box
        instructions = QtWidgets.QLabel()
        instructions.setText(_("Please select the contents of the image type 'Include' and 'Exclude' lists."))
        instructions.setWordWrap(True)
        instructions.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.layout.addWidget(instructions)

        grid = QtWidgets.QWidget()
        gridlayout = QtWidgets.QGridLayout()
        grid.setLayout(gridlayout)

        row = 0
        column = 0
        item = QtWidgets.QLabel()
        item.setText(_("Include types list"))
        gridlayout.addWidget(item, row, column)

        column = 4
        item = QtWidgets.QLabel()
        item.setText(_("Exclude types list"))
        gridlayout.addWidget(item, row, column)

        row = 1
        column = 0
        gridlayout.addWidget(self.list_include, row, column)

        column = 1
        self.arrows_include = make_arrows_column(self.add_include, self.add_include_all, self.remove_include, self.remove_include_all)
        gridlayout.addWidget(self.arrows_include, row, column)

        column = 2
        gridlayout.addWidget(self.list_ignore, row, column)

        column = 3
        self.arrows_exclude = make_arrows_column(self.add_exclude, self.add_exclude_all, self.remove_exclude, self.remove_exclude_all, reverse=True)
        gridlayout.addWidget(self.arrows_exclude, row, column)

        column = 4
        gridlayout.addWidget(self.list_exclude, row, column)

        self.layout.addWidget(grid)

        # Add usage explanation to the dialog box
        instructions = QtWidgets.QLabel()
        instructions.setText(_(
            "CAA images with an image type found in the 'Include' list will be downloaded and used "
            "UNLESS they also have an image type found in the 'Exclude' list. Images with types "
            "found in the 'Exclude' list will NEVER be used. Image types not appearing in the 'Include' "
            "or 'Exclude' lists will not be considered when determining whether or not to download and "
            "use a CAA image.\n")
        )
        instructions.setWordWrap(True)
        instructions.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.layout.addWidget(instructions)

        self.buttonbox = QtWidgets.QDialogButtonBox(self)
        self.buttonbox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonbox.addButton(
            StandardButton(StandardButton.OK), QtWidgets.QDialogButtonBox.AcceptRole)
        self.buttonbox.addButton(StandardButton(StandardButton.CANCEL),
                                 QtWidgets.QDialogButtonBox.RejectRole)
        self.buttonbox.addButton(
            StandardButton(StandardButton.HELP), QtWidgets.QDialogButtonBox.HelpRole)

        extrabuttons = [
            (N_("I&nclude all"), self.include_all),
            (N_("E&xclude all"), self.exclude_all),
            (N_("C&lear all"), self.clear_all),
            (N_("Restore &Defaults"), self.reset_to_defaults),
        ]
        for label, callback in extrabuttons:
            button = QtWidgets.QPushButton(label)
            button.setSizePolicy(
                QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
            self.buttonbox.addButton(button, QtWidgets.QDialogButtonBox.ActionRole)
            button.clicked.connect(callback)

        self.layout.addWidget(self.buttonbox)

        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        self.buttonbox.helpRequested.connect(self.help)

        self.fix_buttons()

    def fill_lists(self, includes, excludes):
        """Fill dialog listboxes.

        First clears the contents of the three listboxes, and then populates the listboxes
        from the dictionary of translated standard CAA types, using the provided 'includes'
        and 'excludes' lists to determine the appropriate list for each type.

        Arguments:
            includes -- list of standard image types to place in the "Include" listbox
            excludes -- list of standard image types to place in the "Exclude" listbox
        """
        self.list_include.clear()
        self.list_exclude.clear()
        self.list_ignore.clear()
        for title in self.image_types_by_display_title:
            name = self.image_types_by_display_title[title]
            if name in includes:
                self.list_include.addItem(title)
            elif name in excludes:
                self.list_exclude.addItem(title)
            else:
                self.list_ignore.addItem(title)

    def help(self):
        webbrowser2.goto('doc_cover_art_types')

    def add_include(self):
        move_selected_items(self.list_ignore, self.list_include)
        self.fix_buttons()

    def remove_include(self):
        move_selected_items(self.list_include, self.list_ignore)
        self.fix_buttons()

    def add_include_all(self):
        move_all_items(self.list_ignore, self.list_include)
        self.fix_buttons()

    def remove_include_all(self):
        move_all_items(self.list_include, self.list_ignore)
        self.fix_buttons()

    def add_exclude(self):
        move_selected_items(self.list_ignore, self.list_exclude)
        self.fix_buttons()

    def remove_exclude(self):
        move_selected_items(self.list_exclude, self.list_ignore)
        self.fix_buttons()

    def add_exclude_all(self):
        move_all_items(self.list_ignore, self.list_exclude)
        self.fix_buttons()

    def remove_exclude_all(self):
        move_all_items(self.list_exclude, self.list_ignore)
        self.fix_buttons()

    def include_all(self):
        move_all_items(self.list_ignore, self.list_include)
        move_all_items(self.list_exclude, self.list_include)
        self.fix_buttons()

    def exclude_all(self):
        move_all_items(self.list_ignore, self.list_exclude)
        move_all_items(self.list_include, self.list_exclude)
        self.fix_buttons()

    def clear_all(self):
        move_all_items(self.list_include, self.list_ignore)
        move_all_items(self.list_exclude, self.list_ignore)
        self.fix_buttons()

    def get_selected_types_include(self):
        return [self.image_types_by_display_title[self.list_include.item(index).text()] for index in range(self.list_include.count())] or ['front']

    def get_selected_types_exclude(self):
        return [self.image_types_by_display_title[self.list_exclude.item(index).text()] for index in range(self.list_exclude.count())] or ['none']

    def focus_set_include(self):
        clear_listbox_focus(self.list_exclude)
        clear_listbox_focus(self.list_ignore)
        self.fix_buttons()

    def focus_set_exclude(self):
        clear_listbox_focus(self.list_include)
        clear_listbox_focus(self.list_ignore)
        self.fix_buttons()

    def focus_set_ignore(self):
        clear_listbox_focus(self.list_include)
        clear_listbox_focus(self.list_exclude)
        self.fix_buttons()

    def focus_clear_all(self):
        clear_listbox_focus(self.list_include)
        clear_listbox_focus(self.list_exclude)
        clear_listbox_focus(self.list_ignore)
        self.fix_buttons()

    def reset_to_defaults(self):
        self.fill_lists(_CAA_IMAGE_TYPE_DEFAULT_INCLUDE, _CAA_IMAGE_TYPE_DEFAULT_EXCLUDE)
        self.fix_buttons()

    def fix_buttons(self):
        has_items_include = self.list_include.count()
        has_items_exclude = self.list_exclude.count()
        has_items_ignore = self.list_ignore.count()

        has_selected_include = True if self.list_include.selectedItems() else False
        has_selected_exclude = True if self.list_exclude.selectedItems() else False
        has_selected_ignore = True if self.list_ignore.selectedItems() else False

        # "Include" list buttons
        buttons = self.arrows_include.findChildren(QtWidgets.QPushButton)
        buttons[0].setEnabled(has_items_ignore and has_selected_ignore)     # '<'
        buttons[1].setEnabled(has_items_ignore)                             # '<<'
        buttons[2].setEnabled(has_items_include and has_selected_include)   # '>'
        buttons[3].setEnabled(has_items_include)                            # '>>'

        # "Exclude" list buttons
        buttons = self.arrows_exclude.findChildren(QtWidgets.QPushButton)
        buttons[0].setEnabled(has_items_ignore and has_selected_ignore)     # '>'
        buttons[1].setEnabled(has_items_ignore)                             # '>>'
        buttons[2].setEnabled(has_items_exclude and has_selected_exclude)   # '<'
        buttons[3].setEnabled(has_items_exclude)                            # '<<'

    @staticmethod
    def run(parent=None, types_include=None, types_exclude=None):
        if types_include is None:
            types_include = []
        if types_exclude is None:
            types_exclude = []
        dialog = CAATypesSelectorDialog(parent, types_include, types_exclude)
        result = dialog.exec_()
        return (dialog.get_selected_types_include(), dialog.get_selected_types_exclude(), result == QtWidgets.QDialog.Accepted)


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
        config.ListOption("setting", "caa_image_types", _CAA_IMAGE_TYPE_DEFAULT_INCLUDE),
        config.BoolOption("setting", "caa_restrict_image_types", True),
        config.ListOption("setting", "caa_image_types_to_omit", _CAA_IMAGE_TYPE_DEFAULT_EXCLUDE),
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
        (types, types_to_omit, ok) = CAATypesSelectorDialog.run(
            self, config.setting["caa_image_types"], config.setting["caa_image_types_to_omit"])
        if ok:
            config.setting["caa_image_types"] = types
            config.setting["caa_image_types_to_omit"] = types_to_omit



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
        self.caa_types_to_omit = list(map(str.lower, config.setting["caa_image_types_to_omit"]))
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
                if self.restrict_types:
                    log.debug('CAA types: included: %s, excluded: %s' % (self.caa_types, self.caa_types_to_omit,))
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
                        if types and self.caa_types_to_omit:
                            types = not set(image["types"]).intersection(
                                set(self.caa_types_to_omit))
                        log.debug('CAA image %s: %s  %s' % ('accepted' if types else 'rejected', image['image'], image['types'],))
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
