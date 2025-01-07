#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2013-2014, 2018, 2020 Laurent Monin
# Copyright (C) 2014 Shadab Zafar
# Copyright (C) 2016 Sambhav Kothari
# Copyright (C) 2022 Philipp Wolfer
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
from distutils.dep_util import newer
from distutils.spawn import (
    DistutilsExecError,
    find_executable,
    spawn,
)
import os.path


def fix_qtcore_import(path):
    with open(path, 'r') as f:
        data = f.read()
    data = data.replace('PySide6', 'PyQt6')
    with open(path, 'w') as f:
        f.write(data)


def main():
    scriptdir = os.path.dirname(os.path.abspath(__file__))
    topdir = os.path.abspath(os.path.join(scriptdir, ".."))
    pyfile = os.path.join(topdir, "picard", "resources.py")
    qrcfile = os.path.join(topdir, "resources", "picard.qrc")
    if newer(qrcfile, pyfile):
        rcc = 'rcc'
        rcc_path = find_executable(rcc, path='/usr/lib/qt6/libexec/') or find_executable(rcc)
        if rcc_path is None:
            log.error("%s command not found, cannot build resource file !", rcc)
        else:
            cmd = [rcc_path, '-g', 'python', '-o', pyfile, qrcfile]
            try:
                spawn(cmd, search_path=0)
                fix_qtcore_import(pyfile)
            except DistutilsExecError as e:
                log.error(e)


if __name__ == "__main__":
    log.set_verbosity(1)
    main()
