# Form implementation generated from reading ui file 'ui/options_advanced_sessions.ui'
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


class Ui_SessionsOptionsPage(object):
    def setupUi(self, SessionsOptionsPage):
        SessionsOptionsPage.setObjectName("SessionsOptionsPage")
        SessionsOptionsPage.resize(397, 557)
        self.vboxlayout = QtWidgets.QVBoxLayout(SessionsOptionsPage)
        self.vboxlayout.setSpacing(2)
        self.vboxlayout.setObjectName("vboxlayout")
        self.page_title = QtWidgets.QLabel(parent=SessionsOptionsPage)
        font = QtGui.QFont()
        font.setBold(True)
        self.page_title.setFont(font)
        self.page_title.setObjectName("page_title")
        self.vboxlayout.addWidget(self.page_title)
        spacerItem = QtWidgets.QSpacerItem(20, 4, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        self.vboxlayout.addItem(spacerItem)
        self.sessions_description = QtWidgets.QLabel(parent=SessionsOptionsPage)
        self.sessions_description.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.sessions_description.setWordWrap(True)
        self.sessions_description.setObjectName("sessions_description")
        self.vboxlayout.addWidget(self.sessions_description)
        spacerItem1 = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        self.vboxlayout.addItem(spacerItem1)
        self.folder_layout = QtWidgets.QHBoxLayout()
        self.folder_layout.setContentsMargins(-1, 0, -1, -1)
        self.folder_layout.setObjectName("folder_layout")
        self.folder_label = QtWidgets.QLabel(parent=SessionsOptionsPage)
        self.folder_label.setObjectName("folder_label")
        self.folder_layout.addWidget(self.folder_label)
        self.folder_path_edit = QtWidgets.QLineEdit(parent=SessionsOptionsPage)
        self.folder_path_edit.setObjectName("folder_path_edit")
        self.folder_layout.addWidget(self.folder_path_edit)
        self.folder_browse_button = QtWidgets.QToolButton(parent=SessionsOptionsPage)
        self.folder_browse_button.setStyleSheet("border: none;")
        self.folder_browse_button.setText("")
        self.folder_browse_button.setObjectName("folder_browse_button")
        self.folder_layout.addWidget(self.folder_browse_button)
        self.vboxlayout.addLayout(self.folder_layout)
        self.safe_restore_checkbox = QtWidgets.QCheckBox(parent=SessionsOptionsPage)
        self.safe_restore_checkbox.setObjectName("safe_restore_checkbox")
        self.vboxlayout.addWidget(self.safe_restore_checkbox)
        self.load_last_checkbox = QtWidgets.QCheckBox(parent=SessionsOptionsPage)
        self.load_last_checkbox.setObjectName("load_last_checkbox")
        self.vboxlayout.addWidget(self.load_last_checkbox)
        self.autosave_layout = QtWidgets.QHBoxLayout()
        self.autosave_layout.setContentsMargins(-1, 0, -1, -1)
        self.autosave_layout.setObjectName("autosave_layout")
        self.autosave_label = QtWidgets.QLabel(parent=SessionsOptionsPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.autosave_label.sizePolicy().hasHeightForWidth())
        self.autosave_label.setSizePolicy(sizePolicy)
        self.autosave_label.setObjectName("autosave_label")
        self.autosave_layout.addWidget(self.autosave_label)
        self.autosave_spin = QtWidgets.QSpinBox(parent=SessionsOptionsPage)
        self.autosave_spin.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.autosave_spin.setMaximum(1440)
        self.autosave_spin.setObjectName("autosave_spin")
        self.autosave_layout.addWidget(self.autosave_spin)
        self.vboxlayout.addLayout(self.autosave_layout)
        self.backup_checkbox = QtWidgets.QCheckBox(parent=SessionsOptionsPage)
        self.backup_checkbox.setObjectName("backup_checkbox")
        self.vboxlayout.addWidget(self.backup_checkbox)
        self.include_mb_data_checkbox = QtWidgets.QCheckBox(parent=SessionsOptionsPage)
        self.include_mb_data_checkbox.setObjectName("include_mb_data_checkbox")
        self.vboxlayout.addWidget(self.include_mb_data_checkbox)
        self.child_layout = QtWidgets.QHBoxLayout()
        self.child_layout.setContentsMargins(-1, 0, -1, -1)
        self.child_layout.setObjectName("child_layout")
        spacerItem2 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Minimum)
        self.child_layout.addItem(spacerItem2)
        self.no_mb_requests_checkbox = QtWidgets.QCheckBox(parent=SessionsOptionsPage)
        self.no_mb_requests_checkbox.setObjectName("no_mb_requests_checkbox")
        self.child_layout.addWidget(self.no_mb_requests_checkbox)
        self.vboxlayout.addLayout(self.child_layout)
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.vboxlayout.addItem(spacerItem3)

        self.retranslateUi(SessionsOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(SessionsOptionsPage)

    def retranslateUi(self, SessionsOptionsPage):
        self.page_title.setText(_("Sessions Management"))
        self.sessions_description.setText(_("Picard can save and restore your current workspace state as a session file under the main File menu. Sessions preserve file placement (unclustered, clusters, albums, specific tracks, and standalone recordings), your manual metadata edits, and selected configuration options so you can resume work later.\n"
"\n"
"These settings determine how the session files are managed."))
        self.folder_label.setText(_("Sessions directory:"))
        self.safe_restore_checkbox.setText(_("No auto-matching on load"))
        self.load_last_checkbox.setText(_("Load last saved session on startup"))
        self.autosave_label.setText(_("Auto-save every N minutes (0 to disable):"))
        self.backup_checkbox.setText(_("Attempt session backup on unexpected shutdown"))
        self.include_mb_data_checkbox.setText(_("Include MusicBrainz data in saved sessions"))
        self.no_mb_requests_checkbox.setText(_("Do not make MusicBrainz requests on restore"))
