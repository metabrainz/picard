# Form implementation generated from reading ui file 'ui/options_lookup.ui'
#
# Created by: PyQt6 UI code generator 6.11.0
#
# Automatically generated - do not edit.
# Use `python setup.py build_ui` to update it.

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import gettext as _


class Ui_LookupOptionsPage(object):
    def setupUi(self, LookupOptionsPage):
        LookupOptionsPage.setObjectName("LookupOptionsPage")
        LookupOptionsPage.resize(403, 200)
        self.vboxlayout = QtWidgets.QVBoxLayout(LookupOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")
        self.lookup_box = QtWidgets.QGroupBox(parent=LookupOptionsPage)
        self.lookup_box.setObjectName("lookup_box")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.lookup_box)
        self.verticalLayout.setObjectName("verticalLayout")
        self.analyze_new_files = QtWidgets.QCheckBox(parent=self.lookup_box)
        self.analyze_new_files.setObjectName("analyze_new_files")
        self.verticalLayout.addWidget(self.analyze_new_files)
        self.cluster_new_files = QtWidgets.QCheckBox(parent=self.lookup_box)
        self.cluster_new_files.setObjectName("cluster_new_files")
        self.verticalLayout.addWidget(self.cluster_new_files)
        self.ignore_file_mbids = QtWidgets.QCheckBox(parent=self.lookup_box)
        self.ignore_file_mbids.setObjectName("ignore_file_mbids")
        self.verticalLayout.addWidget(self.ignore_file_mbids)
        self.vboxlayout.addWidget(self.lookup_box)
        self.query_box = QtWidgets.QGroupBox(parent=LookupOptionsPage)
        self.query_box.setObjectName("query_box")
        self.query_vlayout = QtWidgets.QVBoxLayout(self.query_box)
        self.query_vlayout.setObjectName("query_vlayout")
        self.query_layout = QtWidgets.QHBoxLayout()
        self.query_layout.setObjectName("query_layout")
        self.label_query_limit = QtWidgets.QLabel(parent=self.query_box)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_query_limit.sizePolicy().hasHeightForWidth())
        self.label_query_limit.setSizePolicy(sizePolicy)
        self.label_query_limit.setObjectName("label_query_limit")
        self.query_layout.addWidget(self.label_query_limit)
        self.query_limit = QtWidgets.QComboBox(parent=self.query_box)
        self.query_limit.setCurrentText("50")
        self.query_limit.setObjectName("query_limit")
        self.query_limit.addItem("")
        self.query_limit.setItemText(0, "25")
        self.query_limit.addItem("")
        self.query_limit.setItemText(1, "50")
        self.query_limit.addItem("")
        self.query_limit.setItemText(2, "75")
        self.query_limit.addItem("")
        self.query_limit.setItemText(3, "100")
        self.query_layout.addWidget(self.query_limit)
        self.query_vlayout.addLayout(self.query_layout)
        self.builtin_search = QtWidgets.QCheckBox(parent=self.query_box)
        self.builtin_search.setObjectName("builtin_search")
        self.query_vlayout.addWidget(self.builtin_search)
        self.use_adv_search_syntax = QtWidgets.QCheckBox(parent=self.query_box)
        self.use_adv_search_syntax.setObjectName("use_adv_search_syntax")
        self.query_vlayout.addWidget(self.use_adv_search_syntax)
        self.vboxlayout.addWidget(self.query_box)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_query_limit.setBuddy(self.query_limit)

        self.retranslateUi(LookupOptionsPage)
        self.query_limit.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(LookupOptionsPage)
        LookupOptionsPage.setTabOrder(self.analyze_new_files, self.cluster_new_files)
        LookupOptionsPage.setTabOrder(self.cluster_new_files, self.ignore_file_mbids)
        LookupOptionsPage.setTabOrder(self.ignore_file_mbids, self.query_limit)
        LookupOptionsPage.setTabOrder(self.query_limit, self.builtin_search)
        LookupOptionsPage.setTabOrder(self.builtin_search, self.use_adv_search_syntax)

    def retranslateUi(self, LookupOptionsPage):
        self.lookup_box.setTitle(_("File Loading"))
        self.analyze_new_files.setText(_("Automatically scan all new files"))
        self.cluster_new_files.setText(_("Automatically cluster all new files"))
        self.ignore_file_mbids.setText(_("Ignore MBIDs when loading new files"))
        self.query_box.setTitle(_("Query"))
        self.label_query_limit.setText(_("Maximum number of entities to return per MusicBrainz query"))
        self.builtin_search.setText(_("Use builtin search rather than looking in browser"))
        self.use_adv_search_syntax.setText(_("Use advanced query syntax"))
