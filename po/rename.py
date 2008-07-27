#!/usr/bin/env python

import os, shutil

for name in os.listdir('.'):
    if name.startswith('picard-') and name.endswith('.po'):
        newname = name[7:]
	shutil.move(name, newname)
