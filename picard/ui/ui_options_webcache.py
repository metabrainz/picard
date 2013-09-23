# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\options_webcache.ui'
#
# Created: Tue Jun 11 14:23:36 2013
#      by: PyQt4 UI code generator 4.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_WebcacheOptionsPage(object):
    def setupUi(self, WebcacheOptionsPage):
        WebcacheOptionsPage.setObjectName(_fromUtf8("WebcacheOptionsPage"))
        WebcacheOptionsPage.resize(400, 240)
        self.vboxlayout = QtGui.QVBoxLayout(WebcacheOptionsPage)
        self.vboxlayout.setSpacing(4)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.webcache_enabled = QtGui.QGroupBox(WebcacheOptionsPage)
        self.webcache_enabled.setMinimumSize(QtCore.QSize(0, 20))
        self.webcache_enabled.setCheckable(True)
        self.webcache_enabled.setChecked(False)
        self.webcache_enabled.setObjectName(_fromUtf8("webcache_enabled"))
        self.gridlayout = QtGui.QGridLayout(self.webcache_enabled)
        self.gridlayout.setContentsMargins(9, 4, 9, 9)
        self.gridlayout.setVerticalSpacing(4)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.hlayout_max_size = QtGui.QHBoxLayout()
        self.hlayout_max_size.setSpacing(4)
        self.hlayout_max_size.setObjectName(_fromUtf8("hlayout_max_size"))
        self.max_size_label = QtGui.QLabel(self.webcache_enabled)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.max_size_label.sizePolicy().hasHeightForWidth())
        self.max_size_label.setSizePolicy(sizePolicy)
        self.max_size_label.setObjectName(_fromUtf8("max_size_label"))
        self.hlayout_max_size.addWidget(self.max_size_label)
        self.webcache_max_size = QtGui.QSpinBox(self.webcache_enabled)
        self.webcache_max_size.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.webcache_max_size.setButtonSymbols(QtGui.QAbstractSpinBox.UpDownArrows)
        self.webcache_max_size.setMaximum(9999)
        self.webcache_max_size.setProperty("value", 250)
        self.webcache_max_size.setObjectName(_fromUtf8("webcache_max_size"))
        self.hlayout_max_size.addWidget(self.webcache_max_size)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.hlayout_max_size.addItem(spacerItem)
        self.gridlayout.addLayout(self.hlayout_max_size, 6, 1, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.gridlayout.addItem(spacerItem1, 11, 1, 1, 1)
        self.hLayout_clear_cache = QtGui.QHBoxLayout()
        self.hLayout_clear_cache.setSpacing(4)
        self.hLayout_clear_cache.setObjectName(_fromUtf8("hLayout_clear_cache"))
        self.webcache_current_sizes = QtGui.QLabel(self.webcache_enabled)
        self.webcache_current_sizes.setMinimumSize(QtCore.QSize(0, 20))
        self.webcache_current_sizes.setText(_fromUtf8("You are currently using xMB of a maximum of yMB."))
        self.webcache_current_sizes.setObjectName(_fromUtf8("webcache_current_sizes"))
        self.hLayout_clear_cache.addWidget(self.webcache_current_sizes)
        spacerItem2 = QtGui.QSpacerItem(10, 0, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.hLayout_clear_cache.addItem(spacerItem2)
        self.webcache_clear_cache = QtGui.QPushButton(self.webcache_enabled)
        self.webcache_clear_cache.setEnabled(False)
        self.webcache_clear_cache.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.webcache_clear_cache.setObjectName(_fromUtf8("webcache_clear_cache"))
        self.hLayout_clear_cache.addWidget(self.webcache_clear_cache)
        spacerItem3 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.hLayout_clear_cache.addItem(spacerItem3)
        self.gridlayout.addLayout(self.hLayout_clear_cache, 9, 1, 2, 1)
        self.hLayout_force_cache = QtGui.QHBoxLayout()
        self.hLayout_force_cache.setSpacing(4)
        self.hLayout_force_cache.setObjectName(_fromUtf8("hLayout_force_cache"))
        self.force_cache_label = QtGui.QLabel(self.webcache_enabled)
        self.force_cache_label.setObjectName(_fromUtf8("force_cache_label"))
        self.hLayout_force_cache.addWidget(self.force_cache_label)
        spacerItem4 = QtGui.QSpacerItem(3, 0, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.hLayout_force_cache.addItem(spacerItem4)
        self.webcache_force_cache = QtGui.QCheckBox(self.webcache_enabled)
        self.webcache_force_cache.setText(_fromUtf8(""))
        self.webcache_force_cache.setObjectName(_fromUtf8("webcache_force_cache"))
        self.hLayout_force_cache.addWidget(self.webcache_force_cache)
        spacerItem5 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.hLayout_force_cache.addItem(spacerItem5)
        self.gridlayout.addLayout(self.hLayout_force_cache, 12, 1, 1, 1)
        self.label = QtGui.QLabel(self.webcache_enabled)
        self.label.setWordWrap(True)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridlayout.addWidget(self.label, 13, 1, 1, 1)
        self.vboxlayout.addWidget(self.webcache_enabled)
        self.note = QtGui.QLabel(WebcacheOptionsPage)
        self.note.setWordWrap(True)
        self.note.setObjectName(_fromUtf8("note"))
        self.vboxlayout.addWidget(self.note)
        spacerItem6 = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem6)

        self.retranslateUi(WebcacheOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(WebcacheOptionsPage)
        WebcacheOptionsPage.setTabOrder(self.webcache_enabled, self.webcache_max_size)

    def retranslateUi(self, WebcacheOptionsPage):
        self.webcache_enabled.setTitle(_("Web Cache"))
        self.max_size_label.setText(_("Maximum disk cache requested:"))
        self.webcache_max_size.setSuffix(_("MB"))
        self.webcache_clear_cache.setText(_("Clear Cache"))
        self.force_cache_label.setText(_("Force cache usage:"))
        self.label.setText(_("Note: If you force cache usage, data will always be read from the cache if it is available. To get updated data from the web you will need to clear this setting or clear the cache."))
        self.note.setText(_("Note: Please read the help file and understand what they do before enabling these settings."))

