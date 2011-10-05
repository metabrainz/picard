# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
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
from picard.config import BoolOption, TextOption
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_interface import Ui_InterfaceOptionsPage
from picard.const import UI_LANGUAGES
import operator
import locale


class InterfaceOptionsPage(OptionsPage):

    NAME = "interface"
    TITLE = N_("User Interface")
    PARENT = "advanced"
    SORT_ORDER = 40
    ACTIVE = True

    options = [
        BoolOption("setting", "toolbar_show_labels", True),
        BoolOption("setting", "toolbar_multiselect", False),
        BoolOption("setting", "use_adv_search_syntax", False),
        BoolOption("setting", "quit_confirmation", True),
        TextOption("setting", "ui_language", u""),
    ]

    def __init__(self, parent=None):
        super(InterfaceOptionsPage, self).__init__(parent)
        self.ui = Ui_InterfaceOptionsPage()
        self.ui.setupUi(self)
        self.ui.ui_language.addItem(_('System default'), QtCore.QVariant(''))
        language_list = [(l[0], l[1], _(l[2])) for l in UI_LANGUAGES]
        for lang_code, native, translation in sorted(language_list, key=operator.itemgetter(2),
                                                      cmp=locale.strcoll):
            if native and native != translation:
                name = u'%s (%s)' % (translation, native)
            else:
                name = translation
            self.ui.ui_language.addItem(name, QtCore.QVariant(lang_code))

    def load(self):
        self.ui.toolbar_show_labels.setChecked(self.config.setting["toolbar_show_labels"])
        self.ui.toolbar_multiselect.setChecked(self.config.setting["toolbar_multiselect"])
        self.ui.use_adv_search_syntax.setChecked(self.config.setting["use_adv_search_syntax"])
        self.ui.quit_confirmation.setChecked(self.config.setting["quit_confirmation"])
        current_ui_language = QtCore.QVariant(self.config.setting["ui_language"])
        self.ui.ui_language.setCurrentIndex(self.ui.ui_language.findData(current_ui_language))

    def save(self):
        self.config.setting["toolbar_show_labels"] = self.ui.toolbar_show_labels.isChecked()
        self.config.setting["toolbar_multiselect"] = self.ui.toolbar_multiselect.isChecked()
        self.config.setting["use_adv_search_syntax"] = self.ui.use_adv_search_syntax.isChecked()
        self.config.setting["quit_confirmation"] = self.ui.quit_confirmation.isChecked()
        self.tagger.window.update_toolbar_style()
        new_language = self.ui.ui_language.itemData(self.ui.ui_language.currentIndex()).toString()
        if new_language != self.config.setting["ui_language"]:
            self.config.setting["ui_language"] = self.ui.ui_language.itemData(self.ui.ui_language.currentIndex()).toString()
            dialog = QtGui.QMessageBox(QtGui.QMessageBox.Information, _('Language changed'), _('You have changed the interface language. You have to restart Picard in order for the change to take effect.'), QtGui.QMessageBox.Ok, self)
            dialog.exec_()


register_options_page(InterfaceOptionsPage)
