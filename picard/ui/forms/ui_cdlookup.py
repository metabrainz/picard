# Form implementation generated from reading ui file 'ui/cdlookup.ui'
#
# Created by: PyQt6 UI code generator 6.6.1
#
# Automatically generated - do not edit.
# Use `python setup.py build_ui` to update it.

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import gettext as _


class Ui_CDLookupDialog(object):
    def setupUi(self, CDLookupDialog):
        CDLookupDialog.setObjectName("CDLookupDialog")
        CDLookupDialog.resize(720, 320)
        self.vboxlayout = QtWidgets.QVBoxLayout(CDLookupDialog)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.results_view = QtWidgets.QStackedWidget(parent=CDLookupDialog)
        self.results_view.setObjectName("results_view")
        self.results_page = QtWidgets.QWidget()
        self.results_page.setObjectName("results_page")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.results_page)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.label = QtWidgets.QLabel(parent=self.results_page)
        self.label.setObjectName("label")
        self.verticalLayout_4.addWidget(self.label)
        self.release_list = QtWidgets.QTreeWidget(parent=self.results_page)
        self.release_list.setObjectName("release_list")
        self.release_list.headerItem().setText(0, "1")
        self.verticalLayout_4.addWidget(self.release_list)
        self.results_view.addWidget(self.results_page)
        self.no_results_page = QtWidgets.QWidget()
        self.no_results_page.setObjectName("no_results_page")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.no_results_page)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_3.addItem(spacerItem)
        self.no_results_label = QtWidgets.QLabel(parent=self.no_results_page)
        self.no_results_label.setStyleSheet("margin-bottom: 9px;")
        self.no_results_label.setObjectName("no_results_label")
        self.verticalLayout_3.addWidget(self.no_results_label, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.submit_button = QtWidgets.QToolButton(parent=self.no_results_page)
        self.submit_button.setStyleSheet("")
        icon = QtGui.QIcon.fromTheme("media-optical")
        self.submit_button.setIcon(icon)
        self.submit_button.setIconSize(QtCore.QSize(128, 128))
        self.submit_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.submit_button.setObjectName("submit_button")
        self.verticalLayout_3.addWidget(self.submit_button, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_3.addItem(spacerItem1)
        self.results_view.addWidget(self.no_results_page)
        self.vboxlayout.addWidget(self.results_view)
        self.hboxlayout = QtWidgets.QHBoxLayout()
        self.hboxlayout.setContentsMargins(0, 0, 0, 0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")
        spacerItem2 = QtWidgets.QSpacerItem(111, 31, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.hboxlayout.addItem(spacerItem2)
        self.ok_button = QtWidgets.QPushButton(parent=CDLookupDialog)
        self.ok_button.setEnabled(False)
        self.ok_button.setObjectName("ok_button")
        self.hboxlayout.addWidget(self.ok_button)
        self.lookup_button = QtWidgets.QPushButton(parent=CDLookupDialog)
        self.lookup_button.setObjectName("lookup_button")
        self.hboxlayout.addWidget(self.lookup_button)
        self.cancel_button = QtWidgets.QPushButton(parent=CDLookupDialog)
        self.cancel_button.setObjectName("cancel_button")
        self.hboxlayout.addWidget(self.cancel_button)
        self.vboxlayout.addLayout(self.hboxlayout)

        self.retranslateUi(CDLookupDialog)
        self.results_view.setCurrentIndex(0)
        self.ok_button.clicked.connect(CDLookupDialog.accept) # type: ignore
        self.cancel_button.clicked.connect(CDLookupDialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(CDLookupDialog)
        CDLookupDialog.setTabOrder(self.release_list, self.submit_button)
        CDLookupDialog.setTabOrder(self.submit_button, self.ok_button)
        CDLookupDialog.setTabOrder(self.ok_button, self.lookup_button)
        CDLookupDialog.setTabOrder(self.lookup_button, self.cancel_button)

    def retranslateUi(self, CDLookupDialog):
        CDLookupDialog.setWindowTitle(_("CD Lookup"))
        self.label.setText(_("The following releases on MusicBrainz match the CD:"))
        self.no_results_label.setText(_("No matching releases found for this disc."))
        self.submit_button.setText(_("Submit disc ID"))
        self.ok_button.setText(_("&Load into Picard"))
        self.lookup_button.setText(_("&Submit disc ID"))
        self.cancel_button.setText(_("&Cancel"))
