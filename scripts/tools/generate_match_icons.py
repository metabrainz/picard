#!/usr/bin/env python3
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


#
# Generate match quality icon PNGs for MusicBrainz Picard.
#
# This script produces the static icon files used at runtime.  The rendering
# logic lives here so that colours, levels, and shape can be tweaked without
# editing source SVGs.
#
# Usage:
#   python scripts/generate_match_icons.py [--sheet /tmp/sheet.png]
#
# Generated files go into resources/images/ and are referenced from picard.qrc.
# Re-run this script whenever you change the icon appearance, then commit the
# resulting PNGs.
#
# Requires PyQt6 (uses the offscreen platform automatically).

import argparse
from collections import namedtuple
import os
import sys


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Ensure picard package is importable from the project root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.ui.match_icons import (
    LOW_THRESHOLD,
    NUM_STEPS,
)


# ---------------------------------------------------------------------------
# Configuration — rendering parameters (not needed at runtime)
# ---------------------------------------------------------------------------

ICON_SIZE = 16  # Logical icon size in pixels

# Fill height (in pixels at ICON_SIZE) for the lowest level.
LOW_FILL_PX = 6

# Colour anchors: (threshold, R, G, B).  Linearly interpolated between.
ColorAnchor = namedtuple("ColorAnchor", ["threshold", "r", "g", "b"])
ANCHORS = [
    ColorAnchor(0.00, 0x80, 0x00, 0x00),  # dark red
    ColorAnchor(0.50, 0xFF, 0x2A, 0x2A),  # red
    ColorAnchor(0.60, 0xFF, 0x67, 0x00),  # orange
    ColorAnchor(0.70, 0xFF, 0xAD, 0x00),  # amber
    ColorAnchor(0.80, 0xFF, 0xED, 0x46),  # yellow
    ColorAnchor(0.90, 0x43, 0xD4, 0x5C),  # light-green
    ColorAnchor(1.00, 0x43, 0xB0, 0x5C),  # green
]

# Background (unfilled portion) colour.
BG_COLOR = QtGui.QColor(0xE7, 0xEC, 0xED)

# Desaturation factor for pending icons.
PENDING_DESAT = 0.45


# ---------------------------------------------------------------------------
# Rendering helpers (same logic as the previous dynamic module)
# ---------------------------------------------------------------------------


def _interpolate_color(similarity: float) -> QtGui.QColor:
    import bisect

    thresholds = [a.threshold for a in ANCHORS]
    similarity = max(0.0, min(1.0, similarity))
    i = min(bisect.bisect_right(thresholds, similarity), len(ANCHORS) - 1)
    lo = ANCHORS[max(0, i - 1)]
    hi = ANCHORS[i]
    span = hi.threshold - lo.threshold
    t = (similarity - lo.threshold) / span if span else 1.0
    return QtGui.QColor(
        int(round(lo.r + (hi.r - lo.r) * t)),
        int(round(lo.g + (hi.g - lo.g) * t)),
        int(round(lo.b + (hi.b - lo.b) * t)),
    )


def _desaturate(color: QtGui.QColor, factor: float = PENDING_DESAT) -> QtGui.QColor:
    h, s, v, a = color.getHsvF()
    return QtGui.QColor.fromHsvF(h, s * factor, v, a)


def _render_pixmap(fill_fraction: float, size: int, pending: bool) -> QtGui.QPixmap:
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)

    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    painter.setPen(QtCore.Qt.PenStyle.NoPen)

    margin = max(1, size // 8)
    shape_rect = QtCore.QRectF(margin, 0, size - 2 * margin, size)

    rx = ry = shape_rect.width() * 0.082
    path = QtGui.QPainterPath()
    path.addRoundedRect(shape_rect, rx, ry)

    fill_color = _interpolate_color(fill_fraction)
    if pending:
        fill_color = _desaturate(fill_color)

    if fill_fraction >= 1.0:
        painter.setBrush(QtGui.QBrush(fill_color))
        painter.drawPath(path)
    else:
        fill_fraction = max(0.02, fill_fraction)
        fill_y = shape_rect.bottom() - shape_rect.height() * fill_fraction
        fill_rect = QtCore.QRectF(shape_rect.x(), fill_y, shape_rect.width(), shape_rect.bottom() - fill_y)
        painter.setBrush(QtGui.QBrush(BG_COLOR))
        painter.drawPath(path)
        painter.setClipPath(path)
        painter.setBrush(QtGui.QBrush(fill_color))
        painter.drawRect(fill_rect)

    painter.end()
    return pixmap


# ---------------------------------------------------------------------------
# Level computation (same as runtime module)
# ---------------------------------------------------------------------------


def compute_levels() -> list[float]:
    """Return the fill fractions for each level (0=low, ..., NUM_STEPS, then 1.0)."""
    remaining_px = ICON_SIZE - LOW_FILL_PX
    px_step = remaining_px / (NUM_STEPS + 1)
    fills = [LOW_FILL_PX / ICON_SIZE]
    for i in range(1, NUM_STEPS + 1):
        fills.append((LOW_FILL_PX + i * px_step) / ICON_SIZE)
    fills.append(1.0)  # perfect match
    return fills


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def generate_icons(output_dir: str) -> list[str]:
    """Generate all icon PNGs and return the list of filenames created."""
    levels = compute_levels()
    filenames = []

    # Mapping of scale factor suffix to render size in pixels.
    #
    # Qt automatically selects @Nx variants based on the screen's device pixel
    # ratio (see qt_findAtNxFile in qtbase/src/gui/image/qicon.cpp).  When
    # QIcon::addFile() is called with "icon.png", Qt searches for @Nx files
    # starting from ceil(devicePixelRatio) down to @2x.
    #
    # Convention in Picard: @2x assets are rendered at 4x the base size (64px
    # for a 16px icon).  This matches all other icon assets in the project and
    # ensures sharp rendering on screens with DPR 2–4, since Qt will downscale
    # the 64px image as needed (downscaling preserves quality, upscaling does
    # not).  This convention predates the script and may be revisited in the
    # future to use proper @2x=32px, @3x=48px, @4x=64px variants.
    scale_to_size = {
        1: ICON_SIZE,  # 16px — base size for 1x (96 DPI) screens
        2: ICON_SIZE * 4,  # 64px — covers DPR 2–4 via downscaling
    }

    for level_idx, fill in enumerate(levels):
        for pending in (False, True):
            prefix = "match-pending" if pending else "match"
            basename = f"{prefix}-{level_idx}"

            for scale, size in scale_to_size.items():
                px = _render_pixmap(fill, size, pending)
                if scale == 1:
                    name = f"{basename}.png"
                else:
                    name = f"{basename}@{scale}x.png"
                px.save(os.path.join(output_dir, name), "PNG")
                filenames.append(name)

    return filenames


def _compute_range_labels() -> list[str]:
    """Compute the similarity range label for each level."""
    bucket_width = (1.0 - LOW_THRESHOLD) / NUM_STEPS
    thresholds = [LOW_THRESHOLD + i * bucket_width for i in range(1, NUM_STEPS)]
    boundaries = [LOW_THRESHOLD] + thresholds + [1.0]

    labels = [f"<{LOW_THRESHOLD:.2g}"]
    for i in range(NUM_STEPS - 1):
        lo = boundaries[i]
        hi = boundaries[i + 1]
        labels.append(f"{lo:.2g}–{hi:.2g}")
    labels.append(f"{boundaries[-2]:.2g}–<1.0")
    labels.append("=1.0")
    return labels


def generate_sheet(output_path: str) -> None:
    """Generate a visual reference sheet showing all levels."""
    levels = compute_levels()
    range_labels = _compute_range_labels()
    scale = 4
    render_size = ICON_SIZE * scale

    cols = len(levels)
    padding = 4 * scale
    header_height = 14 * scale
    row_label_width = 100 * scale // 4  # space for "Normal"/"Pending" labels
    cell_w = render_size + padding * 3
    cell_h = render_size + padding

    sheet_w = row_label_width + cols * cell_w + padding
    sheet_h = padding + header_height + 2 * cell_h + padding

    sheet = QtGui.QPixmap(sheet_w, sheet_h)
    sheet.fill(QtGui.QColor(255, 255, 255))

    painter = QtGui.QPainter(sheet)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    font = QtGui.QFont("monospace", max(7, 3 * scale))
    painter.setFont(font)
    painter.setPen(QtGui.QColor(0, 0, 0))

    # Column headers (similarity ranges)
    for col_idx in range(cols):
        x = row_label_width + col_idx * cell_w
        text_rect = QtCore.QRectF(x, padding, cell_w, header_height)
        painter.drawText(
            text_rect,
            QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter,
            range_labels[col_idx],
        )

    # Two rows: Normal, Pending
    for row_idx, (pending, label) in enumerate(zip([False, True], ["Normal", "Pending"], strict=True)):
        y = padding + header_height + row_idx * cell_h

        # Row label
        painter.drawText(
            QtCore.QRectF(0, y, row_label_width - padding, cell_h),
            QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter,
            label,
        )

        # Icons
        for col_idx, fill in enumerate(levels):
            x = row_label_width + col_idx * cell_w + (cell_w - render_size) // 2
            icon_y = y + (cell_h - render_size) // 2
            px = _render_pixmap(fill, render_size, pending)
            painter.drawPixmap(x, icon_y, px)

    painter.end()
    sheet.save(output_path, "PNG")
    print(f"Sheet saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate match quality icon PNGs")
    parser.add_argument(
        "--sheet",
        metavar="PATH",
        help="Also generate a visual reference sheet PNG",
    )
    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv[:1])  # noqa: F841

    # Output directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    output_dir = os.path.join(project_root, "resources", "images")
    os.makedirs(output_dir, exist_ok=True)

    filenames = generate_icons(output_dir)

    levels = compute_levels()
    print(f"Generated {len(filenames)} files in {output_dir}/")
    print(f"  Levels: {len(levels)} (low + {NUM_STEPS} steps + perfect)")
    print(f"  Fill pixels at {ICON_SIZE}px: {', '.join(f'{int(round(f * ICON_SIZE))}px' for f in levels)}")
    print()
    print("Files:")
    for f in sorted(filenames):
        print(f"  {f}")

    if args.sheet:
        generate_sheet(args.sheet)


if __name__ == "__main__":
    main()
