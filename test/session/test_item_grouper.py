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

"""Tests for ItemGrouper."""

from pathlib import Path

from picard.session.session_loader import ItemGrouper


def test_item_grouper_group_items_by_location() -> None:
    grouper = ItemGrouper()
    items = [
        {
            'file_path': "/test/unclustered.mp3",
            'location': {'type': "unclustered"},
        },
        {
            'file_path': "/test/cluster.mp3",
            'location': {'type': "cluster", 'cluster_title': "Album", 'cluster_artist': "Artist"},
        },
        {
            'file_path': "/test/track.mp3",
            'location': {'type': "track", 'album_id': "album-123", 'recording_id': "recording-456"},
        },
        {
            'file_path': "/test/unmatched.mp3",
            'location': {'type': "album_unmatched", 'album_id': "album-789"},
        },
        {
            'file_path': "/test/nat.mp3",
            'location': {'type': "nat", 'recording_id': "recording-999"},
        },
    ]

    grouped = grouper.group(items)

    assert len(grouped.unclustered) == 1
    assert Path(grouped.unclustered[0]).name == "unclustered.mp3"

    assert len(grouped.by_cluster) == 1
    assert ("Album", "Artist") in grouped.by_cluster

    assert "album-123" in grouped.by_album
    assert len(grouped.by_album['album-123'].tracks) == 1

    assert "album-789" in grouped.by_album
    assert len(grouped.by_album['album-789'].unmatched) == 1

    assert len(grouped.nat_items) == 1
    assert grouped.nat_items[0][1] == "recording-999"


def test_item_grouper_group_items_by_location_unknown_type() -> None:
    grouper = ItemGrouper()
    items = [
        {
            'file_path': "/test/unknown.mp3",
            'location': {'type': "unknown_type"},
        },
    ]

    grouped = grouper.group(items)

    assert len(grouped.unclustered) == 1
    assert Path(grouped.unclustered[0]).name == "unknown.mp3"


def test_item_grouper_group_items_by_location_missing_location() -> None:
    grouper = ItemGrouper()
    items = [
        {
            'file_path': "/test/no_location.mp3",
        },
    ]

    grouped = grouper.group(items)

    assert len(grouped.unclustered) == 1
    assert Path(grouped.unclustered[0]).name == "no_location.mp3"


def test_item_grouper_extract_metadata() -> None:
    grouper = ItemGrouper()
    items = [
        {
            'file_path': "/test/file1.mp3",
            'metadata': {'tags': {'title': ["Song 1"], 'artist': ["Artist 1"]}},
        },
        {
            'file_path': "/test/file2.mp3",
        },
        {
            'file_path': "/test/file3.mp3",
            'metadata': {'tags': {'title': ["Song 3"]}},
        },
    ]

    metadata_map = grouper.extract_metadata(items)

    assert len(metadata_map) == 2
    assert Path("/test/file1.mp3") in metadata_map
    assert Path("/test/file3.mp3") in metadata_map
    assert metadata_map[Path("/test/file1.mp3")]['title'] == ["Song 1"]


def test_item_grouper_preserves_path_expansion() -> None:
    grouper = ItemGrouper()
    # Use a tilde path to ensure expanduser is applied
    items = [
        {
            'file_path': str(Path.home() / "does_not_exist.mp3"),
            'location': {'type': "unclustered"},
        }
    ]
    grouped = grouper.group(items)
    # Path should be absolute and expanded
    assert grouped.unclustered[0].is_absolute()


def test_item_grouper_extract_metadata_empty_items() -> None:
    grouper = ItemGrouper()
    metadata_map = grouper.extract_metadata([])
    assert len(metadata_map) == 0


def test_item_grouper_extract_metadata_no_metadata() -> None:
    grouper = ItemGrouper()
    items = [
        {'file_path': "/test/file1.mp3"},
        {'file_path': "/test/file2.mp3"},
    ]
    metadata_map = grouper.extract_metadata(items)
    assert len(metadata_map) == 0
