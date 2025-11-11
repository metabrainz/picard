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


class ReadTheDocs:
    """Provide available documentation information from ReadTheDocs."""

    THROTTLED_MESSAGE = "Request was throttled."
    _webservice = None
    _api_calls = None

    available = {
        'languages': set(),
        'versions': set(),
    }
    """Available languages and versions."""

    matched_language = READTHEDOCS_BASE_LANGUAGE
    """Best match to available languages"""

    matched_version = READTHEDOCS_BASE_VERSION
    """Best match to available versions"""

    _checking_flags = {
        'languages': False,
        'versions': False,
    }
    """Flags indicating check is in progress"""

    @classmethod
    def initialize(cls, webservice=None):
        """Initializes the class variables after retrieving the available languages
        and versions information from ReadTheDocs.

        Args:
            webservice (WebService, optional): WebService to use for making the calls
            to the ReadTheDocs API. Defaults to None.
        """
        cls._webservice = webservice
        cls._api_calls = {
            'languages': {
                'parameter': 'translations',
                'handler': cls._languages_json_loaded,
            },
            'versions': {
                'parameter': 'versions',
                'handler': cls._versions_json_loaded,
            },
        }
        cls.update_documentation_items()

    @classmethod
    def _call_api(cls, query: str):
        """Call the API to query the selected information.

        Args:
            query (str): Information to query.
        """
        # Unknown API query
        if not cls._api_calls or query not in cls._api_calls:
            return

        # Only update if webservice defined
        if not cls._webservice:
            return

        # Only update once per session
        if cls.available[query]:
            return

        # Update currently in progress
        if cls._checking_flags[query]:
            return

        # User has updating disabled
        config = get_config()
        if not config.setting['check_rtd_updates']:
            return

        cls._checking_flags[query] = True
        # Set high limit to avoid paging results
        url = READTHEDOCS_PROJECT_API + '/' + cls._api_calls[query]['parameter'] + '/?limit=500'
        log.debug("Getting documentation %s information from %s", query, url)
        cls._webservice.get_url(
            url=url,
            handler=cls._api_calls[query]['handler'],
            priority=True,
            important=True,
        )

    @classmethod
    def _update_versions(cls):
        """Retrieves the available versions information from ReadTheDocs."""
        cls._call_api('versions')

    @classmethod
    def _versions_json_loaded(cls, response, reply, error):
        """Processes response from specified website api query."""
        error_message = "Error loading documentation available versions list: %s"
        if error:
            log.error(error_message, reply.errorString())
        else:
            # Add item to ensure no future update attempts if no active items in results
            cls.available['versions'].add(READTHEDOCS_BASE_VERSION)
            if response:
                if 'detail' in response:
                    log.error(error_message, response['detail'])
                    if response['detail'].startswith(cls.THROTTLED_MESSAGE):
                        # Clear set to allow retrying future update attempts
                        cls.available['versions'] = set()

                if 'results' in response:
                    # Add item to ensure no future update attempts if no active items in results
                    for item in response['results']:
                        if 'active' in item and item['active']:
                            cls.available['versions'].add(item['slug'])
                    log.info(f"Available documentation versions: {cls.available['versions']}")
                else:
                    log.error(error_message, "No results returned")

        if cls.available['versions']:
            cls.matched_version = cls._get_version()

        cls._version_checking = False

    @classmethod
    def _update_languages(cls):
        """Retrieves the available languages information from ReadTheDocs."""
        cls._call_api('languages')

    @classmethod
    def _languages_json_loaded(cls, response, reply, error):
        """Processes response from specified website api query."""
        error_message = "Error loading documentation available languages list: %s"
        if error:
            log.error(error_message, reply.errorString())
        else:
            # Add item to ensure no future update attempts if no active items in results
            cls.available['languages'].add(READTHEDOCS_BASE_LANGUAGE)
            if response:
                if 'detail' in response:
                    log.error(error_message, response['detail'])
                    if response['detail'].startswith(cls.THROTTLED_MESSAGE):
                        # Clear set to allow retrying future update attempts
                        cls.available['languages'] = set()

                if 'results' in response:
                    for item in response['results']:
                        if 'language' in item and 'code' in item['language']:
                            cls.available['languages'].add(item['language']['code'])
                    log.info(f"Available documentation languages: {cls.available['languages']}")
                else:
                    log.error(error_message, "No results returned")

        if cls.available['languages']:
            cls.matched_language = cls._get_language()

        cls._language_checking = False

    @classmethod
    def _get_language(cls, language: str = None) -> str:
        """Gets the best match of language to available languages.

        Args:
            language (str, optional): User language to match. Defaults to None.

        Returns:
            str: Closest available documentation language.
        """
        if not cls.available['languages']:
            # Languages not updated from the ReadTheDocs API
            return READTHEDOCS_BASE_LANGUAGE

        if language is None:
            config = get_config()
            language = config.setting['ui_language'] or QLocale.system().name() or READTHEDOCS_BASE_LANGUAGE

        if language in cls.available['languages']:
            return language

        # No exact match found so try matching the base language
        base_language = language.split('_')[0]
        for lang in sorted(cls.available['languages']):
            if lang.startswith(base_language):
                return lang

        return READTHEDOCS_BASE_LANGUAGE

    @classmethod
    def _get_version(cls, version: Version = None) -> str:
        """Gets the best match of version to available versions.

        Args:
            version (Version, optional): Program version to match. Defaults to None.

        Returns:
            str: Closest available documentation version.
        """
        if not cls.available['versions']:
            # Versions not updated from the ReadTheDocs API
            return READTHEDOCS_BASE_VERSION

        if version is None:
            version = PICARD_VERSION

        rtd_version = f"v{version.major}.{version.minor}"
        if version.identifier != 'final' or rtd_version not in cls.available['versions']:
            return READTHEDOCS_BASE_VERSION

        return rtd_version

    @classmethod
    def update_documentation_items(cls):
        """Updates the available languages and versions from the ReadTheDocs API if required,
        and updates the best matched language and version variables."""
        cls._update_languages()
        cls._update_versions()
        cls.matched_language = cls._get_language()
        cls.matched_version = cls._get_version()
