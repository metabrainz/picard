# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.

"""Regression test for PICARD-3515.

The album and file column sets differ by the inserted Match column. A file row
rendered while detached from the view uses the wrong (file-view) column indices,
so for a multi-file track every file-info value appeared shifted by one column.
"""

from unittest.mock import Mock, patch

from PyQt6 import QtWidgets

from picard.ui.itemviews import FileItem, TrackItem
from picard.ui.itemviews.columns import ALBUMVIEW_COLUMNS


# File-info columns whose index differs between the two column sets (everything
# after the inserted Match column shifts by one).
_PROBE_KEYS = ('~format', '~bitrate', '~extension', '~file_created_timestamp', '~filesize')


def _make_track(file_count):
    files = []
    for n in range(file_count):
        file = Mock()
        file.column = Mock(side_effect=lambda key, n=n: f"f{n}-{key}")
        file.ui_item = None
        files.append(file)
    track = Mock(num_linked_files=file_count, files=files, errors=None)
    track.is_video.return_value = False
    track.is_data.return_value = False
    return track


def test_multifile_track_columns_aligned(qapp):
    tree = QtWidgets.QTreeWidget()
    tree.columns = ALBUMVIEW_COLUMNS
    tree.setColumnCount(len(ALBUMVIEW_COLUMNS))

    track_item = TrackItem(_make_track(2))
    tree.addTopLevelItem(track_item)

    # Stub out the icon/color decoration that would need a full MainPanel; only
    # the column text placement is under test here.
    with (
        patch.object(TrackItem, 'setIcon'),
        patch.object(FileItem, 'setIcon'),
        patch.object(TrackItem, '_item_colors', return_value=(None, None)),
        patch.object(FileItem, '_item_colors', return_value=(None, None)),
        patch.object(FileItem, 'decide_file_icon_info', return_value=(None, '')),
        patch.object(FileItem, 'decide_fingerprint_icon_info', return_value=(None, '')),
    ):
        TrackItem.icon_audio = None
        track_item.update(update_album=False, update_selection=False)

    assert track_item.childCount() == 2
    for child in (track_item.child(0), track_item.child(1)):
        assert child is not None
        for key in _PROBE_KEYS:
            col = ALBUMVIEW_COLUMNS.pos(key)
            assert child.text(col) == child.obj.column(key)
