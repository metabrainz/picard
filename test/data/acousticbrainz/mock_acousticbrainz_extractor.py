#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Gabriel Ferreira
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


import json
import sys


# remove all arguments with 'py' until the first one without it is found, removing the interpreter and scripts
i = 0
for arg in sys.argv:
    if "py" in arg:
        i += 1
    else:
        break
sys.argv = sys.argv[i:]

if len(sys.argv) != 2:
    message = """Error: wrong number of arguments
Usage: streaming_extractor_music.exe input_audiofile output_textfile [profile]

Music extractor version 'music 1.0'
built with Essentia version v2.1_beta2-1-ge3940c0
"""
    retcode = 1

else:
    if "test.mp3" in sys.argv[0]:
        message = """Process step: Read metadata
Process step: Compute md5 audio hash and codec
Process step: Replay gain
Process step: Compute audio features
Process step: Compute aggregation
All done
Writing results to file out.txt
"""
        retcode = 0
        with open("./test/data/acousticbrainz/acousticbrainz_sample.json", "r", encoding="utf-8") as f:
            ab_features = json.load(f)
        with open(sys.argv[1], "w", encoding="utf-8") as f:
            json.dump(ab_features, f)
    elif "fail.mp3" in sys.argv[0]:
        message = ""
        retcode = 1
    else:
        message = ""
        retcode = 2

print(message)
exit(retcode)
