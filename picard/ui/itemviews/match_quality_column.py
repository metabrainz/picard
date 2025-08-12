# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the GNU General Public License Foundation; either version 2
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


from PyQt6 import QtCore, QtWidgets

from picard.i18n import gettext as _

from picard.ui.columns import ImageColumn


# Mapping of minimum percentage threshold to icon index.
# Checked in descending order so the highest matching threshold wins.
THRESHOLD_TO_ICON_INDEX = {
    1.0: 5,  # 100%
    0.9: 4,  # 90%
    0.8: 3,  # 80%
    0.7: 2,  # 70%
    0.6: 1,  # 60%
    0.5: 0,  # 50%
    0.0: 0,  # <50%
}


class MatchQualityColumn(ImageColumn):
    """Column that displays match quality using match icons at the release level."""

    def __init__(self, title, key, width=120):
        super().__init__(title, key, width=width)
        self.size = QtCore.QSize(16, 16)  # Icon size
        self.width = width

    def paint(self, painter, rect):
        """Override paint method to prevent NotImplementedError from base class."""
        # This column is painted by the delegate, not the header
        # So we just do nothing here to prevent the error
        pass

    def get_match_icon(self, obj):
        """Get the appropriate match icon for the given object."""
        # Only show icons at the release (album) level, not track level
        if not hasattr(obj, 'get_num_matched_tracks') or not hasattr(obj, 'tracks'):
            return None

        # Album object
        matched = obj.get_num_matched_tracks()
        total = len(obj.tracks) if obj.tracks else 0

        if total == 0:
            # Use pending icon for zero tracks
            from picard.ui.itemviews import FileItem

            if hasattr(FileItem, 'match_pending_icons') and len(FileItem.match_pending_icons) > 5:
                return FileItem.match_pending_icons[5]  # match-pending-100.png
            return None

        # Calculate match percentage
        percentage = matched / total

        # Determine which icon to use based on percentage using thresholds
        for threshold in sorted(THRESHOLD_TO_ICON_INDEX.keys(), reverse=True):
            if percentage >= threshold:
                icon_index = THRESHOLD_TO_ICON_INDEX[threshold]
                break

        # Get the match icons from FileItem
        from picard.ui.itemviews import FileItem

        if hasattr(FileItem, "match_icons") and icon_index < len(FileItem.match_icons):
            return FileItem.match_icons[icon_index]

        return None

    def get_match_stats(self, obj):
        """Get comprehensive match statistics for the given object."""
        # Only show stats at the release (album) level, not track level
        if not hasattr(obj, "get_num_matched_tracks") or not hasattr(obj, "tracks"):
            return None

        # Album object
        matched = obj.get_num_matched_tracks()
        total = len(obj.tracks) if obj.tracks else 0
        unmatched = obj.get_num_unmatched_files()

        # Calculate duplicates and extra tracks
        duplicates = 0
        extra = 0
        missing = 0

        # Count files per track to detect duplicates
        track_file_counts = {}
        for track in obj.tracks:
            track_file_counts[track] = len(track.files)

        # Count unmatched files
        unmatched_files = obj.unmatched_files.files if hasattr(obj, "unmatched_files") else []

        # Calculate duplicates (tracks with more than one file)
        for file_count in track_file_counts.values():
            if file_count > 1:
                duplicates += file_count - 1

        # Calculate extra tracks (unmatched files beyond total tracks)
        if unmatched_files:
            extra = len(unmatched_files)

        # Calculate missing tracks (tracks with no files)
        for track in obj.tracks:
            if len(track.files) == 0:
                missing += 1

        return {
            "matched": matched,
            "total": total,
            "unmatched": unmatched,
            "duplicates": duplicates,
            "extra": extra,
            "missing": missing,
        }


class MatchQualityColumnDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate for rendering match quality icons in tree items."""

    def __init__(self, parent=None):
        super().__init__(parent)

    def _get_item_data(self, index):
        """Extract item data and validate it's a match quality column.

        Returns:
            tuple: (obj, column, stats) or (None, None, None) if validation fails
        """
        tree_widget = self.parent()
        if not tree_widget:
            return None, None, None

        item = tree_widget.itemFromIndex(index)
        if not hasattr(item, "obj") or not item.obj:
            return None, None, None

        obj = item.obj

        # Get the column to determine if this is a match quality column
        column_index = index.column()
        columns = getattr(item, "columns", None)
        if not columns or column_index >= len(columns):
            return None, None, None

        column = columns[column_index]
        if not isinstance(column, MatchQualityColumn):
            return None, None, None

        stats = column.get_match_stats(obj)
        if not stats:
            return None, None, None

        return obj, column, stats

    def _format_tooltip_text(self, stats):
        """Format stats into detailed tooltip text.

        Args:
            stats: Dictionary containing match statistics

        Returns:
            str: Formatted tooltip text
        """
        tooltip_parts = []

        # Core match info
        if stats["total"] > 0:
            percentage = (stats["matched"] / stats["total"]) * 100
        else:
            percentage = 0.0
        tooltip_parts.append(
            _("Match: %(matched)d/%(total)d (%(percent).1f%%)")
            % {
                "matched": stats["matched"],
                "total": stats["total"],
                "percent": percentage,
            }
        )

        # Additional stats with explanations
        tooltip_parts.append(_("Missing tracks: %(count)d") % {"count": stats["missing"]})
        tooltip_parts.append(_("Duplicate files: %(count)d") % {"count": stats["duplicates"]})
        tooltip_parts.append(_("Extra files: %(count)d") % {"count": stats["extra"]})
        tooltip_parts.append(_("Unmatched files: %(count)d") % {"count": stats["unmatched"]})

        return "\n".join(tooltip_parts)

    def paint(self, painter, option, index):
        # Initialize the style option
        self.initStyleOption(option, index)

        # Draw the background
        if option.state & QtWidgets.QStyle.StateFlag.State_Selected:
            fill_brush = option.palette.highlight()
        else:
            fill_brush = option.palette.base()
        painter.fillRect(option.rect, fill_brush)

        # Get item data
        obj, column, stats = self._get_item_data(index)
        if not stats:
            return

        # Get the match icon
        icon = column.get_match_icon(obj)

        # Calculate layout
        icon_size = column.size
        icon_margin = 2

        # Always draw icon, regardless of column width
        if icon:
            x = option.rect.x() + icon_margin
            y = option.rect.y() + (option.rect.height() - icon_size.height()) // 2
            icon.paint(painter, QtCore.QRect(x, y, icon_size.width(), icon_size.height()))

    def helpEvent(self, event, view, option, index):
        """Show tooltip with explanation of the stats."""
        # Get item data
        _, __, stats = self._get_item_data(index)
        if not stats:
            return False

        # Format tooltip text
        tooltip_text = self._format_tooltip_text(stats)

        # Show the tooltip
        QtWidgets.QToolTip.showText(event.globalPos(), tooltip_text, view)
        return True

    def sizeHint(self, option, index):
        # Return a size that accommodates both icon and text
        return QtCore.QSize(57, 16)
