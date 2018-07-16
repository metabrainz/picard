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

from picard import (PICARD_VERSION, tagger, log, version_from_string, version_to_string, config)
import picard.util.webbrowser2 as wb2
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox
from picard.util import load_json, compare_version_tuples
from functools import partial
import re
import datetime


# Used to strip leading and trailing text from version string.
_RE_CLEAN_VERSION = re.compile('^[^0-9]*(.*)[^0-9]*$', re.IGNORECASE)


# GitHub API information
GITHUB_API = {
    'host': 'api.github.com',
    'port': 443,
    'endpoint': {
        'releases': '/repos/metabrainz/picard/releases',
        'tags': '/repos/metabrainz/picard/git/refs/tags'
    }
}


class UpdateCheckManager(QtCore.QObject):

    def __init__(self):
        super().__init__()

        # Version tuple format:  str.key: ( str.version, ( int.major, int.minor, int.micro, str.type, int.development ), str.title, str.url )
        self._available_versions = {
            'stable': ('', (0, 0, 0, 'dev', 0), '', ''),
            'beta': ('', (0, 0, 0, 'dev', 0), '', ''),
            'dev': ('', (0, 0, 0, 'dev', 0), '', ''),
        }
        self._show_always = False
        self._update_level = 'dev'

    def check_update(self, show_always=False, update_level='dev', callback=None):
        '''Checks if an update is available.

        Compares the version number of the currently running instance of Picard
        and displays a dialog box informing the user  if an update is available,
        with an option of opening the Picard site in the browser to download the
        update.  If there is no update available, no dialog will be shown unless
        the "show_always" parameter has been set to True.  This allows for silent
        checking during startup if so configured.

        Args:
            show_always: Boolean value indicating whether the results dialog
                should be shown even when there is no update available.
            update_level: Determines what type of updates to check.  If set to
                'final' only stable release versions are checked.  If set to
                'dev' both beta and stable releases are checked.
            callback: Optional callback function.

        Returns:
            none.

        Raises:
            none.
        '''
        self._show_always = show_always
        self._update_level = update_level

        # Gets list of releases from GitHub website api.
        output_text = _("Getting release information from GitHub.")
        log.debug(output_text)
        self.tagger.webservice.get(
            GITHUB_API['host'],
            GITHUB_API['port'],
            GITHUB_API['endpoint']['releases'],
            partial(self._releases_json_loaded, callback=callback),
            parse_response_type=None,
            priority=True,
            important=True
        )

    @property
    def available_versions(self):
        '''Provide a list of the latest version tuples for each type.'''
        return self._available_versions

    def query_available_updates(self, callback=None):
        '''Gets list of releases from GitHub website api.'''
        output_text = _("Getting release information from GitHub.")
        log.debug(output_text)
        self.tagger.webservice.get(
            GITHUB_API['host'],
            GITHUB_API['port'],
            GITHUB_API['endpoint']['releases'],
            partial(self._releases_json_loaded, callback=callback),
            parse_response_type=None,
            priority=True,
            important=True
        )

    def _releases_json_loaded(self, response, reply, error, callback=None):
        '''Processes response from GitHub api query.'''
        if error:
            tagger.window.set_statusbar_message(
                N_("Error loading releases list: %(error)s"),
                {'error': reply.errorString()},
                echo=log.error
            )
        else:
            config.persist['last_update_check'] = datetime.date.today().toordinal()
            releases = load_json(response)

            for release in releases:
                ver = version_from_string(
                    _RE_CLEAN_VERSION.findall(release['tag_name'])[0])
                key = 'beta' if release['prerelease'] else 'stable'
                if compare_version_tuples(self._available_versions[key][1], ver) > 0:
                    self._available_versions[key] = (version_to_string(
                        ver, short=True), ver, release['name'], release['html_url'],)
            for key in self._available_versions.keys():
                log.debug("Version key '%s' --> %s" %
                          (key, self._available_versions[key],))

        # Display results to user.
        msg_title = _("Picard Update")
        if (compare_version_tuples(PICARD_VERSION, self._available_versions['stable'][1]) > 0) | (
                (compare_version_tuples(PICARD_VERSION, self._available_versions['beta'][1]) > 0) & (self._update_level == 'dev')):
            key = 'beta' if (compare_version_tuples(self._available_versions['stable'][1],
                                                    self._available_versions['beta'][1]) > 0) & (self._update_level == 'dev') else 'stable'
            msg_text = _("A new version of Picard is available.\n\nNew version: %s (%s)\n\n"
                         "Would you like to download the new version?") % (self._available_versions[key][2],
                                                                           self._available_versions[key][0])
            if QMessageBox.information(None, msg_title, msg_text, QMessageBox.Ok | QMessageBox.Cancel,
                                       QMessageBox.Cancel) == QMessageBox.Ok:
                wb2.open(self._available_versions[key][3])
        else:
            if self._show_always:
                msg_text = _("There is no update currently available.")
                QMessageBox.information(
                    None, msg_title, msg_text, QMessageBox.Ok, QMessageBox.Ok)
        if callback:
            callback()
