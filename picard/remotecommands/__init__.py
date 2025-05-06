# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022-2023 Bob Swift
# Copyright (C) 2023 Philipp Wolfer
# Copyright (C) 2023-2024 Laurent Monin
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


from functools import partial
import os
import queue
import shlex
from textwrap import fill
import threading

from picard import log

from .handlers import (
    REMOTE_COMMANDS,
    RemoteCommandHandlers,
)


class RemoteCommands:
    """Handler for remote commands processed from the command line using the '-e' option.
    """
    # Collection of command files currently being parsed
    _command_files = set()

    # Flag to indicate whether a 'QUIT' command has been queued
    _has_quit = False

    # Flag to indicate whether a command is currently running
    _command_running = False

    _lock = threading.Lock()
    command_queue = queue.Queue()

    @classmethod
    def cmd_files_contains(cls, filepath: str):
        """Check if the specified filepath is currently open for reading commands.

        Args:
            filepath (str): File path to check.

        Returns:
            bool: True if the filepath is open for processing, otherwise False.
        """
        with cls._lock:
            return filepath in cls._command_files

    @classmethod
    def cmd_files_add(cls, filepath: str):
        """Adds the specified filepath to the collection of files currently open
        for reading commands.

        Args:
            filepath (str): File path to add.
        """
        with cls._lock:
            cls._command_files.add(filepath)

    @classmethod
    def cmd_files_remove(cls, filepath: str):
        """Removes the specified filepath from the collection of files currently
        open for reading commands.

        Args:
            filepath (str): File path to remove.
        """
        with cls._lock:
            cls._command_files.discard(filepath)

    @classmethod
    def has_quit(cls):
        """Indicates whether a 'QUIT' command has been added to the command queue.

        Returns:
            bool: True if a 'QUIT' command has been queued, otherwise False.
        """
        with cls._lock:
            return cls._has_quit

    @classmethod
    def set_quit(cls, value: bool):
        """Sets the status of the 'has_quit()' flag.

        Args:
            value (bool): Value to set for the 'has_quit()' flag.
        """
        with cls._lock:
            cls._has_quit = value

    @classmethod
    def get_running(cls):
        """Indicates whether a command is currently set as active regardless of
        processing status.

        Returns:
            bool: True if there is an active command, otherwise False.
        """
        with cls._lock:
            return cls._command_running

    @classmethod
    def set_running(cls, value: bool):
        """Sets the status of the 'get_running()' flag.

        Args:
            value (bool): Value to set for the 'get_running()' flag.
        """
        with cls._lock:
            cls._command_running = value

    @classmethod
    def parse_commands_to_queue(cls, commands):
        """Parses the list of command tuples, and adds them to the command queue.  If the command
        is 'FROM_FILE' then the commands will be read from the file recursively.  Once a 'QUIT'
        command has been queued, all further commands will be ignored and not placed in the queue.

        Args:
            commands (list): Command tuples in the form (command, [args]) to add to the queue.
        """
        if cls.has_quit():
            # Don't queue any more commands after a QUIT command.
            return

        for (cmd, cmdargs) in commands:
            cmd = cmd.upper()
            if cmd not in REMOTE_COMMANDS:
                log.error("Unknown command: %s", cmd)
                continue
            for cmd_arg in cmdargs or ['']:
                if cmd == 'FROM_FILE':
                    cls.get_commands_from_file(cmd_arg)
                else:
                    log.debug(f"Queueing command: {cmd} {repr(cmd_arg)}")
                    cls.command_queue.put([cmd, cmd_arg])

                    # Set flag so as to not queue any more commands after a QUIT command.
                    if cmd == 'QUIT':
                        cls.set_quit(True)
                        return

    @staticmethod
    def _read_commands_from_file(filepath: str):
        """Reads the commands from the specified filepath.

        Args:
            filepath (str): File to read.

        Returns:
            list: Command tuples in the form (command, [args]).
        """
        commands = []
        try:
            lines = open(filepath).readlines()
        except Exception as e:
            log.error("Error reading command file '%s': %s", filepath, e)
            return commands
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            elements = shlex.split(line)
            if not elements:
                continue
            command_args = elements[1:] or ['']
            commands.append((elements[0], command_args))
        return commands

    @classmethod
    def get_commands_from_file(cls, filepath: str):
        """Reads and parses the commands from the specified filepath and adds
        them to the command queue for processing.

        Args:
            filepath (str): File to read.
        """
        log.debug("Reading commands from: %r", filepath)
        if not os.path.exists(filepath):
            log.error("Missing command file: '%s'", filepath)
            return
        absfilepath = os.path.abspath(filepath)
        if cls.cmd_files_contains(absfilepath):
            log.warning("Circular command file reference ignored: '%s'", filepath)
            return
        cls.cmd_files_add(absfilepath)
        cls.parse_commands_to_queue(cls._read_commands_from_file(absfilepath))
        cls.cmd_files_remove(absfilepath)

    @classmethod
    def help(cls, maxwidth):
        informative_text = []

        message = """Usage: picard -e [command] [arguments ...]
        or picard -e [command 1] [arguments ...] -e [command 2] [arguments ...]

    List of the commands available to execute in Picard from the command-line:
    """

        for name in sorted(REMOTE_COMMANDS):
            remcmd = REMOTE_COMMANDS[name]
            s = "  - %-34s %s" % (name + " " + remcmd.help_args, remcmd.help_text)
            informative_text.append(fill(s, width=maxwidth, subsequent_indent=' '*39))

        informative_text.append('')

        def fmt(s):
            informative_text.append(fill(s, width=maxwidth))

        fmt("Commands are case insensitive.")
        fmt("Picard will try to load all the positional arguments before processing commands.")
        fmt("If there is no instance to pass the arguments to, Picard will start and process the commands after the "
            "positional arguments are loaded, as mentioned above. Otherwise they will be handled by the running "
            "Picard instance")
        fmt("Arguments are optional, but some commands may require one or more arguments to actually do something.")

        return message, "\n".join(informative_text)

    @classmethod
    def commands(cls):
        handlers = RemoteCommandHandlers(cls)
        return {name: partial(remcmd.method, handlers) for name, remcmd in REMOTE_COMMANDS.items()}
