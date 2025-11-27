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

    # ANSI color codes - universal colors that work on both light and dark terminals
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Colors with good contrast on both light and dark backgrounds
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'

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

    def _colorize(self, text, *codes):
        """Apply color codes to text if color is enabled."""
        if not self.color or not codes:
            return text
        return ''.join(codes) + text + self.RESET

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
            print(f'{self.GREEN}✓{self.RESET} {msg}', file=self.stdout)
        else:
            print(f'✓ {msg}', file=self.stdout)

    def error(self, msg):
        """Print error message to stderr."""
        if self.color:
            print(f'{self.RED}✗{self.RESET} {msg}', file=self.stderr)
        else:
            print(f'✗ {msg}', file=self.stderr)

    def warning(self, msg):
        """Print warning message to stderr."""
        if self.color:
            print(f'{self.YELLOW}⚠{self.RESET} {msg}', file=self.stderr)
        else:
            print(f'⚠ {msg}', file=self.stderr)

    def info(self, msg):
        """Print info message with indent."""
        print(f'  {msg}', file=self.stdout)

    # Color helper methods
    def bold(self, text):
        """Make text bold."""
        return self._colorize(text, self.BOLD)

    def dim(self, text):
        """Make text dim/gray."""
        return self._colorize(text, self.DIM)

    def red(self, text):
        """Make text red."""
        return self._colorize(text, self.RED)

    def green(self, text):
        """Make text green."""
        return self._colorize(text, self.GREEN)

    def yellow(self, text):
        """Make text yellow."""
        return self._colorize(text, self.YELLOW)

    def blue(self, text):
        """Make text blue."""
        return self._colorize(text, self.BLUE)

    def magenta(self, text):
        """Make text magenta."""
        return self._colorize(text, self.MAGENTA)

    def cyan(self, text):
        """Make text cyan."""
        return self._colorize(text, self.CYAN)

    # Semantic display methods - describe WHAT the data is
    def d_id(self, identifier):
        """Display identifier (plugin_id, etc.)."""
        return self._colorize(identifier, self.BOLD)

    def d_name(self, name):
        """Display human-readable name."""
        return self._colorize(name, self.BOLD)

    def d_version(self, version):
        """Display version number."""
        return self._colorize(version, self.CYAN)

    def d_status_enabled(self, text='enabled'):
        """Display enabled status."""
        return self._colorize(text, self.GREEN)

    def d_status_disabled(self, text='disabled'):
        """Display disabled status."""
        return self._colorize(text, self.DIM)

    def d_url(self, url):
        """Display URL."""
        return self._colorize(url, self.CYAN)

    def d_path(self, path):
        """Display file path."""
        return self._colorize(str(path), self.DIM)

    def d_git_info(self, info):
        """Display git info (branch/commit)."""
        return self._colorize(info, self.DIM)

    def d_commit_old(self, commit):
        """Display old commit hash."""
        return self._colorize(commit, self.DIM)

    def d_commit_new(self, commit):
        """Display new commit hash."""
        return self._colorize(commit, self.GREEN)

    def d_arrow(self):
        """Display update arrow."""
        return self._colorize('→', self.YELLOW)

    def d_number(self, num):
        """Display important number."""
        return self._colorize(str(num), self.BOLD)

    def d_uuid(self, uuid):
        """Display UUID."""
        return self._colorize(uuid, self.DIM)

    def d_date(self, date):
        """Display date/time."""
        return self._colorize(date, self.DIM)

    def d_warning(self, text):
        """Display warning text in red."""
        return self._colorize(text, self.RED)

    def d_command(self, text):
        """Display command or option (e.g., --reinstall, picard plugins ...)."""
        return self._colorize(text, self.CYAN + self.BOLD)

    def d_prompt(self, question, default='N'):
        """Format a yes/no prompt with colorized question and options."""
        if default.upper() == 'Y':
            options = f"[{self._colorize('Y', self.BOLD)}/n]"
        else:
            options = f"[y/{self._colorize('N', self.BOLD)}]"
        return f"{self._colorize(question, self.YELLOW)} {options}: "

    def yesno(self, question, default='N'):
        """Ask a yes/no question and return True if yes, False otherwise."""
        response = input(self.d_prompt(question, default)).strip().lower()
        return response in ('y', 'yes')
