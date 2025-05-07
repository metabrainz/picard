# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2009, 2011-2014, 2017 Lukáš Lalinský
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008 amckinle
# Copyright (C) 2008-2010, 2014-2015, 2018-2025 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2010 Andrew Barnert
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2011-2014, 2017-2019 Wieland Hoffmann
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2013 Calvin Walton
# Copyright (C) 2013 Ionuț Ciocîrlan
# Copyright (C) 2013 brainz34
# Copyright (C) 2013-2014, 2017 Sophist-UK
# Copyright (C) 2013-2015, 2017-2024 Laurent Monin
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016 Simon Legner
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017-2018 Vishal Choudhary
# Copyright (C) 2018 virusMac
# Copyright (C) 2018, 2022-2023 Bob Swift
# Copyright (C) 2019 Joel Lintunen
# Copyright (C) 2020 Julius Michaelis
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2022 Kamil
# Copyright (C) 2022 skelly37
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
import re
import time
from urllib.parse import urlparse

from PyQt6 import QtCore

from picard import log
from picard.const.sys import IS_WIN
from picard.file import File
from picard.util import thread
from picard.util.cdrom import (
    DISCID_NOT_LOADED_MESSAGE,
    discid as _discid,
    get_cdrom_drives,
)


REMOTE_COMMANDS = dict()


class ParseItemsToLoad:

    WINDOWS_DRIVE_TEST = re.compile(r"^[a-z]\:", re.IGNORECASE)

    def __init__(self, items):
        self.files = set()
        self.mbids = set()
        self.urls = set()

        for item in items:
            parsed = urlparse(item)
            log.debug("Parsed: %r", parsed)
            if not parsed.scheme:
                self.files.add(item)
            if parsed.scheme == 'file':
                # remove file:// prefix safely
                self.files.add(item[7:])
            elif parsed.scheme == 'mbid':
                self.mbids.add(parsed.netloc + parsed.path)
            elif parsed.scheme in {'http', 'https'}:
                # .path returns / before actual link
                self.urls.add(parsed.path[1:])
            elif IS_WIN and self.WINDOWS_DRIVE_TEST.match(item):
                # Treat all single-character schemes as part of the file spec to allow
                # specifying a drive identifier on Windows systems.
                self.files.add(item)

    # needed to indicate whether Picard should be brought to the front
    def non_executable_items(self):
        return bool(self.files or self.mbids or self.urls)

    def __bool__(self):
        return bool(self.files or self.mbids or self.urls)

    def __str__(self):
        return f"files: {repr(self.files)}  mbids: f{repr(self.mbids)}  urls: {repr(self.urls)}"


class RemoteCommand:
    def __init__(self, method, help_text, help_args=None):
        self.method = method
        self.help_text = help_text
        self.help_args = help_args or ""


def remote_command(help_text, help_args=None):
    def inner(method):
        def wrapper(*args, **kwargs):
            method(*args, **kwargs)

        name = method.__name__.upper()
        REMOTE_COMMANDS[name] = RemoteCommand(method, help_text, help_args=help_args)
        return wrapper

    return inner


class RemoteCommandHandlers:
    def __init__(self, remotecommands_class):
        self.tagger = QtCore.QCoreApplication.instance()
        self.remotecommands_class = remotecommands_class

    @remote_command("Clear the Picard logs")
    def clear_logs(self, argstring):
        self.tagger.window.log_dialog.clear()
        self.tagger.window.history_dialog.clear()

    @remote_command("Cluster all files in the cluster pane.")
    def cluster(self, argstring):
        self.tagger.cluster(self.tagger.unclustered_files.files)

    @remote_command("Calculate acoustic fingerprints for all (matched) files in the album pane.")
    def fingerprint(self, argstring):
        for album_name in self.tagger.albums:
            self.tagger.analyze(self.tagger.albums[album_name].iterfiles())

    @remote_command(
        "Load commands from a file.",
        help_args="[path]"
    )
    def from_file(self, argstring):
        self.remotecommands_class.get_commands_from_file(argstring)

    @remote_command(
        "Load one or more files/MBIDs/URLs to Picard.",
        help_args="[path/mbid/url]",
    )
    def load(self, argstring):
        parsed_items = ParseItemsToLoad([argstring])
        log.debug(str(parsed_items))

        if parsed_items.files:
            self.tagger.add_paths(parsed_items.files)

        if parsed_items.urls or parsed_items.mbids:
            file_lookup = self.tagger.get_file_lookup()
            for item in parsed_items.mbids | parsed_items.urls:
                file_lookup.mbid_lookup(item)

    @remote_command(
        "Lookup files in the clustering pane. Defaults to all files.",
        help_args="[all|clustered|unclustered]",
    )
    def lookup(self, argstring):
        if not argstring:
            arg = 'ALL'
        else:
            arg = argstring.upper()

        if arg not in {'ALL', 'CLUSTERED', 'UNCLUSTERED'}:
            log.error("Invalid LOOKUP command argument: '%s'", arg)

        if arg in {'ALL', 'CLUSTERED'}:
            self.tagger.autotag(self.tagger.clusters)

        if arg in {'ALL', 'UNCLUSTERED'}:
            self.tagger.autotag(self.tagger.unclustered_files.files)

    @remote_command(
        "Read CD from the selected drive and lookup on MusicBrainz. "
        "Without argument, it defaults to the first (alphabetically) available disc drive.",
        help_args="[path]",
    )
    def lookup_cd(self, argstring):
        if not _discid:
            log.error(DISCID_NOT_LOADED_MESSAGE)
            return

        devices = get_cdrom_drives()
        if not argstring:
            if devices:
                device = devices[0]
            else:
                device = None
        elif argstring in devices:
            device = argstring
        else:
            self.tagger.run_lookup_discid_from_logfile(argstring)
            return

        self.tagger.run_lookup_cd(device)

    @remote_command(
        "Pause executable command processing for the specified time in seconds.",
        help_args="[number]",
    )
    def pause(self, argstring):
        arg = argstring.strip()
        if arg:
            try:
                delay = float(arg)
                if delay < 0:
                    raise ValueError
                log.debug("Pausing command execution by %d seconds.", delay)
                thread.run_task(partial(time.sleep, delay))
            except ValueError:
                log.error("Invalid command pause time specified: %r", argstring)
        else:
            log.error("No command pause time specified.")

    @remote_command(
        "Exit the running instance of Picard. "
        "Use the argument 'force' to bypass Picard's unsaved files check.",
        help_args="[force]",
    )
    def quit(self, argstring):
        if argstring.upper() == 'FORCE' or self.tagger.window.show_quit_confirmation():
            self.tagger.quit()
        else:
            log.info("QUIT command cancelled by the user.")
            self.remotecommands_class.set_quit(False)  # Allow queueing more commands.
            return

    @remote_command(
        "Remove the file matching the specified absolute path from Picard. "
        "Do nothing if no arguments provided.",
        help_args="[path]"
    )
    def remove(self, argstring):
        for file in self.tagger.iter_all_files():
            if file.filename == argstring:
                self.tagger.remove_files([file])
                return

    @remote_command("Remove all files from Picard.")
    def remove_all(self, argstring):
        self.tagger.remove_files(list(self.tagger.iter_all_files()))

    @remote_command("Remove all empty clusters and albums.")
    def remove_empty(self, argstring):
        for album in list(self.tagger.albums.values()):
            if not any(album.iterfiles()):
                self.tagger.remove_album(album)

        for cluster in self.tagger.clusters:
            if not any(cluster.iterfiles()):
                self.tagger.remove_cluster(cluster)

    @remote_command("Remove all saved files from the album pane.")
    def remove_saved(self, argstring):
        for track in self.tagger.iter_album_files():
            if track.state == File.NORMAL:
                self.tagger.remove([track])

    @remote_command("Remove all unclustered files from the cluster pane.")
    def remove_unclustered(self, argstring):
        self.tagger.remove(self.tagger.unclustered_files.files)

    @remote_command("Save all matched files from the album pane.")
    def save_matched(self, argstring):
        for album in self.tagger.albums.values():
            for track in album.iter_correctly_matched_tracks():
                track.files[0].save()

    @remote_command("Save all modified files from the album pane.")
    def save_modified(self, argstring):
        for track in self.tagger.iter_album_files():
            if track.state == File.CHANGED:
                track.save()

    @remote_command("Scan all files in the cluster pane.")
    def scan(self, argstring):
        self.tagger.analyze(self.tagger.unclustered_files.files)

    @remote_command("Make the running instance the currently active window.")
    def show(self, argstring):
        self.tagger.bring_tagger_front()

    @remote_command("Submit outstanding acoustic fingerprints for all (matched) files in the album pane.")
    def submit_fingerprints(self, argstring):
        self.tagger.acoustidmanager.submit()

    @remote_command(
        "Write Picard logs to a given path.",
        help_args="[path]",
    )
    def write_logs(self, argstring):
        try:
            with open(argstring, 'w', encoding='utf-8') as f:
                for x in self.tagger.window.log_dialog.log_tail.contents():
                    f.write(f"{x.message}\n")
        except Exception as e:
            log.error("Error writing logs to a file: %s", e)
