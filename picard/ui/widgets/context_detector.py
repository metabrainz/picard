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


class ContextDetector:
    """Detects completion context from cursor position.

    This class handles the detection of what type of completion should be shown
    based on the text to the left of the cursor position.
    """

    def __init__(self):
        """Initialize the context detector."""
        pass

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
        if self._is_function_context(left_text):
            return CompletionMode.FUNCTION_NAME
        elif self._is_variable_context(left_text):
            return CompletionMode.VARIABLE
        elif self._is_tag_arg_context(left_text):
            return CompletionMode.TAG_NAME_ARG
        return CompletionMode.DEFAULT

    def _is_function_context(self, left_text: str) -> bool:
        """Check if cursor is in a function name context."""
        return (
            left_text.endswith('$')
            or (left_text.endswith(' ') and left_text.rstrip().endswith('$'))
            or (left_text.endswith('$') and not left_text.endswith('$$'))
            or self._is_partial_function_context(left_text)
        )

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
        # Look for function calls that expect tag names as first argument
        for func_name in TAG_NAME_FIRST_ARG_FUNCTIONS:
            # Pattern: $func_name( or $func_name(variable_name
            if left_text.endswith(f'${func_name}(') or self._is_partial_tag_arg(left_text, func_name):
                return True
        return False

    def _is_partial_tag_arg(self, left_text: str, func_name: str) -> bool:
        """Check if cursor is in a partial tag name argument."""
        # Pattern: $func_name(variable_name (without closing parenthesis)
        pattern = f'${func_name}('
        if pattern in left_text:
            # Find the last occurrence and check if we're inside the first argument
            last_func_pos = left_text.rfind(pattern)
            if last_func_pos != -1:
                after_func = left_text[last_func_pos + len(pattern) :]
                # Check if we're in the first argument (no comma yet)
                if ',' not in after_func and not after_func.endswith(')'):
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
