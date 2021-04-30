#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013-2014, 2018 Laurent Monin
# Copyright (C) 2014 Sophist-UK
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2017 Ville Skyttä
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

"""Build a Qt resources file with all png images found under images/
It will update qrc file only if images newer than it are found
"""

from distutils import log
from distutils.dep_util import newer
import fnmatch
import os
import re


def tryint(s):
    try:
        return int(s)
    except BaseException:
        return s


def natsort_key(s):
    return [tryint(c) for c in re.split(r'(\d+)', s)]


def find_files(topdir, directory, patterns):
    tdir = os.path.join(topdir, directory)
    for root, dirs, files in os.walk(tdir):
        for basename in files:
            for pattern in patterns:
                if fnmatch.fnmatch(basename, pattern):
                    filepath = os.path.join(root, basename)
                    filename = os.path.relpath(filepath, topdir)
                    yield filename


def main():
    scriptdir = os.path.dirname(os.path.abspath(__file__))
    topdir = os.path.abspath(os.path.join(scriptdir, ".."))
    resourcesdir = os.path.join(topdir, "resources")
    qrcfile = os.path.join(resourcesdir, "picard.qrc")
    images = [i for i in find_files(resourcesdir, 'images', ['*.gif', '*.png'])]
    newimages = 0
    for filename in images:
        filepath = os.path.join(resourcesdir, filename)
        if newer(filepath, qrcfile):
            newimages += 1
    if newimages:
        log.info("%d images newer than %s found" % (newimages, qrcfile))
        with open(qrcfile, 'wb+') as f:
            f.write(b'<!DOCTYPE RCC><RCC version="1.0">\n<qresource>\n')
            for filename in sorted(images, key=natsort_key):
                f.write(('    <file>%s</file>\n' % filename.replace('\\', '/')).encode())
            f.write(b'</qresource>\n</RCC>\n')
            log.info("File %s written, %d images" % (qrcfile, len(images)))


if __name__ == "__main__":
    log.set_verbosity(1)
    main()
