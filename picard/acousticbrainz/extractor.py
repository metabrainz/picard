# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright 2020-2021 Gabriel Ferreira
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

import hashlib
import re

from picard import log
from picard.util import run_executable


def precompute_extractor_sha(essentia_path):
    # Precompute extractor sha1
    h = hashlib.sha1()  # nosec
    h.update(open(essentia_path, "rb").read())
    return h.hexdigest()


def check_extractor_version(essentia_path):
    # returns something like this (at least on windows)
    # 'Error: wrong number of arguments\r\n
    # Usage: streaming_extractor_music.exe input_audiofile output_textfile [profile]\r\n
    # \r\n
    # Music extractor version 'music 1.0'\r\n
    # built with Essentia version v2.1_beta2-1-ge3940c0\r\n
    # \r\n
    # '
    version = None

    try:
        return_code, stdout, stderr = run_executable(essentia_path, timeout=2)
        version_regex = re.compile(r"Essentia version (.*[^ \r\n])")
        version = version_regex.findall(stdout)[0]
    except IndexError:
        log.error("Failed to extract AcousticBrainz feature extractor version")
    except Exception as e:
        log.error("AcousticBrainz extractor failed with error: %s" % e)

    return version
