# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Bob Swift
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


from PyQt6.QtCore import QLocale

from picard import (
    PICARD_VERSION,
    log,
)
from picard.config import get_config
from picard.const import (
    READTHEDOCS_BASE_LANGUAGE,
    READTHEDOCS_BASE_VERSION,
    READTHEDOCS_PROJECT_API,
)
from picard.version import Version


class RtdApiItem:
    """ReadTheDocs API item"""

    def __init__(self, title: str, parameter: str):
        self.available_items = set()
        """Available items"""

        self.check_in_progress = False
        """Checking in progress flag"""

        self.title = title
        """Title of the API item"""

        self.parameter = parameter
        """Parameter to use in the API call URL"""


class ReadTheDocs:
    """Provide available documentation information from ReadTheDocs."""

    THROTTLED_MESSAGE = "Request was throttled."
    _webservice = None

    _languages_api = RtdApiItem('languages', 'translations')
    _versions_api = RtdApiItem('versions', 'versions')

    matched_language = READTHEDOCS_BASE_LANGUAGE
    """Best match to available languages"""

    matched_version = READTHEDOCS_BASE_VERSION
    """Best match to available versions"""

    @classmethod
    def initialize(cls, webservice=None):
        """Initializes the class variables after retrieving the available languages
        and versions information from ReadTheDocs.
        Args:
            webservice (WebService, optional): WebService to use for making the calls
            to the ReadTheDocs API. Defaults to None.
        """
        cls._webservice = webservice
        cls.update_documentation_items()

    @classmethod
    def _call_api(cls, api_item: RtdApiItem, handler: callable = None):
        """Call the API to query the selected information.
        Args:
            item (RtdApiItem): Item to query.
            handler (callable): Method to call to process the API response.
        """
        # Only update if webservice defined
        if not cls._webservice:
            log.warning("No webservice defined.")
            return

        # No handler provided
        if not handler:
            log.warning("No API return handler provided for %s query.", api_item.title)
            return

        # Only update once per session (set not empty)
        if api_item.available_items:
            return

        # Update currently in progress
        if api_item.check_in_progress:
            return

        # User has updating disabled
        config = get_config()
        if not config.setting['check_rtd_updates']:
            log.info("Updates disabled in user settings.")
            return

        api_item.check_in_progress = True
        # Set high limit to avoid paging results
        url = READTHEDOCS_PROJECT_API + '/' + api_item.parameter + '/?limit=500'
        log.debug("Getting documentation %s information from %s", api_item.title, url)
        cls._webservice.get_url(
            url=url,
            handler=handler,
            priority=True,
            important=True,
        )

    @classmethod
    def _update_versions(cls):
        """Retrieves the available versions information from ReadTheDocs."""
        cls._call_api(cls._versions_api, handler=cls._versions_json_loaded)

    @classmethod
    def _versions_json_loaded(cls, response, reply, error):
        """Processes response from specified website api query."""
        error_message = "Error loading documentation available versions list: %s"
        if error:
            log.error(error_message, reply.errorString())
        else:
            # Add item to ensure no future update attempts if no active items in results
            cls._versions_api.available_items.add(READTHEDOCS_BASE_VERSION)
            if response:
                if 'detail' in response:
                    log.error(error_message, response['detail'])
                    if response['detail'].startswith(cls.THROTTLED_MESSAGE):
                        # Clear set to allow retrying future update attempts
                        cls._versions_api.available_items = set()

                if 'results' in response:
                    # Add item to ensure no future update attempts if no active items in results
                    for item in response['results']:
                        if 'active' in item and item['active']:
                            cls._versions_api.available_items.add(item['slug'])
                    log.info(f"Available documentation versions: {cls._versions_api.available_items}")
                else:
                    log.error(error_message, "No results returned")

        if cls._versions_api.available_items:
            cls.matched_version = cls._get_version()

        cls._versions_api.check_in_progress = False

    @classmethod
    def _update_languages(cls):
        """Retrieves the available languages information from ReadTheDocs."""
        cls._call_api(cls._languages_api, handler=cls._languages_json_loaded)

    @classmethod
    def _languages_json_loaded(cls, response, reply, error):
        """Processes response from specified website api query."""
        error_message = "Error loading documentation available languages list: %s"
        if error:
            log.error(error_message, reply.errorString())
        else:
            # Add item to ensure no future update attempts if no active items in results
            cls._languages_api.available_items.add(READTHEDOCS_BASE_LANGUAGE)
            if response:
                if 'detail' in response:
                    log.error(error_message, response['detail'])
                    if response['detail'].startswith(cls.THROTTLED_MESSAGE):
                        # Clear set to allow retrying future update attempts
                        cls._languages_api.available_items = set()

                if 'results' in response:
                    for item in response['results']:
                        if 'language' in item and 'code' in item['language']:
                            cls._languages_api.available_items.add(item['language']['code'])
                    log.info(f"Available documentation languages: {cls._languages_api.available_items}")
                else:
                    log.error(error_message, "No results returned")

        if cls._languages_api.available_items:
            cls.matched_language = cls._get_language()

        cls._languages_api.check_in_progress = False

    @classmethod
    def _get_language(cls, language: str = None) -> str:
        """Gets the best match of language to available languages.
        Args:
            language (str, optional): User language to match. Defaults to None.
        Returns:
            str: Closest available documentation language.
        """
        matched_language = READTHEDOCS_BASE_LANGUAGE
        if cls._languages_api.available_items:
            if language is None:
                config = get_config()
                language = config.setting['ui_language'] or QLocale.system().name() or READTHEDOCS_BASE_LANGUAGE

            if language in cls._languages_api.available_items:
                matched_language = language

            else:
                # No exact match found so try matching the base language
                base_language = language.split('_')[0]
                for lang in sorted(cls._languages_api.available_items):
                    if lang.startswith(base_language):
                        matched_language = lang
                        break

            log.debug("Matched documentation language set to '%s'", matched_language)

        return matched_language

    @classmethod
    def _get_version(cls, version: Version = None) -> str:
        """Gets the best match of version to available versions.
        Args:
            version (Version, optional): Program version to match. Defaults to None.
        Returns:
            str: Closest available documentation version.
        """
        matched_version = READTHEDOCS_BASE_VERSION
        if cls._versions_api.available_items:
            if version is None:
                version = PICARD_VERSION

            rtd_version = f"v{version.major}.{version.minor}"
            if version.identifier == 'final' and rtd_version in cls._versions_api.available_items:
                matched_version = rtd_version

            log.debug("Matched documentation version set to '%s'", matched_version)

        return matched_version

    @classmethod
    def update_documentation_items(cls):
        """Updates the available languages and versions from the ReadTheDocs API if required,
        and updates the best matched language and version variables."""
        cls._update_languages()
        cls._update_versions()
        cls.matched_language = cls._get_language()
        cls.matched_version = cls._get_version()
