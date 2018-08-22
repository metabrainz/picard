#!/usr/bin/env python

from distutils import log
from distutils.dep_util import newer
from distutils.spawn import (
    DistutilsExecError,
    find_executable,
    spawn,
)
import os.path


def main():
    scriptdir = os.path.dirname(os.path.abspath(__file__))
    topdir = os.path.abspath(os.path.join(scriptdir, ".."))
    pyfile = os.path.join(topdir, "picard", "resources.py")
    qrcfile = os.path.join(topdir, "resources", "picard.qrc")
    if newer(qrcfile, pyfile):
        pyrcc = 'pyrcc5'
        pyrcc_path = find_executable(pyrcc)
        if pyrcc_path is None:
            log.error("%s command not found, cannot build resource file !", pyrcc)
        else:
            cmd = [pyrcc_path, qrcfile, "-o", pyfile]
            try:
                spawn(cmd, search_path=0)
            except DistutilsExecError as e:
                log.error(e)


if __name__ == "__main__":
    log.set_verbosity(1)
    main()
