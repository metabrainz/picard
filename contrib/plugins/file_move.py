# -*- coding: utf-8 -*-

PLUGIN_NAME = u"Copy files instead of moving them"
PLUGIN_AUTHOR = u'Zas'
PLUGIN_DESCRIPTION = "Replace shutil.move() by shutil.copy2()."
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["1.3.0"]

import shutil

from picard.file import register_file_move
from picard import log

def _file_move(old, new):
    log.debug("Copy %r to %r" % (old, new))
    shutil.copy2(old, new)

register_file_move(_file_move)
