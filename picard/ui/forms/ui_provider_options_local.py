# Form implementation generated from reading ui file 'ui/provider_options_local.ui'
#
# Created by: PyQt6 UI code generator 6.9.1
#
# Automatically generated - do not edit.
# Use `python setup.py build_ui` to update it.

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import gettext as _


class Ui_LocalOptions(object):
    def setupUi(self, LocalOptions):
        LocalOptions.setObjectName("LocalOptions")
        LocalOptions.resize(472, 215)
        self.verticalLayout = QtWidgets.QVBoxLayout(LocalOptions)
        self.verticalLayout.setObjectName("verticalLayout")
        self.local_cover_use_script = QtWidgets.QCheckBox(parent=LocalOptions)
        self.local_cover_use_script.setObjectName("local_cover_use_script")
        self.verticalLayout.addWidget(self.local_cover_use_script)
        self.local_cover_regex_label = QtWidgets.QLabel(parent=LocalOptions)
        self.local_cover_regex_label.setObjectName("local_cover_regex_label")
        self.verticalLayout.addWidget(self.local_cover_regex_label)
        self.local_cover_regex_edit = QtWidgets.QLineEdit(parent=LocalOptions)
        self.local_cover_regex_edit.setObjectName("local_cover_regex_edit")
        self.verticalLayout.addWidget(self.local_cover_regex_edit)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.local_cover_regex_error = QtWidgets.QLabel(parent=LocalOptions)
        self.local_cover_regex_error.setText("")
        self.local_cover_regex_error.setObjectName("local_cover_regex_error")
        self.horizontalLayout_2.addWidget(self.local_cover_regex_error)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.regex_note = QtWidgets.QLabel(parent=LocalOptions)
        font = QtGui.QFont()
        font.setItalic(True)
        self.regex_note.setFont(font)
        self.regex_note.setWordWrap(True)
        self.regex_note.setObjectName("regex_note")
        self.verticalLayout.addWidget(self.regex_note)
        self.local_cover_script_label = QtWidgets.QLabel(parent=LocalOptions)
        self.local_cover_script_label.setObjectName("local_cover_script_label")
        self.verticalLayout.addWidget(self.local_cover_script_label)
        self.local_cover_script_edit = ScriptTextEdit(parent=LocalOptions)
        self.local_cover_script_edit.setMaximumSize(QtCore.QSize(16777215, 100))
        self.local_cover_script_edit.setObjectName("local_cover_script_edit")
        self.verticalLayout.addWidget(self.local_cover_script_edit)
        self.script_preview_label = QtWidgets.QLabel(parent=LocalOptions)
        self.script_preview_label.setObjectName("script_preview_label")
        self.verticalLayout.addWidget(self.script_preview_label)
        self.script_preview_value = QtWidgets.QLabel(parent=LocalOptions)
        self.script_preview_value.setText("")
        self.script_preview_value.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.script_preview_value.setWordWrap(True)
        self.script_preview_value.setObjectName("script_preview_value")
        self.verticalLayout.addWidget(self.script_preview_value)
        self.script_note = QtWidgets.QLabel(parent=LocalOptions)
        font = QtGui.QFont()
        font.setItalic(True)
        self.script_note.setFont(font)
        self.script_note.setWordWrap(True)
        self.script_note.setObjectName("script_note")
        self.verticalLayout.addWidget(self.script_note)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(LocalOptions)
        QtCore.QMetaObject.connectSlotsByName(LocalOptions)

    def retranslateUi(self, LocalOptions):
        LocalOptions.setWindowTitle(_("Form"))
        self.local_cover_use_script.setText(_("Use scripting syntax instead of regular expression"))
        self.local_cover_regex_label.setText(_("Local cover art files match the following regular expression:"))
        self.regex_note.setText(_("First group in the regular expression, if any, will be used as type, ie. cover-back-spine.jpg will be set as types Back + Spine. If no type is found, it will default to Front type."))
        self.local_cover_script_label.setText(_("Local cover art files match the following script:"))
        self.script_preview_label.setText(_("Example:"))
        self.script_note.setText(_("The script will be evaluated for each file\'s metadata. Use variables like %albumartist%, %album%, etc."))
from picard.ui.widgets.scripttextedit import ScriptTextEdit
