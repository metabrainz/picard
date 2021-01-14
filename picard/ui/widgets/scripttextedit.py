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

from picard.script import script_function_names
from picard.util.tags import (
    PRESERVED_TAGS,
    TAG_NAMES,
)

from picard.ui import FONT_FAMILY_MONOSPACE
from picard.ui.theme import theme


EXTRA_VARIABLES = [
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
]


class TaggerScriptSyntaxHighlighter(QtGui.QSyntaxHighlighter):

    def __init__(self, document):
        super().__init__(document)
        syntax_theme = theme.syntax_theme
        self.func_re = QtCore.QRegExp(r"\$(?!noop)[a-zA-Z][_a-zA-Z0-9]*\(")
        self.func_fmt = QtGui.QTextCharFormat()
        self.func_fmt.setFontWeight(QtGui.QFont.Bold)
        self.func_fmt.setForeground(syntax_theme.func)
        self.var_re = QtCore.QRegExp(r"%[_a-zA-Z0-9:]*%")
        self.var_fmt = QtGui.QTextCharFormat()
        self.var_fmt.setForeground(syntax_theme.var)
        self.escape_re = QtCore.QRegExp(r"\\.")
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
        choices = ['$' + name for name in script_function_names()]
        choices += self.all_tags
        super().__init__(choices, parent)
        self.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.highlighted.connect(self.set_highlighted)
        self.last_selected = ''

    @property
    def all_tags(self):
        tags = list(TAG_NAMES.keys()) + list(PRESERVED_TAGS) + EXTRA_VARIABLES
        return ['%' + name.replace('~', '_') + '%' for name in tags]

    def set_highlighted(self, text):
        self.last_selected = text

    def get_selected(self):
        return self.last_selected


class ScriptTextEdit(QTextEdit):
    autocomplete_trigger_chars = re.compile('[$%A-Za-z0-9_]')

    def __init__(self, parent):
        super().__init__(parent)
        self.highlighter = TaggerScriptSyntaxHighlighter(self.document())
        self.enable_completer()
        self.setFontFamily(FONT_FAMILY_MONOSPACE)

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
        pos = tc.position()
        # Peek at the next character to include it in the replacement
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
        if not full_word:
            tc.setPosition(current_position, QTextCursor.KeepAnchor)
        selected_text = tc.selectedText()
        # Check for start of function or end of variable
        if selected_text and selected_text[0] in ('(', '%'):
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
        # requested auto completion with Ctrl+Space
        force_completion_popup = event.key() == QtCore.Qt.Key_Space and event.modifiers() & QtCore.Qt.ControlModifier
        if not (force_completion_popup
                or event.key() in (Qt.Key_Backspace, Qt.Key_Delete)
                or self.autocomplete_trigger_chars.match(event.text())):
            self.popup_hide()
            return

        tc = self.cursor_select_word(full_word=True)
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
