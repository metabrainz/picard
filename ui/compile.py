#!/usr/bin/env python

from PyQt4 import uic
import glob
import os.path

print "Compiling UI files..."
for uifile in glob.glob("*.ui"):
    pyfile = "ui_%s.py" % os.path.splitext(os.path.basename(uifile))[0]
    pyfile = os.path.join("..", "picard", "ui", pyfile)
    print " * %s => %s" % (uifile, pyfile)
    uic.compileUi(uifile, file(pyfile, "w"), translator="_")

