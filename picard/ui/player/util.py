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


def get_logarithmic_volume(player_value: float):
    """Return logarithmic scale volume to set slider position"""
    return QAudio.convertVolume(
        player_value,
        QAudio.VolumeScale.LinearVolumeScale,
        QAudio.VolumeScale.LogarithmicVolumeScale,
    )


def get_linear_volume(slider_value: float):
    """Return linear scale volume from slider position"""
    return QAudio.convertVolume(
        slider_value,
        QAudio.VolumeScale.LogarithmicVolumeScale,
        QAudio.VolumeScale.LinearVolumeScale,
    )
