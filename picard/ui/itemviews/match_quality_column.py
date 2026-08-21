# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Khoa Nguyen
# Copyright (C) 2025 The MusicBrainz Team
# Copyright (C) 2026 Laurent Monin
# Copyright (C) 2026 Philipp Wolfer
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


from collections import namedtuple

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import gettext as _
from picard.item import Item

from picard.ui.itemviews.custom_columns import DelegateColumn
from picard.ui.itemviews.custom_columns.protocols import (
    ColumnValueProvider,
    DelegateProvider,
)
from picard.ui.match_icons import (
    match_icons,
    similarity_to_level,
)


# Structured container for delegate item data
MatchItemData = namedtuple("MatchItemData", ["obj", "column", "stats"])


class MatchQualityProvider(ColumnValueProvider, DelegateProvider):
    """Column that displays match quality using match icons at the release level."""

    def __init__(self) -> None:
        """Initialize the match quality provider."""
        self._delegate_class = MatchQualityColumnDelegate

    def evaluate(self, obj: Item) -> str:
        """Return the match percentage as a string for sorting.

        Parameters
        ----------
        obj
            The item to evaluate.

        Returns
        -------
        str
            The match percentage as a string (e.g., "0.75" for 75%).
        """
        if not hasattr(obj, 'get_num_matched_tracks') or not hasattr(obj, 'tracks'):
            return "0.0"

        # Album object
        total = len(obj.tracks) if obj.tracks else 0

        if total == 0:
            return "0.0"

        get_num_matched_tracks = getattr(obj, 'get_num_matched_tracks', None)
        if not callable(get_num_matched_tracks):
            return "0.0"

        matched = int(get_num_matched_tracks())
        percentage = matched / total
        return str(percentage)

    def get_match_stats(self, obj: Item) -> dict[str, int] | None:
        """Get comprehensive match statistics for the given object.

        Parameters
        ----------
        obj
            The item to evaluate.

        Returns
        -------
        dict[str, int] | None
            A dictionary with keys ``matched``, ``total``, ``unmatched``,
            ``duplicates``, ``extra``, and ``missing``. Returns ``None`` if
            stats are not available for the given object.
        """
        # Only show stats at the release (album) level, not track level
        if not hasattr(obj, 'get_num_matched_tracks') or not hasattr(obj, 'tracks'):
            return None

        # Album object
        matched = obj.get_num_matched_tracks()
        tracks = getattr(obj, 'tracks', None)
        total = len(tracks) if tracks else 0
        unmatched = obj.get_num_unmatched_files()

        # Calculate duplicates and extra tracks
        duplicates = 0
        extra = 0
        missing = 0

        # Count files per track to detect duplicates
        track_file_counts = {}
        if tracks:
            for track in tracks:
                track_file_counts[track] = len(track.files)

        # Count unmatched files
        unmatched_files = obj.unmatched_files.files if hasattr(obj, 'unmatched_files') else []

        # Calculate duplicates (tracks with more than one file)
        for file_count in track_file_counts.values():
            if file_count > 1:
                duplicates += file_count - 1

        # Calculate extra tracks (unmatched files beyond total tracks)
        if unmatched_files:
            extra = len(unmatched_files)

        # Calculate missing tracks (tracks with no files)
        if tracks:
            for track in tracks:
                if len(track.files) == 0:
                    missing += 1

        return {
            'matched': matched,
            'total': total,
            'unmatched': unmatched,
            'duplicates': duplicates,
            'extra': extra,
            'missing': missing,
        }

    def get_delegate_class(self) -> type[QtWidgets.QStyledItemDelegate]:
        """Return the delegate class for custom rendering.

        Returns
        -------
        type[QtWidgets.QStyledItemDelegate]
            The delegate class (subclass of QStyledItemDelegate).
        """
        return self._delegate_class


class MatchQualityColumnDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate for rendering match quality icons in tree items."""

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)

    def _get_item_data(self, index: QtCore.QModelIndex) -> MatchItemData | None:
        """Extract item data and validate it's a match quality column.

        Returns:
            MatchItemData | None: Named tuple with fields `obj`, `column`, `stats`,
            or `None` if validation fails.
        """
        tree_widget = self.parent()
        if not tree_widget:
            return None

        item = tree_widget.itemFromIndex(index)
        if not hasattr(item, 'obj') or not item.obj:
            return None

        obj = item.obj

        # Get the column to determine if this is a match quality column
        column_index = index.column()
        columns = getattr(item, 'columns', None)
        if not columns or column_index >= len(columns):
            return None

        column = columns[column_index]
        if not isinstance(column, DelegateColumn):
            return None

        # Get stats from the provider (not from delegate)
        provider = column.delegate_provider
        if hasattr(provider, '_base'):
            provider = provider._base  # Unwrap adapter

        stats = provider.get_match_stats(obj)
        if not stats:
            return None

        return MatchItemData(obj=obj, column=column, stats=stats)

    def _get_match_icon(self, obj: Item, column: DelegateColumn) -> QtGui.QIcon | None:
        """Select the appropriate match icon using delegate-side logic."""
        # Compute stats using provider, but map to icons here (UI concern)
        provider = column.delegate_provider
        if hasattr(provider, '_base'):
            provider = provider._base  # Unwrap adapter

        stats = provider.get_match_stats(obj)
        if not stats:
            return None

        total = stats.get('total', 0)
        if total == 0:
            return match_icons[0]

        matched = stats.get('matched', 0)
        percentage = matched / total if total else 0.0
        return match_icons[similarity_to_level(percentage)]

    def _format_tooltip_text(self, stats: dict[str, int]) -> str:
        """Format stats into a detailed tooltip string.

        Parameters
        ----------
        stats
            Dictionary containing integer match statistics.

        Returns
        -------
        str
            The formatted tooltip text.
        """
        tooltip_parts = []

        # Core match info
        if stats['total'] > 0:
            percentage = (stats['matched'] / stats['total']) * 100
        else:
            percentage = 0.0
        tooltip_parts.append(
            _("Match: %(matched)d/%(total)d (%(percent).1f%%)")
            % {
                'matched': stats['matched'],
                'total': stats['total'],
                'percent': percentage,
            }
        )

        # Additional stats with explanations
        tooltip_parts.append(_("Missing tracks: %(count)d") % {'count': stats['missing']})
        tooltip_parts.append(_("Duplicate files: %(count)d") % {'count': stats['duplicates']})
        tooltip_parts.append(_("Extra files: %(count)d") % {'count': stats['extra']})
        tooltip_parts.append(_("Unmatched files: %(count)d") % {'count': stats['unmatched']})

        return "\n".join(tooltip_parts)

    def paint(
        self,
        painter: QtGui.QPainter | None,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> None:
        """Paint the match quality icon in the item cell.

        Parameters
        ----------
        painter
            The painter used for drawing.
        option
            The style options for the item.
        index
            The model index identifying the item.
        """
        # Initialize the style option
        self.initStyleOption(option, index)

        # Draw the background
        if painter is None:
            return
        if option.state & QtWidgets.QStyle.StateFlag.State_Selected:
            fill_brush = option.palette.highlight()
        else:
            fill_brush = option.palette.base()
        painter.fillRect(option.rect, fill_brush)

        # Get item data
        item_data = self._get_item_data(index)
        if not item_data:
            return

        # Get the match icon from the provider
        icon = self._get_match_icon(item_data.obj, item_data.column)

        # Calculate layout
        icon_size = item_data.column.size
        icon_margin = 2

        # Always draw icon, regardless of column width
        if icon:
            x = option.rect.x() + icon_margin
            y = option.rect.y() + (option.rect.height() - icon_size.height()) // 2
            icon.paint(painter, QtCore.QRect(x, y, icon_size.width(), icon_size.height()))

    def helpEvent(
        self,
        event: QtGui.QHelpEvent | None,
        view: QtWidgets.QAbstractItemView | None,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> bool:
        """Show a tooltip with an explanation of the stats.

        Parameters
        ----------
        event
            The help event providing cursor position.
        view
            The view showing the items.
        option
            The style options for the item.
        index
            The model index identifying the item.

        Returns
        -------
        bool
            ``True`` if the event was handled, else ``False``.
        """
        # Get item data
        item_data = self._get_item_data(index)
        if not item_data or event is None:
            return False

        # Format tooltip text
        tooltip_text = self._format_tooltip_text(item_data.stats)

        # Show the tooltip
        QtWidgets.QToolTip.showText(event.globalPos(), tooltip_text, view)
        return True

    def sizeHint(
        self,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> QtCore.QSize:
        """Return the recommended size for the item cell.

        Parameters
        ----------
        option
            The style options for the item.
        index
            The model index identifying the item.

        Returns
        -------
        QtCore.QSize
            A size that accommodates both icon and text.
        """
        # Return a size that accommodates the icon with margin
        icon_size = 16
        icon_margin = 2
        return QtCore.QSize(icon_size + 2 * icon_margin, icon_size)
