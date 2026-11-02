# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Matthias Friedrich
# Copyright (C) 2007-2008 Lukáš Lalinský
# Copyright (C) 2008 Robert Kaye
# Copyright (C) 2009, 2013, 2018-2023, 2026 Philipp Wolfer
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2013 Johannes Dewender
# Copyright (C) 2013 Sebastian Ramacher
# Copyright (C) 2013 Wieland Hoffmann
# Copyright (C) 2013, 2018-2021, 2023-2026 Laurent Monin
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2026 metaisfacil
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


import traceback

from picard import log
from picard.config import get_config
from picard.debug_opts import DebugOpt
from picard.disc.cyanriplog import toc_from_file as _cyanrip_toc_from_file
from picard.disc.dbpoweramplog import toc_from_file as _dbpoweramp_toc_from_file
from picard.disc.eaclog import toc_from_file as _eac_toc_from_file
from picard.disc.presentation import disc_presentation
from picard.disc.scsitoc import toc_from_file as _scsitoc_toc_from_file
from picard.disc.whipperlog import toc_from_file as _whipper_toc_from_file
from picard.extension_points.disc_log_readers import (
    ext_point_disc_log_readers,
    register_disc_log_reader,
)
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.services import services
from picard.util.cdrom import (
    discid,
    has_isrc_support,
)
from picard.util.isrc import (
    format_isrc,
    valid_isrc,
)
from picard.util.mbserver import build_submission_url


class Disc:
    def __init__(self, id: str | None = None):
        self.id = id
        self.mcn = None
        self.tracks = 0
        self.toc_string = None
        self.isrcs: dict[int, str] = {}
        self._skip_dialog = False
        self._files_to_match = None

    def read(self, device=None):
        assert discid, "discid is not available"
        if device is None:
            device = discid.get_default_device()
        log.debug("Reading CD using device: %r", device)
        features = ['mcn']
        if has_isrc_support():
            config = get_config()
            if config.setting['read_isrcs_from_disc']:
                features.append('isrc')
        try:
            disc = discid.read(device, features=features)
            self._set_disc_details(disc)
        except discid.DiscError as e:
            log.error("Error while reading %r: %s", device, e)
            raise

    def put(self, toc):
        assert discid, "discid is not available"
        log.debug("Generating disc ID using TOC: %r", toc)
        try:
            first, last, sectors, *offsets = toc
            disc = discid.put(first, last, sectors, offsets)
            self._set_disc_details(disc)
        except discid.TOCError as e:
            log.error("Error while processing TOC %r: %s", toc, e)
            raise
        except ValueError as e:
            log.error("Error while processing TOC %r: %s", toc, e)
            raise discid.TOCError(e) from e

    def read_log(self, path):
        """Read a disc TOC from a CD ripper log file and compute the disc ID.

        Tries each registered disc-log reader (the ``disc_log_readers``
        extension point) until one parses ``path`` into a MusicBrainz TOC, then
        computes the disc ID from it (via :meth:`put`). Raises if no reader can
        parse the file. UI-agnostic: callers run this on a worker thread and
        report errors through their own frontend.
        """
        for reader in ext_point_disc_log_readers:
            module_name = reader.__module__
            try:
                log.debug('Trying to parse "%s" with %s…', path, module_name)
                toc = reader(path)
                break
            except Exception:
                log.debug('Failed parsing ripping log "%s" with %s', path, module_name, exc_info=True)
        else:
            msg = N_('Failed parsing ripping log "%s"')
            log.warning(msg, path)
            raise Exception(_(msg) % path)
        self.put(toc)

    def _set_disc_details(self, disc):
        self.id = disc.id
        self.mcn = disc.mcn
        self.tracks = len(disc.tracks)
        self.toc_string = disc.toc_string
        self.isrcs = self._extract_isrcs(disc.tracks)
        log.debug("Read disc ID %s with MCN %s", self.id, self.mcn)
        if self.isrcs:
            log.info("Read %d ISRCs from disc:", len(self.isrcs))
            for track_num, isrc in sorted(self.isrcs.items()):
                log.info("  Track %d: ISRC %s", track_num, format_isrc(isrc))

    @staticmethod
    def _extract_isrcs(tracks) -> dict[int, str]:
        """Extract validated ISRCs from disc tracks.

        Returns a dict mapping track number to normalized ISRC.
        Tracks without ISRCs, with invalid ISRCs, or with duplicate
        ISRCs (same ISRC on multiple tracks) are skipped.
        Duplicate ISRCs are a known issue with some CD drives that
        report the same ISRC for adjacent tracks.
        """
        isrcs: dict[int, str] = {}
        dbg = log.debug_if(DebugOpt.ISRC)
        for track in tracks:
            isrc = getattr(track, 'isrc', None)
            if isrc:
                normalized = valid_isrc(isrc)
                if normalized:
                    isrcs[track.number] = normalized
                elif dbg:
                    dbg(
                        "Disc ISRC: track %d has invalid ISRC %r, skipping",
                        track.number,
                        isrc,
                    )
            elif dbg:
                dbg("Disc ISRC: track %d has no ISRC", track.number)
        # Detect duplicates: same ISRC assigned to multiple tracks
        seen: dict[str, list[int]] = {}
        for track_num, isrc in isrcs.items():
            seen.setdefault(isrc, []).append(track_num)
        duplicates = {isrc: tracks for isrc, tracks in seen.items() if len(tracks) > 1}
        if duplicates:
            for isrc, track_nums in duplicates.items():
                log.warning(
                    "Duplicate ISRC %s found on tracks %s (possible drive read error), skipping",
                    format_isrc(isrc),
                    ', '.join(str(n) for n in track_nums),
                )
                for track_num in track_nums:
                    del isrcs[track_num]
        return isrcs

    @staticmethod
    def _submission_url(id, tracks, toc_string):
        return build_submission_url(
            "/cdtoc/attach",
            query_args={
                'id': id,
                'tracks': tracks,
                'toc': toc_string.replace(' ', '+'),
            },
        )

    @property
    def submission_url(self):
        if self.id and self.tracks and self.toc_string:
            return self._submission_url(self.id, self.tracks, self.toc_string)
        else:
            return None

    def lookup(self):
        if self.id:
            services().mb_api.lookup_discid(self.id, self._lookup_finished)
        else:
            log.warning("Disc.lookup called without disc ID set, cannot lookup")

    def lookup_by_toc(self, toc_string, skip_dialog=False, files_to_match=None):
        """Lookup releases by table of contents string.

        Args:
            toc_string: The TOC string (e.g., "1+2+150+22337+44910")
            skip_dialog: If True and exactly one match found, auto-load without showing dialog
            files_to_match: List of files to match to the album after load
        """
        self._skip_dialog = skip_dialog
        self._files_to_match = files_to_match
        services().mb_api.lookup_toc(toc_string, self._toc_lookup_finished)

    def _lookup_finished(self, document, http, error):
        disc_presentation().lookup_finished()
        releases = []
        if error:
            log.error("%r", http.errorString())
        else:
            try:
                releases = document['releases']
            except (AttributeError, IndexError):
                log.error(traceback.format_exc())

        disc_presentation().present_releases(self, releases)

    def _toc_lookup_finished(self, document, http, error):
        """Handle the result of a TOC lookup."""
        disc_presentation().lookup_finished()
        releases = []
        if error:
            log.error("TOC lookup error: %r", http.errorString())
        else:
            try:
                releases = document.get('releases', [])
            except (AttributeError, KeyError) as e:
                log.error("Error parsing TOC lookup response: %r", e)

        # With skip_dialog, the facade auto-loads a single match without a
        # picker (the lookup-from-tags / non-interactive behaviour); otherwise
        # it presents the picker (GUI) or auto-loads a single match (headless).
        disc_presentation().present_releases(
            self, releases, files_to_match=self._files_to_match, skip_dialog=self._skip_dialog
        )


discid_version: str | None = None
if discid is not None:
    discid_version = "discid %s, %s" % (discid.__version__, discid.LIBDISCID_VERSION_STRING)


# Register built-in disc log readers
register_disc_log_reader(_eac_toc_from_file)
register_disc_log_reader(_whipper_toc_from_file)
register_disc_log_reader(_cyanrip_toc_from_file)
register_disc_log_reader(_dbpoweramp_toc_from_file)
register_disc_log_reader(_scsitoc_toc_from_file)
