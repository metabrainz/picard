#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2013-2014, 2018 Laurent Monin
# Copyright (C) 2014 Shadab Zafar
# Copyright (C) 2016 Sambhav Kothari
# Copyright (C) 2022-2024 Philipp Wolfer
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

from distutils import log
from distutils.spawn import (
    DistutilsExecError,
    spawn,
)
import os.path

from setuptools.modified import newer


def main():
    scriptdir = os.path.dirname(os.path.abspath(__file__))
    topdir = os.path.abspath(os.path.join(scriptdir, ".."))
    pyfile = os.path.join(topdir, "picard", "resources.py")
    qrcfile = os.path.join(topdir, "resources", "picard.qrc")
    if newer(qrcfile, pyfile):
        cmd = ['pyside6-rcc', '-o', pyfile, qrcfile]
        try:
            spawn(cmd, search_path=0)
        except DistutilsExecError as e:
            log.error(e)


if __name__ == "__main__":
    log.set_verbosity(1)
    main()
