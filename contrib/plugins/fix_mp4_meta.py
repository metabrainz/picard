# -*- coding: utf-8 -*-

PLUGIN_NAME = u"Fix MP4 'meta' atoms"
PLUGIN_AUTHOR = u"Lukáš Lalinský"
PLUGIN_DESCRIPTION = """Fix lengths of 'meta' atoms in MP4 files. If you
don't know why would you need this, you probably don't want to use this
plugin. If you do want to use it, don't forget to <b>backup your files</b>
before.
"""
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.9.0", "0.10"]


import struct
from PyQt4 import QtCore
from mutagen import mp4
from picard.file import File
from picard.util import encode_filename
from picard.ui.itemviews import BaseAction, register_file_action


class FixMp4Meta(BaseAction):
    NAME = "Fix MP4 'meta' atoms..."

    def fix(self, filename):
        fileobj = open(filename, "rb+")
        modified = False
        try:
            atoms = mp4.Atoms(fileobj)
            try:
                path = atoms.path("moov", "udta", "meta")
            except KeyError:
                pass
            else:
                for atom in reversed(path):
                    size = (sum(c.length for c in atom.children) + 8 +
                            mp4._SKIP_SIZE.get(atom.name, 0))
                    if size != atom.length:
                        fileobj.seek(atom.offset)
                        fileobj.write(struct.pack(">I", size))
                        atom.length = size
                        modified = True
        finally:
            fileobj.close()
        return modified

    def callback(self, objs):
        files = [o for o in objs if isinstance(o, File)]
        for file in files:
            if self.fix(encode_filename(file.filename)):
                self.log.info("fix_mp4_meta: %s - Fixed", file.filename)
            else:
                self.log.info("fix_mp4_meta: %s - Not needed", file.filename)
            QtCore.QCoreApplication.processEvents()


register_file_action(FixMp4Meta())
