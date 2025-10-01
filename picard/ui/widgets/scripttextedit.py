# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2009 Lukáš Lalinský
# Copyright (C) 2014 m42i
# Copyright (C) 2020-2024 Laurent Monin
# Copyright (C) 2020-2024 Philipp Wolfer
# Copyright (C) 2021-2022, 2025 Bob Swift
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


import contextlib
import re
import unicodedata

from PyQt6 import (
    QtCore,
    QtGui,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QAction,
    QCursor,
    QKeySequence,
    QTextCursor,
)
from PyQt6.QtWidgets import (
    QCompleter,
    QTextEdit,
    QToolTip,
)

from picard.config import get_config
from picard.const.sys import IS_MACOS
from picard.i18n import gettext as _
from picard.script import (
    ScriptFunctionDocError,
    ScriptFunctionDocUnknownFunctionError,
    script_function_documentation,
    script_function_names,
)
from picard.script.parser import (
    ScriptError,
    ScriptExpression,
    ScriptFunction,
    ScriptParser,
    ScriptText,
)
from picard.tags import (
    display_tag_tooltip,
    script_variable_tag_names,
)

from picard.ui import FONT_FAMILY_MONOSPACE
from picard.ui.colors import interface_colors


def find_regex_index(regex, text, start=0):
    m = regex.search(text[start:])
    if m:
        return start + m.start()
    else:
        return -1


class HighlightRule:
    def __init__(self, fmtname, regex, start_offset=0, end_offset=0):
        self.fmtname = fmtname
        self.regex = re.compile(regex)
        self.start_offset = start_offset
        self.end_offset = end_offset


class HighlightFormat(QtGui.QTextCharFormat):
    def __init__(self, fg_color=None, italic=False, bold=False):
        super().__init__()
        if fg_color is not None:
            self.setForeground(interface_colors.get_qcolor(fg_color))
        if italic:
            self.setFontItalic(True)
        if bold:
            self.setFontWeight(QtGui.QFont.Weight.Bold)


class TaggerScriptSyntaxHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.textcharformats = {
            'escape': HighlightFormat(fg_color='syntax_hl_escape'),
            'func': HighlightFormat(fg_color='syntax_hl_func', bold=True),
            'noop': HighlightFormat(fg_color='syntax_hl_noop', bold=True, italic=True),
            'special': HighlightFormat(fg_color='syntax_hl_special'),
            'unicode': HighlightFormat(fg_color='syntax_hl_unicode'),
            'unknown_func': HighlightFormat(fg_color='syntax_hl_error', italic=True),
            'var': HighlightFormat(fg_color='syntax_hl_var'),
        }

        self.rules = list(self.func_rules())
        self.rules.extend(
            (
                HighlightRule('unknown_func', r"\$(?!noop)[_a-zA-Z0-9]*\(", end_offset=-1),
                HighlightRule('var', r"%[_a-zA-Z0-9:]*%"),
                HighlightRule('unicode', r"\\u[a-fA-F0-9]{4}"),
                HighlightRule('escape', r"\\[^u]"),
                HighlightRule('special', r"(?<!\\)[(),]"),
            )
        )

    def func_rules(self):
        for func_name in script_function_names():
            if func_name != 'noop':
                pattern = re.escape("$" + func_name + "(")
                yield HighlightRule('func', pattern, end_offset=-1)

    def highlightBlock(self, text):
        self.setCurrentBlockState(0)

        already_matched = set()
        for rule in self.rules:
            for m in rule.regex.finditer(text):
                index = m.start() + rule.start_offset
                length = m.end() - m.start() + rule.end_offset
                if (index, length) not in already_matched:
                    already_matched.add((index, length))
                    fmt = self.textcharformats[rule.fmtname]
                    self.setFormat(index, length, fmt)

        noop_re = re.compile(r"\$noop\(")
        noop_fmt = self.textcharformats['noop']

        # Ignore everything if we're already in a noop function
        index = find_regex_index(noop_re, text) if self.previousBlockState() <= 0 else 0
        open_brackets = self.previousBlockState() if self.previousBlockState() > 0 else 0
        text_length = len(text)
        bracket_re = re.compile(r"[()]")
        while index >= 0:
            next_index = find_regex_index(bracket_re, text, index)

            # Skip escaped brackets
            if next_index > 0 and text[next_index - 1] == '\\':
                next_index += 1

            # Reached end of text?
            if next_index >= text_length:
                self.setFormat(index, text_length - index, noop_fmt)
                break

            if next_index > -1 and text[next_index] == '(':
                open_brackets += 1
            elif next_index > -1 and text[next_index] == ')':
                open_brackets -= 1

            if next_index > -1:
                self.setFormat(index, next_index - index + 1, noop_fmt)
            elif next_index == -1 and open_brackets > 0:
                self.setFormat(index, text_length - index, noop_fmt)

            # Check for next noop operation, necessary for multiple noops in one line
            if open_brackets == 0:
                next_index = find_regex_index(noop_re, text, next_index)

            index = next_index + 1 if next_index > -1 and next_index < text_length else -1

        self.setCurrentBlockState(open_brackets)


class ScriptCompleter(QCompleter):
    def __init__(self, parent=None):
        # Initialize internal state before constructing QCompleter to avoid
        # accessing properties that depend on initialized attributes.
        self.last_selected = ''
        self._parser = ScriptParser()
        self._script_hash: int | None = None
        self._user_defined_variables: set[str] = set()

        # Construct base QCompleter with parent only; we'll set the model explicitly later.
        super().__init__(parent)

        # Persistent model for dynamic completions.
        # QCompleter caches its model; we update this single instance as the script changes
        # to ensure new user-defined variables appear without recreating the model object.
        self._model: QtCore.QStringListModel = QtCore.QStringListModel()
        self.setModel(self._model)
        self.highlighted.connect(self.set_highlighted)

        # Initialize the model with initial choices
        self._model.setStringList(list(self.choices))

    def update_dynamic_variables(self, script_content: str, force: bool = False):
        """Update dynamic variables from the current script content.

        Caches by script hash to avoid unnecessary re-parsing.
        """
        script_hash = hash(script_content)
        if not force and script_hash == self._script_hash:
            return
        self._script_hash = script_hash
        self._user_defined_variables = self._extract_set_variables(script_content)

        # Refresh the completion model contents using the persistent model
        # (avoids replacing the model object and preserves any connections/state).
        with contextlib.suppress(Exception):
            # If model update fails, continue without updating the model
            # This ensures the completer remains functional even if the model has issues
            self._model.setStringList(list(self.choices))

    def _extract_set_variables(self, script_content: str):
        """Return a set of variable names assigned via `$set(name, ...)`.

        Strategy (robus and readable):
        1) Full parse for accuracy: handles nested and cross-line constructs.
        2) Per-line parse for resilience during live edits (one bad line won't block another).
        3) Regex fallback: If user is currently typing an incomplete token
           (e.g. a lone '%' after a valid `$set(...)`), parsing that line fails.
           A lightweight pattern still lets us extract static names.

        Results are deduplicated via set union.
        """
        from_full = self._collect_set_variables_from_full_parse(script_content)
        from_line = self._collect_set_variables_from_line_parse(script_content)
        from_regex = self._collect_set_variables_from_regex(script_content)
        return from_full | from_line | from_regex

    def _collect_set_variables_from_full_parse(self, script_content: str) -> set[str]:
        """Collect variable names from a full parse of the script content."""
        names: set[str] = set()
        with contextlib.suppress(ScriptError):
            expression = self._parser.parse(script_content)
            self._collect_set_variables_from_ast(expression, names)
        return names

    def _collect_set_variables_from_line_parse(self, script_content: str) -> set[str]:
        """Collect variable names from a per-line parse of the script content."""
        names: set[str] = set()
        for line in script_content.splitlines():
            if not line:
                continue
            with contextlib.suppress(ScriptError):
                expression = self._parser.parse(line)
                self._collect_set_variables_from_ast(expression, names)
        return names

    def _collect_set_variables_from_regex(self, script_content: str) -> set[str]:
        """Collect variable names from a regex pattern of the script content."""
        return {
            m.group(1) for m in re.finditer(r"\$set\(\s*([A-Za-z0-9_\u00C0-\u017F\u4E00-\u9FFF]+)\s*,", script_content)
        }

    def _collect_set_variables_from_ast(self, node: ScriptExpression | ScriptFunction | ScriptText, out: set[str]):
        """Traverse the AST and collect variable names from `$set(name, ...)` expressions.

        Accepts names composed only of ScriptText tokens to avoid positives
        such as `$set($if(...), ...)`.
        """
        if isinstance(node, ScriptFunction):
            if node.name == "set" and node.args:
                static_name = self._extract_static_name(node.args[0])
                if static_name:
                    out.add(static_name)
            for arg in node.args:
                self._collect_set_variables_from_ast(arg, out)
            return
        if isinstance(node, ScriptExpression):
            for item in node:
                self._collect_set_variables_from_ast(item, out)

    def _extract_static_name(self, node: ScriptExpression | ScriptText) -> str | None:
        """Extract a static name from a node.

        Accepts names composed only of ScriptText tokens to avoid positives
        such as `$set($if(...), ...)`.
        """
        if not isinstance(node, ScriptExpression):
            return None
        if not all(isinstance(item, ScriptText) for item in node):
            return None
        value = "".join(str(token) for token in node).strip()
        return value or None

    @property
    def choices(self):
        yield from sorted(f'${name}' for name in script_function_names())

        # Keep a list of built-inn varibles because we're introducing user-defined variables.
        builtin_variables = set(script_variable_tag_names())
        for name in sorted(builtin_variables):
            yield f'%{name}%'

        # User-defined variables from `$set(name, ...)`
        for user_variable in sorted(v for v in self._user_defined_variables if v not in builtin_variables):
            yield f'%{user_variable}%'

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
        except ScriptFunctionDocUnknownFunctionError:
            return _('<em>Function <code>$%s</code> does not exist.<br><br>Are you missing a plugin?</em>') % function
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
        return display_tag_tooltip(tag)


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
            try:
                tooltip = unicodedata.name(char)
            except ValueError:
                tooltip = f'U+{text[2:].upper()}'
            if unicodedata.category(char)[0] != "C":
                tooltip += f': "{char}"'
            return tooltip
        return None


def _clean_text(text):
    return "".join(_replace_control_chars(text))


def _replace_control_chars(text):
    simple_ctrl_chars = {'\n', '\r', '\t'}
    for ch in text:
        if ch not in simple_ctrl_chars and unicodedata.category(ch)[0] == "C":
            yield '\\u' + hex(ord(ch))[2:].rjust(4, '0')
        else:
            yield ch


class ScriptTextEdit(QTextEdit):
    autocomplete_trigger_chars = re.compile('[$%A-Za-z0-9_]')

    def __init__(self, parent):
        super().__init__(parent)
        config = get_config()
        self.highlighter = TaggerScriptSyntaxHighlighter(self.document())
        self.initialize_completer()

        # Initialize dynamic variables from current (possibly empty) script content.
        self.completer.update_dynamic_variables(self.toPlainText())

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
        self.textChanged.connect(self._on_text_changed)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        menu.addAction(self.wordwrap_action)
        menu.addAction(self.show_tooltips_action)
        menu.exec(event.globalPos())

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

    def _on_text_changed(self):
        # Update completer dynamic variables cache
        self.completer.update_dynamic_variables(self.toPlainText())
        # Update tooltips after parsing to avoid timing issues
        self.update_tooltip()

    def get_tooltip_at_mouse_position(self, position):
        cursor = self.cursorForPosition(position)
        return self.get_tooltip_at_cursor(cursor)

    def get_tooltip_at_cursor(self, cursor):
        position = cursor.position()
        doc = self.document()
        documented_tokens = {
            FunctionScriptToken(doc, position),
            VariableScriptToken(doc, position),
            UnicodeEscapeScriptToken(doc, position),
        }
        while position >= 0 and documented_tokens:
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
        """Toggles wordwrap in the script editor"""
        wordwrap = self.wordwrap_action.isChecked()
        config = get_config()
        config.persist['script_editor_wordwrap'] = wordwrap
        if wordwrap:
            self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        else:
            self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

    def update_show_tooltips(self):
        """Toggles wordwrap in the script editor"""
        self._show_tooltips = self.show_tooltips_action.isChecked()
        config = get_config()
        config.persist['script_editor_tooltips'] = self._show_tooltips
        if not self._show_tooltips:
            QToolTip.hideText()
            self.setToolTip('')

    def initialize_completer(self):
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
            tc.setPosition(pos + 1, QTextCursor.MoveMode.KeepAnchor)
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
        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        selected_text = tc.selectedText()
        # Check for start of function or end of variable
        if current_position > 0 and selected_text and selected_text[0] in {'(', '%'}:
            current_position -= 1
            tc.setPosition(current_position)
            tc.select(QTextCursor.SelectionType.WordUnderCursor)
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
            tc.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            selected_text = tc.selectedText()
            # No match, reset position (otherwise we could replace an additional character)
            if not selected_text.startswith('$') and not selected_text.startswith('%'):
                tc.setPosition(start)
                tc.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        if not full_word:
            tc.setPosition(current_position, QTextCursor.MoveMode.KeepAnchor)
        return tc

    def keyPressEvent(self, event):
        if self.completer.popup().isVisible():
            if event.key() in {Qt.Key.Key_Tab, Qt.Key.Key_Return, Qt.Key.Key_Enter}:
                self.completer.activated.emit(self.completer.get_selected())
                return

        super().keyPressEvent(event)
        self.handle_autocomplete(event)

    def handle_autocomplete(self, event):
        # Only trigger autocomplete on actual text input or if the user explicitly
        # requested auto completion with Ctrl+Space (Control+Space on macOS)
        modifier = QtCore.Qt.KeyboardModifier.MetaModifier if IS_MACOS else QtCore.Qt.KeyboardModifier.ControlModifier
        force_completion_popup = event.key() == QtCore.Qt.Key.Key_Space and event.modifiers() & modifier
        if not (
            force_completion_popup
            or event.key() in {Qt.Key.Key_Backspace, Qt.Key.Key_Delete}
            or self.autocomplete_trigger_chars.match(event.text())
        ):
            self.popup_hide()
            return

        tc = self.cursor_select_word(full_word=False)
        selected_text = tc.selectedText()
        if force_completion_popup or (selected_text and selected_text[0] in {'$', '%'}):
            self.completer.setCompletionPrefix(selected_text)
            popup = self.completer.popup()
            popup.setCurrentIndex(self.completer.currentIndex())

            cr = self.cursorRect()
            cr.setWidth(popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width())
            self.completer.complete(cr)
        else:
            self.popup_hide()
