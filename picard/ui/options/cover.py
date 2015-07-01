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
            options_widget = None
            if hasattr(provider, 'OPTIONS') and callable(provider.OPTIONS):
                options_widget = provider.OPTIONS(self)
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
