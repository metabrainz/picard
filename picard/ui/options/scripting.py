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
from picard.config import BoolOption, TextOption
from picard.script import ScriptParser
from picard.ui.options import OptionsPage, OptionsCheckError, register_options_page
from picard.ui.ui_options_script import Ui_ScriptingOptionsPage


class TaggerScriptSyntaxHighlighter(QtGui.QSyntaxHighlighter):

    def __init__(self, document):
        QtGui.QSyntaxHighlighter.__init__(self, document)
        self.func_re = QtCore.QRegExp(r"\$[a-zA-Z][_a-zA-Z0-9]*\(")
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
        self.rules = [
            (self.func_re, self.func_fmt, 0, -1),
            (self.var_re, self.var_fmt, 0, 0),
            (self.escape_re, self.escape_fmt, 0, 0),
            (self.special_re, self.special_fmt, 1, -1),
        ]

    def highlightBlock(self, text):
        for expr, fmt, a, b in self.rules:
            index = expr.indexIn(text)
            while index >= 0:
                length = expr.matchedLength()
                self.setFormat(index + a, length + b, fmt)
                index = expr.indexIn(text, index + length + b)


class ScriptingOptionsPage(OptionsPage):

    NAME = "scripting"
    TITLE = N_("Scripting")
    PARENT = "advanced"
    SORT_ORDER = 30
    ACTIVE = True

    options = [
        BoolOption("setting", "enable_tagger_script", False),
        TextOption("setting", "tagger_script", ""),
    ]

    STYLESHEET_ERROR = "QWidget { background-color: #f55; color: white; font-weight:bold }"

    def __init__(self, parent=None):
        super(ScriptingOptionsPage, self).__init__(parent)
        self.ui = Ui_ScriptingOptionsPage()
        self.ui.setupUi(self)
        self.highlighter = TaggerScriptSyntaxHighlighter(self.ui.tagger_script.document())
        self.ui.tagger_script.textChanged.connect(self.live_checker)

    def live_checker(self):
        self.ui.script_error.setStyleSheet("");
        self.ui.script_error.setText("")
        try:
            self.check()
        except OptionsCheckError, e:
            self.ui.script_error.setStyleSheet(self.STYLESHEET_ERROR);
            self.ui.script_error.setText(e.info)
            return

    def check(self):
        parser = ScriptParser()
        try:
            parser.eval(unicode(self.ui.tagger_script.toPlainText()))
        except Exception, e:
            raise OptionsCheckError(_("Script Error"), str(e))

    def load(self):
        self.ui.enable_tagger_script.setChecked(self.config.setting["enable_tagger_script"])
        self.ui.tagger_script.document().setPlainText(self.config.setting["tagger_script"])

    def save(self):
        self.config.setting["enable_tagger_script"] = self.ui.enable_tagger_script.isChecked()
        self.config.setting["tagger_script"] = self.ui.tagger_script.toPlainText()

    def display_error(self, error):
        pass


register_options_page(ScriptingOptionsPage)
