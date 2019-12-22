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

from PyQt5 import (
    QtCore,
    QtGui,
)

from picard import config
from picard.const import PICARD_URLS
from picard.script import ScriptParser
from picard.util import restore_method

from picard.ui.moveable_list_view import MoveableListView
from picard.ui.options import (
    OptionsCheckError,
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_script import Ui_ScriptingOptionsPage
from picard.ui.widgets.scriptlistwidget import ScriptListWidgetItem


class ScriptCheckError(OptionsCheckError):
    pass


class TaggerScriptSyntaxHighlighter(QtGui.QSyntaxHighlighter):

    def __init__(self, document):
        super().__init__(document)
        self.func_re = QtCore.QRegExp(r"\$(?!noop)[a-zA-Z][_a-zA-Z0-9]*\(")
        self.func_fmt = QtGui.QTextCharFormat()
        self.func_fmt.setFontWeight(QtGui.QFont.Bold)
        self.func_fmt.setForeground(QtCore.Qt.blue)
        self.var_re = QtCore.QRegExp(r"%[_a-zA-Z0-9:]*%")
        self.var_fmt = QtGui.QTextCharFormat()
        self.var_fmt.setForeground(QtCore.Qt.darkCyan)
        self.escape_re = QtCore.QRegExp(r"\\.")
        self.escape_fmt = QtGui.QTextCharFormat()
        self.escape_fmt.setForeground(QtCore.Qt.darkRed)
        self.special_re = QtCore.QRegExp(r"[^\\][(),]")
        self.special_fmt = QtGui.QTextCharFormat()
        self.special_fmt.setForeground(QtCore.Qt.blue)
        self.bracket_re = QtCore.QRegExp(r"[()]")
        self.noop_re = QtCore.QRegExp(r"\$noop\(")
        self.noop_fmt = QtGui.QTextCharFormat()
        self.noop_fmt.setFontWeight(QtGui.QFont.Bold)
        self.noop_fmt.setFontItalic(True)
        self.noop_fmt.setForeground(QtCore.Qt.darkGray)
        self.rules = [
            (self.func_re, self.func_fmt, 0, -1),
            (self.var_re, self.var_fmt, 0, 0),
            (self.escape_re, self.escape_fmt, 0, 0),
            (self.special_re, self.special_fmt, 1, -1),
        ]

    def highlightBlock(self, text):
        self.setCurrentBlockState(0)

        for expr, fmt, a, b in self.rules:
            index = expr.indexIn(text)
            while index >= 0:
                length = expr.matchedLength()
                self.setFormat(index + a, length + b, fmt)
                index = expr.indexIn(text, index + length + b)

        # Ignore everything if we're already in a noop function
        index = self.noop_re.indexIn(text) if self.previousBlockState() <= 0 else 0
        open_brackets = self.previousBlockState() if self.previousBlockState() > 0 else 0
        while index >= 0:
            next_index = self.bracket_re.indexIn(text, index)

            # Skip escaped brackets
            if (next_index > 0) and text[next_index - 1] == '\\':
                next_index += 1

            if (next_index > -1) and text[next_index] == '(':
                open_brackets += 1
            elif (next_index > -1) and text[next_index] == ')':
                open_brackets -= 1

            if next_index > -1:
                self.setFormat(index, next_index - index + 1, self.noop_fmt)
            elif (next_index == -1) and (open_brackets > 0):
                self.setFormat(index, len(text) - index, self.noop_fmt)

            # Check for next noop operation, necessary for multiple noops in one line
            if open_brackets == 0:
                next_index = self.noop_re.indexIn(text, next_index)

            index = next_index + 1 if (next_index > -1) and (next_index < len(text)) else -1

        self.setCurrentBlockState(open_brackets)


class ScriptingOptionsPage(OptionsPage):

    NAME = "scripting"
    TITLE = N_("Scripting")
    PARENT = None
    SORT_ORDER = 85
    ACTIVE = True

    options = [
        config.BoolOption("setting", "enable_tagger_scripts", False),
        config.ListOption("setting", "list_of_scripts", []),
        config.IntOption("persist", "last_selected_script_pos", 0),
        config.Option("persist", "scripting_splitter", QtCore.QByteArray()),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ScriptingOptionsPage()
        self.ui.setupUi(self)
        self.highlighter = TaggerScriptSyntaxHighlighter(self.ui.tagger_script.document())
        self.ui.tagger_script.setEnabled(False)
        self.ui.splitter.setStretchFactor(0, 1)
        self.ui.splitter.setStretchFactor(1, 2)
        font = QtGui.QFont('Monospace')
        font.setStyleHint(QtGui.QFont.TypeWriter)
        self.ui.tagger_script.setFont(font)
        self.move_view = MoveableListView(self.ui.script_list, self.ui.move_up_button,
                                          self.ui.move_down_button)

    def script_selected(self):
        items = self.ui.script_list.selectedItems()
        if items:
            item = items[0]
            self.ui.tagger_script.setEnabled(True)
            self.ui.tagger_script.setText(item.script)
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

        args = {
            "picard-doc-scripting-url": PICARD_URLS['doc_scripting'],
        }
        text = _('<a href="%(picard-doc-scripting-url)s">Open Scripting'
                 ' Documentation in your browser</a>') % args
        self.ui.scripting_doc_link.setText(text)

    def _all_scripts(self):
        for row in range(0, self.ui.script_list.count()):
            item = self.ui.script_list.item(row)
            yield item.get_all()

    @restore_method
    def restore_state(self):
        # Preserve previous splitter position
        self.ui.splitter.restoreState(config.persist["scripting_splitter"])

    def save(self):
        config.setting["enable_tagger_scripts"] = self.ui.enable_tagger_scripts.isChecked()
        config.setting["list_of_scripts"] = list(self._all_scripts())
        config.persist["last_selected_script_pos"] = self.ui.script_list.currentRow()
        config.persist["scripting_splitter"] = self.ui.splitter.saveState()

    def display_error(self, error):
        # Ignore scripting errors, those are handled inline
        if not isinstance(error, ScriptCheckError):
            super().display_error(error)


register_options_page(ScriptingOptionsPage)
