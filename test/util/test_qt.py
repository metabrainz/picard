# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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


import gc
import weakref

from PyQt6 import (
    QtCore,
    sip,
)

from picard.util.qt import (
    _qt_message_handler,
    cancel_on_destroyed,
    install_qt_message_handler,
)

import pytest


@pytest.mark.usefixtures("qapp")
class TestCancelOnDestroyed:
    def test_runs_while_object_alive(self):
        obj = QtCore.QObject()
        calls = []
        cb = cancel_on_destroyed(obj, lambda: calls.append(1))
        cb()
        cb()
        assert calls == [1, 1]

    def test_disarmed_after_object_destroyed(self):
        obj = QtCore.QObject()
        calls = []
        cb = cancel_on_destroyed(obj, lambda: calls.append(1))
        cb()
        assert calls == [1]
        # Destroy the object; the destroyed signal disarms the callback.
        sip.delete(obj)
        cb()
        cb()
        assert calls == [1]  # no further calls

    def test_passes_through_args_and_return(self):
        obj = QtCore.QObject()
        cb = cancel_on_destroyed(obj, lambda x, y: x + y)
        assert cb(2, 3) == 5
        obj.deleteLater()

    def test_connection_does_not_keep_object_alive(self):
        # cancel_on_destroyed connects a slot to obj.destroyed and keeps the
        # returned wrapper alive. If that machinery held a strong Python
        # reference back to obj (e.g. by using a bound method of obj as the
        # slot, or capturing obj in the cancel closure), obj could not be
        # garbage collected while the wrapper lives -- recreating the very
        # retention this helper guards against.
        #
        # Note: sip.delete() force-deletes the C++ side regardless of Python
        # refs, so it would NOT catch such a leak. We instead keep the wrapper
        # alive, drop our own reference to obj, run a GC pass, and assert obj
        # was collected via a weakref -- which only holds if cancel_on_destroyed
        # left no strong reference to obj.
        obj = QtCore.QObject()
        ref = weakref.ref(obj)
        # Keep the wrapper referenced for the rest of the test: the realistic
        # leak would be the long-lived wrapper holding a strong ref to obj, so
        # obj must be collectable even while wrapper is alive.
        wrapper = cancel_on_destroyed(obj, lambda: None)
        del obj
        gc.collect()
        assert ref() is None
        del wrapper

    def test_on_destroyed_called_once_when_object_destroyed(self):
        obj = QtCore.QObject()
        aborts = []
        cancel_on_destroyed(obj, lambda: None, on_destroyed=lambda: aborts.append(1))
        sip.delete(obj)
        assert aborts == [1]

    def test_on_destroyed_not_called_while_alive(self):
        obj = QtCore.QObject()
        aborts = []
        cb = cancel_on_destroyed(obj, lambda: None, on_destroyed=lambda: aborts.append(1))
        cb()
        assert aborts == []
        obj.deleteLater()


class TestQtMessageHandler:
    def test_suppresses_benign_ssl_read_warning(self, monkeypatch):
        records = []
        monkeypatch.setattr('picard.util.qt.log.warning', lambda *a, **k: records.append(a))
        _qt_message_handler(
            QtCore.QtMsgType.QtWarningMsg,
            None,
            'QIODevice::read (QSslSocket): device not open',
        )
        assert records == []  # dropped, not forwarded

    def test_suppresses_benign_message_embedded_in_longer_text(self, monkeypatch):
        records = []
        monkeypatch.setattr('picard.util.qt.log.warning', lambda *a, **k: records.append(a))
        _qt_message_handler(
            QtCore.QtMsgType.QtWarningMsg,
            None,
            'prefix QIODevice::read (QSslSocket): device not open suffix',
        )
        assert records == []

    def test_forwards_other_warning(self, monkeypatch):
        records = []
        monkeypatch.setattr('picard.util.qt.log.warning', lambda msg, text: records.append((msg, text)))
        _qt_message_handler(QtCore.QtMsgType.QtWarningMsg, None, 'some other Qt warning')
        assert records == [('Qt: %s', 'some other Qt warning')]

    def test_critical_maps_to_error(self, monkeypatch):
        records = []
        monkeypatch.setattr('picard.util.qt.log.error', lambda msg, text: records.append((msg, text)))
        _qt_message_handler(QtCore.QtMsgType.QtCriticalMsg, None, 'boom')
        assert records == [('Qt: %s', 'boom')]

    def test_debug_maps_to_debug(self, monkeypatch):
        records = []
        monkeypatch.setattr('picard.util.qt.log.debug', lambda msg, text: records.append((msg, text)))
        _qt_message_handler(QtCore.QtMsgType.QtDebugMsg, None, 'chatter')
        assert records == [('Qt: %s', 'chatter')]

    def test_install_sets_handler(self):
        # Installing then restoring the previous handler must not raise, and
        # the installer returns the handler object Qt had before.
        previous = QtCore.qInstallMessageHandler(None)
        try:
            install_qt_message_handler()
        finally:
            QtCore.qInstallMessageHandler(previous)
