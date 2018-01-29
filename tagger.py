#!/usr/bin/env python3

import os.path
import sys

sys.path.insert(0, '.')

from picard.tagger import main

# This is needed to find resources when using pyinstaller
if getattr(sys, 'frozen', False):
    basedir = sys._MEIPASS
else:
    basedir = os.path.dirname(os.path.abspath(__file__))

main(os.path.join(basedir, 'locale'), True)
