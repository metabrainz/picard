#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020 Philipp Wolfer
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

import glob
import json
import os.path

import nshutil as nsh


def language_from_filename(path):
    lang = os.path.splitext(os.path.basename(path))[0]
    return (lang, nsh.language_to_code(lang))


def extract_strings(f):
    for line in f:
        parsed = nsh.parse_langstring(line)
        if parsed:
            yield parsed


def main():
    scriptdir = os.path.dirname(os.path.abspath(__file__))
    sourcesdir = os.path.join(scriptdir, 'sources')
    outdir = os.path.join(scriptdir, 'out')

    for path in glob.glob(os.path.join(outdir, '*.nsh')):
        language, language_code = language_from_filename(path)
        if not language_code:
            print(f'Unknown language "{language}", skipping')
            continue
        target_file = os.path.join(sourcesdir, f'{language_code}.json')
        print(f'{path} => {target_file}')
        with open(path, 'r', encoding='utf-8') as infile:
            output = {}
            for identifier, text in extract_strings(infile):
                output[identifier] = text

            with open(target_file, 'w+', encoding='utf-8') as outfile:
                outfile.write(json.dumps(output, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    main()
