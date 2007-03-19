#!/usr/bin/env python

import os.path
import sys

sys.path.insert(0, '.')
from picard.tagger import main

localedir = os.path.join(os.path.dirname(sys.argv[0]), 'locale')
main(localedir, True)

