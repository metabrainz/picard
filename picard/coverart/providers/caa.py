# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007 Oliver Charles
# Copyright (C) 2007, 2010-2011 Lukáš Lalinský
# Copyright (C) 2007-2011, 2015, 2018-2023 Philipp Wolfer
# Copyright (C) 2011 Michael Wiencek
# Copyright (C) 2011-2012 Wieland Hoffmann
# Copyright (C) 2013-2015, 2018-2022 Laurent Monin
# Copyright (C) 2015-2016 Rahul Raturi
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Frederik “Freso” S. Olesen
# Copyright (C) 2018 Bob Swift
# Copyright (C) 2018 Vishal Choudhary
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
from functools import partial

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)
from PyQt5.QtNetwork import (
    QNetworkReply,
    QNetworkRequest,
)

from picard import log
from picard.config import (
    BoolOption,
    IntOption,
    ListOption,
    get_config,
)
from picard.const import CAA_URL
from picard.coverart.image import (
    CaaCoverArtImage,
    CaaThumbnailCoverArtImage,
)
from picard.coverart.providers.provider import (
    CoverArtProvider,
    ProviderOptions,
)
from picard.coverart.utils import (
    CAA_TYPES,
    translate_caa_type,
)
from picard.webservice import ratecontrol

from picard.ui import PicardDialog
from picard.ui.ui_provider_options_caa import Ui_CaaOptions
from picard.ui.util import (
    StandardButton,
    qlistwidget_items,
)


CaaSizeItem = namedtuple('CaaSizeItem', ['thumbnail', 'label'])

_CAA_THUMBNAIL_SIZE_MAP = OrderedDict([
    (250, CaaSizeItem('250', N_('250 px'))),
    (500, CaaSizeItem('500', N_('500 px'))),
    (1200, CaaSizeItem('1200', N_('1200 px'))),
    (-1, CaaSizeItem(None, N_('Full size'))),
])
_CAA_THUMBNAIL_SIZE_ALIASES = {
    '500': 'large',
    '250': 'small',
}
_CAA_IMAGE_SIZE_DEFAULT = 500

_CAA_IMAGE_TYPE_DEFAULT_INCLUDE = ['front']
_CAA_IMAGE_TYPE_DEFAULT_EXCLUDE = ['matrix/runout', 'raw/unedited', 'watermark']

ratecontrol.set_minimum_delay_for_url(CAA_URL, 0)
ratecontrol.set_minimum_delay_for_url('https://archive.org', 0)


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
        url = thumbnails.get(item.thumbnail, None)
        if url is None:
            size_alias = _CAA_THUMBNAIL_SIZE_ALIASES.get(item.thumbnail, None)
            if size_alias is not None:
                url = thumbnails.get(size_alias, None)
        if url is not None:
            urls.append(url)
    return urls


class ArrowButton(QtWidgets.QPushButton):
    """Standard arrow button for CAA image type selection dialog.

    Keyword Arguments:
        label {string} -- Label to display on the button
        command {command} -- Command to execute when the button is clicked (default: {None})
        parent {[type]} -- Parent of the QPushButton object being created (default: {None})
    """

    def __init__(self, icon_name, command=None, parent=None):
        icon = QtGui.QIcon(":/images/16x16/" + icon_name + '.png')
        super().__init__(icon, "", parent=parent)
        if command is not None:
            self.clicked.connect(command)


class ArrowsColumn(QtWidgets.QWidget):
    """Standard arrow buttons column for CAA image type selection dialog.

    Keyword Arguments:
        selection_list {ListBox} -- ListBox of selected items associated with this arrow column
        ignore_list {ListBox} -- ListBox of unselected items associated with this arrow column
        callback {command} -- Command to execute after items are moved between lists (default: {None})
        reverse {bool} -- Determines whether the arrow directions should be reversed (default: {False})
        parent {[type]} -- Parent of the QWidget object being created (default: {None})
    """

    def __init__(self, selection_list, ignore_list, callback=None, reverse=False, parent=None):
        super().__init__(parent=parent)
        self.selection_list = selection_list
        self.ignore_list = ignore_list
        self.callback = callback
        spacer_item = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        arrows_layout = QtWidgets.QVBoxLayout()
        arrows_layout.addItem(QtWidgets.QSpacerItem(spacer_item))
        self.button_add = ArrowButton('go-next' if reverse else 'go-previous', self.move_from_ignore)
        arrows_layout.addWidget(self.button_add)
        self.button_add_all = ArrowButton('move-all-right' if reverse else 'move-all-left', self.move_all_from_ignore)
        arrows_layout.addWidget(self.button_add_all)
        self.button_remove = ArrowButton('go-previous' if reverse else 'go-next', self.move_to_ignore)
        arrows_layout.addWidget(self.button_remove)
        self.button_remove_all = ArrowButton('move-all-left' if reverse else 'move-all-right', self.move_all_to_ignore)
        arrows_layout.addWidget(self.button_remove_all)
        arrows_layout.addItem(QtWidgets.QSpacerItem(spacer_item))
        self.setLayout(arrows_layout)

    def move_from_ignore(self):
        self.ignore_list.move_selected_items(self.selection_list, callback=self.callback)

    def move_all_from_ignore(self):
        self.ignore_list.move_all_items(self.selection_list, callback=self.callback)

    def move_to_ignore(self):
        self.selection_list.move_selected_items(self.ignore_list, callback=self.callback)

    def move_all_to_ignore(self):
        self.selection_list.move_all_items(self.ignore_list, callback=self.callback)


class ListBox(QtWidgets.QListWidget):
    """Standard list box for CAA image type selection dialog.

    Keyword Arguments:
        parent {[type]} -- Parent of the QListWidget object being created (default: {None})
    """

    LISTBOX_WIDTH = 100
    LISTBOX_HEIGHT = 250

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setMinimumSize(QtCore.QSize(self.LISTBOX_WIDTH, self.LISTBOX_HEIGHT))
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.setSortingEnabled(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)

    def move_item(self, item, target_list):
        """Move the specified item to another listbox."""
        self.takeItem(self.row(item))
        target_list.addItem(item)

    def move_selected_items(self, target_list, callback=None):
        """Move the selected item to another listbox."""
        for item in self.selectedItems():
            self.move_item(item, target_list)
        if callback:
            callback()

    def move_all_items(self, target_list, callback=None):
        """Move all items to another listbox."""
        while self.count():
            self.move_item(self.item(0), target_list)
        if callback:
            callback()

    def all_items_data(self, role=QtCore.Qt.ItemDataRole.UserRole):
        for item in qlistwidget_items(self):
            yield item.data(role)


class CAATypesSelectorDialog(PicardDialog):
    """Display dialog box to select the CAA image types to include and exclude from download and use.

    Keyword Arguments:
        parent {[type]} -- Parent of the QDialog object being created (default: {None})
        types_include {[string]} -- List of CAA image types to include (default: {None})
        types_exclude {[string]} -- List of CAA image types to exclude (default: {None})
    """

    help_url = 'doc_cover_art_types'

    def __init__(self, parent=None, types_include=None, types_exclude=None):
        super().__init__(parent)
        if types_include is None:
            types_include = []
        if types_exclude is None:
            types_exclude = []

        self.setWindowTitle(_("Cover art types"))
        self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetFixedSize)

        # Create list boxes for dialog
        self.list_include = ListBox()
        self.list_exclude = ListBox()
        self.list_ignore = ListBox()

        # Populate list boxes from current settings
        self.fill_lists(types_include, types_exclude)

        # Set triggers when the lists receive the current focus
        self.list_include.clicked.connect(partial(self.clear_focus, [self.list_ignore, self.list_exclude]))
        self.list_exclude.clicked.connect(partial(self.clear_focus, [self.list_ignore, self.list_include]))
        self.list_ignore.clicked.connect(partial(self.clear_focus, [self.list_include, self.list_exclude]))

        # Add instructions to the dialog box
        instructions = QtWidgets.QLabel()
        instructions.setText(_("Please select the contents of the image type 'Include' and 'Exclude' lists."))
        instructions.setWordWrap(True)
        instructions.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.layout.addWidget(instructions)

        self.arrows_include = ArrowsColumn(
            self.list_include,
            self.list_ignore,
            callback=self.set_buttons_enabled_state,
        )

        self.arrows_exclude = ArrowsColumn(
            self.list_exclude,
            self.list_ignore,
            callback=self.set_buttons_enabled_state,
            reverse=True
        )

        lists_layout = QtWidgets.QHBoxLayout()

        include_list_layout = QtWidgets.QVBoxLayout()
        include_list_layout.addWidget(QtWidgets.QLabel(_("Include types list")))
        include_list_layout.addWidget(self.list_include)
        lists_layout.addLayout(include_list_layout)

        lists_layout.addWidget(self.arrows_include)

        ignore_list_layout = QtWidgets.QVBoxLayout()
        ignore_list_layout.addWidget(QtWidgets.QLabel(""))
        ignore_list_layout.addWidget(self.list_ignore)
        lists_layout.addLayout(ignore_list_layout)

        lists_layout.addWidget(self.arrows_exclude)

        exclude_list_layout = QtWidgets.QVBoxLayout()
        exclude_list_layout.addWidget(QtWidgets.QLabel(_("Exclude types list")))
        exclude_list_layout.addWidget(self.list_exclude)
        lists_layout.addLayout(exclude_list_layout)

        self.layout.addLayout(lists_layout)

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
        instructions.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.layout.addWidget(instructions)

        self.buttonbox = QtWidgets.QDialogButtonBox(self)
        self.buttonbox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonbox.addButton(
            StandardButton(StandardButton.OK), QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self.buttonbox.addButton(StandardButton(StandardButton.CANCEL),
                                 QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        self.buttonbox.addButton(
            StandardButton(StandardButton.HELP), QtWidgets.QDialogButtonBox.ButtonRole.HelpRole)

        extrabuttons = [
            (N_("I&nclude all"), self.move_all_to_include_list),
            (N_("E&xclude all"), self.move_all_to_exclude_list),
            (N_("C&lear all"), self.move_all_to_ignore_list),
            (N_("Restore &Defaults"), self.reset_to_defaults),
        ]
        for label, callback in extrabuttons:
            button = QtWidgets.QPushButton(_(label))
            self.buttonbox.addButton(button, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
            button.clicked.connect(callback)

        self.layout.addWidget(self.buttonbox)

        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        self.buttonbox.helpRequested.connect(self.show_help)

        self.set_buttons_enabled_state()

    def move_all_to_include_list(self):
        self.list_ignore.move_all_items(self.list_include)
        self.list_exclude.move_all_items(self.list_include)
        self.set_buttons_enabled_state()

    def move_all_to_exclude_list(self):
        self.list_ignore.move_all_items(self.list_exclude)
        self.list_include.move_all_items(self.list_exclude)
        self.set_buttons_enabled_state()

    def move_all_to_ignore_list(self):
        self.list_include.move_all_items(self.list_ignore)
        self.list_exclude.move_all_items(self.list_ignore)
        self.set_buttons_enabled_state()

    def fill_lists(self, includes, excludes):
        """Fill dialog listboxes.

        First clears the contents of the three listboxes, and then populates the listboxes
        from the dictionary of standard CAA types, using the provided 'includes' and
        'excludes' lists to determine the appropriate list for each type.

        Arguments:
            includes -- list of standard image types to place in the "Include" listbox
            excludes -- list of standard image types to place in the "Exclude" listbox
        """
        self.list_include.clear()
        self.list_exclude.clear()
        self.list_ignore.clear()
        for caa_type in CAA_TYPES:
            name = caa_type['name']
            title = translate_caa_type(name)
            item = QtWidgets.QListWidgetItem(title)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, name)
            if name in includes:
                self.list_include.addItem(item)
            elif name in excludes:
                self.list_exclude.addItem(item)
            else:
                self.list_ignore.addItem(item)

    def get_selected_types_include(self):
        return list(self.list_include.all_items_data()) or ['front']

    def get_selected_types_exclude(self):
        return list(self.list_exclude.all_items_data()) or ['none']

    def clear_focus(self, lists):
        for temp_list in lists:
            temp_list.clearSelection()
        self.set_buttons_enabled_state()

    def reset_to_defaults(self):
        self.fill_lists(_CAA_IMAGE_TYPE_DEFAULT_INCLUDE, _CAA_IMAGE_TYPE_DEFAULT_EXCLUDE)
        self.set_buttons_enabled_state()

    def set_buttons_enabled_state(self):
        has_items_include = self.list_include.count()
        has_items_exclude = self.list_exclude.count()
        has_items_ignore = self.list_ignore.count()

        has_selected_include = bool(self.list_include.selectedItems())
        has_selected_exclude = bool(self.list_exclude.selectedItems())
        has_selected_ignore = bool(self.list_ignore.selectedItems())

        # "Include" list buttons
        self.arrows_include.button_add.setEnabled(has_items_ignore and has_selected_ignore)
        self.arrows_include.button_add_all.setEnabled(has_items_ignore)
        self.arrows_include.button_remove.setEnabled(has_items_include and has_selected_include)
        self.arrows_include.button_remove_all.setEnabled(has_items_include)

        # "Exclude" list buttons
        self.arrows_exclude.button_add.setEnabled(has_items_ignore and has_selected_ignore)
        self.arrows_exclude.button_add_all.setEnabled(has_items_ignore)
        self.arrows_exclude.button_remove.setEnabled(has_items_exclude and has_selected_exclude)
        self.arrows_exclude.button_remove_all.setEnabled(has_items_exclude)

    @staticmethod
    def run(parent=None, types_include=None, types_exclude=None):
        if types_include is None:
            types_include = []
        if types_exclude is None:
            types_exclude = []
        dialog = CAATypesSelectorDialog(parent, types_include, types_exclude)
        result = dialog.exec_()
        return (dialog.get_selected_types_include(), dialog.get_selected_types_exclude(), result == QtWidgets.QDialog.DialogCode.Accepted)


class ProviderOptionsCaa(ProviderOptions):
    """
        Options for Cover Art Archive cover art provider
    """

    TITLE = N_("Cover Art Archive")
    HELP_URL = '/config/options_cover_art_archive.html'

    options = [
        BoolOption("setting", "caa_approved_only", False),
        IntOption("setting", "caa_image_size", _CAA_IMAGE_SIZE_DEFAULT),
        ListOption("setting", "caa_image_types", _CAA_IMAGE_TYPE_DEFAULT_INCLUDE),
        BoolOption("setting", "caa_restrict_image_types", True),
        ListOption("setting", "caa_image_types_to_omit", _CAA_IMAGE_TYPE_DEFAULT_EXCLUDE),
    ]

    _options_ui = Ui_CaaOptions

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui.restrict_images_types.clicked.connect(self.update_caa_types)
        self.ui.select_caa_types.clicked.connect(self.select_caa_types)

    def restore_defaults(self):
        self.caa_image_types = _CAA_IMAGE_TYPE_DEFAULT_INCLUDE
        self.caa_image_types_to_omit = _CAA_IMAGE_TYPE_DEFAULT_EXCLUDE
        super().restore_defaults()

    def load(self):
        self.ui.cb_image_size.clear()
        for item_id, item in _CAA_THUMBNAIL_SIZE_MAP.items():
            self.ui.cb_image_size.addItem(_(item.label), userData=item_id)

        config = get_config()
        size = config.setting["caa_image_size"]
        index = self.ui.cb_image_size.findData(size)
        if index < 0:
            index = self.ui.cb_image_size.findData(_CAA_IMAGE_SIZE_DEFAULT)
        self.ui.cb_image_size.setCurrentIndex(index)

        self.ui.cb_approved_only.setChecked(config.setting["caa_approved_only"])
        self.ui.restrict_images_types.setChecked(
            config.setting["caa_restrict_image_types"])
        self.caa_image_types = config.setting["caa_image_types"]
        self.caa_image_types_to_omit = config.setting["caa_image_types_to_omit"]
        self.update_caa_types()

    def save(self):
        config = get_config()
        size = self.ui.cb_image_size.currentData()
        config.setting["caa_image_size"] = size
        config.setting["caa_approved_only"] = \
            self.ui.cb_approved_only.isChecked()
        config.setting["caa_restrict_image_types"] = \
            self.ui.restrict_images_types.isChecked()
        config.setting["caa_image_types"] = self.caa_image_types
        config.setting["caa_image_types_to_omit"] = self.caa_image_types_to_omit

    def update_caa_types(self):
        enabled = self.ui.restrict_images_types.isChecked()
        self.ui.select_caa_types.setEnabled(enabled)

    def select_caa_types(self):
        (types, types_to_omit, ok) = CAATypesSelectorDialog.run(
            self, self.caa_image_types, self.caa_image_types_to_omit)
        if ok:
            self.caa_image_types = types
            self.caa_image_types_to_omit = types_to_omit


class CoverArtProviderCaa(CoverArtProvider):

    """Get cover art from Cover Art Archive using release mbid"""

    NAME = "Cover Art Archive"
    TITLE = N_('Cover Art Archive: Release')
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
            self.len_included_types = len(self.included_types)

    @property
    def _has_suitable_artwork(self):
        # MB web service indicates if CAA has artwork
        # https://tickets.metabrainz.org/browse/MBS-4536
        if 'cover-art-archive' not in self.release:
            log.debug('No Cover Art Archive information for %s', self.release['id'])
            return False

        caa_node = self.release['cover-art-archive']
        caa_has_suitable_artwork = caa_node['artwork']

        if not caa_has_suitable_artwork:
            log.debug('There are no images in the Cover Art Archive for %s', self.release['id'])
            return False

        if self.restrict_types:
            want_front = 'front' in self.included_types
            want_back = 'back' in self.included_types
            caa_has_front = caa_node['front']
            caa_has_back = caa_node['back']

            if self.len_included_types == 2 and (want_front or want_back):
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

            elif self.len_included_types == 1 and (want_front or want_back):
                front_in_caa = caa_has_front and want_front
                back_in_caa = caa_has_back and want_back
                caa_has_suitable_artwork = front_in_caa or back_in_caa

        if not caa_has_suitable_artwork:
            log.debug('There are no suitable images in the Cover Art Archive for %s', self.release['id'])
        else:
            log.debug('There are suitable images in the Cover Art Archive for %s', self.release['id'])

        return caa_has_suitable_artwork

    def enabled(self):
        """Check if CAA artwork has to be downloaded"""
        if not super().enabled():
            return False
        if self.restrict_types and not self.len_included_types:
            log.debug('User disabled all Cover Art Archive types')
            return False
        return self._has_suitable_artwork

    @property
    def _caa_path(self):
        return "/release/%s/" % self.metadata["musicbrainz_albumid"]

    def queue_images(self):
        self.album.tagger.webservice.get_url(
            url=CAA_URL + self._caa_path,
            handler=self._caa_json_downloaded,
            priority=True,
            important=False,
            cacheloadcontrol=QNetworkRequest.CacheLoadControl.PreferNetwork,
        )
        self.album._requests += 1
        # we will call next_in_queue() after json parsing
        return CoverArtProvider.WAIT

    def _caa_json_downloaded(self, data, http, error):
        """Parse CAA JSON file and queue CAA cover art images for download"""
        self.album._requests -= 1
        if error:
            if not (error == QNetworkReply.NetworkError.ContentNotFoundError and self.ignore_json_not_found_error):
                self.error('CAA JSON error: %s' % (http.errorString()))
        else:
            if self.restrict_types:
                log.debug('CAA types: included: %s, excluded: %s', self.included_types, self.excluded_types)
            try:
                config = get_config()
                for image in data['images']:
                    if config.setting['caa_approved_only'] and not image['approved']:
                        continue
                    is_pdf = image['image'].endswith('.pdf')
                    if is_pdf and not config.setting['save_images_to_files']:
                        log.debug("Skipping pdf cover art : %s", image["image"])
                        continue
                    # if image has no type set, we still want it to match
                    # pseudo type 'unknown'
                    if not image['types']:
                        image['types'] = ['unknown']
                    else:
                        image['types'] = [t.lower() for t in image['types']]
                    if self.restrict_types:
                        # only keep enabled caa types
                        types = set(image['types']).intersection(self.included_types)
                        if types and self.excluded_types:
                            types = not set(image['types']).intersection(self.excluded_types)
                        log.debug('CAA image %s: %s  %s',
                            ('accepted' if types else 'rejected'),
                            image['image'],
                            image['types']
                        )
                    else:
                        types = True
                    if types:
                        urls = caa_url_fallback_list(config.setting['caa_image_size'], image['thumbnails'])
                        if not urls or is_pdf:
                            url = image['image']
                        else:
                            # FIXME: try other urls in case of 404
                            url = urls[0]
                        coverartimage = self.coverartimage_class(
                            url,
                            types=image['types'],
                            is_front=image['front'],
                            comment=image['comment'],
                        )
                        if urls and is_pdf:
                            # thumbnail will be used to "display" PDF in info
                            # dialog
                            thumbnail = self.coverartimage_thumbnail_class(
                                url=urls[0],
                                types=image['types'],
                                is_front=image['front'],
                                comment=image['comment'],
                            )
                            self.queue_put(thumbnail)
                            coverartimage.thumbnail = thumbnail
                            # PDFs cannot be saved to tags (as 2014/05/29)
                            coverartimage.can_be_saved_to_tags = False
                        self.queue_put(coverartimage)
                        if config.setting['save_only_one_front_image'] and \
                                config.setting['save_images_to_files'] and \
                                image['front']:
                            break
            except (AttributeError, KeyError, TypeError) as e:
                self.error('CAA JSON error: %s' % e)

        self.next_in_queue()
