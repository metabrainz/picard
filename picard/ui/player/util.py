# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2023, 2026 Philipp Wolfer
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

from PyQt6.QtMultimedia import QAudio


def get_logarithmic_volume(linear_volume: float):
    """Return logarithmic scale volume for given linear volume"""
    if linear_volume == 1.0:  # 100% should be 100%, without rounding errors
        return 1.0
    return QAudio.convertVolume(
        linear_volume,
        QAudio.VolumeScale.LinearVolumeScale,
        QAudio.VolumeScale.LogarithmicVolumeScale,
    )


def get_linear_volume(logarithmic_volume: float):
    """Return linear scale volume for given logarithmic volume"""
    if logarithmic_volume == 1.0:  # 100% should be 100%, without rounding errors
        return 1.0
    return QAudio.convertVolume(
        logarithmic_volume,
        QAudio.VolumeScale.LogarithmicVolumeScale,
        QAudio.VolumeScale.LinearVolumeScale,
    )
