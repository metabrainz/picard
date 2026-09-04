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


from unittest.mock import Mock

from PyQt6 import QtGui

from picard.file import File

from picard.ui.itemviews import (
    _AUTO_COLOR,
    FileItem,
    MainPanel,
    TrackItem,
    TreeItem,
    _match_bgcolor,
)


def _run_refresh_colors(qapp):
    """Invoke MainPanel._refresh_colors with a crafted palette, no real window.

    The palette's current group is forced to Disabled to reproduce the state
    right after the options dialog closes on "Make It So".
    """
    palette = QtGui.QPalette()
    Text = QtGui.QPalette.ColorRole.Text
    Base = QtGui.QPalette.ColorRole.Base
    Active = QtGui.QPalette.ColorGroup.Active
    Disabled = QtGui.QPalette.ColorGroup.Disabled
    palette.setColor(Active, Text, QtGui.QColor('#f0f0f0'))
    palette.setColor(Active, Base, QtGui.QColor('#242424'))
    palette.setColor(Disabled, Text, QtGui.QColor('#828282'))
    palette.setColor(Disabled, Base, QtGui.QColor('#323232'))
    palette.setCurrentColorGroup(Disabled)

    panel = MainPanel.__new__(MainPanel)
    panel.palette = Mock(return_value=palette)
    panel._views = []
    panel._refresh_colors()


def test_default_foreground_is_automatic_not_baked(qapp):
    """Normal/changed track and file text must not bake a concrete colour.

    Regression test: the default foreground used to be baked from the palette's
    current colour group. When refreshed while the panel was in the Disabled
    group (options dialog closing), the greyed disabled colour (#828282) was
    frozen into the track names, leaving them unreadable grey-on-grey until
    restart. The default now resolves to _AUTO_COLOR so Qt renders it
    automatically per colour group.
    """
    _run_refresh_colors(qapp)

    assert TrackItem.track_colors[File.State.NORMAL] is not _AUTO_COLOR  # saved = custom green
    assert TrackItem.track_colors[File.State.CHANGED] is _AUTO_COLOR
    assert FileItem.file_colors[File.State.NORMAL] is _AUTO_COLOR
    assert FileItem.file_colors[File.State.CHANGED] is _AUTO_COLOR
    # Unmapped states fall back to automatic too.
    assert TrackItem.track_colors['some-unmapped-state'] is _AUTO_COLOR


def test_custom_entity_colors_stay_baked(qapp):
    """Pending/error entity colours are genuine custom colours and stay baked."""
    _run_refresh_colors(qapp)

    for colors in (TrackItem.track_colors, FileItem.file_colors):
        assert isinstance(colors[File.State.PENDING], QtGui.QColor)
        assert isinstance(colors[File.State.ERROR], QtGui.QColor)


def test_base_color_pinned_to_active_group(qapp):
    """base_color (the match-tint gradient input) is taken from the Active group."""
    _run_refresh_colors(qapp)
    assert TreeItem.base_color.name() == '#242424'


def test_perfect_match_background_is_automatic(qapp):
    """A perfect match needs no tint, so its background is automatic."""
    _run_refresh_colors(qapp)
    assert _match_bgcolor(1) is _AUTO_COLOR
    assert _match_bgcolor(1.0) is _AUTO_COLOR


def test_imperfect_match_background_is_tinted(qapp):
    """An imperfect match keeps a concrete tint colour (custom highlight)."""
    _run_refresh_colors(qapp)
    bg = _match_bgcolor(0.5)
    assert isinstance(bg, QtGui.QColor)
    assert bg is not _AUTO_COLOR
