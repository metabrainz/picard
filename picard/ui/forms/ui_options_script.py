# Form implementation generated from reading ui file 'ui/options_script.ui'
#
# Created by: PyQt6 UI code generator 6.6.1
#
# Automatically generated - do not edit.
# Use `python setup.py build_ui` to update it.

from PySide6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import gettext as _


class Ui_ScriptingOptionsPage(object):
    def setupUi(self, ScriptingOptionsPage):
        ScriptingOptionsPage.setObjectName("ScriptingOptionsPage")
        ScriptingOptionsPage.resize(605, 551)
        self.vboxlayout = QtWidgets.QVBoxLayout(ScriptingOptionsPage)
        self.vboxlayout.setContentsMargins(9, 9, 9, 0)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.enable_tagger_scripts = QtWidgets.QGroupBox(parent=ScriptingOptionsPage)
        self.enable_tagger_scripts.setCheckable(True)
        self.enable_tagger_scripts.setObjectName("enable_tagger_scripts")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.enable_tagger_scripts)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(-1, -1, -1, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(parent=self.enable_tagger_scripts)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.scripting_options_splitter = QtWidgets.QSplitter(parent=self.enable_tagger_scripts)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scripting_options_splitter.sizePolicy().hasHeightForWidth())
        self.scripting_options_splitter.setSizePolicy(sizePolicy)
        self.scripting_options_splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.scripting_options_splitter.setChildrenCollapsible(False)
        self.scripting_options_splitter.setObjectName("scripting_options_splitter")
        self.script_list = ScriptListWidget(parent=self.scripting_options_splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.script_list.sizePolicy().hasHeightForWidth())
        self.script_list.setSizePolicy(sizePolicy)
        self.script_list.setMinimumSize(QtCore.QSize(120, 0))
        self.script_list.setObjectName("script_list")
        self.formWidget = QtWidgets.QWidget(parent=self.scripting_options_splitter)
        self.formWidget.setObjectName("formWidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.formWidget)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tagger_script = ScriptTextEdit(parent=self.formWidget)
        self.tagger_script.setAcceptRichText(False)
        self.tagger_script.setObjectName("tagger_script")
        self.verticalLayout_2.addWidget(self.tagger_script)
        self.verticalLayout.addWidget(self.scripting_options_splitter)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.move_up_button = QtWidgets.QToolButton(parent=self.enable_tagger_scripts)
        icon = QtGui.QIcon.fromTheme(":/images/16x16/go-up.png")
        self.move_up_button.setIcon(icon)
        self.move_up_button.setObjectName("move_up_button")
        self.horizontalLayout.addWidget(self.move_up_button)
        self.move_down_button = QtWidgets.QToolButton(parent=self.enable_tagger_scripts)
        icon = QtGui.QIcon.fromTheme(":/images/16x16/go-down.png")
        self.move_down_button.setIcon(icon)
        self.move_down_button.setObjectName("move_down_button")
        self.horizontalLayout.addWidget(self.move_down_button)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.add_button = QtWidgets.QToolButton(parent=self.enable_tagger_scripts)
        self.add_button.setObjectName("add_button")
        self.horizontalLayout.addWidget(self.add_button)
        self.remove_button = QtWidgets.QToolButton(parent=self.enable_tagger_scripts)
        self.remove_button.setObjectName("remove_button")
        self.horizontalLayout.addWidget(self.remove_button)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.import_button = QtWidgets.QToolButton(parent=self.enable_tagger_scripts)
        self.import_button.setObjectName("import_button")
        self.horizontalLayout.addWidget(self.import_button)
        self.export_button = QtWidgets.QToolButton(parent=self.enable_tagger_scripts)
        self.export_button.setObjectName("export_button")
        self.horizontalLayout.addWidget(self.export_button)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.scripting_documentation_button = QtWidgets.QToolButton(parent=self.enable_tagger_scripts)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scripting_documentation_button.sizePolicy().hasHeightForWidth())
        self.scripting_documentation_button.setSizePolicy(sizePolicy)
        self.scripting_documentation_button.setObjectName("scripting_documentation_button")
        self.horizontalLayout.addWidget(self.scripting_documentation_button)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.script_error = QtWidgets.QLabel(parent=self.enable_tagger_scripts)
        self.script_error.setText("")
        self.script_error.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.script_error.setObjectName("script_error")
        self.verticalLayout.addWidget(self.script_error)
        self.vboxlayout.addWidget(self.enable_tagger_scripts)

        self.retranslateUi(ScriptingOptionsPage)
        self.add_button.clicked.connect(self.script_list.add_script) # type: ignore
        self.tagger_script.textChanged.connect(ScriptingOptionsPage.live_update_and_check) # type: ignore
        self.script_list.itemSelectionChanged.connect(ScriptingOptionsPage.script_selected) # type: ignore
        self.remove_button.clicked.connect(self.script_list.remove_selected_script) # type: ignore
        self.enable_tagger_scripts.toggled['bool'].connect(ScriptingOptionsPage.enable_tagger_scripts_toggled) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(ScriptingOptionsPage)
        ScriptingOptionsPage.setTabOrder(self.enable_tagger_scripts, self.script_list)
        ScriptingOptionsPage.setTabOrder(self.script_list, self.tagger_script)
        ScriptingOptionsPage.setTabOrder(self.tagger_script, self.move_up_button)
        ScriptingOptionsPage.setTabOrder(self.move_up_button, self.move_down_button)
        ScriptingOptionsPage.setTabOrder(self.move_down_button, self.remove_button)

    def retranslateUi(self, ScriptingOptionsPage):
        self.enable_tagger_scripts.setTitle(_("Enable Tagger Script(s)"))
        self.label.setText(_("Tagger scripts that have been activated below will be executed automatically for each track of a release loaded from MusicBrainz."))
        self.tagger_script.setPlaceholderText(_("Enter your tagger script here."))
        self.move_up_button.setToolTip(_("Move tagger script up"))
        self.move_down_button.setToolTip(_("Move tagger script down"))
        self.add_button.setToolTip(_("Add new tagger script"))
        self.add_button.setText(_("Add new tagger script"))
        self.remove_button.setToolTip(_("Remove the selected tagger script"))
        self.remove_button.setText(_("Remove tagger script"))
        self.import_button.setText(_("Import"))
        self.export_button.setText(_("Export"))
        self.scripting_documentation_button.setText(_("Documentation"))
from picard.ui.widgets.scriptlistwidget import ScriptListWidget
from picard.ui.widgets.scripttextedit import ScriptTextEdit
