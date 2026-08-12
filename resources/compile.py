#!/usr/bin/env python
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2013-2014, 2018, 2020, 2026 Laurent Monin
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


import logging
import os
from pathlib import Path
from shutil import which
import subprocess
import sys
import tempfile


log = logging.getLogger(__name__)


def fix_qtcore_import(path):
    data = path.read_text()
    data = data.replace('from PySide6', 'from PyQt6')
    path.write_text(data)


def find_rcc():
    """Find the Qt6 rcc binary."""
    rcc = 'rcc'
    for path in (
        '/usr/lib64/qt6/libexec',
        '/usr/lib/qt6/libexec',
    ):
        rcc_path = which(rcc, path=path)
        if rcc_path:
            return rcc_path
    return which(rcc)


def main():
    topdir = Path(__file__).resolve().parent.parent
    pyfile = topdir / "picard" / "resources.py"
    qrcfile = topdir / "resources" / "picard.qrc"
    rcc_path = find_rcc()
    if rcc_path is None:
        log.error("rcc command not found, cannot build resource file!")
        sys.exit(1)
    if not pyfile.exists() or qrcfile.stat().st_mtime > pyfile.stat().st_mtime:
        log.info("Using rcc: %s", rcc_path)
        fd, tmp_name = tempfile.mkstemp(dir=pyfile.parent, suffix='.tmp')
        os.close(fd)
        tmp_path = Path(tmp_name)
        try:
            cmd = [rcc_path, '-g', 'python', '-o', str(tmp_path), str(qrcfile)]
            subprocess.check_call(cmd)
            fix_qtcore_import(tmp_path)
            tmp_path.replace(pyfile)
        except BaseException:
            tmp_path.unlink(missing_ok=True)
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
