#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2023 Philipp Wolfer
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


import argparse
import logging
import os
import os.path
import sys

from wlc import (
    Component,
    Weblate,
)
from wlc.config import WeblateConfig


WEBLATE_URL = 'https://translations.metabrainz.org/api/'
PROJECT_NAME = 'musicbrainz'
PROJECT_COMPONENTS = (
    'attributes',
    'countries',
)
MIN_TRANSLATED_PERCENT = 10


logging.basicConfig(
    force=True,
    format="%(asctime)s:%(levelname)s: %(message)s",
    level=logging.INFO,
    stream=sys.stderr,
)


def fetch_translations(component_name: str, user_key: str = '', config: WeblateConfig = None):
    weblate = Weblate(key=user_key, url=WEBLATE_URL, config=config)
    component = Component(weblate, f'components/{PROJECT_NAME}/{component_name}/')
    logging.info('Processing component %s...', component['name'])
    translations = component.list()
    source_language = component['source_language']['code']
    output_dir = get_output_dir(component_name)
    logging.info('Output dir: %s', output_dir)
    for translation in translations:
        # Skip incomplete translations and translation templates
        language_name = translation['language']['name']
        language_code = translation['language']['code']
        if (translation['translated_percent'] < MIN_TRANSLATED_PERCENT
            or translation['is_template']):
            logging.info('Skipping translation file for %s.', language_name)
            continue

        if language_code == source_language:
            filename = f'{component_name}.pot'
        else:
            filename = f'{language_code}.po'

        logging.info('Downloading translation file %s...', filename)
        data = translation.download()
        output_path = os.path.join(output_dir, filename)
        with open(output_path, 'bw') as output_file:
            output_file.write(data)


def get_output_dir(component_name: str) -> str:
    path = os.path.join(os.path.dirname(__file__), '..', '..', 'po', component_name)
    os.makedirs(path, exist_ok=True)
    return path


def load_config() -> WeblateConfig:
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', '.weblate.ini')
    if os.path.exists:
        config = WeblateConfig()
        config.load(config_path)
        return config
    else:
        return None


def main():
    parser = argparse.ArgumentParser(
        prog='pull-shared-translations',
        description=(
            'Fetches the translations for attributes and countries from '
            'the MusicBrainz Server project on Weblate.'
        ),
        epilog=(
            'Instead of passing the --key parameter the key can also be set in '
            'a file .weblate.ini in the repositories root directory. See '
            'po/README.md for details.'
        ))
    parser.add_argument('-k', '--key', help='Weblate user key')
    args = parser.parse_args()

    config = None
    if not args.key:
        config = load_config()
        if not config:
            parser.print_usage()
            parser.error('No Weblate user key specified. See po/README.md for details.')
        url, key = config.get_url_key()
        if not key or url != WEBLATE_URL:
            parser.print_usage()
            parser.error('Invalid .weblate.ini. See po/README.md for details.')

    for component_name in PROJECT_COMPONENTS:
        fetch_translations(component_name, user_key=args.key, config=config)


if __name__ == '__main__':
    logging.debug("Starting...")
    main()
