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

"""Tests for retry helper."""

from unittest.mock import (
    Mock,
    patch,
)

from picard.session.retry_helper import RetryHelper

import pytest


@patch("PyQt6.QtCore.QTimer.singleShot")
def test_retry_until_condition_met_immediately(mock_single_shot: Mock) -> None:
    """Test retry_until when condition is met immediately."""
    condition_called = False
    action_called = False

    def condition_fn() -> bool:
        nonlocal condition_called
        condition_called = True
        return True

    def action_fn() -> None:
        nonlocal action_called
        action_called = True

    RetryHelper.retry_until(condition_fn, action_fn)

    assert condition_called
    assert action_called
    mock_single_shot.assert_not_called()


@patch("PyQt6.QtCore.QTimer.singleShot")
def test_retry_until_condition_not_met(mock_single_shot: Mock) -> None:
    """Test retry_until when condition is not met."""

    def condition_fn() -> bool:
        return False

    def action_fn() -> None:
        pass

    RetryHelper.retry_until(condition_fn, action_fn)

    mock_single_shot.assert_called_once()


@patch("PyQt6.QtCore.QTimer.singleShot")
def test_retry_until_with_custom_delay(mock_single_shot: Mock) -> None:
    """Test retry_until with custom delay."""

    def condition_fn() -> bool:
        return False

    def action_fn() -> None:
        pass

    RetryHelper.retry_until(condition_fn, action_fn, delay_ms=500)

    mock_single_shot.assert_called_once_with(500, mock_single_shot.call_args[0][1])


@patch("PyQt6.QtCore.QTimer.singleShot")
def test_retry_until_with_max_attempts(mock_single_shot: Mock) -> None:
    """Test retry_until with maximum attempts limit."""
    attempt_count = 0

    def condition_fn() -> bool:
        nonlocal attempt_count
        attempt_count += 1
        return False

    def action_fn() -> None:
        pass

    # Mock the callback to simulate retries
    def mock_callback(delay, callback):
        callback()  # Simulate retry

    mock_single_shot.side_effect = mock_callback

    RetryHelper.retry_until(condition_fn, action_fn, max_attempts=3)

    # Should schedule retry for max_attempts times
    assert mock_single_shot.call_count == 3


@patch("PyQt6.QtCore.QTimer.singleShot")
def test_retry_until_condition_becomes_true_after_retries(mock_single_shot: Mock) -> None:
    """Test retry_until when condition becomes true after some retries."""
    call_count = 0

    def condition_fn() -> bool:
        nonlocal call_count
        call_count += 1
        return call_count >= 3  # True after 3 calls

    def action_fn() -> None:
        pass

    # Mock the callback to simulate retries
    def mock_callback(delay, callback):
        if call_count < 3:
            callback()  # Simulate retry

    mock_single_shot.side_effect = mock_callback

    RetryHelper.retry_until(condition_fn, action_fn)

    # Should have scheduled retries
    assert mock_single_shot.call_count > 0


def test_retry_until_condition_function_exception() -> None:
    """Test retry_until when condition function raises exception."""

    def condition_fn() -> bool:
        raise RuntimeError("Condition error")

    def action_fn() -> None:
        pass

    with pytest.raises(RuntimeError, match="Condition error"):
        RetryHelper.retry_until(condition_fn, action_fn)


def test_retry_until_action_function_exception() -> None:
    """Test retry_until when action function raises exception."""

    def condition_fn() -> bool:
        return True

    def action_fn() -> None:
        raise RuntimeError("Action error")

    with pytest.raises(RuntimeError, match="Action error"):
        RetryHelper.retry_until(condition_fn, action_fn)
