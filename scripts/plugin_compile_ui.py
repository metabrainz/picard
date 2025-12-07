#!/usr/bin/env python3
"""Convert Qt6 .ui files into Python files for use by Picard plugins.

Usage:
    plugin_compile_ui.py --help
    plugin_compile_ui.py <ui_file>

Options:
    -h, --help   show this help message and exit
    --force, -f  Force compilation even if up-to-date

Examples:
    # Compile ui_options.ui to ui_options.py
    plugin_compile_ui.py /path/to/plugin/ui_options.ui
"""

import argparse
from io import StringIO
import os
from pathlib import Path
import re
import sys

from PyQt6 import uic


def compile_ui(ui_file: Path, py_file: Path) -> None:
    print(f"compiling {ui_file} -> {py_file}")
    tmp_out = StringIO()
    uic.compileUi(str(ui_file), tmp_out)
    output = tmp_out.getvalue()
    output = rewrite_ui_code(output)
    with open(py_file, "w") as f:
        f.write(output)


def newer(file1: Path, file2: Path) -> bool:
    """Returns True, if file1 has been modified after file2"""
    if not file2.exists():
        return True
    return os.path.getmtime(file1) > os.path.getmtime(file2)


replacements = (
    (re.compile(r'(from PyQt6.*)'), r'\1\n\nfrom picard.plugin3 import PluginApi'),
    (
        re.compile(r'QtCore\.QCoreApplication.translate'),
        'PluginApi.get_api().tr',
    ),
    (re.compile(r'\b_translate\(.*?, (.*?)(?:, None)?\)'), r'_translate(\1)'),
)


def rewrite_ui_code(ui_code: str) -> str:
    for pattern, replace in replacements:
        ui_code = pattern.sub(replace, ui_code)

    return ui_code


def main():
    parser = argparse.ArgumentParser(description='Convert Qt6 .ui files into Python files for use by Picard plugins.')
    parser.add_argument('ui_file', help='Path to a .ui file')
    parser.add_argument('--force', '-f', action='store_true', help='Force compilation even if up-to-date')
    args = parser.parse_args()

    ui_file = Path(args.ui_file)
    py_file = ui_file.parent.joinpath(os.path.splitext(ui_file)[0] + '.py')

    if not ui_file.exists():
        print(f"File {ui_file} does not exist.")
        sys.exit(1)

    if newer(ui_file, py_file) or args.force:
        compile_ui(ui_file, py_file)
    else:
        print(f"skipping {ui_file} -> {py_file}: up to date")


if __name__ == '__main__':
    sys.exit(main())
