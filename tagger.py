#!/usr/bin/env python

import os.path
import sys
import sip

sip.setapi("QString", 2)
sip.setapi("QVariant", 2)

sys.path.insert(0, '.')
from picard.tagger import main

localedir = os.path.join(os.path.dirname(sys.argv[0]), 'locale')
main(localedir, True)
