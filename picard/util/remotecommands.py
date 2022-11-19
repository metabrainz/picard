# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022 Bob Swift
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

import datetime
import os
import queue
import shlex
import threading
import time

from picard import log


class RemoteCommand:
    def __init__(self, method_name, help_text=None, help_args=None):
        self.method_name = method_name
        self.help_text = help_text or ""
        self.help_args = help_args or ""


REMOTE_COMMANDS = {
    "CLEAR_LOGS": RemoteCommand(
        "handle_command_clear_logs",
        help_text="Clear the Picard logs",
    ),
    "CLUSTER": RemoteCommand(
        "handle_command_cluster",
        help_text="Cluster all files in the cluster pane.",
    ),
    "FINGERPRINT": RemoteCommand(
        "handle_command_fingerprint",
        help_text="Calculate acoustic fingerprints for all (matched) files in the album pane.",
    ),
    "FROM_FILE": RemoteCommand(
        "handle_command_from_file",
        help_text="Load command pipeline from a file.",
        help_args="[Absolute path to a file containing command pipeline]",
    ),
    "LOAD": RemoteCommand(
        "handle_command_load",
        help_text="Load 1 or more files/MBIDs/URLs to Picard.",
        help_args="[supported MBID/URL or absolute path to a file]",
    ),
    "LOOKUP": RemoteCommand(
        "handle_command_lookup",
        help_text="Lookup files in the clustering pane. Defaults to all files.",
        help_args="[clustered|unclustered|all]"
    ),
    "LOOKUP_CD": RemoteCommand(
        "handle_command_lookup_cd",
        help_text="Read CD from the selected drive and lookup on MusicBrainz. "
        "Without argument, it defaults to the first (alphabetically) available disc drive",
        help_args="[device/log file]",
    ),
    "QUIT": RemoteCommand(
        "handle_command_quit",
        help_text="Exit the running instance of Picard.",
    ),
    "REMOVE": RemoteCommand(
        "handle_command_remove",
        help_text="Remove the file from Picard. Do nothing if no arguments provided.",
        help_args="[absolute path to 1 or more files]",
    ),
    "REMOVE_ALL": RemoteCommand(
        "handle_command_remove_all",
        help_text="Remove all files from Picard.",
    ),
    "REMOVE_EMPTY": RemoteCommand(
        "handle_command_remove_empty",
        help_text="Remove all empty clusters and albums.",
    ),
    "REMOVE_SAVED": RemoteCommand(
        "handle_command_remove_saved",
        help_text="Remove all saved releases from the album pane.",
    ),
    "REMOVE_UNCLUSTERED": RemoteCommand(
        "handle_command_remove_unclustered",
        help_text="Remove all unclustered files from the cluster pane.",
    ),
    "SAVE_MATCHED": RemoteCommand(
        "handle_command_save_matched",
        help_text="Save all matched releases from the album pane."
    ),
    "SAVE_MODIFIED": RemoteCommand(
        "handle_command_save_modified",
        help_text="Save all modified files from the album pane.",
    ),
    "SCAN": RemoteCommand(
        "handle_command_scan",
        help_text="Scan all files in the cluster pane.",
    ),
    "SHOW": RemoteCommand(
        "handle_command_show",
        help_text="Make the running instance the currently active window.",
    ),
    "SUBMIT_FINGERPRINTS": RemoteCommand(
        "handle_command_submit_fingerprints",
        help_text="Submit outstanding acoustic fingerprints for all (matched) files in the album pane.",
    ),
    "WRITE_LOGS": RemoteCommand(
        "handle_command_write_logs",
        help_text="Write Picard logs to a given path.",
        help_args="[absolute path to 1 file]",
    ),
}


class RemoteCommands:
    # Collection of command files currently being parsed
    _command_files = set()

    # Flag to indicate whether a 'QUIT' command has been queued
    _has_quit = False

    # Flag to indicate whether a command is currently running
    _command_running = False

    _lock = threading.Lock()
    command_queue = queue.Queue()
    _threads = set()

    @classmethod
    def cmd_files_contains(cls, filepath):
        with cls._lock:
            return filepath in cls._command_files

    @classmethod
    def cmd_files_add(cls, filepath):
        with cls._lock:
            cls._command_files.add(filepath)

    @classmethod
    def cmd_files_remove(cls, filepath):
        with cls._lock:
            cls._command_files.discard(filepath)

    @classmethod
    def has_quit(cls):
        with cls._lock:
            return cls._has_quit

    @classmethod
    def set_quit(cls, value):
        with cls._lock:
            cls._has_quit = value

    @classmethod
    def thread_add(cls, thread_id):
        with cls._lock:
            cls._threads.add(thread_id)

    @classmethod
    def thread_remove(cls, thread_id):
        with cls._lock:
            cls._threads.discard(thread_id)

    @classmethod
    def processing(cls):
        with cls._lock:
            return (len(cls._threads) > 0)

    @classmethod
    def get_running(cls):
        with cls._lock:
            return cls._command_running

    @classmethod
    def set_running(cls, value):
        with cls._lock:
            cls._command_running = value

    @classmethod
    def clear_command_running(cls, force=False, timeout=None):
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=timeout) if timeout else None
        while True:
            if not cls.processing() or force or (timeout and datetime.datetime.now() > end_time):
                with cls._lock:
                    cls._command_running = False
                    cls._threads = set()
                break
            time.sleep(.01)

    @classmethod
    def parse_commands_to_queue(cls, commands):
        if cls.has_quit():
            # Don't queue any more commands after a QUIT command.
            print(f"has_quit = {cls.has_quit()}\n\n")
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
    def _read_commands_from_file(filepath):
        commands = []
        try:
            lines = open(filepath).readlines()
        except Exception as e:
            log.error("Error reading command file '%s': %s" % (filepath, e))
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
    def get_commands_from_file(cls, argstring):
        log.debug("Reading commands from: %r", argstring)
        if not os.path.exists(argstring):
            log.error("Missing command file: '%s'", argstring)
            return
        filepath = os.path.abspath(argstring)
        if cls.cmd_files_contains(filepath):
            log.warning("Circular command file reference ignored: '%s'", argstring)
            return
        cls.cmd_files_add(filepath)
        cls.parse_commands_to_queue(cls._read_commands_from_file(filepath))
        cls.cmd_files_remove(filepath)
