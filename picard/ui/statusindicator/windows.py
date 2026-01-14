# -*- coding: utf-8 -*-
#
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

from PyQt6.QtWidgets import QMainWindow

from picard import log

from . import AbstractProgressStatusIndicator


# Progress states
TBPF_NOPROGRESS = 0x0
# TBPF_INDETERMINATE = 0x1
TBPF_NORMAL = 0x2
# TBPF_ERROR = 0x4
# TBPF_PAUSED = 0x8

CLSID_TaskbarList = "{56FDF344-FD6D-11d0-958A-006097C9A090}"


class WindowsTaskbarStatusIndicator(AbstractProgressStatusIndicator):
    def __init__(self, window: QMainWindow):
        super().__init__()
        self._handle = int(window.winId())
        self._taskbar = None

        try:
            import comtypes.client as cc

            # The below needs TaskbarLib.tlb to be available.
            # Build from TaskbarLib.idl:
            # midl TaskbarLib.idl /tlb TaskbarLib.tlb
            cc.GetModule("TaskbarLib.tlb")

            import comtypes.gen.TaskbarLib as tbl

            self._taskbar = cc.CreateObject(CLSID_TaskbarList, interface=tbl.ITaskbarList3)
        except Exception as err:
            log.warning('Failed initializing taskbar integration', exc_info=err)

    @property
    def is_available(self):
        return self._taskbar is not None

    def set_progress(self, progress: float):
        if self.is_available:
            val = int(progress * 100)
            self._taskbar.SetProgressState(self._handle, TBPF_NORMAL)
            self._taskbar.SetProgressValue(self._handle, val, 100)

    def hide_progress(self):
        if self.is_available:
            self._taskbar.SetProgressState(self._handle, TBPF_NOPROGRESS)
