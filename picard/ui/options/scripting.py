# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2009 Lukáš Lalinský
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2009-2010, 2019-2021 Philipp Wolfer
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2013-2015, 2017-2020 Laurent Monin
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2016-2017 Suhas
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


from PyQt5 import QtCore

from picard.config import (
    BoolOption,
    IntOption,
    ListOption,
    Option,
    get_config,
)
from picard.const import PICARD_URLS
from picard.const.sys import IS_MACOS
from picard.script import (
    ScriptParser,
    script_function_documentation_all,
)
from picard.util import restore_method

from picard.ui import (
    FONT_FAMILY_MONOSPACE,
    PicardDialog,
    SingletonDialog,
)
from picard.ui.moveable_list_view import MoveableListView
from picard.ui.options import (
    OptionsCheckError,
    OptionsPage,
    register_options_page,
)
from picard.ui.theme import theme
from picard.ui.ui_options_script import Ui_ScriptingOptionsPage
from picard.ui.ui_scripting_documentation_dialog import (
    Ui_ScriptingDocumentationDialog,
)
from picard.ui.widgets.scriptlistwidget import ScriptListWidgetItem


class ScriptCheckError(OptionsCheckError):
    pass


DOCUMENTATION_HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
<style>
dt {
    color: %(script_function_fg)s
}
dd {
    /* Qt does not support margin-inline-start, use margin-left/margin-right instead */
    margin-%(inline_start)s: 50px;
    margin-bottom: 50px;
}
code {
    font-family: %(monospace_font)s;
}
</style>
</head>
<body dir="%(dir)s">
    %(html)s
</body>
</html>
'''


class ScriptingDocumentationDialog(PicardDialog, SingletonDialog):
    defaultsize = QtCore.QSize(570, 400)
    autorestore = False

    def __init__(self, parent):
        super().__init__(parent)
        # on macOS having this not a dialog causes the window to be placed
        # behind the options dialog.
        if not IS_MACOS:
            self.setWindowFlags(QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.parent = parent
        self.ui = Ui_ScriptingDocumentationDialog()
        self.ui.setupUi(self)
        self.restore_geometry()
        args = {
            "picard-doc-scripting-url": PICARD_URLS['doc_scripting'],
        }
        text = _('<a href="%(picard-doc-scripting-url)s">Open Scripting'
                 ' Documentation in your browser</a>') % args
        self.ui.scripting_doc_link.setText(text)

        def process_html(html, function):
            if not html:
                html = ''
            template = '<dt>%s%s</dt><dd>%s</dd>'
            if function.module is not None and function.module != 'picard.script.functions':
                module = ' [' + function.module + ']'
            else:
                module = ''
            try:
                firstline, remaining = html.split("\n", 1)
                return template % (firstline, module, remaining)
            except ValueError:
                return template % ("<code>$%s()</code>" % function.name, module, html)

        funcdoc = script_function_documentation_all(
            fmt='html',
            postprocessor=process_html,
        )

        if self.ui.textBrowser.layoutDirection() == QtCore.Qt.RightToLeft:
            text_direction = 'rtl'
        else:
            text_direction = 'ltr'

        html = DOCUMENTATION_HTML_TEMPLATE % {
            'html': "<dl>%s</dl>" % funcdoc,
            'script_function_fg': theme.syntax_theme.func.name(),
            'monospace_font': FONT_FAMILY_MONOSPACE,
            'dir': text_direction,
            'inline_start': 'right' if text_direction == 'rtl' else 'left'
        }
        # Scripting code is always left-to-right. Qt does not support the dir
        # attribute on inline tags, insert explicit left-right-marks instead.
        html = html.replace('<code>', '<code>&#8206;')
        self.ui.textBrowser.setHtml(html)
        self.ui.buttonBox.rejected.connect(self.close)

    def closeEvent(self, event):
        super().closeEvent(event)


class ScriptingOptionsPage(OptionsPage):

    NAME = "scripting"
    TITLE = N_("Scripting")
    PARENT = None
    SORT_ORDER = 85
    ACTIVE = True
    HELP_URL = '/config/options_scripting.html'

    options = [
        BoolOption("setting", "enable_tagger_scripts", False),
        ListOption("setting", "list_of_scripts", []),
        IntOption("persist", "last_selected_script_pos", 0),
        Option("persist", "scripting_splitter", QtCore.QByteArray()),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ScriptingOptionsPage()
        self.ui.setupUi(self)
        self.ui.tagger_script.setEnabled(False)
        self.ui.splitter.setStretchFactor(0, 1)
        self.ui.splitter.setStretchFactor(1, 2)
        self.move_view = MoveableListView(self.ui.script_list, self.ui.move_up_button,
                                          self.ui.move_down_button)
        self.ui.scripting_documentation_button.clicked.connect(self.show_scripting_documentation)

    def show_scripting_documentation(self):
        ScriptingDocumentationDialog.show_instance(parent=self)

    def enable_tagger_scripts_toggled(self, on):
        if on and self.ui.script_list.count() == 0:
            self.ui.script_list.add_script()

    def script_selected(self):
        items = self.ui.script_list.selectedItems()
        if items:
            item = items[0]
            self.ui.tagger_script.setEnabled(True)
            self.ui.tagger_script.setText(item.script)
            self.ui.tagger_script.setFocus(QtCore.Qt.OtherFocusReason)
        else:
            self.ui.tagger_script.setEnabled(False)
            self.ui.tagger_script.setText("")

    def live_update_and_check(self):
        items = self.ui.script_list.selectedItems()
        if items:
            script = items[0]
            script.script = self.ui.tagger_script.toPlainText()
        self.ui.script_error.setStyleSheet("")
        self.ui.script_error.setText("")
        try:
            self.check()
        except OptionsCheckError as e:
            self.ui.script_error.setStyleSheet(self.STYLESHEET_ERROR)
            self.ui.script_error.setText(e.info)
            return

    def check(self):
        parser = ScriptParser()
        try:
            parser.eval(self.ui.tagger_script.toPlainText())
        except Exception as e:
            raise ScriptCheckError(_("Script Error"), str(e))

    def restore_defaults(self):
        # Remove existing scripts
        self.ui.script_list.clear()
        self.ui.tagger_script.setText("")
        super().restore_defaults()

    def load(self):
        config = get_config()
        self.ui.enable_tagger_scripts.setChecked(config.setting["enable_tagger_scripts"])
        for pos, name, enabled, text in config.setting["list_of_scripts"]:
            list_item = ScriptListWidgetItem(name, enabled, text)
            self.ui.script_list.addItem(list_item)

        # Select the last selected script item
        last_selected_script_pos = config.persist["last_selected_script_pos"]
        last_selected_script = self.ui.script_list.item(last_selected_script_pos)
        if last_selected_script:
            self.ui.script_list.setCurrentItem(last_selected_script)
            last_selected_script.setSelected(True)

        self.restore_state()

    def _all_scripts(self):
        for row in range(0, self.ui.script_list.count()):
            item = self.ui.script_list.item(row)
            yield item.get_all()

    @restore_method
    def restore_state(self):
        # Preserve previous splitter position
        config = get_config()
        self.ui.splitter.restoreState(config.persist["scripting_splitter"])

    def save(self):
        config = get_config()
        config.setting["enable_tagger_scripts"] = self.ui.enable_tagger_scripts.isChecked()
        config.setting["list_of_scripts"] = list(self._all_scripts())
        config.persist["last_selected_script_pos"] = self.ui.script_list.currentRow()
        config.persist["scripting_splitter"] = self.ui.splitter.saveState()

    def display_error(self, error):
        # Ignore scripting errors, those are handled inline
        if not isinstance(error, ScriptCheckError):
            super().display_error(error)


register_options_page(ScriptingOptionsPage)
