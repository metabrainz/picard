# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Matthias Friedrich
# Copyright (C) 2007-2008 Lukáš Lalinský
# Copyright (C) 2008 Robert Kaye
# Copyright (C) 2009, 2013, 2018-2023 Philipp Wolfer
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2013 Johannes Dewender
# Copyright (C) 2013 Sebastian Ramacher
# Copyright (C) 2013 Wieland Hoffmann
# Copyright (C) 2013, 2018-2021, 2023-2024 Laurent Monin
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


from functools import partial
import traceback

from PyQt6 import QtCore

from picard import log
from picard.util.mbserver import build_submission_url

from picard.ui.cdlookup import CDLookupDialog


try:
    # use python-libdiscid (http://pythonhosted.org/python-libdiscid/)
    from libdiscid.compat import discid  # type: ignore[unresolved-import]
except ImportError:
    try:
        # use python-discid (http://python-discid.readthedocs.org/en/latest/)
        import discid  # type: ignore[unresolved-import]
    except (ImportError, OSError):
        discid = None


class Disc:
    def __init__(self, id=None):
        self.tagger = QtCore.QCoreApplication.instance()
        self.id = id
        self.mcn = None
        self.tracks = 0
        self.toc_string = None
        self._skip_dialog = False
        self._files_to_match = None

    def read(self, device=None):
        if device is None:
            device = discid.get_default_device()
        log.debug("Reading CD using device: %r", device)
        try:
            disc = discid.read(device, features=['mcn'])
            self._set_disc_details(disc)
        except discid.DiscError as e:
            log.error("Error while reading %r: %s", device, e)
            raise

    def put(self, toc):
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

    def _set_disc_details(self, disc):
        self.id = disc.id
        self.mcn = disc.mcn
        self.tracks = len(disc.tracks)
        self.toc_string = disc.toc_string
        log.debug("Read disc ID %s with MCN %s", self.id, self.mcn)

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
        self.tagger.mb_api.lookup_discid(self.id, self._lookup_finished)

    def lookup_by_toc(self, toc_string, skip_dialog=False, files_to_match=None):
        """Lookup releases by table of contents string.

        Args:
            toc_string: The TOC string (e.g., "1+2+150+22337+44910")
            skip_dialog: If True and exactly one match found, auto-load without showing dialog
            files_to_match: List of files to match to the album after load
        """
        self._skip_dialog = skip_dialog
        self._files_to_match = files_to_match
        self.tagger.mb_api.lookup_toc(toc_string, self._toc_lookup_finished)

    def _lookup_finished(self, document, http, error):
        self.tagger.restore_cursor()
        releases = []
        if error:
            log.error("%r", http.errorString())
        else:
            try:
                releases = document['releases']
            except (AttributeError, IndexError):
                log.error(traceback.format_exc())

        dialog = CDLookupDialog(releases, self, parent=self.tagger.window)
        dialog.exec()

    def _toc_lookup_finished(self, document, http, error):
        """Handle the result of a TOC lookup."""
        self.tagger.restore_cursor()
        releases = []
        if error:
            log.error("TOC lookup error: %r", http.errorString())
        else:
            try:
                releases = document.get('releases', [])
            except (AttributeError, KeyError) as e:
                log.error("Error parsing TOC lookup response: %r", e)

        # If we have exactly one match and skip_dialog is True, auto-load it
        if self._skip_dialog and len(releases) == 1:
            release = releases[0]
            release_id = release.get('id')
            if release_id:
                album = self.tagger.load_album(release_id)
                # Match the files if provided
                if self._files_to_match:
                    self.tagger.move_files_to_album(self._files_to_match, album=album)
            return

        # Otherwise show the dialog for user to select
        dialog = CDLookupDialog(releases, self, parent=self.tagger.window)
        # If files were provided, match them after user selection
        if self._files_to_match:
            dialog.accepted.connect(partial(self._on_dialog_accepted, dialog))
        dialog.exec()

    def _on_dialog_accepted(self, dialog):
        """Handle when user accepts a release selection in the TOC lookup dialog."""
        release_id = dialog.get_selected_release_id()
        if release_id and self._files_to_match:
            album = self.tagger.load_album(release_id)
            self.tagger.move_files_to_album(self._files_to_match, album=album)


if discid is not None:
    discid_version = "discid %s, %s" % (discid.__version__, discid.LIBDISCID_VERSION_STRING)
else:
    discid_version = None
