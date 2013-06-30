#!/usr/bin/env python

import os, fnmatch
import re
from distutils import log
from distutils.dep_util import newer

"""Build a Qt resources file with all png images found under images/
It will update qrc file only if images newer than it are found
"""

def tryint(s):
    try:
        return int(s)
    except:
        return s

def natsort_key(s):
    return [ tryint(c) for c in re.split('(\d+)', s) ]


def find_files(topdir, directory, pattern):
    tdir = os.path.join(topdir, directory)
    for root, dirs, files in os.walk(tdir):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filepath = os.path.join(root, basename)
                filename = os.path.relpath(filepath, topdir)
                yield filename

def main():
    scriptdir = os.path.dirname(os.path.abspath(__file__))
    topdir = os.path.abspath(os.path.join(scriptdir, ".."))
    resourcesdir = os.path.join(topdir, "resources")
    qrcfile = os.path.join(resourcesdir, "picard.qrc")
    images = [i for i in find_files(resourcesdir, 'images', '*.png')]
    newimages = 0
    for filename in images:
        filepath = os.path.join(resourcesdir, filename)
        if newer(filepath, qrcfile):
            newimages += 1
    if newimages:
        log.info("%d images newer than %s found" % (newimages, qrcfile))
        with open(qrcfile, 'wb+') as f:
            f.write('<!DOCTYPE RCC><RCC version="1.0">\n<qresource>\n')
            for filename in sorted(images, key=natsort_key):
                f.write('    <file>%s</file>\n' % filename)
            f.write('</qresource>\n</RCC>\n')
            log.info("File %s written, %d images" % (qrcfile, len(images)))


if __name__ == "__main__":
    log.set_verbosity(1)
    main()
