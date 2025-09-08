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

"""Tests for session constants."""

from picard.session.constants import SessionConstants

import pytest


def test_session_constants_values() -> None:
    """Test that SessionConstants has expected values."""
    assert SessionConstants.SESSION_FILE_EXTENSION == ".mbps.gz"
    assert SessionConstants.SESSION_FORMAT_VERSION == 1
    assert SessionConstants.DEFAULT_RETRY_DELAY_MS == 200
    assert SessionConstants.FAST_RETRY_DELAY_MS == 150
    assert SessionConstants.INTERNAL_TAG_PREFIX == "~"
    assert frozenset({"length", "~length"}) == SessionConstants.EXCLUDED_OVERRIDE_TAGS
    assert SessionConstants.LOCATION_UNCLUSTERED == "unclustered"
    assert SessionConstants.LOCATION_TRACK == "track"
    assert SessionConstants.LOCATION_ALBUM_UNMATCHED == "album_unmatched"
    assert SessionConstants.LOCATION_CLUSTER == "cluster"
    assert SessionConstants.LOCATION_NAT == "nat"


def test_session_constants_immutable() -> None:
    """Test that SessionConstants values are immutable."""
    # Test that frozenset is immutable
    with pytest.raises(AttributeError):
        SessionConstants.EXCLUDED_OVERRIDE_TAGS.add("new_tag")

    # Test that constants are class attributes
    assert hasattr(SessionConstants, 'SESSION_FILE_EXTENSION')
    assert hasattr(SessionConstants, 'SESSION_FORMAT_VERSION')
    assert hasattr(SessionConstants, 'DEFAULT_RETRY_DELAY_MS')
    assert hasattr(SessionConstants, 'FAST_RETRY_DELAY_MS')
    assert hasattr(SessionConstants, 'INTERNAL_TAG_PREFIX')
    assert hasattr(SessionConstants, 'EXCLUDED_OVERRIDE_TAGS')
    assert hasattr(SessionConstants, 'LOCATION_UNCLUSTERED')
    assert hasattr(SessionConstants, 'LOCATION_TRACK')
    assert hasattr(SessionConstants, 'LOCATION_ALBUM_UNMATCHED')
    assert hasattr(SessionConstants, 'LOCATION_CLUSTER')
    assert hasattr(SessionConstants, 'LOCATION_NAT')
