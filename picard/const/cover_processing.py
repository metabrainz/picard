# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Bob Swift
# Copyright (C) 2024 Giorgio Fontanive
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

from collections import namedtuple
from enum import IntEnum

from picard.i18n import N_


class ResizeModes(IntEnum):
    MAINTAIN_ASPECT_RATIO = 0,
    SCALE_TO_WIDTH = 1,
    SCALE_TO_HEIGHT = 2,
    CROP_TO_FIT = 3,
    STRETCH_TO_FIT = 4


CoverResizeMode = namedtuple('CoverResizeMode', ['mode', 'title', 'tooltip'])

COVER_RESIZE_MODES = [
    # Items are entered in the order they should appear in the combo box.
    # The number is the mode number stored in the settings and may be
    # different from the order of appearance in the combo box.  This will
    # allow modes to be added or removed and re-ordered if required.

    CoverResizeMode(ResizeModes.MAINTAIN_ASPECT_RATIO, N_('Maintain aspect ratio'), N_(
        "<p>"
        "Scale the source image so that it fits within the target dimensions."
        "</p><p>"
        "One of the final image dimensions may be less than the target dimension if "
        "the source image and target dimensions have different aspect ratios."
        "</p><p>"
        "For example, a 2000x1000 image resized to target dimensions of "
        "1000x1000 would result in a final image size of 1000x500."
        "</p>"
    )),

    CoverResizeMode(ResizeModes.SCALE_TO_WIDTH, N_('Scale to width'), N_(
        "<p>"
        "Scale the width of the source image to the target width while keeping aspect ratio."
        "</p><p>"
        "For example, a 2000x1000 image resized to a target width of "
        "1000 would result in a final image size of 1000x500."
        "</p>"
    )),

    CoverResizeMode(ResizeModes.SCALE_TO_HEIGHT, N_('Scale to height'), N_(
        "<p>"
        "Scale the height of the source image to the target height while keeping aspect ratio."
        "</p><p>"
        "For example, a 1000x2000 image resized to a target height of "
        "1000 would result in a final image size of 500x1000."
        "</p>"
    )),

    CoverResizeMode(ResizeModes.CROP_TO_FIT, N_('Crop to fit'), N_(
        "<p>"
        "Scale the source image so that it completely fills the target dimensions "
        "in both directions."
        "</p><p>"
        "If the source image and target dimensions have different aspect ratios"
        "then there will be overflow in one direction which will be (center) cropped."
        "</p><p>"
        "For example, a 500x1000 image resized to target dimensions of "
        "1000x1000 would first scale up to 1000x2000, then the excess height "
        "would be center cropped resulting in the final image size of 1000x1000."
        "</p>"
    )),

    CoverResizeMode(ResizeModes.STRETCH_TO_FIT, N_('Stretch to fit'), N_(
        "<p>"
        "Stretch the image to exactly fit the specified dimensions, "
        "distorting it if necessary."
        "</p><p>"
        "For example, a 500x1000 image with target dimension of 1000x1000 "
        "would be stretched horizontally resulting in the final image "
        "size of 1000x1000."
        "</p>"
    )),
]

COVER_CONVERTING_FORMATS = ['JPEG', 'PNG', 'WebP', 'TIFF']
