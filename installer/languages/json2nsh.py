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
    return (nsh.code_to_language(lang), lang)


def write_langstring(f, language, identifier, text):
    langstring = nsh.make_langstring(language, identifier, text)
    f.write(langstring)


def merge_translations(*translations):
    merged = {}
    for trans in translations:
        for k, v in trans.items():
            if v:
                merged[k] = v
    return merged


def main():
    scriptdir = os.path.dirname(os.path.abspath(__file__))
    sourcesdir = os.path.join(scriptdir, 'sources')
    outdir = os.path.join(scriptdir, 'out')
    os.makedirs(outdir, exist_ok=True)

    # Read the english sources for defaults
    with open(os.path.join(sourcesdir, 'en.json'), 'r', encoding='utf-8') as infile:
        data_en = json.loads(infile.read())

    for path in glob.glob(os.path.join(sourcesdir, '*.json')):
        language, language_code = language_from_filename(path)
        if not language:
            print(f'Unknown language code "{language_code}", skipping')
            continue
        target_file = os.path.join(outdir, f'{language}.nsh')
        print(f'{path} => {target_file}')
        with open(path, 'r', encoding='utf-8') as infile:
            data = json.loads(infile.read())
            data = merge_translations(data_en, data)
            with open(target_file, 'w+', encoding='utf-8') as outfile:
                for identifier, text in data.items():
                    write_langstring(outfile, language, identifier, text)


if __name__ == "__main__":
    main()
