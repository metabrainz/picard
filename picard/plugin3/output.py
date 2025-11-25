# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
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

import sys


class PluginOutput:
    """Simple output wrapper for plugin CLI with optional color support."""

    def __init__(self, stdout=None, stderr=None, color=None):
        """Initialize output wrapper.

        Args:
            stdout: Output stream for normal messages (default: sys.stdout)
            stderr: Output stream for errors (default: sys.stderr)
            color: Enable color output (default: auto-detect from tty)
        """
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr
        # Auto-detect color support if not specified
        if color is None:
            self.color = hasattr(self.stdout, 'isatty') and self.stdout.isatty()
        else:
            self.color = color

    def print(self, msg=''):
        """Print normal output."""
        print(msg, file=self.stdout)

    def nl(self, count=1):
        """Print blank line(s)."""
        for _ in range(count):
            print('', file=self.stdout)

    def success(self, msg):
        """Print success message with checkmark."""
        if self.color:
            # Green checkmark
            print(f'\033[32m✓\033[0m {msg}', file=self.stdout)
        else:
            print(f'✓ {msg}', file=self.stdout)

    def error(self, msg):
        """Print error message to stderr."""
        if self.color:
            # Red X
            print(f'\033[31m✗\033[0m {msg}', file=self.stderr)
        else:
            print(f'✗ {msg}', file=self.stderr)

    def warning(self, msg):
        """Print warning message to stderr."""
        if self.color:
            # Yellow warning
            print(f'\033[33m⚠\033[0m {msg}', file=self.stderr)
        else:
            print(f'⚠ {msg}', file=self.stderr)

    def info(self, msg):
        """Print info message with indent."""
        print(f'  {msg}', file=self.stdout)
