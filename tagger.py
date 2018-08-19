#!/usr/bin/env python3

import os.path
import sys

from picard.tagger import main
from picard.util import (
    frozen_temp_path,
    is_frozen,
)

sys.path.insert(0, '.')



# This is needed to find resources when using pyinstaller
if is_frozen:
    basedir = frozen_temp_path
else:
    basedir = os.path.dirname(os.path.abspath(__file__))

main(os.path.join(basedir, 'locale'), True)
