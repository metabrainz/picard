# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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


"""Check that the picard-cli PyInstaller build bundles every subcommand module.

picard-cli loads its subcommands with importlib.import_module(), which
PyInstaller's static analysis cannot see (PICARD-3478). This runs only the
Analysis() phase of picard.spec, without producing any artifact, and fails if a
module listed in picard.cli.SUBCOMMANDS would be missing from the picard-cli
bundle. Run it from the repository root, before `pyinstaller picard.spec`.
"""

from pathlib import PurePath
import sys
import tempfile
from unittest import mock

import PyInstaller.__main__
from PyInstaller.building import (
    api,
    build_main,
)


sys.path.insert(0, '.')
from picard.cli import SUBCOMMANDS  # noqa: E402


CLI_ENTRY_POINT = 'picard/cli/__main__.py'
SPEC_FILE = 'picard.spec'


class _Skipped:
    """Stand-in for the build steps that produce artifacts (PYZ, EXE, COLLECT)."""

    def __init__(self, *args, **kwargs):
        pass


def _run_analyses():
    """Run SPEC_FILE with only Analysis() active, return (entry scripts, module names) for each."""
    original_analysis = build_main.Analysis
    results = []

    class RecordingAnalysis(original_analysis):
        def __init__(self, scripts, *args, **kwargs):
            super().__init__(scripts, *args, **kwargs)
            results.append(([PurePath(script).as_posix() for script in scripts], {name for name, *_ in self.pure}))

    with (
        mock.patch.object(build_main, 'Analysis', RecordingAnalysis),
        mock.patch.object(api, 'PYZ', _Skipped),
        mock.patch.object(api, 'EXE', _Skipped),
        mock.patch.object(api, 'COLLECT', _Skipped),
        tempfile.TemporaryDirectory() as tmpdir,
    ):
        PyInstaller.__main__.run(
            ['--noconfirm', '--log-level', 'WARN', '--workpath', tmpdir, '--distpath', tmpdir, SPEC_FILE]
        )
    return results


def main():
    cli_modules = [modules for scripts, modules in _run_analyses() if CLI_ENTRY_POINT in scripts]
    if not cli_modules:
        # e.g. portable or macOS builds don't include picard-cli
        print(f"No picard-cli build in {SPEC_FILE}, nothing to check")
        return 0

    missing = [cmd.module_path for cmd in SUBCOMMANDS if cmd.module_path not in cli_modules[0]]
    if missing:
        print(f"ERROR: picard-cli would be built without its subcommand modules: {', '.join(missing)}", file=sys.stderr)
        print(f"Add them to the picard-cli hiddenimports in {SPEC_FILE} (see PICARD-3478)", file=sys.stderr)
        return 1

    print(f"OK: picard-cli bundles all {len(SUBCOMMANDS)} subcommand modules")
    return 0


if __name__ == '__main__':
    sys.exit(main())
