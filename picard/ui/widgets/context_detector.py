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

"""Context detector for script completion."""

from enum import Enum
from typing import TypedDict


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


class CompletionMode(Enum):
    """Completion mode for the completer."""

    DEFAULT = "default"
    FUNCTION_NAME = "function_name"
    VARIABLE = "variable"
    TAG_NAME_ARG = "tag_name_arg"


class CompletionContext(TypedDict, total=False):
    """Completion context for the completer.

    Keys
    ----
    mode : CompletionMode
        The completion mode
    function_name : str
        For TAG_NAME_ARG mode, the function name (e.g. "set")
    arg_index : int
        For TAG_NAME_ARG mode, the zero-basedargument index (e.g. 0 for the first argument)
    """

    mode: CompletionMode
    function_name: str
    arg_index: int


class ContextDetector:
    """Detects completion context from cursor position.

    This class handles the detection of what type of completion should be shown
    based on the text to the left of the cursor position.
    """

    def detect_context(self, left_text: str) -> CompletionMode:
        """Detect completion context from cursor position.

        Parameters
        ----------
        left_text : str
            The text to the left of the cursor position

        Returns
        -------
        CompletionMode
            The detected completion mode
        """
        details = self.detect_context_details(left_text)
        return details['mode']

    def detect_context_details(self, left_text: str) -> CompletionContext:
        """Detect completion context details from cursor position.

        Parameters
        ----------
        left_text : str
            The text to the left of the cursor position
        """
        if self._is_function_context(left_text):
            return {'mode': CompletionMode.FUNCTION_NAME}
        if self._is_variable_context(left_text):
            return {'mode': CompletionMode.VARIABLE}
        tag_context = self._find_tag_arg_context(left_text)
        if tag_context is not None:
            return tag_context
        return {'mode': CompletionMode.DEFAULT}

    def _is_function_context(self, left_text: str) -> bool:
        """Check if cursor is in a function name context."""
        stripped = left_text.rstrip()
        # Accept any trailing '$' (including '$$') as a function context
        if stripped.endswith('$'):
            return True
        return self._is_partial_function_context(left_text)

    def _is_variable_context(self, left_text: str) -> bool:
        """Check if cursor is in a variable context."""
        # Handle the %% edge cases first
        stripped = left_text.rstrip()
        if not stripped.endswith('%'):
            # If it doesn't end with %, check for partial variable context
            return self._is_partial_variable_context(left_text)

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

        # Handle normal cases
        return (
            left_text.endswith('%')
            or (left_text.endswith(' ') and left_text.rstrip().endswith('%'))
            or self._is_partial_variable_context(left_text)
        )

    def _is_tag_arg_context(self, left_text: str) -> bool:
        """Check if cursor is in a tag name argument context."""
        return self._find_tag_arg_context(left_text) is not None

    def _is_partial_tag_arg(self, left_text: str, func_name: str) -> bool:
        """Check if cursor is in a partial tag name argument."""
        # Pattern: $func_name(variable_name (without closing parenthesis)
        pattern = f'${func_name}('
        if pattern in left_text:
            # Find the last occurrence and check if we're inside the first argument
            last_func_pos = left_text.rfind(pattern)
            if last_func_pos != -1:
                after_func = left_text[last_func_pos + len(pattern) :]
                # Check if we're in the first argument (no comma yet) and not closed
                if ',' not in after_func and not after_func.endswith(')'):
                    # Additional validation: ensure we don't have invalid syntax like double parentheses
                    # If the text immediately after the function is just another (, it's invalid syntax
                    if after_func == '(':
                        return False
                    return True
        return False

    def _find_tag_arg_context(self, left_text: str) -> CompletionContext | None:
        """Find a tag-name argument context and return details.

        Returns
        -------
        CompletionContext | None
            Context with mode TAG_NAME_ARG and details when inside first agument; otherwise None.
        """
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
