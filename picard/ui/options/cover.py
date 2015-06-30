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
from picard.coverart.utils import CAA_TYPES, translate_caa_type
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.util import StandardButton
from picard.ui.ui_options_cover import Ui_CoverOptionsPage
from picard.util import webbrowser2
from picard.coverart.providers import cover_art_providers, is_provider_enabled
from picard.ui.sortchecklist import SortCheckListItem, SortCheckListView


_DEFAULT_LOCAL_COVER_ART_REGEX = '^(?:cover|folder|albumart)(.*)\.(?:jpe?g|png|gif|tiff?)$'


class CAATypesSelectorDialog(QtGui.QDialog):
    _columns = 4

    def __init__(self, parent=None, types=[]):
        super(CAATypesSelectorDialog, self).__init__(parent)

        self.setWindowTitle(_("Cover art types"))
        self._items = {}
        self.layout = QtGui.QVBoxLayout(self)

        grid = QtGui.QWidget()
        gridlayout = QtGui.QGridLayout()
        grid.setLayout(gridlayout)

        rows = len(CAA_TYPES) // self._columns + 1
        positions = [(i, j) for i in range(rows) for j in range(self._columns)]

        for position, caa_type in zip(positions, CAA_TYPES):
            name = caa_type["name"]
            text = translate_caa_type(name)
            item = QtGui.QCheckBox(text)
            item.setChecked(name in types)
            self._items[item] = caa_type
            gridlayout.addWidget(item, *position)

        self.layout.addWidget(grid)

        self.buttonbox = QtGui.QDialogButtonBox(self)
        self.buttonbox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonbox.addButton(
            StandardButton(StandardButton.OK), QtGui.QDialogButtonBox.AcceptRole)
        self.buttonbox.addButton(StandardButton(StandardButton.CANCEL),
                                 QtGui.QDialogButtonBox.RejectRole)
        self.buttonbox.addButton(
            StandardButton(StandardButton.HELP), QtGui.QDialogButtonBox.HelpRole)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        self.buttonbox.helpRequested.connect(self.help)

        extrabuttons = [
            (N_("Chec&k all"), self.checkall),
            (N_("&Uncheck all"), self.uncheckall),
        ]
        for label, callback in extrabuttons:
            button = QtGui.QPushButton(_(label))
            button.setSizePolicy(
                QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding)
            self.buttonbox.addButton(button, QtGui.QDialogButtonBox.ActionRole)
            button.clicked.connect(callback)

        self.layout.addWidget(self.buttonbox)

        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

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
        types = []
        for item, typ in self._items.iteritems():
            if item.isChecked():
                types.append(typ['name'])
        if not types:
            return [u'front']
        return types

    @staticmethod
    def run(parent=None, types=[]):
        dialog = CAATypesSelectorDialog(parent, types)
        result = dialog.exec_()
        return (dialog.get_selected_types(), result == QtGui.QDialog.Accepted)


class CoverOptionsPage(OptionsPage):

    NAME = "cover"
    TITLE = N_("Cover Art")
    PARENT = None
    SORT_ORDER = 35
    ACTIVE = True

    options = [
        config.BoolOption("setting", "save_images_to_tags", True),
        config.BoolOption("setting", "save_only_front_images_to_tags", True),
        config.BoolOption("setting", "save_images_to_files", False),
        config.TextOption("setting", "cover_image_filename", "cover"),
        config.BoolOption("setting", "save_images_overwrite", False),
        config.BoolOption("setting", "caa_approved_only", False),
        config.BoolOption("setting", "caa_image_type_as_filename", False),
        config.IntOption("setting", "caa_image_size", 1),
        config.ListOption("setting", "caa_image_types", [u"front"]),
        config.BoolOption("setting", "caa_restrict_image_types", True),
        config.ListOption("setting", "ca_providers",   [
            (N_('Cover Art Archive'), True),
            (N_('Amazon'), True),
            (N_('Whitelist'), True),
            (N_('CaaReleaseGroup'), False),
            (N_('Local'), False)]),
        config.TextOption("setting", "local_cover_regex",
                          _DEFAULT_LOCAL_COVER_ART_REGEX),
    ]

    def __init__(self, parent=None):
        super(CoverOptionsPage, self).__init__(parent)
        self.ui = Ui_CoverOptionsPage()
        self.ui.setupUi(self)
        self.ui.save_images_to_files.clicked.connect(self.update_filename)
        self.ui.restrict_images_types.clicked.connect(self.update_caa_types)
        self.ca_providers_list = SortCheckListView()
        self.ui.ca_providers_hbox.insertWidget(0, self.ca_providers_list)
        self.ca_providers_list.onChange(self.update_ca_providers)
        self.init_regex_checker(self.ui.local_cover_regex_edit, self.ui.local_cover_regex_error)
        self.ui.local_cover_regex_default.clicked.connect(self.set_local_cover_regex_default)

    def set_local_cover_regex_default(self):
        self.ui.local_cover_regex_edit.setText(_DEFAULT_LOCAL_COVER_ART_REGEX)

    def update_ca_providers(self, items):
        self.rebuild_ca_providers_opt(items)
        self.ui.tab_cover_art_archive.setEnabled(is_provider_enabled('Cover Art Archive') or
                                  is_provider_enabled('CaaReleaseGroup'))
        self.ui.tab_local_cover_art.setEnabled(is_provider_enabled('Local'))

    def ca_provider_label(self, provider_name):
        # TODO: move outside
        labels = {
            'Whitelist': N_('Sites in the whitelist'),
            'CaaReleaseGroup': N_('CAA Release Group image')
        }
        if provider_name in labels:
            return labels[provider_name]
        return provider_name

    def load(self):
        self.ui.local_cover_regex_edit.setText(config.setting["local_cover_regex"])
        self.ui.save_images_to_tags.setChecked(config.setting["save_images_to_tags"])
        self.ui.cb_embed_front_only.setChecked(config.setting["save_only_front_images_to_tags"])
        self.ui.save_images_to_files.setChecked(config.setting["save_images_to_files"])
        self.ui.cover_image_filename.setText(config.setting["cover_image_filename"])
        self.ui.save_images_overwrite.setChecked(config.setting["save_images_overwrite"])
        self.update_filename()

        providers = cover_art_providers()
        items = []
        for provider, name in providers:
            items.append(SortCheckListItem(text=_(self.ca_provider_label(name)),
                                           checked=is_provider_enabled(name),
                                           data=name))

        self.ca_providers_list.setItems(items)
        self.rebuild_ca_providers_opt()

        self.ui.cb_image_size.setCurrentIndex(config.setting["caa_image_size"])
        self.ui.cb_approved_only.setChecked(config.setting["caa_approved_only"])
        self.ui.cb_type_as_filename.setChecked(config.setting["caa_image_type_as_filename"])
        self.ui.select_caa_types.clicked.connect(self.select_caa_types)
        self.ui.restrict_images_types.setChecked(
            config.setting["caa_restrict_image_types"])
        self.update_caa_types()
        self.update_filename()

    def save(self):
        config.setting["local_cover_regex"] = unicode(self.ui.local_cover_regex_edit.text())
        config.setting["save_images_to_tags"] = self.ui.save_images_to_tags.isChecked()
        config.setting["save_only_front_images_to_tags"] = self.ui.cb_embed_front_only.isChecked()
        config.setting["save_images_to_files"] = self.ui.save_images_to_files.isChecked()
        config.setting["cover_image_filename"] = unicode(self.ui.cover_image_filename.text())
        config.setting["caa_image_size"] =\
            self.ui.cb_image_size.currentIndex()
        config.setting["caa_approved_only"] =\
            self.ui.cb_approved_only.isChecked()
        config.setting["caa_image_type_as_filename"] = \
            self.ui.cb_type_as_filename.isChecked()

        config.setting["save_images_overwrite"] = self.ui.save_images_overwrite.isChecked()
        config.setting["caa_restrict_image_types"] = \
            self.ui.restrict_images_types.isChecked()

        self.rebuild_ca_providers_opt()

    def rebuild_ca_providers_opt(self, items=None):
        if items is None:
            items = self.ca_providers_list.getItems()
        config.setting['ca_providers'] = [(item.data(), item.checked()) for item in items]


    def update_filename(self):
        enabled = self.ui.save_images_to_files.isChecked()
        self.ui.cover_image_filename.setEnabled(enabled)
        self.ui.save_images_overwrite.setEnabled(enabled)

    def update_caa_types(self):
        enabled = self.ui.restrict_images_types.isChecked()
        self.ui.select_caa_types.setEnabled(enabled)

    def select_caa_types(self):
        (types, ok) = CAATypesSelectorDialog.run(
            self, config.setting["caa_image_types"])
        if ok:
            config.setting["caa_image_types"] = types


register_options_page(CoverOptionsPage)
