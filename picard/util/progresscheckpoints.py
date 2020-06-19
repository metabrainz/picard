# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020 Laurent Monin
# Copyright (C) 2020 Gabriel Ferreira
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


class ProgressCheckpoints:

    def __init__(self, num_jobs, num_checkpoints=10):
        """Create a set of unique and evenly spaced indexes of jobs, used as checkpoints for progress"""
        self.num_jobs = num_jobs
        self._checkpoints = {}

        if num_checkpoints > 0:
            self._offset = num_jobs/num_checkpoints
            for i in range(1, num_checkpoints):
                self._checkpoints[int(i*self._offset)] = 100*i//num_checkpoints
            if num_jobs > 0:
                self._checkpoints[num_jobs-1] = 100

    def is_checkpoint(self, index):
        if index in self._checkpoints:
            return True
        return False

    def progress(self, index):
        try:
            return self._checkpoints[index]
        except KeyError:
            return None
