# -*- coding: utf-8 -*-
# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class ArtworkTable(QtGui.QTableWidget):
    def __init__(self, display_existing_art):
        QtGui.QTableWidget.__init__(self, 0, 2)
        self.display_existing_art = display_existing_art
        h_header = self.horizontalHeader()
        v_header = self.verticalHeader()
        h_header.setDefaultSectionSize(200)
        v_header.setDefaultSectionSize(230)
        if self.display_existing_art:
            self._existing_cover_col = 0
            self._type_col = 1
            self._new_cover_col = 2
            self.insertColumn(2)
            self.setHorizontalHeaderLabels([_("Existing Cover"), _("Type"),
                _("New Cover")])
            self.arrow_pixmap = QtGui.QPixmap(":/images/arrow.png")
        else:
            self._type_col = 0
            self._new_cover_col = 1
            self.setHorizontalHeaderLabels([_("Type"), _("Cover")])
            self.setColumnWidth(self._type_col, 140)

    def get_coverart_widget(self, pixmap, text):
        """Return a QWidget that can be added to artwork column cell of ArtworkTable."""
        coverart_widget = QtGui.QWidget()
        image_label = QtGui.QLabel()
        text_label = QtGui.QLabel()
        layout = QtGui.QVBoxLayout()
        image_label.setPixmap(pixmap.scaled(170,170,QtCore.Qt.KeepAspectRatio,
                                            QtCore.Qt.SmoothTransformation))
        image_label.setAlignment(QtCore.Qt.AlignCenter)
        text_label.setText(text)
        text_label.setAlignment(QtCore.Qt.AlignCenter)
        text_label.setWordWrap(True)
        layout.addWidget(image_label)
        layout.addWidget(text_label)
        coverart_widget.setLayout(layout)
        return coverart_widget

    def get_type_widget(self, type_text):
        """Return a QWidget that can be added to type column cell of ArtworkTable.
        If both existing and new artwork are to be displayed, insert an arrow icon to make comparison
        obvious.
        """
        type_widget = QtGui.QWidget()
        type_label = QtGui.QLabel()
        layout = QtGui.QVBoxLayout()
        type_label.setText(type_text)
        type_label.setAlignment(QtCore.Qt.AlignCenter)
        type_label.setWordWrap(True)
        if self.display_existing_art:
            arrow_label = QtGui.QLabel()
            arrow_label.setPixmap(self.arrow_pixmap.scaled(170, 170, QtCore.Qt.KeepAspectRatio,
                                                           QtCore.Qt.SmoothTransformation))
            arrow_label.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(arrow_label)
            layout.addWidget(type_label)
        else:
            layout.addWidget(type_label)
        type_widget.setLayout(layout)
        return type_widget


class Ui_InfoDialog(object):
    def setupUi(self, InfoDialog, display_existing_art):
        InfoDialog.setObjectName(_fromUtf8("InfoDialog"))
        if display_existing_art:
            InfoDialog.resize(665, 436)
        else:
            InfoDialog.resize(535, 436)
        self.verticalLayout = QtGui.QVBoxLayout(InfoDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tabWidget = QtGui.QTabWidget(InfoDialog)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.info_tab = QtGui.QWidget()
        self.info_tab.setObjectName(_fromUtf8("info_tab"))
        self.vboxlayout = QtGui.QVBoxLayout(self.info_tab)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.info_scroll = QtGui.QScrollArea(self.info_tab)
        self.info_scroll.setWidgetResizable(True)
        self.info_scroll.setObjectName(_fromUtf8("info_scroll"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setEnabled(True)
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 493, 334))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.verticalLayoutLabel = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayoutLabel.setObjectName(_fromUtf8("verticalLayoutLabel"))
        self.info = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.info.setText(_fromUtf8(""))
        self.info.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.info.setWordWrap(True)
        self.info.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.info.setObjectName(_fromUtf8("info"))
        self.verticalLayoutLabel.addWidget(self.info)
        self.info_scroll.setWidget(self.scrollAreaWidgetContents)
        self.vboxlayout.addWidget(self.info_scroll)
        self.tabWidget.addTab(self.info_tab, _fromUtf8(""))
        self.artwork_tab = QtGui.QWidget()
        self.artwork_tab.setObjectName(_fromUtf8("artwork_tab"))
        self.vboxlayout1 = QtGui.QVBoxLayout(self.artwork_tab)
        self.vboxlayout1.setObjectName(_fromUtf8("vboxlayout1"))
        self.artwork_table = ArtworkTable(display_existing_art)
        self.artwork_table.setObjectName(_fromUtf8("artwork_table"))
        self.vboxlayout1.addWidget(self.artwork_table)
        self.tabWidget.addTab(self.artwork_tab, _fromUtf8(""))
        self.verticalLayout.addWidget(self.tabWidget)
        self.buttonBox = QtGui.QDialogButtonBox(InfoDialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(InfoDialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(InfoDialog)
        InfoDialog.setTabOrder(self.tabWidget, self.artwork_table)
        InfoDialog.setTabOrder(self.artwork_table, self.buttonBox)

    def retranslateUi(self, InfoDialog):
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.info_tab), _("&Info"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.artwork_tab), _("A&rtwork"))

