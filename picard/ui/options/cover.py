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

from collections import defaultdict
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QPalette
from picard import config
from picard.coverart.utils import CAA_TYPES, translate_caa_type
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.util import StandardButton
from picard.ui.ui_options_cover import Ui_CoverOptionsPage
from picard.ui.ui_provider_tab import Ui_ProviderTab
from picard.util import webbrowser2
from picard.coverart.providers import cover_art_providers, is_provider_enabled


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


class ProviderOptions(QtGui.QWidget):

    """
        Abstract class for provider's options
    """

    options = []

    _options_ui = None

    def __init__(self, options_page, parent=None):
        super(ProviderOptions, self).__init__(parent)
        self.options_page = options_page
        if callable(self._options_ui):
            self.ui = self._options_ui()
            self.ui.setupUi(self)

    def load(self):
        pass

    def save(self):
        pass


from picard.ui.ui_provider_options_caa import Ui_CaaOptions
class ProviderOptionsCaa(ProviderOptions):
    """
        Options for Cover Art Archive cover art provider
    """

    options = [
        config.BoolOption("setting", "caa_approved_only", False),
        config.BoolOption("setting", "caa_image_type_as_filename", False),
        config.IntOption("setting", "caa_image_size", 1),
        config.ListOption("setting", "caa_image_types", [u"front"]),
        config.BoolOption("setting", "caa_restrict_image_types", True),
    ]

    _options_ui = Ui_CaaOptions

    def __init__(self, options_page, parent=None):
        super(ProviderOptionsCaa, self).__init__(options_page, parent)
        self.ui.restrict_images_types.clicked.connect(self.update_caa_types)
        self.ui.select_caa_types.clicked.connect(self.select_caa_types)

    def load(self):
        self.ui.cb_image_size.setCurrentIndex(config.setting["caa_image_size"])
        self.ui.cb_approved_only.setChecked(config.setting["caa_approved_only"])
        self.ui.cb_type_as_filename.setChecked(config.setting["caa_image_type_as_filename"])
        self.ui.restrict_images_types.setChecked(
            config.setting["caa_restrict_image_types"])
        self.update_caa_types()

    def save(self):
        config.setting["caa_image_size"] =\
            self.ui.cb_image_size.currentIndex()
        config.setting["caa_approved_only"] =\
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
            self.options_page, config.setting["caa_image_types"])
        if ok:
            config.setting["caa_image_types"] = types


from picard.ui.ui_provider_options_local import Ui_LocalOptions
class ProviderOptionsLocal(ProviderOptions):
    """
        Options for Local Files cover art provider
    """

    _DEFAULT_LOCAL_COVER_ART_REGEX = '^(?:cover|folder|albumart)(.*)\.(?:jpe?g|png|gif|tiff?)$'

    options = [
        config.TextOption("setting", "local_cover_regex",
                          _DEFAULT_LOCAL_COVER_ART_REGEX),
    ]

    _options_ui = Ui_LocalOptions

    def __init__(self, options_page, parent=None):
        super(ProviderOptionsLocal, self).__init__(options_page, parent)
        self.options_page.init_regex_checker(self.ui.local_cover_regex_edit, self.ui.local_cover_regex_error)
        self.ui.local_cover_regex_default.clicked.connect(self.set_local_cover_regex_default)

    def set_local_cover_regex_default(self):
        self.ui.local_cover_regex_edit.setText(self._DEFAULT_LOCAL_COVER_ART_REGEX)

    def load(self):
        self.ui.local_cover_regex_edit.setText(config.setting["local_cover_regex"])

    def save(self):
        config.setting["local_cover_regex"] = unicode(self.ui.local_cover_regex_edit.text())


class ProviderTab(QtGui.QWidget):

    def __init__(self, provider, parent=None):
        super(ProviderTab, self).__init__(parent)
        self.provider = provider
        self.ui = Ui_ProviderTab()
        self.ui.setupUi(self)


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
        config.ListOption("setting", "ca_providers", [
            ('Cover Art Archive', True),
            ('Amazon', True),
            ('Whitelist', True),
            ('CaaReleaseGroup', False),
            ('Local', False),
        ]),
    ]

    def __init__(self, parent=None):
        super(CoverOptionsPage, self).__init__(parent)
        self.ui = Ui_CoverOptionsPage()
        self.ui.setupUi(self)
        self.ui.save_images_to_files.clicked.connect(self.update_filename)

    def tabTitle(self, provider):
        if hasattr(provider, 'TITLE'):
            tab_title = _(provider.TITLE)
        else:
            tab_title = provider.NAME
        return tab_title

    def setTabColor(self, tabs, idx, enabled):
        palette = tabs.palette()
        normal_color = palette.color(QPalette.Normal, QPalette.WindowText)
        disabled_color = palette.color(QPalette.Disabled, QPalette.WindowText)
        if enabled:
            color = normal_color
        else:
            color = disabled_color
        tabs.tabBar().setTabTextColor(idx, color)

    def rebuild_ca_providers_opt(self):
        tabs = self.ui.tab_cover_art_providers
        new = []
        for idx in range(0, tabs.count()):
            widget = tabs.widget(idx)
            key = widget.provider.NAME
            enabled = widget.ui.enabled.isChecked()
            new.append((key, enabled))
            self.setTabColor(tabs, idx, enabled)
        config.setting['ca_providers'] = new

    def load_ca_providers(self):
        """
            Load available providers, initialize tabs, restore state of each
        """
        self.provider_options = defaultdict(list)
        providers = cover_art_providers()
        for provider in providers:
            tab = ProviderTab(provider)
            self.ui.tab_cover_art_providers.addTab(tab, self.tabTitle(provider))
            tab.ui.enabled.setChecked(is_provider_enabled(provider.NAME))
            # TODO : improve this
            options_widget = None
            if provider.NAME == 'Cover Art Archive':
                options_widget = ProviderOptionsCaa(self)
            elif provider.NAME == 'Local':
                options_widget = ProviderOptionsLocal(self)
            if options_widget is not None:
                tab.ui.scrollArea.setWidget(options_widget)
                for method in ('load', 'save'):
                    if hasattr(options_widget, method):
                        self.provider_options[method].append(getattr(options_widget,
                                                                     method))
            else:
                tab.ui.scrollArea.hide()
            tab.ui.enabled.toggled.connect(self.providerToggled)

        self.ui.moveleft.clicked.connect(self.moveTabLeft)
        self.ui.moveright.clicked.connect(self.moveTabRight)
        self.ui.tab_cover_art_providers.tabBar().tabMoved.connect(self.rebuild_ca_providers_opt)
        self.rebuild_ca_providers_opt()

    def providerToggled(self, state):
        self.rebuild_ca_providers_opt()

    def moveTab(self, tabs, old, new):
        """
            Move tab within TabWidget `tabs` from `old` index to `new` index
        """
        if old != new:
            widget = tabs.widget(old)
            tabs.insertTab(new, widget, self.tabTitle(widget.provider))
            tabs.setCurrentIndex(new)
            self.rebuild_ca_providers_opt()

    def moveTabLeft(self):
        """
            Move current tab to the left, wrap around if needed
        """
        tabs = self.ui.tab_cover_art_providers
        current = tabs.currentIndex()
        if current != -1:
            if current > 0:
                left = current - 1
            else:
                left = tabs.count() - 1
            self.moveTab(tabs, current, left)

    def moveTabRight(self):
        """
            Move current tab to the right, wrap around if needed
        """
        tabs = self.ui.tab_cover_art_providers
        current = tabs.currentIndex()
        if current != -1:
            if current < tabs.count() - 1:
                right = current + 1
            else:
                right = 0
            self.moveTab(tabs, current, right)

    def load(self):
        self.ui.save_images_to_tags.setChecked(config.setting["save_images_to_tags"])
        self.ui.cb_embed_front_only.setChecked(config.setting["save_only_front_images_to_tags"])
        self.ui.save_images_to_files.setChecked(config.setting["save_images_to_files"])
        self.ui.cover_image_filename.setText(config.setting["cover_image_filename"])
        self.ui.save_images_overwrite.setChecked(config.setting["save_images_overwrite"])
        self.update_filename()
        self.load_ca_providers()
        for func in self.provider_options['load']:
            func()

    def save(self):
        config.setting["save_images_to_tags"] = self.ui.save_images_to_tags.isChecked()
        config.setting["save_only_front_images_to_tags"] = self.ui.cb_embed_front_only.isChecked()
        config.setting["save_images_to_files"] = self.ui.save_images_to_files.isChecked()
        config.setting["cover_image_filename"] = unicode(self.ui.cover_image_filename.text())
        config.setting["save_images_overwrite"] = self.ui.save_images_overwrite.isChecked()
        for func in self.provider_options['save']:
            func()

    def update_filename(self):
        enabled = self.ui.save_images_to_files.isChecked()
        self.ui.cover_image_filename.setEnabled(enabled)
        self.ui.save_images_overwrite.setEnabled(enabled)


register_options_page(CoverOptionsPage)
