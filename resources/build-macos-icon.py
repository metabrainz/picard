#!/usr/bin/env python
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Philipp Wolfer
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.

from collections.abc import Generator
from contextlib import contextmanager
import logging
from pathlib import Path
import shutil
import subprocess
import tempfile


SIZES = (16, 32, 128, 256, 512)


log = logging.getLogger(__name__)
resources_dir = Path(__file__).resolve().parent


@contextmanager
def create_iconset_temp_dir() -> Generator[Path]:
    iconset_dir = 'picard.iconset'
    with tempfile.TemporaryDirectory() as tmpdir:
        iconset_path = Path(tmpdir) / iconset_dir
        iconset_path.mkdir()
        yield iconset_path


def copy_icon(size: int, iconset_path: Path) -> None:
    image_path = resources_dir / 'images'
    for suffix in ('', '@2x'):
        filename = f'icon_{size}{suffix}.png'
        print(f'Copying {filename}...')
        source_file = image_path / f'{size}x{size}' / f'macos_{filename}'
        dest_file = iconset_path / filename
        shutil.copy(source_file, dest_file)


def run_iconutil(iconset_path: Path) -> None:
    outfile = resources_dir.parent / 'picard.icns'
    cmd = ['iconutil', '-c', 'icns', str(iconset_path), '-o', str(outfile)]
    print(f'Running {" ".join(cmd)}')
    subprocess.check_call(cmd)


def build_iconset():
    with create_iconset_temp_dir() as iconset_path:
        for size in SIZES:
            copy_icon(size, iconset_path)

        run_iconutil(iconset_path)


def main():
    print("Building macOS icon set...")
    build_iconset()


if __name__ == "__main__":
    main()
