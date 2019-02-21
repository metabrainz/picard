# -*- coding: utf-8 -*-
import struct
import unittest

from PyQt5 import QtCore

from picard import (
    config,
    log,
)


class FakeTagger(QtCore.QObject):

    tagger_stats_changed = QtCore.pyqtSignal()

    def __init__(self):
        QtCore.QObject.__init__(self)
        QtCore.QObject.config = config
        QtCore.QObject.log = log
        self.tagger_stats_changed.connect(self.emit)
        self.exit_cleanup = []
        self.files = {}

    def register_cleanup(self, func):
        self.exit_cleanup.append(func)

    def run_cleanup(self):
        for f in self.exit_cleanup:
            f()

    def emit(self, *args):
        pass


class PicardTestCase(unittest.TestCase):
    def setUp(self):
        QtCore.QObject.tagger = FakeTagger()
        config.setting = {}


def create_fake_png(extra):
    """Creates fake PNG data that satisfies Picard's internal image type detection"""
    return b'\x89PNG\x0D\x0A\x1A\x0A' + (b'a' * 4) + b'IHDR' + struct.pack('>LL', 100, 100) + extra
