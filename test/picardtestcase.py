# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2019-2023 Philipp Wolfer
# Copyright (C) 2020-2021 Laurent Monin
# Copyright (C) 2021 Bob Swift
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


import json
import logging
import os
import shutil
import struct
from tempfile import (
    mkdtemp,
    mkstemp,
)
import unittest
from unittest.mock import Mock

from PyQt5 import QtCore

from picard import (
    config,
    log,
)
from picard.releasegroup import ReleaseGroup


class FakeThreadPool(QtCore.QObject):

    def start(self, runnable, priority):
        runnable.run()


class FakeTagger(QtCore.QObject):

    tagger_stats_changed = QtCore.pyqtSignal()

    def __init__(self):
        QtCore.QObject.__init__(self)
        QtCore.QObject.config = config
        QtCore.QObject.log = log
        self.tagger_stats_changed.connect(self.emit)
        self.exit_cleanup = []
        self.files = {}
        self.stopping = False
        self.thread_pool = FakeThreadPool()
        self.priority_thread_pool = FakeThreadPool()

    def register_cleanup(self, func):
        self.exit_cleanup.append(func)

    def run_cleanup(self):
        for f in self.exit_cleanup:
            f()

    def emit(self, *args):
        pass

    def get_release_group_by_id(self, rg_id):  # pylint: disable=no-self-use
        return ReleaseGroup(rg_id)


class PicardTestCase(unittest.TestCase):
    def setUp(self):
        log.set_level(logging.DEBUG)
        self.tagger = FakeTagger()
        QtCore.QObject.tagger = self.tagger
        QtCore.QCoreApplication.instance = lambda: self.tagger
        self.addCleanup(self.tagger.run_cleanup)
        self.init_config()

    @staticmethod
    def init_config():
        fake_config = Mock()
        fake_config.setting = {}
        fake_config.persist = {}
        fake_config.profiles = {}
        # Make config object available for legacy use
        config.config = fake_config
        config.setting = fake_config.setting
        config.persist = fake_config.persist
        config.profiles = fake_config.profiles

    @staticmethod
    def set_config_values(setting=None, persist=None, profiles=None):
        if setting:
            for key, value in setting.items():
                config.config.setting[key] = value
        if persist:
            for key, value in persist.items():
                config.config.persist[key] = value
        if profiles:
            for key, value in profiles.items():
                config.config.profiles[key] = value

    def mktmpdir(self, ignore_errors=False):
        tmpdir = mkdtemp(suffix=self.__class__.__name__)
        self.addCleanup(shutil.rmtree, tmpdir, ignore_errors=ignore_errors)
        return tmpdir

    def copy_file_tmp(self, filepath, ext):
        fd, copy = mkstemp(suffix=ext)
        os.close(fd)
        self.addCleanup(self.remove_file_tmp, copy)
        shutil.copy(filepath, copy)
        return copy

    @staticmethod
    def remove_file_tmp(filepath):
        if os.path.isfile(filepath):
            os.unlink(filepath)


def get_test_data_path(*paths):
    return os.path.join('test', 'data', *paths)


def create_fake_png(extra):
    """Creates fake PNG data that satisfies Picard's internal image type detection"""
    return b'\x89PNG\x0D\x0A\x1A\x0A' + (b'a' * 4) + b'IHDR' + struct.pack('>LL', 100, 100) + extra


def load_test_json(filename):
    with open(get_test_data_path('ws_data', filename), encoding='utf-8') as f:
        return json.load(f)
