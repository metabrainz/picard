#!/usr/bin/env python3

import os
import sys

IS_WIN = sys.platform == 'win32'

# On Windows try to attach to the console as early as possible in order
# to get stdout / stderr logged to console. This needs to happen before
# logging gets imported.
# See https://stackoverflow.com/questions/54536/win32-gui-app-that-writes-usage-text-to-stdout-when-invoked-as-app-exe-help
if IS_WIN:
    from ctypes import windll
    if windll.kernel32.AttachConsole(-1):
        sys.stdout = open('CON', 'w')
        sys.stderr = open('CON', 'w')

sys.path.insert(0, '.')

# This is needed to find resources when using pyinstaller
if getattr(sys, 'frozen', False):
    basedir = getattr(sys, '_MEIPASS', '')
else:
    basedir = os.path.dirname(os.path.abspath(__file__))

if IS_WIN:
    os.environ['PATH'] = basedir + ';' + os.environ['PATH']

from picard.tagger import main
main(os.path.join(basedir, 'locale'), True)
