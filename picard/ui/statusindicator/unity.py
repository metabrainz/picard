# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2023 Philipp Wolfer
# Copyright (C) 2020 Julius Michaelis
# Copyright (C) 2020-2021, 2023-2024 Laurent Monin
# Copyright (C) 2021 Gabriel Ferreira
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

from PyQt6.QtCore import (
    QObject,
    pyqtClassInfo,
    pyqtSlot,
)
from PyQt6.QtDBus import (
    QDBusAbstractAdaptor,
    QDBusConnection,
    QDBusMessage,
)

from picard import PICARD_DESKTOP_NAME

from . import AbstractProgressStatusIndicator


DBUS_INTERFACE = 'com.canonical.Unity.LauncherEntry'


class UnityLauncherEntryService(QObject):
    def __init__(self, bus, app_id):
        super().__init__()
        self._bus = bus
        self._app_uri = 'application://' + app_id
        self._path = '/com/canonical/unity/launcherentry/1'
        self._progress = 0
        self._visible = False
        self._dbus_adaptor = UnityLauncherEntryAdaptor(self)
        self._available = bus.registerObject(self._path, self)

    @property
    def current_progress(self):
        return {
            'progress': self._progress,
            'progress-visible': self._visible,
        }

    @property
    def is_available(self):
        return self._available

    def update(self, progress, visible=True):
        self._progress = progress
        self._visible = visible
        # Automatic forwarding of Qt signals does not work in this case
        # since Qt cannot handle the complex "a{sv}" type.
        # Create the signal message manually.
        message = QDBusMessage.createSignal(self._path, DBUS_INTERFACE, 'Update')
        message.setArguments([self._app_uri, self.current_progress])
        self._bus.send(message)

    def query(self):
        return [self._app_uri, self.current_progress]


@pyqtClassInfo('D-Bus Interface', DBUS_INTERFACE)
@pyqtClassInfo(
    'D-Bus Introspection',
    '<interface name="%s">\n'
    '  <signal name="Update">\n'
    '    <arg direction="out" type="s" name="app_uri"/>\n'
    '    <arg direction="out" type="a{sv}" name="properties"/>\n'
    '  </signal>\n'
    '  <method name="Query">\n'
    '    <arg direction="out" type="s" name="app_uri"/>\n'
    '    <arg direction="out" type="a{sv}" name="properties"/>\n'
    '  </method>\n'
    '</interface>' % DBUS_INTERFACE,
)
class UnityLauncherEntryAdaptor(QDBusAbstractAdaptor):
    """This provides the DBus adapter to the outside world"""

    def __init__(self, parent):
        super().__init__(parent)

    @pyqtSlot(name="Query", result=list)
    def query(self):
        return self.parent().query()


class UnityLauncherEntryStatusIndicator(AbstractProgressStatusIndicator):
    def __init__(self, window):
        super().__init__()
        bus = QDBusConnection.sessionBus()
        self._service = UnityLauncherEntryService(bus, PICARD_DESKTOP_NAME)

    @property
    def is_available(self):
        return self._service.is_available

    def hide_progress(self):
        self._service.update(0, False)

    def set_progress(self, progress: float):
        self._service.update(progress)
