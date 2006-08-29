#!/usr/bin/env python

import os.path
import sys

sys.path.insert(0, '.')
from picard.tagger import main

localeDir = os.path.join(os.path.dirname(sys.argv[0]), 'locale')
main(localeDir)

