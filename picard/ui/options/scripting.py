# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2009 Lukáš Lalinský
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2009-2010, 2019-2020 Philipp Wolfer
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2013-2015, 2017-2020 Laurent Monin
# Copyright (C) 2014 m42i
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


from PyQt5 import (
    QtCore,
    QtGui,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (
    QCompleter,
    QTextEdit,
)

from picard import config
from picard.const import PICARD_URLS
from picard.script import (
    ScriptParser,
    script_function_documentation_all,
    script_function_names,
)
from picard.util import restore_method

from picard.ui import PicardDialog
from picard.ui.colors import interface_colors
from picard.ui.moveable_list_view import MoveableListView
from picard.ui.options import (
    OptionsCheckError,
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_script import Ui_ScriptingOptionsPage
from picard.ui.ui_scripting_documentation_dialog import (
    Ui_ScriptingDocumentationDialog,
)
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


DOCUMENTATION_HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
<style>
dt {
    font-family: monospace;
    /* font-weight: bold; */
    color: %(script_function_fg)s
}
dd {
    padding: 50px;
    margin-bottom: 50px;
}
p {
    font-family: serif;
}
code {
    font-family: sans-serif;
}
</style>
</head>
<body>
    %(html)s
</body>
</html>
'''


class ScriptingDocumentationDialog(PicardDialog):
    defaultsize = QtCore.QSize(570, 400)

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.parent = parent
        self.parent.scripting_documentation_shown = True
        self.setWindowFlags(QtCore.Qt.Window)
        self.ui = Ui_ScriptingDocumentationDialog()
        self.ui.setupUi(self)
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
            if function.module is not None and function.module != 'picard.script':
                module = ' [' + function.module + ']'
            else:
                module = ''
            try:
                firstline, remaining = html.split("\n", 1)
                return template % (firstline, module, remaining)
            except ValueError:
                return template % ("$%s()" % function.name, module, html)

        funcdoc = script_function_documentation_all(
            fmt='html',
            preprocessor=process_html,
        )
        enclosed_by = ('<dl>', '</dl>')

        color_fg = interface_colors.get_color('script_function_fg')
        html = DOCUMENTATION_HTML_TEMPLATE % {
            'html': "%s%s%s" % (enclosed_by[0], funcdoc, enclosed_by[1]),
            'script_function_fg': color_fg,
        }
        self.ui.textBrowser.setHtml(html)
        self.ui.buttonBox.rejected.connect(self.close)

    def closeEvent(self, event):
        self.parent.scripting_documentation_shown = False
        super().closeEvent(event)


class ScriptCompleter(QCompleter):
    insertText = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        choices = list(['$' + name for name in script_function_names()])
        super().__init__(choices, parent)
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.highlighted.connect(self.set_highlighted)
        self.last_selected = ''

    def set_highlighted(self, text):
        self.last_selected = text

    def get_selected(self):
        return self.last_selected


class ScriptTextEdit(QTextEdit):

    def enable_completer(self):
        self.completer = ScriptCompleter()
        self.completer.setWidget(self)
        self.completer.insertText.connect(self.insert_completion)
        self.popup_shown = False

    def insert_completion(self, completion):
        tc = self.cursor_select_word()
        tc.insertText(completion)
        self.setTextCursor(tc)
        self.popup_hide()

    def focusInEvent(self, event):
        if self.completer:
            self.completer.setWidget(self)
        super().focusInEvent(event)

    def popup_hide(self):
        self.completer.popup().hide()

    def cursor_select_word(self):
        tc = self.textCursor()
        current_position = tc.position()
        tc.select(QTextCursor.WordUnderCursor)
        selected_text = tc.selectedText()
        start = tc.selectionStart()
        end = tc.selectionEnd()
        if current_position < start or current_position > end:
            # If the cursor is between words WordUnderCursor will select the
            # previous word. Reset the selection if the new selection is
            # outside the old cursor position.
            tc.setPosition(current_position)
        elif not selected_text.startswith('$') and not selected_text.startswith('%'):
            # Update selection to include the character before the
            # selected word to include the $ or %.
            tc.setPosition(start - 1 if start > 0 else 0)
            tc.setPosition(end, QTextCursor.KeepAnchor)
        return tc

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab and self.completer.popup().isVisible():
            self.completer.insertText.emit(self.completer.get_selected())
            return

        super().keyPressEvent(event)

        tc = self.cursor_select_word()
        selected_text = tc.selectedText()
        if selected_text:
            self.completer.setCompletionPrefix(selected_text)
            popup = self.completer.popup()
            popup.setCurrentIndex(self.completer.completionModel().index(0, 0))

            cr = self.cursorRect()
            cr.setWidth(
                popup.sizeHintForColumn(0)
                + popup.verticalScrollBar().sizeHint().width()
            )
            self.completer.complete(cr)
        else:
            self.popup_hide()


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
        self.ui.tagger_script.__class__ = ScriptTextEdit  # hacky
        self.ui.tagger_script.enable_completer()
        self.highlighter = TaggerScriptSyntaxHighlighter(self.ui.tagger_script.document())
        self.ui.tagger_script.setEnabled(False)
        self.ui.splitter.setStretchFactor(0, 1)
        self.ui.splitter.setStretchFactor(1, 2)
        font = QtGui.QFont('Monospace')
        font.setStyleHint(QtGui.QFont.TypeWriter)
        self.ui.tagger_script.setFont(font)
        self.move_view = MoveableListView(self.ui.script_list, self.ui.move_up_button,
                                          self.ui.move_down_button)
        self.ui.scripting_documentation_button.clicked.connect(self.show_scripting_documentation)
        self.scripting_documentation_shown = None

    def show_scripting_documentation(self):
        if not self.scripting_documentation_shown:
            self.scriptdoc_dialog = ScriptingDocumentationDialog(parent=self)
            self.scriptdoc_dialog.show()
        else:
            self.scriptdoc_dialog.raise_()
            self.scriptdoc_dialog.activateWindow()

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
