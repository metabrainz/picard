# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2021 Philipp Wolfer
# Copyright (C) 2020 Julius Michaelis
# Copyright (C) 2020 Laurent Monin
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


from picard.const.sys import (
    IS_HAIKU,
    IS_MACOS,
    IS_WIN,
)


DesktopStatusIndicator = None


class AbstractProgressStatusIndicator:
    def __init__(self):
        self._max_pending = 0
        self._last_pending = 0

    def update(self, files=0, albums=0, pending_files=0, pending_requests=0):
        if not self.is_available:
            return

        # Weight pending network requests higher as they are slower then file loads
        total_pending = pending_files + 10 * pending_requests

        if total_pending == self._last_pending:
            return  # No changes, avoid update

        previous_done = self._max_pending - self._last_pending
        self._max_pending = max(self._max_pending, previous_done + total_pending)
        self._last_pending = total_pending

        if total_pending == 0 or self._max_pending <= 1:  # No need to show progress for single item
            self._max_pending = 0
            self.hide_progress()
            return

        progress = 1 - (total_pending / self._max_pending)
        self.set_progress(progress)

    @property
    def is_available(self):
        return True

    def hide_progress(self):
        raise NotImplementedError

    def set_progress(self, progress):
        raise NotImplementedError


if IS_WIN:
    from PyQt5.QtWinExtras import QWinTaskbarButton

    class WindowsTaskbarStatusIndicator(AbstractProgressStatusIndicator):
        def __init__(self, window):
            super().__init__()
            taskbar_button = QWinTaskbarButton(window)
            taskbar_button.setWindow(window)
            self._progress = taskbar_button.progress()

        @property
        def is_available(self):
            return bool(self._progress)

        def hide_progress(self):
            self._progress.hide()

        def set_progress(self, progress):
            self._progress.setValue(int(progress * 100))
            self._progress.show()

    DesktopStatusIndicator = WindowsTaskbarStatusIndicator

elif not (IS_MACOS or IS_HAIKU):
    QDBusConnection = None

    try:
        from PyQt5.QtCore import (
            Q_CLASSINFO,
            QObject,
            pyqtSlot,
        )
        from PyQt5.QtDBus import (
            QDBusAbstractAdaptor,
            QDBusConnection,
            QDBusMessage,
        )

    except ImportError:
        pass

    else:

        from picard import PICARD_DESKTOP_NAME

        DBUS_INTERFACE = 'com.canonical.Unity.LauncherEntry'

        class UnityLauncherEntryService(QObject):

            def __init__(self, bus, app_id):
                QObject.__init__(self)
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
                    "progress": self._progress,
                    "progress-visible": self._visible,
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

        class UnityLauncherEntryAdaptor(QDBusAbstractAdaptor):
            """ This provides the DBus adaptor to the outside world"""

            Q_CLASSINFO("D-Bus Interface", DBUS_INTERFACE)
            Q_CLASSINFO("D-Bus Introspection",
                '<interface name="%s">\n'
                '  <signal name="Update">\n'
                '    <arg direction="out" type="s" name="app_uri"/>\n'
                '    <arg direction="out" type="a{sv}" name="properties"/>\n'
                '  </signal>\n'
                '  <method name="Query">\n'
                '    <arg direction="out" type="s" name="app_uri"/>\n'
                '    <arg direction="out" type="a{sv}" name="properties"/>\n'
                '  </method>\n'
                '</interface>' % DBUS_INTERFACE)

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

            def set_progress(self, progress):
                self._service.update(progress)

        DesktopStatusIndicator = UnityLauncherEntryStatusIndicator
