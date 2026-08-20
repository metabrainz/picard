# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020-2021 Philipp Wolfer
# Copyright (C) 2020-2022 Laurent Monin
# Copyright (C) 2024 Giorgio Fontanive
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


import os
from pathlib import Path
import re
import shutil
import tempfile
from unittest.mock import Mock

from picard.coverart.image import LocalFileCoverArtImage
from picard.coverart.providers.local import CoverArtProviderLocal

import pytest


@pytest.fixture
def testdir():
    tmpdir = Path(tempfile.mkdtemp())
    Path(tmpdir / 'cover.jpg').touch()
    Path(tmpdir / 'artwork').mkdir()
    Path(tmpdir / 'artwork/cover.jpg').touch()
    Path(tmpdir / 'artwork/cover.png').touch()
    Path(tmpdir / 'artwork/back.png').touch()
    yield str(tmpdir)
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.mark.parametrize(
    ("pattern", "expected_paths"),
    [
        (r"nomatch", []),
        (r"cover\.jpg", ['cover.jpg', 'artwork/cover.jpg']),
        (r"cover\.png", ['artwork/cover.png']),
        (r"cover\.(jpg|png)", ['cover.jpg', 'artwork/cover.png', 'artwork/cover.jpg']),
        (r"^artwork/.*\.png$", ['artwork/cover.png', 'artwork/back.png']),
        (r"^artwork/.*\.gif$", []),
        (r"^artwork/back\.png$", ['artwork/back.png']),
    ],
)
def test_find_local_images(testdir, pattern, expected_paths):
    provider = CoverArtProviderLocal(Mock())
    images = list(provider.find_local_images(testdir, re.compile(pattern)))
    assert all(isinstance(image, LocalFileCoverArtImage) for image in images)
    found_paths = set(os.path.normpath(image.url.toLocalFile()) for image in images if image.url)
    expected_paths = set(os.path.normpath(os.path.join(testdir, path)) for path in expected_paths)
    assert found_paths == expected_paths
