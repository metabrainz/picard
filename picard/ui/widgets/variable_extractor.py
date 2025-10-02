# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
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

"""Variable extractor for script completion."""

import contextlib
import re

from picard.script.parser import (
    ScriptError,
    ScriptExpression,
    ScriptFunction,
    ScriptText,
)


# Pre-compiled regex for better performance in UI context
_SET_VARIABLE_PATTERN = re.compile(r"\$set\(\s*([A-Za-z0-9_\u00C0-\u017F\u4E00-\u9FFF]+)\s*,")


class VariableExtractor:
    """Extracts variable names from script content using multiple strategies.

    This class handles the extraction of user-defined variables from script content
    using three different approaches: full parsing, line-by-line parsing, and regex fallback.
    """

    def __init__(self, parser):
        """Initialize the variable extractor with a script parser.

        Parameters
        ----------
        parser : ScriptParser
            The script parser to use for AST-based extraction
        """
        self._parser = parser

    def extract_variables(self, script_content: str) -> set[str]:
        """Extract variables using multiple strategies.

        Strategy (robust and readable):
        1) Full parse for accuracy: handles nested and cross-line constructs.
        2) Per-line parse for resilience during live edits (one bad line won't block another).
        3) Regex fallback: If user is currently typing an incomplete token
           (e.g. a lone '%' after a valid `$set(...)`), parsing that line fails.
           A lightweight pattern still lets us extract static names.

        Results are deduplicated via set union.

        Parameters
        ----------
        script_content : str
            The script content to extract variables from

        Returns
        -------
        set[str]
            Set of variable names found in the script content
        """
        from_full = self._collect_from_full_parse(script_content)
        from_line = self._collect_from_line_parse(script_content)
        from_regex = self._collect_from_regex(script_content)
        return from_full | from_line | from_regex

    def _collect_from_full_parse(self, script_content: str) -> set[str]:
        """Collect variable names from a full parse of the script content."""
        names: set[str] = set()
        with contextlib.suppress(ScriptError):
            expression = self._parser.parse(script_content)
            self._collect_from_ast(expression, names)
        return names

    def _collect_from_line_parse(self, script_content: str) -> set[str]:
        """Collect variable names from a per-line parse of the script content."""
        names: set[str] = set()
        for line in script_content.splitlines():
            if not line:
                continue
            with contextlib.suppress(ScriptError):
                expression = self._parser.parse(line)
                self._collect_from_ast(expression, names)
        return names

    def _collect_from_regex(self, script_content: str) -> set[str]:
        """Collect variable names from a regex pattern of the script content."""
        return {m.group(1) for m in _SET_VARIABLE_PATTERN.finditer(script_content)}

    def _collect_from_ast(self, node: ScriptExpression | ScriptFunction | ScriptText, out: set[str]):
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
                self._collect_from_ast(arg, out)
            return
        if isinstance(node, ScriptExpression):
            for item in node:
                self._collect_from_ast(item, out)

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
