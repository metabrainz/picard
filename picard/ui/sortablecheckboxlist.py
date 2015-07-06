from PyQt4 import QtGui
from PyQt4 import QtCore
import sys
from functools import partial


class Signal(object):

    """Signal class from http://blog.abstractfactory.io/dynamic-signals-in-pyqt/
    """

    def __init__(self):
        self.__subscribers = []

    def emit(self, *args, **kwargs):
        for subs in self.__subscribers:
            subs(*args, **kwargs)

    def connect(self, func):
        self.__subscribers.append(func)

    def disconnect(self, func):
        try:
            self.__subscribers.remove(func)
        except ValueError:
            print 'Warning: function %s not removed from signal %s' % (func, self)


class SortableCheckboxListWidget(QtGui.QWidget):
    _CHECKBOX_POS = 0
    _BUTTON_UP = 1
    _BUTTON_DOWN = 2

    __no_emit = False

    def __init__(self, parent=None):
        super(SortableCheckboxListWidget, self).__init__(parent)
        layout = QtGui.QGridLayout()
        layout.setHorizontalSpacing(5)
        layout.setVerticalSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.changed = Signal()
        self.__items = []

    def addItems(self, items):
        for item in items:
            self.addItem(item)

    def setSignals(self, row):
        layout = self.layout()
        checkbox = layout.itemAtPosition(row, self._CHECKBOX_POS).widget()
        up = layout.itemAtPosition(row, self._BUTTON_UP).widget()
        down = layout.itemAtPosition(row, self._BUTTON_DOWN).widget()
        checkbox.stateChanged.connect(partial(self.checkbox_toggled, row))
        up.clicked.connect(partial(self.move_button_clicked, row, up=True))
        down.clicked.connect(partial(self.move_button_clicked, row, up=False))

    def moveItem(self, from_row, to_row):
        to_row = to_row % len(self.__items)
        self.__items[to_row], self.__items[from_row] = \
            self.__items[from_row], self.__items[to_row]
        self.updateRow(to_row)
        self.updateRow(from_row)
        self._emit_changed()

    def checkbox_toggled(self, row, state):
        self.__items[row].setChecked(state == QtCore.Qt.Checked)
        self._emit_changed()

    def move_button_clicked(self, row, up):
        if up:
            to = row - 1
        else:
            to = row + 1
        self.moveItem(row, to)

    def updateRow(self, row):
        self.__no_emit = True
        item = self.__items[row]
        layout = self.layout()
        checkbox = layout.itemAtPosition(row, self._CHECKBOX_POS).widget()
        checkbox.setText(item.text)
        checkbox.setChecked(item.checked)
        self.__no_emit = False

    def addItem(self, item):
        self.__items.append(item)
        row = len(self.__items) - 1
        layout = self.layout()
        layout.addWidget(QtGui.QCheckBox(), row, self._CHECKBOX_POS)
        self.updateRow(row)
        up_button = QtGui.QToolButton()
        up_button.setArrowType(QtCore.Qt.UpArrow)
        up_button.setMaximumSize(QtCore.QSize(16, 16))
        down_button = QtGui.QToolButton()
        down_button.setArrowType(QtCore.Qt.DownArrow)
        down_button.setMaximumSize(QtCore.QSize(16, 16))
        layout.addWidget(up_button, row, self._BUTTON_UP)
        layout.addWidget(down_button, row, self._BUTTON_DOWN)
        self.setSignals(row)

    def _emit_changed(self):
        if not self.__no_emit:
            self.changed.emit(self.__items)


class SortableCheckboxListItem(object):

    def __init__(self, text=u'', checked=False, data=None):
        self._checked = checked
        self._text = text
        self._data = data

    @property
    def text(self):
        return self._text

    def setText(self, text):
        self._text = text

    @property
    def checked(self):
        return self._checked

    def setChecked(self, state):
        self._checked = state

    @property
    def data(self):
        return self._data

    def setData(self, data):
        self._data = data

    def __repr__(self):
        params = []
        params.append('text=' + repr(self.text))
        params.append('checked=' + repr(self.checked))
        if self.data is not None:
            params.append('data=' + repr(self.data))
        return "%s(%s)" % (self.__class__.__name__, ", ".join(params))
