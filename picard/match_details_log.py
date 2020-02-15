# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2020 Ray Bouchard
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

import numbers
import traceback

from picard import log


__all_file_result_jsons = {}  # dictionary of song file name and json result from acoustid or musicbrainz
__all_file_match_dtls = {}    # dictionary of a song file and match detail entries associated with it.
__cur_file = None


def set_cur_file(p_file):
    """ set current file we are processing

    which file is currently being processed and we want to associate log calls to.
    There are better/OO ways to do this, but we don't want to be too intrusive to the existing code flow
    """
    global __cur_file
    __cur_file = p_file


def set_file_result_json(p_filename, p_json):
    """ Sets the result json associated with this file

    This is the raw response from AcoustId or MusicBrains when we attempted to match metadata for a file
    """
    if (p_json is not None):
        __all_file_result_jsons[p_filename] = str(p_json)


def get_file_result_json(filename):
    return __all_file_result_jsons[filename]


def get_match_dtls(filename):
    return __all_file_match_dtls.get(filename)


def get_all_match_dtls():
    return __all_file_match_dtls


def add_match_dtl_entry(match_dtl_entry):

    # Only log if we are being called for a file comparison (AcoustId Scan or Lookup CD) not track comparison (Search Similiar)
    global __cur_file
    if (__cur_file is None):
        return

    log.debug("MATCH:" + str(match_dtl_entry))

    match_dtl_entries = __all_file_match_dtls.get(__cur_file.filename)
    if match_dtl_entries is None:
        match_dtl_entries = []

    match_dtl_entries.append(match_dtl_entry)
    __all_file_match_dtls[__cur_file.filename] = match_dtl_entries


class match_dtl_entry:
    """matching/scoring info for a single track in list of results

    When we get data back from AcoustID or MusicBrainz Picard iterates over the possible matches and has to pick one.
    It does that by scoring each resulting track.
    This class holds the information of each track and its associated scoring info
    For purposes of logging and displaying in dialog.
    """

    def __init__(self, match_dtl_entry_type, track, release, parts=[], release_parts=[], recording_base_score=-1.0, similarity=0.0, is_new=False):
        try:
            self.match_dtl_entry_type = match_dtl_entry_type
            self.is_new_str = " **NEW-BEST**" if is_new else " "

            self.acoust_id = track.get('acoustid', '')
            self.rec_id = track.get('id')
            self.rec_title = track.get('title', '')
            self.rec_src_cnt = track.get('sources', -1)
            self.rec_artist = track['artist-credit'][0]['name'] if 'artist-credit' in track else ''
            self.rec_len_ms = track.get('length', 0)
            self.rec_len_str = "{min:02d}:{sec:02d}".format(min=((int)(self.rec_len_ms / 1000.0 / 60.0)), sec=((int)((self.rec_len_ms / 1000.0) % 60))) if isinstance(self.rec_len_ms, numbers.Number) else 0

            if release is None:
                self.rg_id = self.rg_title = self.rg_pri_type = self.rg_sec_type = self.rel_id = self.rel_ctry = self.rel_dt = self.med_fmt = self.trk_id = ""
                self.med_tot_cnt = self.rel_tot_trk_cnt = self.med_pos = self.med_trk_cnt = self.trk_pos = 0
            else:
                self.rg_id = release['release-group'].get('id', "")
                self.rg_title = release.get('title', '')
                self.rg_pri_type = release['release-group'].get('primary-type', "no pri-type")
                self.rg_sec_type = release['release-group'].get('secondary-types', "no sec-type")

                self.rel_id = release['id']
                self.rel_ctry = release.get('country', 'no-ctry')

                if 'date' in release:
                    dt = release['date']
                    if isinstance(dt, dict):
                        self.rel_dt = "%4d" % dt.get('year', "")
                        self.rel_dt += "-%02d" % dt.get('month', "")
                        self.rel_dt += "-%02d" % dt.get('day', "")
                    else:
                        self.rel_dt = dt
                else:
                    self.rel_dt = ""

                self.med_tot_cnt = release.get('medium_count', 0)
                self.rel_tot_trk_cnt = release.get('track-count', 0)

                if 'media' in release:
                    medium = release['media'][0]
                    self.med_fmt = medium.get('format', "")
                    self.med_pos = medium.get('position', 0)
                    self.med_trk_cnt = medium.get('track-count', 0)
                    self.trk_pos = medium['tracks'].get('position', '') if 'tracks' in medium else 0
                    self.trk_id = medium['tracks'].get('id', '') if 'tracks' in medium else ""
                else:
                    self.med_fmt = ""
                    self.med_pos = 0
                    self.med_trk_cnt = 0
                    self.trk_pos = 0
                    self.trk_id = ""

            self.parts = parts
            self.release_parts = release_parts
            self.recording_base_score = recording_base_score
            self.similarity = similarity

            add_match_dtl_entry(self)

        except Exception:
            log.error(traceback.format_exc())

    def __str__(self):
        return self.fmt_with_labels()

    @staticmethod
    def get_hdr_tsv():
        hdr = ("nbr\tmsg\tis_better\tsimilarity\tresult_id\t"
               "recording_id\trec_title\trec_len\trec_src_cnt\trec_artist\t"
               "relgrp_id\trelgrp_title\tprim-type\tsec-type\t"
               "rel_id\tcountry\tdate\t"
               "media_fmt\tmed_pos\tmed_tot_cnt\t"
               "track_id\ttrk_pos\tmedia_trk_cnt\trel_tot_trk_cnt\t"
               "Score components: parts\tScore components: release parts\trecording_base_score")
        return hdr

    def fmt_as_tsv(self):
        fmt = ("{match_dtl_entry_type:s}\t"
               "{is_new_str:s}\t"
               "{similarity:.4f}\t"
               "{acoust_id:s}\t"
               "{rec_id:s}\t"
               "{rec_title:s}\t"
               "{rec_len_str:s}\t"
               "{rec_src_cnt:3d}\t"
               "{rec_artist:s}\t"
               "{rg_id:s}\t"
               "{rg_title:s}\t"
               "{rg_pri_type:s}\t"
               "{rg_sec_type:s}\t"
               "{rel_id:s}\t"
               "{rel_ctry:s}\t"
               "{rel_dt:s}\t"
               "{med_fmt:s}\t"
               "{med_pos:2d}\t"
               "{med_tot_cnt:2d}\t"
               "{trk_id:s}\t"
               "{trk_pos:2d}\t"
               "{med_trk_cnt:2d}\t"
               "{rel_tot_trk_cnt:2d}\t"
               "{parts:s}\t"
               "{release_parts:s}\t"
               "{recording_base_score:5.3f}")

        fmtd_str = fmt.format(match_dtl_entry_type=self.match_dtl_entry_type,
                              is_new_str=self.is_new_str,
                              similarity=self.similarity,
                              acoust_id=self.acoust_id,
                              rec_id=self.rec_id,
                              rec_title=self.rec_title,
                              rec_len_str=self.rec_len_str,
                              rec_src_cnt=self.rec_src_cnt,
                              rec_artist=self.rec_artist,
                              rg_id=self.rg_id,
                              rg_title=self.rg_title,
                              rg_pri_type=self.rg_pri_type,
                              rg_sec_type=str(self.rg_sec_type),
                              rel_id=self.rel_id,
                              rel_ctry=self.rel_ctry,
                              rel_dt=self.rel_dt,
                              med_fmt=self.med_fmt,
                              med_pos=self.med_pos,
                              med_tot_cnt=self.med_tot_cnt,
                              trk_id=self.trk_id,
                              trk_pos=self.trk_pos,
                              med_trk_cnt=self.med_trk_cnt,
                              rel_tot_trk_cnt=self.rel_tot_trk_cnt,
                              parts=str(self.parts),
                              release_parts=str(self.release_parts),
                              recording_base_score=self.recording_base_score)

        return fmtd_str

    def fmt_with_labels(self):
        fmt = ('{match_dtl_entry_type:47s}\t'
               '{is_new_str:13s},\t'
               'similarity:{similarity:.4f},\t'
               'result_id:{acoust_id:s},\t'
               'recording_id:{rec_id:s},\t'
               'rec_title:{rec_title:50s},\t'
               'rec_len:{rec_len_str:s},\t'
               'rec_src_cnt:{rec_src_cnt:3d},\t'
               'rec_artist:{rec_artist:s},\t'
               'release_group_id:{rg_id:s},\t'
               'relgrp_title:{rg_title:50s},\t'
               'prim-type:{rg_pri_type:10s},\t'
               'sec-type:{rg_sec_type},\t'
               'rel_id:{rel_id:s},\t'
               'country:{rel_ctry:7s},\t'
               'dt:{rel_dt:10s},\t'
               'media_fmt:{med_fmt:15s},\t{med_pos:2d}\t/\t{med_tot_cnt:2d}\t'
               'track id:{trk_id:s},\t#:\t{trk_pos:2d}\t/\t{med_trk_cnt:2d}\t/\t{rel_tot_trk_cnt:2d},\t'
               'Score components:'
               '(parts:{parts:s}\t+\t'
               'release parts:{release_parts:s})\t*\t'
               'recording_base_score:{recording_base_score:5.3f})')

        try:
            fmtd_str = fmt.format(match_dtl_entry_type=self.match_dtl_entry_type,
                                  is_new_str=self.is_new_str,
                                  similarity=self.similarity,
                                  acoust_id=self.acoust_id,
                                  rec_id=self.rec_id,
                                  rec_title=self.rec_title,
                                  rec_len_str=self.rec_len_str,
                                  rec_src_cnt=self.rec_src_cnt,
                                  rec_artist=self.rec_artist,
                                  rg_id=self.rg_id,
                                  rg_title=self.rg_title,
                                  rg_pri_type=self.rg_pri_type,
                                  rg_sec_type=str(self.rg_sec_type),
                                  rel_id=self.rel_id,
                                  rel_ctry=self.rel_ctry,
                                  rel_dt=self.rel_dt,
                                  med_fmt=self.med_fmt,
                                  med_pos=self.med_pos,
                                  med_tot_cnt=self.med_tot_cnt,
                                  trk_id=self.trk_id,
                                  trk_pos=self.trk_pos,
                                  med_trk_cnt=self.med_trk_cnt,
                                  rel_tot_trk_cnt=self.rel_tot_trk_cnt,
                                  parts=str(self.parts),
                                  release_parts=str(self.release_parts),
                                  recording_base_score=self.recording_base_score)
        except TypeError:
            log.error(traceback.format_exc())

        return fmtd_str
