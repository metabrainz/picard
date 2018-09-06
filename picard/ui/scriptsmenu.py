# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2018 Philipp Wolfer
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

from PyQt5 import QtWidgets

from picard import log
from picard.album import Album
from picard.cluster import (
    Cluster,
    ClusterList,
)
from picard.script import (
    ScriptError,
    ScriptParser,
)
from picard.track import Track
from picard.util import uniqify


class ScriptsMenu(QtWidgets.QMenu):

    def __init__(self, scripts, *args):
        super().__init__(*args)

        for script in scripts:
            action = self.addAction(script[1])
            action.triggered.connect(partial(self._run_script, script))

    def _run_script(self, script):
        s_name = script[1]
        s_text = script[3]
        parser = ScriptParser()

        for obj in self._get_unique_metadata_objects():
            try:
                parser.eval(s_text, obj.metadata)
                obj.update()
            except ScriptError as e:
                log.exception('Error running tagger script "%s" on object %r', s_name, obj)
                msg = N_('Script error in "%(script)s": %(message)s')
                mparms = {
                    'script': s_name,
                    'message': str(e),
                }
                self.tagger.window.set_statusbar_message(msg, mparms)

    def _get_unique_metadata_objects(self):
        objs = self._get_metadata_objects(self.tagger.window.selected_objects)
        return uniqify(objs)

    def _get_metadata_objects(self, objs):
        for obj in objs:
            if hasattr(obj, 'metadata'):
                yield obj
            if isinstance(obj, Cluster):
                yield from self._get_metadata_objects(obj.files)
            if isinstance(obj, ClusterList):
                yield from self._get_metadata_objects(obj)
            if isinstance(obj, Album):
                yield from self._get_metadata_objects(obj.tracks)
                yield from self._get_metadata_objects(obj.unmatched_files.iterfiles())
            if isinstance(obj, Track):
                yield from self._get_metadata_objects(obj.linked_files)
