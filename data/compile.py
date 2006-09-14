#!/usr/bin/env python

import os.path

pyfile = os.path.join("..", "picard", "resources.py")
os.system("pyrcc4 picard.qrc -o %s" % pyfile)

