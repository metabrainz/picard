# -*- coding: utf-8 -*-
#
# MIT License
#
# Copyright(c) 2018 Konstantin Mochalov
# Copyright(c) 2022 Philipp Wolfer
#
# Original code from https://gist.github.com/kolen/765526
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files(the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and / or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

PREGAP_LENGTH = 150
DATA_TRACK_GAP = 11400


class NotSupportedTOCError(Exception):
    pass


def calculate_mb_toc_numbers(toc):
    """
    Take iterator of toc entries, return a tuple of numbers for musicbrainz disc id

    Each toc entry is a dict with the following keys:
    - num: track number
    - start_sector: start sector of the track
    - end_sector: end sector of the track
    """
    toc = tuple(toc)
    toc = _remove_data_track(toc)
    num_tracks = len(toc)
    if not num_tracks:
        raise NotSupportedTOCError("Empty track list: %s", toc)

    expected_tracknums = tuple(range(1, num_tracks+1))
    tracknums = tuple(int(e['num']) for e in toc)
    if expected_tracknums != tracknums:
        raise NotSupportedTOCError("Non-standard track number sequence: %s", tracknums)

    leadout_offset = int(toc[-1]['end_sector']) + PREGAP_LENGTH + 1
    offsets = tuple((int(x['start_sector']) + PREGAP_LENGTH) for x in toc)
    return (1, num_tracks, leadout_offset) + offsets


def _remove_data_track(toc):
    if len(toc) > 1:
        last_track_gap = int(toc[-1]['start_sector']) - int(toc[-2]['end_sector'])
        if last_track_gap == DATA_TRACK_GAP + 1:
            toc = toc[:-1]
    return toc
