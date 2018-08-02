# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2018 Bob Swift
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

from picard import (PICARD_VERSION, PICARD_FANCY_VERSION_STR, PROGRAM_UPDATE_LEVELS, log)
import picard.util.webbrowser2 as wb2
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox
from picard.util import load_json, compare_version_tuples
from functools import partial
import re


# Used to strip leading and trailing text from version string.
_RE_CLEAN_VERSION = re.compile('^[^0-9]*(.*)[^0-9]*$', re.IGNORECASE)


# GitHub API information
VERSIONS_API = {
    'host': 'picard.musicbrainz.org',
    'port': 443,
    'endpoint': '/api/releases'
}


class UpdateCheckManager(QtCore.QObject):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._parent = parent

        # PICARD_VERSIONS dictionary valid keys are: 'stable', 'beta' and 'dev'.
        # Each of these keys contains a dictionary with the keys: 'tag' (string),
        # 'version' (tuple) and 'urls' (dictionary).  The 'version' tuple comprises
        # major (int), minor (int), micro (int), type (str) and development (int)
        # as defined in PEP-440.  The Picard developers have standardized on using
        # only 'dev' or 'final' as the str_type segment of the version tuple.  Each
        # key in the 'urls' dictionary contains a string with the specified url.
        # Valid keys include: 'download' and 'changelog'.  The only required key in
        # the 'urls' dictionary is 'download'.

        # Initialize empty dictionary for 'stable' key
        self._available_versions = {
            'stable': { 'tag': '', 'version': (0, 0, 0, 'dev', 0), 'urls': {'download': ''} },
        }
        self._show_always = False
        self._update_level = 0

    def check_update(self, show_always=False, update_level=0, callback=None):
        '''Checks if an update is available.

        Compares the version number of the currently running instance of Picard
        and displays a dialog box informing the user  if an update is available,
        with an option of opening the download site in their browser.  If there
        is no update available, no dialog will be shown unless the "show_always"
        parameter has been set to True.  This allows for silent checking during
        startup if so configured.

        Args:
            show_always: Boolean value indicating whether the results dialog
                should be shown even when there is no update available.
            update_level: Determines what type of updates to check.  Options are:
                0 = only stable release versions are checked.
                1 = stable and beta releases are checked.
                2 = stable, beta and dev releases are checked.

        Returns:
            none.

        Raises:
            none.
        '''
        self._show_always = show_always
        self._update_level = update_level

        if self._available_versions['stable']['tag']:
            # Release information already acquired from specified website api.
            self._display_results()
        else:
            # Gets list of releases from specified website api.
            self._query_available_updates(callback=callback)

    @property
    def available_versions(self):
        '''Provide a list of the latest version tuples for each update type.'''
        return self._available_versions

    def _query_available_updates(self, callback=None):
        '''Gets list of releases from specified website api.'''
        log.debug(_("Getting release information from {host_url}.".format(host_url=VERSIONS_API['host'],)))
        self.tagger.webservice.get(
            VERSIONS_API['host'],
            VERSIONS_API['port'],
            VERSIONS_API['endpoint'],
            partial(self._releases_json_loaded, callback=callback),
            parse_response_type=None,
            priority=True,
            important=True
        )

    def _releases_json_loaded(self, response, reply, error, callback=None):
        '''Processes response from specified website api query.'''
        if error:
            log.error(N_("Error loading releases list: {error_message}".format(error_message=reply.errorString(),)))
            if self._show_always:
                QMessageBox.information(
                    self._parent,
                    _("Picard Update"),
                    _("Unable to retrieve the latest version information."),
                    QMessageBox.Ok, QMessageBox.Ok)
        else:
            self._available_versions = load_json(response)['versions']
            for key in self._available_versions.keys():
                log.debug("Version key '{version_key}' --> {version_information}".format(
                    version_key=key, version_information=self._available_versions[key],))
            self._display_results()
        if callback:
            callback(not error)

    def _display_results(self):
        # Display results to user.
        key = ''
        high_version = PICARD_VERSION
        for test_key in PROGRAM_UPDATE_LEVELS.keys():
            if self._update_level >= PROGRAM_UPDATE_LEVELS[test_key]['level'] and  compare_version_tuples(high_version, self._available_versions[test_key]['version']) > 0:
                key = test_key
                high_version = self._available_versions[test_key]['version']
        if key:
            if QMessageBox.information(
                self._parent,
                _("Picard Update"),
                _("A new version of Picard is available.\n\n"
                  "Old version: {picard_old_version}\n"
                  "New version: {picard_new_version}\n\n"
                  "Would you like to download the new version?").format(
                      picard_old_version=PICARD_FANCY_VERSION_STR,
                      picard_new_version=self._available_versions[key]['tag']
                    ),
                QMessageBox.Ok | QMessageBox.Cancel,
                QMessageBox.Cancel
            ) == QMessageBox.Ok:
                wb2.open(self._available_versions[key]['urls']['download'])
        else:
            if self._show_always:
                for key in PROGRAM_UPDATE_LEVELS.keys():
                    if self._update_level == PROGRAM_UPDATE_LEVELS[key]['level']:
                        update_level_text = PROGRAM_UPDATE_LEVELS[key]['title']
                QMessageBox.information(
                    self._parent,
                    _("Picard Update"),
                    _("There is no update currently available for your subscribed update level: {update_level}\n\n"
                      "Your version: {picard_old_version}\n").format(
                        update_level=_(update_level_text if update_level_text else 'unknown'),
                        picard_old_version=PICARD_FANCY_VERSION_STR,
                      ),
                    QMessageBox.Ok, QMessageBox.Ok
                )
