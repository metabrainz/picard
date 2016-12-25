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
from picard.const import PICARD_URLS
from picard.script import ScriptParser
from picard.ui.options import OptionsPage, OptionsCheckError, register_options_page
from picard.ui.ui_options_script import Ui_ScriptingOptionsPage


class TaggerScriptSyntaxHighlighter(QtGui.QSyntaxHighlighter):

    def __init__(self, document):
        QtGui.QSyntaxHighlighter.__init__(self, document)
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

            if (next_index > -1):
                self.setFormat(index, next_index - index + 1, self.noop_fmt)
            elif (next_index == -1) and (open_brackets > 0):
                self.setFormat(index, len(text) - index, self.noop_fmt)

            # Check for next noop operation, necessary for multiple noops in one line
            if open_brackets == 0:
                next_index = self.noop_re.indexIn(text, next_index)

            index = next_index + 1 if (next_index > -1) and (next_index < len(text)) else -1

        self.setCurrentBlockState(open_brackets)


class ScriptItem:

    def __init__(self, position, title=None, state=True,text=""):
        self.pos = position
        if title is None:
            self.name = "My Script"
        else:
            self.name = title
        self.enabled = state
        self.text_item = text

    def get_all(self):
        tup = (self.pos, self.name, self.enabled, self.text_item)
        return tup

class ScriptingOptionsPage(OptionsPage):

    NAME = "scripting"
    TITLE = N_("Scripting")
    PARENT = "advanced"
    SORT_ORDER = 30
    ACTIVE = True

    options = [
        config.BoolOption("setting", "enable_tagger_script", False),
        config.TextOption("setting", "tagger_script", ""),
        config.ListOption("setting", "list_of_scripts", []),
    ]

    def __init__(self, parent=None):
        super(ScriptingOptionsPage, self).__init__(parent)
        self.ui = Ui_ScriptingOptionsPage()
        self.ui.setupUi(self)
        self.highlighter = TaggerScriptSyntaxHighlighter(self.ui.tagger_script.document())
        self.ui.tagger_script.textChanged.connect(self.live_update_and_check)
        self.ui.add_script.clicked.connect(self.add_to_lscript)
        self.ui.remove_script.clicked.connect(self.remove_from_lscript)
        self.ui.up_script.clicked.connect(self.move_script_up)
        self.ui.down_script.clicked.connect(self.move_script_down)
        self.ui.script_list.itemSelectionChanged.connect(self.script_selected)
        self.ui.script_list.itemChanged.connect(self.script_attr_changed)
        self.ui.tagger_script.setEnabled(False)

        self.listitem_to_scriptitem = {}
        self.list_of_scripts = []

    def script_attr_changed(self,item):
        item.setSelected(True)
        script = self.listitem_to_scriptitem[item]
        if item.checkState():
            script.enabled = True
        else:
            script.enabled = False
        script.name = item.text()
        self.list_of_scripts[script.pos] = script.get_all()

    def script_selected(self):
        items = self.ui.script_list.selectedItems()
        if items:
            self.ui.tagger_script.setEnabled(True)
            script = self.listitem_to_scriptitem[items[0]]
            self.ui.tagger_script.setText(script.text_item)

    def add_to_lscript(self):
        count = self.ui.script_list.count()
        script = ScriptItem(position=count, title="My Script "+str(count+1))
        list_item = QtGui.QListWidgetItem(script.name)
        list_item.setFlags(list_item.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable)
        list_item.setCheckState(QtCore.Qt.Checked)
        self.ui.script_list.addItem(list_item)
        self.listitem_to_scriptitem[list_item] = script
        self.list_of_scripts.append(script.get_all())

    def remove_from_lscript(self):
        item = self.ui.script_list.takeItem(self.ui.script_list.currentRow())
        if item:
            script = self.listitem_to_scriptitem[item]
            item = None
            del self.list_of_scripts[script.pos]
            del script
            if self.ui.script_list.count() == 0:
                self.ui.tagger_script.setText("")
                self.ui.tagger_script.setEnabled(False)

    def move_script_up(self):
        currentRow = self.ui.script_list.currentRow()
        item1 = self.ui.script_list.item(currentRow)
        if currentRow != 0:
            item2 = self.ui.script_list.item(currentRow-1)
        else:
            item2 = None
        if item1 and item2:
            # make changes in the ui
            item1 = self.ui.script_list.takeItem(currentRow)
            self.ui.script_list.insertItem(currentRow-1, item1)

            # make changes in the picklable list
            script1 = self.listitem_to_scriptitem[item1]
            script2 = self.listitem_to_scriptitem[item2]
            # workaround since tuples are immutable
            self.list_of_scripts[script1.pos] = (script1.pos-1, script1.name, script1.enabled, script1.text_item)
            self.list_of_scripts[script2.pos] = (script2.pos+1, script2.name, script2.enabled, script2.text_item)
            self.list_of_scripts = sorted(self.list_of_scripts,key=lambda x: x[0])
            for l in self.list_of_scripts:
                print l

    def move_script_down(self):
        currentRow = self.ui.script_list.currentRow()
        item1 = self.ui.script_list.takeItem(currentRow)
        if currentRow != self.ui.script_list.count():
            item2 = self.ui.script_list.item(currentRow+1)
        else:
            item2 = None
        if item1 and item2:
            # make changes in the ui
            self.ui.script_list.insertItem(currentRow+1, item1)

            # make changes in the picklable list
            script1 = self.listitem_to_scriptitem[item1]
            script2 = self.listitem_to_scriptitem[item2]
            # workaround since tuples are immutable
            self.list_of_scripts[script1.pos] = (script1.pos + 1, script1.name, script1.enabled, script1.text_item)
            self.list_of_scripts[script2.pos] = (script2.pos - 1, script2.name, script2.enabled, script2.text_item)
            self.list_of_scripts = sorted(self.list_of_scripts, key=lambda x: x[0])

    def live_update_and_check(self):
        items = self.ui.script_list.selectedItems()
        if items:
            script = self.listitem_to_scriptitem[items[0]]
            script.text_item = self.ui.tagger_script.toPlainText()
            self.list_of_scripts[script.pos] = script.get_all()
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
            parser.eval(unicode(self.ui.tagger_script.toPlainText()))
        except Exception as e:
            raise OptionsCheckError(_("Script Error"), str(e))

    def load(self):
        self.ui.enable_tagger_script.setChecked(config.setting["enable_tagger_script"])
        self.ui.tagger_script.document().setPlainText(config.setting["tagger_script"])
        self.list_of_scripts = config.setting["list_of_scripts"]
        for item in self.list_of_scripts:
            script = ScriptItem(item[0], item[1], item[2], item[3])
            script.list_item = QtGui.QListWidgetItem(script.name)
            script.list_item.setFlags(script.list_item.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable)
            script.list_item.setCheckState(QtCore.Qt.Checked if item[2] else QtCore.Qt.Unchecked)
            self.listitem_to_scriptitem[script.list_item] = script
            self.ui.script_list.addItem(script.list_item)

        args = {
            "picard-doc-scripting-url": PICARD_URLS['doc_scripting'],
        }
        text = _(u'<a href="%(picard-doc-scripting-url)s">Open Scripting'
                 ' Documentation in your browser</a>') % args
        self.ui.scripting_doc_link.setText(text)

    def save(self):
        config.setting["enable_tagger_script"] = self.ui.enable_tagger_script.isChecked()
        config.setting["tagger_script"] = self.ui.tagger_script.toPlainText()
        for l in self.list_of_scripts:
            print l
        config.setting["list_of_scripts"] = self.list_of_scripts

    def display_error(self, error):
        pass


register_options_page(ScriptingOptionsPage)
