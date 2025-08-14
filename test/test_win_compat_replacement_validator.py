# -*- coding: utf-8 -*-

from __future__ import annotations

import re

from PyQt6 import QtGui

import pytest

from picard.ui.options.renaming_compat import WinCompatReplacementValidator as NewValidator


class OldValidator(QtGui.QValidator):
    """Pre-change validator behavior (BEFORE).

    Accepts only zero-length or a single non-illegal, non-whitespace character.
    """

    _re_valid_win_replacement = re.compile(r'^[^"*:<>?|/\\\s]?$')

    def validate(self, text: str, pos: int):
        if self._re_valid_win_replacement.match(text):
            state = QtGui.QValidator.State.Acceptable
        else:
            state = QtGui.QValidator.State.Invalid
        return state, text, pos


@pytest.fixture
def validators() -> tuple:
    """Provide instances of the BEFORE and AFTER validators.

    Returns (old_validator, new_validator).
    """
    return OldValidator(), NewValidator()


def _is_acceptable(validator: QtGui.QValidator, text: str) -> bool:
    state, _text, _pos = validator.validate(text, 0)
    return state == QtGui.QValidator.State.Acceptable


@pytest.mark.parametrize(
    "text",
    [
        "",  # empty
        "_",  # underscore
        "a",  # any single allowed character
        "-",  # dash
    ],
)
def test_accepts_all_inputs_previously_accepted(text: str, validators: tuple) -> None:
    old_validator, new_validator = validators
    assert _is_acceptable(old_validator, text) is True
    # New behavior should be a superset of old acceptable inputs
    assert _is_acceptable(new_validator, text) is True


@pytest.mark.parametrize(
    "text",
    [
        '"',
        "*",
        ":",
        "<",
        ">",
        "?",
        "|",
        "/",
        "\\",
    ],
)
def test_rejects_windows_illegal_characters_consistently(text: str, validators: tuple) -> None:
    old_validator, new_validator = validators
    assert _is_acceptable(old_validator, text) is False
    assert _is_acceptable(new_validator, text) is False


@pytest.mark.parametrize(
    "text",
    [
        " - ",  # spaces around dash
        "foo",  # multi-character word
        "__",  # multi-character underscores
        "  ",  # spaces only
        "a b",  # spaces inside are fine now
    ],
)
def test_now_allows_multi_character_and_whitespace(text: str, validators: tuple) -> None:
    old_validator, new_validator = validators
    # Previously invalid due to length>1 and/or whitespace
    assert _is_acceptable(old_validator, text) is False
    # Now acceptable as long as no illegal characters are present
    assert _is_acceptable(new_validator, text) is True


@pytest.mark.parametrize(
    "text",
    [
        "a/b",
        "a\\b",
        "/ ",
        " \\",
    ],
)
def test_still_rejects_any_string_containing_dir_separators(text: str, validators: tuple) -> None:
    old_validator, new_validator = validators
    assert _is_acceptable(old_validator, text) is False
    assert _is_acceptable(new_validator, text) is False


@pytest.mark.parametrize(
    "text",
    [
        "abcd",  # > 3 chars
        "foo ",  # > 3 with trailing space
        " -  ",  # > 3 spaces and dash
    ],
)
def test_validator_allows_more_than_three_characters(text: str, validators: tuple) -> None:
    _old, new_validator = validators
    # Old never allowed >1, so no need to assert
    assert _is_acceptable(new_validator, text) is True


@pytest.mark.parametrize(
    "text",
    [
        'a"b',
        "a*b",
        "a:b",
        "a<b",
        "a>b",
        "a?b",
        "a|b",
        " pre/post ",
    ],
)
def test_rejects_when_forbidden_character_is_anywhere_in_string(text: str, validators: tuple) -> None:
    _old, new_validator = validators
    assert _is_acceptable(new_validator, text) is False


@pytest.mark.parametrize(
    "text",
    [
        " ",
        "\t",  # tab
        " \t ",
    ],
)
def test_allows_whitespace_only_strings(text: str, validators: tuple) -> None:
    _old, new_validator = validators
    assert _is_acceptable(new_validator, text) is True


@pytest.mark.parametrize("text", ["", "_", " - ", "foo"])
@pytest.mark.parametrize("pos", [0, 1, 2])
def test_position_passthrough(text: str, pos: int, validators: tuple) -> None:
    _old, new_validator = validators
    state, out_text, out_pos = new_validator.validate(text, pos)
    assert out_text == text
    assert out_pos == pos
    assert (state == QtGui.QValidator.State.Acceptable) == _is_acceptable(new_validator, text)
