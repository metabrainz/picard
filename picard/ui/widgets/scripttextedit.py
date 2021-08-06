# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2009 Lukáš Lalinský
# Copyright (C) 2014 m42i
# Copyright (C) 2020 Laurent Monin
# Copyright (C) 2020-2021 Philipp Wolfer
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


import re
import unicodedata

from PyQt5 import (
    QtCore,
    QtGui,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QCursor,
    QKeySequence,
    QTextCursor,
)
from PyQt5.QtWidgets import (
    QAction,
    QCompleter,
    QTextEdit,
    QToolTip,
)

from picard.config import (
    BoolOption,
    get_config,
)
from picard.const.sys import IS_MACOS
from picard.script import (
    ScriptFunctionDocError,
    script_function_documentation,
    script_function_names,
)
from picard.util.tags import (
    PRESERVED_TAGS,
    TAG_NAMES,
    display_tag_name,
)

from picard.ui import FONT_FAMILY_MONOSPACE
from picard.ui.theme import theme


EXTRA_VARIABLES = (
    '~absolutetracknumber',
    '~albumartists_sort',
    '~albumartists',
    '~artists_sort',
    '~datatrack',
    '~discpregap',
    '~multiartist',
    '~musicbrainz_discids',
    '~performance_attributes',
    '~pregap',
    '~primaryreleasetype',
    '~rating',
    '~recording_firstreleasedate',
    '~recordingcomment',
    '~recordingtitle',
    '~releasecomment',
    '~releasecountries',
    '~releasegroup_firstreleasedate',
    '~releasegroup',
    '~releasegroupcomment',
    '~releaselanguage',
    '~secondaryreleasetype',
    '~silence',
    '~totalalbumtracks',
    '~video',
)


class TaggerScriptSyntaxHighlighter(QtGui.QSyntaxHighlighter):

    def __init__(self, document):
        super().__init__(document)
        syntax_theme = theme.syntax_theme
        self.func_re = QtCore.QRegExp(r"\$(?!noop)[_a-zA-Z0-9]*\(")
        self.func_fmt = QtGui.QTextCharFormat()
        self.func_fmt.setFontWeight(QtGui.QFont.Bold)
        self.func_fmt.setForeground(syntax_theme.func)
        self.var_re = QtCore.QRegExp(r"%[_a-zA-Z0-9:]*%")
        self.var_fmt = QtGui.QTextCharFormat()
        self.var_fmt.setForeground(syntax_theme.var)
        self.unicode_re = QtCore.QRegExp(r"\\u[a-fA-F0-9]{4}")
        self.unicode_fmt = QtGui.QTextCharFormat()
        self.unicode_fmt.setForeground(syntax_theme.escape)
        self.escape_re = QtCore.QRegExp(r"\\[^u]")
        self.escape_fmt = QtGui.QTextCharFormat()
        self.escape_fmt.setForeground(syntax_theme.escape)
        self.special_re = QtCore.QRegExp(r"[^\\][(),]")
        self.special_fmt = QtGui.QTextCharFormat()
        self.special_fmt.setForeground(syntax_theme.special)
        self.bracket_re = QtCore.QRegExp(r"[()]")
        self.noop_re = QtCore.QRegExp(r"\$noop\(")
        self.noop_fmt = QtGui.QTextCharFormat()
        self.noop_fmt.setFontWeight(QtGui.QFont.Bold)
        self.noop_fmt.setFontItalic(True)
        self.noop_fmt.setForeground(syntax_theme.noop)
        self.rules = [
            (self.func_re, self.func_fmt, 0, -1),
            (self.var_re, self.var_fmt, 0, 0),
            (self.unicode_re, self.unicode_fmt, 0, 0),
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
        text_length = len(text)
        while index >= 0:
            next_index = self.bracket_re.indexIn(text, index)

            # Skip escaped brackets
            if next_index > 0 and text[next_index - 1] == '\\':
                next_index += 1

            # Reached end of text?
            if next_index >= text_length:
                self.setFormat(index, text_length - index, self.noop_fmt)
                break

            if next_index > -1 and text[next_index] == '(':
                open_brackets += 1
            elif next_index > -1 and text[next_index] == ')':
                open_brackets -= 1

            if next_index > -1:
                self.setFormat(index, next_index - index + 1, self.noop_fmt)
            elif next_index == -1 and open_brackets > 0:
                self.setFormat(index, text_length - index, self.noop_fmt)

            # Check for next noop operation, necessary for multiple noops in one line
            if open_brackets == 0:
                next_index = self.noop_re.indexIn(text, next_index)

            index = next_index + 1 if next_index > -1 and next_index < text_length else -1

        self.setCurrentBlockState(open_brackets)


class ScriptCompleter(QCompleter):
    def __init__(self, parent=None):
        super().__init__(sorted(self.choices), parent)
        self.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.highlighted.connect(self.set_highlighted)
        self.last_selected = ''

    @property
    def choices(self):
        yield from {'$' + name for name in script_function_names()}
        yield from {'%' + name.replace('~', '_') + '%' for name in self.all_tags}

    @property
    def all_tags(self):
        yield from TAG_NAMES.keys()
        yield from PRESERVED_TAGS
        yield from EXTRA_VARIABLES

    def set_highlighted(self, text):
        self.last_selected = text

    def get_selected(self):
        return self.last_selected


class DocumentedScriptToken:

    allowed_chars = re.compile('[A-Za-z0-9_]')

    def __init__(self, doc, cursor_position):
        self._doc = doc
        self._cursor_position = cursor_position

    def is_start_char(self, char):
        return False

    def is_allowed_char(self, char, position):
        return self.allowed_chars.match(char)

    def get_tooltip(self, position):
        return None

    def _read_text(self, position, count):
        text = ''
        while count:
            char = self._doc.characterAt(position)
            if not char:
                break
            text += char
            count -= 1
            position += 1
        return text

    def _read_allowed_chars(self, position):
        doc = self._doc
        text = ''
        while True:
            char = doc.characterAt(position)
            if not self.allowed_chars.match(char):
                break
            text += char
            position += 1
        return text


class FunctionScriptToken(DocumentedScriptToken):

    def is_start_char(self, char):
        return char == '$'

    def get_tooltip(self, position):
        if self._doc.characterAt(position) != '$':
            return None
        function = self._read_allowed_chars(position + 1)
        try:
            return script_function_documentation(function, 'html')
        except ScriptFunctionDocError:
            return None


class VariableScriptToken(DocumentedScriptToken):

    allowed_chars = re.compile('[A-Za-z0-9_:]')

    def is_start_char(self, char):
        return char == '%'

    def get_tooltip(self, position):
        if self._doc.characterAt(position) != '%':
            return None
        tag = self._read_allowed_chars(position + 1)
        return display_tag_name(tag)


class UnicodeEscapeScriptToken(DocumentedScriptToken):

    allowed_chars = re.compile('[uA-Fa-f0-9]')
    unicode_escape_sequence = re.compile('^\\\\u[a-fA-F0-9]{4}$')

    def is_start_char(self, char):
        return char == '\\'

    def is_allowed_char(self, char, position):
        return self.allowed_chars.match(char) and self._cursor_position - position < 6

    def get_tooltip(self, position):
        text = self._read_text(position, 6)
        if self.unicode_escape_sequence.match(text):
            codepoint = int(text[2:], 16)
            char = chr(codepoint)
            tooltip = unicodedata.name(char)
            if unicodedata.category(char)[0] != "C":
                tooltip += ': "%s"' % char
            return tooltip
        return None


def _clean_text(text):
    return "".join(_replace_control_chars(text))


def _replace_control_chars(text):
    simple_ctrl_chars = {'\n', '\r', '\t'}
    for ch in text:
        if ch not in simple_ctrl_chars and unicodedata.category(ch)[0] == "C":
            yield '\\u' + hex(ord(ch))[2:]
        else:
            yield ch


class ScriptTextEdit(QTextEdit):
    autocomplete_trigger_chars = re.compile('[$%A-Za-z0-9_]')

    options = [
        BoolOption('persist', 'script_editor_wordwrap', False),
        BoolOption('persist', 'script_editor_tooltips', True),
    ]

    def __init__(self, parent):
        super().__init__(parent)
        config = get_config()
        self.highlighter = TaggerScriptSyntaxHighlighter(self.document())
        self.enable_completer()
        self.setFontFamily(FONT_FAMILY_MONOSPACE)
        self.setMouseTracking(True)
        self.setAcceptRichText(False)
        self.wordwrap_action = QAction(_("&Word wrap script"), self)
        self.wordwrap_action.setToolTip(_("Word wrap long lines in the editor"))
        self.wordwrap_action.triggered.connect(self.update_wordwrap)
        self.wordwrap_action.setShortcut(QKeySequence(_("Ctrl+Shift+W")))
        self.wordwrap_action.setCheckable(True)
        self.wordwrap_action.setChecked(config.persist['script_editor_wordwrap'])
        self.update_wordwrap()
        self.addAction(self.wordwrap_action)
        self._show_tooltips = config.persist['script_editor_tooltips']
        self.show_tooltips_action = QAction(_("Show help &tooltips"), self)
        self.show_tooltips_action.setToolTip(_("Show tooltips for script elements"))
        self.show_tooltips_action.triggered.connect(self.update_show_tooltips)
        self.show_tooltips_action.setShortcut(QKeySequence(_("Ctrl+Shift+T")))
        self.show_tooltips_action.setCheckable(True)
        self.show_tooltips_action.setChecked(self._show_tooltips)
        self.addAction(self.show_tooltips_action)
        self.textChanged.connect(self.update_tooltip)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        menu.addAction(self.wordwrap_action)
        menu.addAction(self.show_tooltips_action)
        menu.exec_(event.globalPos())

    def mouseMoveEvent(self, event):
        if self._show_tooltips:
            tooltip = self.get_tooltip_at_mouse_position(event.pos())
            if not tooltip:
                QToolTip.hideText()
            self.setToolTip(tooltip)
        return super().mouseMoveEvent(event)

    def update_tooltip(self):
        if self.underMouse() and self.toolTip():
            position = self.mapFromGlobal(QCursor.pos())
            tooltip = self.get_tooltip_at_mouse_position(position)
            if tooltip != self.toolTip():
                # Hide tooltip if the entity causing this tooltip
                # was moved away from the mouse position
                QToolTip.hideText()
                self.setToolTip(tooltip)

    def get_tooltip_at_mouse_position(self, position):
        cursor = self.cursorForPosition(position)
        return self.get_tooltip_at_cursor(cursor)

    def get_tooltip_at_cursor(self, cursor):
        position = cursor.position()
        doc = self.document()
        documented_tokens = {
            FunctionScriptToken(doc, position),
            VariableScriptToken(doc, position),
            UnicodeEscapeScriptToken(doc, position)
        }
        while position and documented_tokens:
            char = doc.characterAt(position)
            for token in list(documented_tokens):
                if token.is_start_char(char):
                    return token.get_tooltip(position)
                elif not token.is_allowed_char(char, position):
                    documented_tokens.remove(token)
            position -= 1
        return None

    def insertFromMimeData(self, source):
        text = _clean_text(source.text())
        # Create a new data object, as modifying the existing one does not
        # work on Windows if copying from outside the Qt app.
        source = QtCore.QMimeData()
        source.setText(text)
        return super().insertFromMimeData(source)

    def setPlainText(self, text):
        super().setPlainText(text)
        self.update_wordwrap()

    def update_wordwrap(self):
        """Toggles wordwrap in the script editor
        """
        wordwrap = self.wordwrap_action.isChecked()
        config = get_config()
        config.persist['script_editor_wordwrap'] = wordwrap
        if wordwrap:
            self.setLineWrapMode(QTextEdit.WidgetWidth)
        else:
            self.setLineWrapMode(QTextEdit.NoWrap)

    def update_show_tooltips(self):
        """Toggles wordwrap in the script editor
        """
        self._show_tooltips = self.show_tooltips_action.isChecked()
        config = get_config()
        config.persist['script_editor_tooltips'] = self._show_tooltips
        if not self._show_tooltips:
            QToolTip.hideText()
            self.setToolTip('')

    def enable_completer(self):
        self.completer = ScriptCompleter()
        self.completer.setWidget(self)
        self.completer.activated.connect(self.insert_completion)
        self.popup_shown = False

    def insert_completion(self, completion):
        if not completion:
            return
        tc = self.cursor_select_word()
        if completion.startswith('$'):
            completion += '('
        tc.insertText(completion)
        # Peek at the next character to include it in the replacement
        if not tc.atEnd():
            pos = tc.position()
            tc = self.textCursor()
            tc.setPosition(pos + 1, QTextCursor.KeepAnchor)
            first_char = completion[0]
            next_char = tc.selectedText()
            if (first_char == '$' and next_char == '(') or (first_char == '%' and next_char == '%'):
                tc.removeSelectedText()
            else:
                tc.setPosition(pos)  # Reset position
        self.setTextCursor(tc)
        self.popup_hide()

    def popup_hide(self):
        self.completer.popup().hide()

    def cursor_select_word(self, full_word=True):
        tc = self.textCursor()
        current_position = tc.position()
        tc.select(QTextCursor.WordUnderCursor)
        selected_text = tc.selectedText()
        # Check for start of function or end of variable
        if current_position > 0 and selected_text and selected_text[0] in ('(', '%'):
            current_position -= 1
            tc.setPosition(current_position)
            tc.select(QTextCursor.WordUnderCursor)
            selected_text = tc.selectedText()
        start = tc.selectionStart()
        end = tc.selectionEnd()
        if current_position < start or current_position > end:
            # If the cursor is between words WordUnderCursor will select the
            # previous word. Reset the selection if the new selection is
            # outside the old cursor position.
            tc.setPosition(current_position)
            selected_text = tc.selectedText()
        if not selected_text.startswith('$') and not selected_text.startswith('%'):
            # Update selection to include the character before the
            # selected word to include the $ or %.
            tc.setPosition(start - 1 if start > 0 else 0)
            tc.setPosition(end, QTextCursor.KeepAnchor)
            selected_text = tc.selectedText()
            # No match, reset position (otherwise we could replace an additional character)
            if not selected_text.startswith('$') and not selected_text.startswith('%'):
                tc.setPosition(start)
                tc.setPosition(end, QTextCursor.KeepAnchor)
        if not full_word:
            tc.setPosition(current_position, QTextCursor.KeepAnchor)
        return tc

    def keyPressEvent(self, event):
        if self.completer.popup().isVisible():
            if event.key() in (Qt.Key_Tab, Qt.Key_Return, Qt.Key_Enter):
                self.completer.activated.emit(self.completer.get_selected())
                return

        super().keyPressEvent(event)
        self.handle_autocomplete(event)

    def handle_autocomplete(self, event):
        # Only trigger autocomplete on actual text input or if the user explicitly
        # requested auto completion with Ctrl+Space (Control+Space on macOS)
        modifier = QtCore.Qt.MetaModifier if IS_MACOS else QtCore.Qt.ControlModifier
        force_completion_popup = event.key() == QtCore.Qt.Key_Space and event.modifiers() & modifier
        if not (force_completion_popup
                or event.key() in (Qt.Key_Backspace, Qt.Key_Delete)
                or self.autocomplete_trigger_chars.match(event.text())):
            self.popup_hide()
            return

        tc = self.cursor_select_word(full_word=False)
        selected_text = tc.selectedText()
        if force_completion_popup or (selected_text and selected_text[0] in ('$', '%')):
            self.completer.setCompletionPrefix(selected_text)
            popup = self.completer.popup()
            popup.setCurrentIndex(self.completer.currentIndex())

            cr = self.cursorRect()
            cr.setWidth(
                popup.sizeHintForColumn(0)
                + popup.verticalScrollBar().sizeHint().width()
            )
            self.completer.complete(cr)
        else:
            self.popup_hide()
