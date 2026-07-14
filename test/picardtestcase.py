# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2019-2024 Philipp Wolfer
# Copyright (C) 2020-2024 Laurent Monin
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
import stat
import struct
import sys
from tempfile import (
    mkdtemp,
    mkstemp,
)
import unittest
from unittest.mock import (
    MagicMock,
    Mock,
    patch,
)

from PyQt6 import QtCore

from picard import (
    config,
    log,
)
from picard.formats import DEFAULT_FORMATS
from picard.formats.registry import FormatRegistry
from picard.i18n import setup_i18n
from picard.releasegroup import ReleaseGroup
from picard.tagger import Tagger


class FakeThreadPool(QtCore.QObject):
    def start(self, runnable, priority):
        runnable.run()


def MockTagger():
    tagger = MagicMock(spec=Tagger)
    tagger.thread_pool = FakeThreadPool()
    tagger.priority_thread_pool = FakeThreadPool()
    tagger.get_release_group_by_id = MagicMock(side_effect=lambda rg_id: ReleaseGroup(rg_id))
    tagger.stopping = False
    tagger.files = {}
    tagger.window = MagicMock()
    tagger.webservice = MagicMock()
    return tagger


class PicardTestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        log.set_verbosity(logging.DEBUG)
        setup_i18n(None, 'C')
        self.tagger = MockTagger()
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

    def patch_tagger_instance(self, *modules):
        """Patch tagger_instance in the given module(s) to return self.tagger.

        Usage:
            self.patch_tagger_instance('picard.item')
        """
        for module in modules:
            patcher = patch(f'{module}.tagger_instance', return_value=self.tagger)
            patcher.start()
            self.addCleanup(patcher.stop)

    def patch_app_instance(self, *modules):
        """Patch app_instance in the given module(s) to return self.tagger.

        Usage:
            self.patch_app_instance('picard.plugin3.registry')
        """
        for module in modules:
            patcher = patch(f'{module}.app_instance', return_value=self.tagger)
            patcher.start()
            self.addCleanup(patcher.stop)

    def mktmpdir(self, ignore_errors=False):
        tmpdir = mkdtemp(suffix=self.__class__.__name__)
        self.addCleanup(self._rmtmpdir, tmpdir, ignore_errors=ignore_errors)
        return tmpdir

    @staticmethod
    def _rmtmpdir(tmpdir, ignore_errors=False):
        def _remove_readonly(func, path, _exc_info):
            os.chmod(path, stat.S_IWRITE)
            func(path)

        if sys.version_info >= (3, 12):
            shutil.rmtree(tmpdir, ignore_errors=ignore_errors, onexc=_remove_readonly)
        else:
            shutil.rmtree(tmpdir, ignore_errors=ignore_errors, onerror=_remove_readonly)

    def copy_file_tmp(self, filepath, ext, dir=None):
        fd, copy = mkstemp(suffix=ext, dir=dir)
        os.close(fd)
        self.addCleanup(self.remove_file_tmp, copy)
        shutil.copy(filepath, copy)
        return copy

    @staticmethod
    def remove_file_tmp(filepath):
        if os.path.isfile(filepath):
            os.unlink(filepath)

    def setup_test_format_registry(self):
        self.format_registry = FormatRegistry()
        for format in DEFAULT_FORMATS:
            self.format_registry.register(format)
        self.tagger.format_registry = self.format_registry


def get_test_data_path(*paths):
    return os.path.join('test', 'data', *paths)


def create_fake_png(extra: bytes = b''):
    """Creates fake PNG data that satisfies Picard's internal image type detection"""
    return b'\x89PNG\x0d\x0a\x1a\x0a' + (b'a' * 4) + b'IHDR' + struct.pack('>LL', 100, 100) + extra


def load_test_json(filename):
    with open(get_test_data_path('ws_data', filename), encoding='utf-8') as f:
        return json.load(f)
