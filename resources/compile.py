#!/usr/bin/env python

import os.path
import subprocess
from distutils import log
from distutils.dep_util import newer


def main():
    scriptdir = os.path.dirname(os.path.abspath(__file__))
    topdir = os.path.abspath(os.path.join(scriptdir, ".."))
    pyfile = os.path.join(topdir, "picard", "resources.py")
    qrcfile = os.path.join(topdir, "resources", "picard.qrc")
    if newer(qrcfile, pyfile):
        log.info("compiling %s -> %s", qrcfile, pyfile)
        subprocess.call(["pyrcc4", qrcfile, "-o", pyfile])

if __name__ == "__main__":
    log.set_verbosity(1)
    main()
