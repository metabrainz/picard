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

from picard.ui.colors import interface_colors
from picard.ui.itemviews import (
    _AUTO_COLOR,
    MATCH_TINT_ALPHA_DARK,
    MATCH_TINT_ALPHA_LIGHT,
    FileItem,
    MainPanel,
    TrackItem,
    TreeItem,
    _match_bgcolor,
)
from picard.ui.match_icons import (
    NUM_LEVELS,
    similarity_to_level,
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


def test_base_color_follows_current_color_group(qapp):
    """base_color (the match-tint gradient input) tracks the current colour group.

    Regression test for the "great match" banding: base_color used to be pinned
    to the Active group, so baked great-match tints stayed light while perfect
    matches (automatic rendering) greyed out with the Disabled group whenever
    the window was disabled — the near-perfect rows banded against the rest.
    _run_refresh_colors forces the palette's current group to Disabled, so
    base_color must resolve to the Disabled base (#323232), not the Active one.
    """
    _run_refresh_colors(qapp)
    assert TreeItem.base_color.name() == '#323232'


def test_match_tint_composited_over_current_group_base(qapp):
    """The match tint composites the low colour over the current group's base.

    Regression test for the "great match" banding: the tint is composited over
    base_color, which tracks the current colour group. With the group forced to
    Disabled (#323232), the tint must be nearer the Disabled base than the
    Active base (#242424), so it does not band against the greyed automatic
    rows. The exact value matches the alpha-composite formula in _match_bgcolor.
    """
    _run_refresh_colors(qapp)
    similarity = 0.99  # a "great match": high, but not an exact 1.0
    level = similarity_to_level(similarity)
    top_level = NUM_LEVELS - 1
    assert level < top_level  # not the perfect/top level

    bg = _match_bgcolor(similarity)
    assert isinstance(bg, QtGui.QColor)

    max_alpha = MATCH_TINT_ALPHA_DARK if interface_colors.dark_theme else MATCH_TINT_ALPHA_LIGHT
    t = (max_alpha * (top_level - level) / top_level) / 255
    base = QtGui.QColor('#323232')
    low = interface_colors.get_qcolor('match_similarity_low')
    expected = QtGui.QColor(
        int(base.red() + (low.red() - base.red()) * t),
        int(base.green() + (low.green() - base.green()) * t),
        int(base.blue() + (low.blue() - base.blue()) * t),
    )
    assert bg.name() == expected.name()
    # Closer to the Disabled base than to the Active base (no banding).
    assert abs(bg.red() - base.red()) < abs(bg.red() - QtGui.QColor('#242424').red()) + 100


def test_match_tint_scales_with_level(qapp):
    """A poorer match is tinted more strongly than a better one, capped by alpha.

    The poorest match (level 0) gets the strongest tint (full MATCH_TINT_ALPHA)
    but is still composited over the base — it is not the raw low colour — so it
    stays subtle. Better matches are progressively closer to the base.
    """
    _run_refresh_colors(qapp)
    base = TreeItem.base_color
    low = interface_colors.get_qcolor('match_similarity_low')

    def delta(sim):
        bg = _match_bgcolor(sim)
        return max(
            abs(bg.red() - base.red()),
            abs(bg.green() - base.green()),
            abs(bg.blue() - base.blue()),
        )

    poor = delta(0.0)  # level 0
    great = delta(0.99)  # near-perfect, but not exact
    # Poorer match is more strongly tinted than the great match.
    assert poor > great
    # The great match is still perceptible (not identical to the base).
    assert great >= 5
    # Even the poorest match is capped — not the raw low colour.
    assert delta(0.0) < max(
        abs(low.red() - base.red()),
        abs(low.green() - base.green()),
        abs(low.blue() - base.blue()),
    )


def test_perfect_match_background_is_automatic(qapp):
    """A perfect (exact 1.0) match needs no tint, so its background is automatic."""
    _run_refresh_colors(qapp)
    assert _match_bgcolor(1) is _AUTO_COLOR
    assert _match_bgcolor(1.0) is _AUTO_COLOR


def test_imperfect_match_background_is_tinted(qapp):
    """An imperfect match keeps a concrete tint colour (custom highlight)."""
    _run_refresh_colors(qapp)
    bg = _match_bgcolor(0.5)
    assert isinstance(bg, QtGui.QColor)
    assert bg is not _AUTO_COLOR
