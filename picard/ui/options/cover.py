# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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

from PyQt4 import QtCore, QtGui
from picard import config
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_cover import Ui_CoverOptionsPage
from picard.coverartarchive import CAA_TYPES, CAA_TYPES_SEPARATOR


class CAATypesSelector(object):
    def __init__(self, widget, enabled_types=''):
        self.widget = widget
        self._enabled_types = enabled_types.split(CAA_TYPES_SEPARATOR)
        self._items = {}
        self._populate()

    def _populate(self):
        for caa_type in CAA_TYPES:
            enabled = caa_type["name"] in self._enabled_types
            self._add_item(caa_type, enabled=enabled)

    def _add_item(self, typ, enabled=False):
        item = QtGui.QListWidgetItem(self.widget)
        item.setText(typ['title'])
        tooltip = u"CAA: %(name)s" % typ
        item.setToolTip(tooltip)
        if enabled:
            state = QtCore.Qt.Checked
        else:
            state = QtCore.Qt.Unchecked
        item.setCheckState(state)
        self._items[item] = typ

    def get_selected_types(self):
        types = []
        for item, typ in self._items.iteritems():
            if item.checkState() == QtCore.Qt.Checked:
                types.append(typ['name'])
        return types

    def get_selected_types_as_string(self):
        return CAA_TYPES_SEPARATOR.join(self.get_selected_types())

    def __str__(self):
        return self.get_selected_types_as_string()


class CoverOptionsPage(OptionsPage):

    NAME = "cover"
    TITLE = N_("Cover Art")
    PARENT = None
    SORT_ORDER = 35
    ACTIVE = True

    options = [
        config.BoolOption("setting", "save_images_to_tags", True),
        config.BoolOption("setting", "save_only_front_images_to_tags", False),
        config.BoolOption("setting", "save_images_to_files", False),
        config.TextOption("setting", "cover_image_filename", "cover"),
        config.BoolOption("setting", "save_images_overwrite", False),
        config.BoolOption("setting", "ca_provider_use_amazon", False),
        config.BoolOption("setting", "ca_provider_use_cdbaby", False),
        config.BoolOption("setting", "ca_provider_use_caa", False),
        config.BoolOption("setting", "ca_provider_use_whitelist", False),
        config.BoolOption("setting", "caa_approved_only", False),
        config.BoolOption("setting", "caa_image_type_as_filename", False),
        config.IntOption("setting", "caa_image_size", 2),
        config.TextOption("setting", "caa_image_types", u"front"),
    ]

    def __init__(self, parent=None):
        super(CoverOptionsPage, self).__init__(parent)
        self.ui = Ui_CoverOptionsPage()
        self.ui.setupUi(self)
        self.ui.save_images_to_files.clicked.connect(self.update_filename)

    def load(self):
        self.ui.save_images_to_tags.setChecked(config.setting["save_images_to_tags"])
        self.ui.cb_embed_front_only.setChecked(config.setting["save_only_front_images_to_tags"])
        self.ui.save_images_to_files.setChecked(config.setting["save_images_to_files"])
        self.ui.cover_image_filename.setText(config.setting["cover_image_filename"])
        self.ui.save_images_overwrite.setChecked(config.setting["save_images_overwrite"])
        self.update_filename()
        self.ui.caprovider_amazon.setChecked(config.setting["ca_provider_use_amazon"])
        self.ui.caprovider_cdbaby.setChecked(config.setting["ca_provider_use_cdbaby"])
        self.ui.caprovider_caa.setChecked(config.setting["ca_provider_use_caa"])
        self.ui.caprovider_whitelist.setChecked(config.setting["ca_provider_use_whitelist"])
        self.ui.gb_caa.setEnabled(config.setting["ca_provider_use_caa"])

        self.ui.cb_image_size.setCurrentIndex(config.setting["caa_image_size"])
        widget = self.ui.caa_types_selector_1
        self._selector = CAATypesSelector(widget, config.setting["caa_image_types"])
        config.setting["caa_image_types"] = \
                self._selector.get_selected_types_as_string()
        self.ui.cb_approved_only.setChecked(config.setting["caa_approved_only"])
        self.ui.cb_type_as_filename.setChecked(config.setting["caa_image_type_as_filename"])
        self.connect(self.ui.caprovider_caa, QtCore.SIGNAL("toggled(bool)"),
                self.ui.gb_caa.setEnabled)

    def save(self):
        config.setting["save_images_to_tags"] = self.ui.save_images_to_tags.isChecked()
        config.setting["save_only_front_images_to_tags"] = self.ui.cb_embed_front_only.isChecked()
        config.setting["save_images_to_files"] = self.ui.save_images_to_files.isChecked()
        config.setting["cover_image_filename"] = unicode(self.ui.cover_image_filename.text())
        config.setting["ca_provider_use_amazon"] =\
            self.ui.caprovider_amazon.isChecked()
        config.setting["ca_provider_use_cdbaby"] =\
            self.ui.caprovider_cdbaby.isChecked()
        config.setting["ca_provider_use_caa"] =\
            self.ui.caprovider_caa.isChecked()
        config.setting["ca_provider_use_whitelist"] =\
            self.ui.caprovider_whitelist.isChecked()
        config.setting["caa_image_size"] =\
            self.ui.cb_image_size.currentIndex()
        config.setting["caa_image_types"] = \
            self._selector.get_selected_types_as_string()
        config.setting["caa_approved_only"] =\
            self.ui.cb_approved_only.isChecked()
        config.setting["caa_image_type_as_filename"] = \
            self.ui.cb_type_as_filename.isChecked()

        config.setting["save_images_overwrite"] = self.ui.save_images_overwrite.isChecked()

    def update_filename(self):
        enabled = self.ui.save_images_to_files.isChecked()
        self.ui.cover_image_filename.setEnabled(enabled)
        self.ui.save_images_overwrite.setEnabled(enabled)


register_options_page(CoverOptionsPage)
