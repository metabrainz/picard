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
from enum import Enum
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
from picard.extension_points.script_variables import get_plugin_variable_names
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


class CompletionMode(Enum):
    """Completion mode for the completer."""

    DEFAULT = "default"
    FUNCTION_NAME = "function_name"
    VARIABLE = "variable"
    TAG_NAME_ARG = "tag_name_arg"


# Functions whose first argument is a tag / variable name.
# Used to enable tag-name completion inside the first parameter position.
TAG_NAME_FIRST_ARG_FUNCTIONS = {
    "set",
    "get",
    "unset",
    "getunset",
    "delete",
    "setmulti",
    "copy",
    "copymerge",
}


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

        # Context-aware variable parsing
        self._last_script: str = ""
        self._var_usage_counts: dict[str, int] = {}
        self._context: dict | None = None

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

        # Keep track of last script and variable usage counts for context-awareness
        self._last_script = script_content
        self._var_usage_counts = self._count_variable_usage(script_content)

        # Refresh the completion model contents using the persistent model
        # (avoids replacing the model object and preserves any connections/state).
        with contextlib.suppress(RuntimeError, TypeError, AttributeError, ValueError):
            self._model.setStringList(list(self.choices))

    def _set_context(self, context: dict | None):
        """Set the current completion context (e.g. inside $set(first, ...))"""
        self._context = context
        # Update the model immediately to reflect context-sensitive choices
        with contextlib.suppress(RuntimeError, TypeError, AttributeError, ValueError):
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
        context: dict[str, CompletionMode] = self._context or {}
        mode: CompletionMode = context.get('mode', CompletionMode.DEFAULT)
        builtin_vars = set(script_variable_tag_names())
        plugin_vars = get_plugin_variable_names()
        user_vars = set(v for v in self._user_defined_variables if v not in builtin_vars and v not in plugin_vars)

        if mode == CompletionMode.TAG_NAME_ARG and context.get('arg_index', 0) == 0:
            # Suggest bare tag names for functions expecting a tag name as first argument.
            # Order by usage count (descending), then alphabetically.
            candidates = list(builtin_vars | user_vars | plugin_vars)
            candidates.sort(key=lambda x: (-self._var_usage_counts.get(x, 0), x))
            for name in candidates:
                yield name
            return

        # Default: functions then variables, variables ranked by usage count
        if mode in (CompletionMode.DEFAULT, CompletionMode.FUNCTION_NAME):
            for name in sorted(script_function_names()):
                yield f'${name}'
        if mode in (CompletionMode.DEFAULT, CompletionMode.VARIABLE):
            ranked_vars = list(builtin_vars | user_vars | plugin_vars)
            ranked_vars.sort(key=lambda x: (-self._var_usage_counts.get(x, 0), x))
            for name in ranked_vars:
                yield f'%{name}%'

    def set_highlighted(self, text):
        self.last_selected = text

    def get_selected(self):
        return self.last_selected

    def _count_variable_usage(self, script_content: str) -> dict[str, int]:
        """Count variable usages in the script content."""
        counts: dict[str, int] = {}
        for m in re.finditer(r'%([A-Za-z0-9_:]+)%', script_content):
            name = m.group(1)
            counts[name] = counts.get(name, 0) + 1
        # Also cout references via `$get(name)`
        for m in re.finditer(r'\$get\(\s*([A-Za-z0-9_]+)\s*\)', script_content):
            name = m.group(1)
            counts[name] = counts.get(name, 0) + 1
        return counts


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
    autocomplete_trigger_chars = re.compile('[$%A-Za-z0-9_(]')

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

        # If we just inserted a function completion, trigger tag name context
        if completion.startswith('$') and completion.endswith('('):
            # Check if this is a tag-name function
            function_name = completion[1:-1]  # Remove $ and (
            if function_name in TAG_NAME_FIRST_ARG_FUNCTIONS:
                # Update completion context to show tag names
                self._update_completion_context(self.textCursor())
                # Show completion popup
                self.completer.setCompletionPrefix('')
                popup = self.completer.popup()
                popup.setCurrentIndex(self.completer.currentIndex())
                cr = self.cursorRect()
                cr.setWidth(popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width())
                self.completer.complete(cr)
                return  # Don't hide popup, we just showed a new one

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

        # Always call _update_completion_context for trigger characters, even if no selected text
        # This allows context detection for characters like '(' that don't select text
        should_update_context = (
            force_completion_popup
            or (selected_text and selected_text[0] in {'$', '%'})
            or event.text() in {'(', '$', '%'}
        )

        # Also update context if we're already in a tag name argument context
        # This ensures we continue showing completions when typing in the first argument
        if not should_update_context:
            doc_text = self.toPlainText()
            cursor_pos = self.textCursor().position()
            left_text = doc_text[:cursor_pos]
            if self._detect_tag_name_arg_context(left_text) is not None:
                should_update_context = True

        if should_update_context:
            # Update context for smarter suggestions.
            # Get a fresh cursor to ensure we have the correct position after character insertion
            fresh_cursor = self.textCursor()
            self._update_completion_context(fresh_cursor)

            # Check if we should show the popup based on current context
            if self._should_show_completion_popup():
                # For tag-name function context, use empty prefix to show all tag names
                # Only do this if we're actually in a tag name argument context (inside function call)
                doc_text = self.toPlainText()
                cursor_pos = fresh_cursor.position()
                left_text = doc_text[:cursor_pos]
                tag_context = self._detect_tag_name_arg_context(left_text)
                if tag_context is not None:
                    if selected_text:
                        self.completer.setCompletionPrefix(selected_text)
                    else:
                        self.completer.setCompletionPrefix('')
                else:
                    self.completer.setCompletionPrefix(selected_text)

                popup = self.completer.popup()
                popup.setCurrentIndex(self.completer.currentIndex())

                cr = self.cursorRect()
                cr.setWidth(popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width())
                self.completer.complete(cr)
            else:
                self.popup_hide()
        else:
            self.popup_hide()

    def _update_completion_context(self, text_cursor: QTextCursor) -> None:
        """Infer completion context based on cursor for smarter completions.ArithmeticError

        Flow:
        1. Function name context (typing right after '$' but not '$$')
        2. Variable context (typing right after '%' but not '%%')
        3. Tag name argument context (inside first arg of known functions)
        4. Default context
        """
        doc_text = self.toPlainText()
        cursor_pos = text_cursor.position()
        left_text = doc_text[:cursor_pos]

        # 1. Function name context
        if self._is_function_name_context(left_text):
            self.completer._set_context({'mode': CompletionMode.FUNCTION_NAME})
            return

        # 2. Variable context
        if self._is_variable_context(left_text):
            self.completer._set_context({'mode': CompletionMode.VARIABLE})
            return

        # 3. Tag name argument context (inside function call)
        tag_arg_context = self._detect_tag_name_arg_context(left_text)
        if tag_arg_context is not None:
            self.completer._set_context(tag_arg_context)
            return

        # 4. After tag-name function context (for tab completion only)
        # This is handled separately in insert_completion method

        # 5. Default context
        self.completer._set_context({'mode': CompletionMode.DEFAULT})

    def _is_function_name_context(self, left_text: str) -> bool:
        """Return true if cursor is immediately after '$' starting a function."""
        return left_text.endswith('$') and not left_text.endswith('$$')

    def _is_variable_context(self, left_text: str) -> bool:
        """Return true if cursor is immediately after '%' starting a variable."""
        stripped = left_text.rstrip()
        if not stripped.endswith('%'):
            return False

        # If it ends with %%, we need to check if it's a literal %% or a new variable
        if stripped.endswith('%%'):
            # If the text is exactly '%%', it's a literal double %
            if stripped == '%%':
                return False
            # If we have something like %foo%%, it's a new variable starting
            # Check if there's a complete variable before the %%
            before_last_percent = stripped[:-1]  # Remove the last %
            if before_last_percent.endswith('%'):
                # We have %foo%%, so this is a new variable
                return True
            # If it's just %% at the end, it's a literal double %
            return False

        return True

    def _is_partial_variable_context(self, left_text: str) -> bool:
        """Return true if cursor is in a partial variable name context (like %f, %fo, etc.)."""
        # Find the last % in the text
        last_percent = left_text.rfind('%')
        if last_percent == -1:
            return False

        # Extract the part after the last %
        variable_part = left_text[last_percent + 1 :]

        # Check if it's a valid partial variable name (alphanumeric/underscore characters)
        if variable_part and all(c.isalnum() or c == '_' for c in variable_part):
            return True

        return False

    def _is_after_tag_name_function(self) -> bool:
        """Return true if cursor is immediately after a tag-name function (for tab completion)."""
        doc_text = self.toPlainText()
        cursor_pos = self.textCursor().position()
        left_text = doc_text[:cursor_pos]

        # Check if we're immediately after a known tag-name function
        # This should only be true when we've just completed a function via tab completion
        # and are about to start typing the first argument
        for function_name in TAG_NAME_FIRST_ARG_FUNCTIONS:
            if left_text.endswith(f'${function_name}'):
                return True
        return False

    def _is_partial_function_context(self, left_text: str) -> bool:
        """Return true if cursor is in a partial function name context (like $s, $se, etc.)."""
        # Find the last $ in the text
        last_dollar = left_text.rfind('$')
        if last_dollar == -1:
            return False

        # Extract the part after the last $
        function_part = left_text[last_dollar + 1 :]

        # Check if it's a valid partial function name (alphanumeric/underscore characters)
        if function_part and all(c.isalnum() or c == '_' for c in function_part):
            return True

        return False

    def _should_show_completion_popup(self) -> bool:
        """Return true if the current context warrants showing the completion popup."""
        doc_text = self.toPlainText()
        cursor_pos = self.textCursor().position()
        left_text = doc_text[:cursor_pos]

        # Show popup for function name context (typing after $)
        if self._is_function_name_context(left_text):
            return True

        # Show popup for variable context (typing after %)
        if self._is_variable_context(left_text):
            return True

        # Show popup for partial variable context (typing variable name)
        if self._is_partial_variable_context(left_text):
            return True

        # Show popup for tag name argument context (inside function call)
        tag_context = self._detect_tag_name_arg_context(left_text)
        if tag_context is not None:
            return True

        # Show popup for partial function names (like $s, $se, etc.)
        if self._is_partial_function_context(left_text):
            return True

        # Don't show popup for default context or other cases
        return False

    def _detect_tag_name_arg_context(self, left_text: str) -> dict[str, object] | None:
        """Detect being inside first arg of a known tag-name function and return context."""
        # Find all $ positions and their corresponding ( positions
        dollar_positions = []
        for i, char in enumerate(left_text):
            if char == '$':
                dollar_positions.append(i)

        # Check each $ position from most recent to oldest
        for dollar_pos in reversed(dollar_positions):
            # Find the next ( after this $
            paren_pos = left_text.find('(', dollar_pos)
            if paren_pos == -1:
                continue

            # Extract function name between '$' and '('
            function_name = ''.join(ch for ch in left_text[dollar_pos + 1 : paren_pos] if ch.isalnum() or ch == "_")

            # Only consider this function if it's a known tag-name function
            if function_name not in TAG_NAME_FIRST_ARG_FUNCTIONS:
                continue

            # Check for invalid syntax: if there's another '(' immediately after the function call,
            # this is invalid (like $set(( or $get(( )
            if paren_pos + 1 < len(left_text) and left_text[paren_pos + 1] == '(':
                continue

            # Determine argument index by counting commas between '(' and end of text
            arg_segment = left_text[paren_pos + 1 :]
            arg_index = arg_segment.count(',')

            # If we're in the first argument (no commas), return the context
            if arg_index == 0:
                return {'mode': CompletionMode.TAG_NAME_ARG, 'function_name': function_name, 'arg_index': arg_index}

        return None
