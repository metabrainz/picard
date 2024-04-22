# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_script.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## Use `python setup.py build_ui` to update it.
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QLabel,
    QListWidgetItem, QSizePolicy, QSpacerItem, QSplitter,
    QToolButton, QVBoxLayout, QWidget)

from picard.ui.widgets.scriptlistwidget import ScriptListWidget
from picard.ui.widgets.scripttextedit import ScriptTextEdit

from picard.i18n import gettext as _

class Ui_ScriptingOptionsPage(object):
    def setupUi(self, ScriptingOptionsPage):
        if not ScriptingOptionsPage.objectName():
            ScriptingOptionsPage.setObjectName(u"ScriptingOptionsPage")
        ScriptingOptionsPage.resize(605, 551)
        self.vboxLayout = QVBoxLayout(ScriptingOptionsPage)
        self.vboxLayout.setSpacing(6)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.vboxLayout.setContentsMargins(9, 9, 9, 0)
        self.enable_tagger_scripts = QGroupBox(ScriptingOptionsPage)
        self.enable_tagger_scripts.setObjectName(u"enable_tagger_scripts")
        self.enable_tagger_scripts.setCheckable(True)
        self.verticalLayout = QVBoxLayout(self.enable_tagger_scripts)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(-1, -1, -1, 0)
        self.label = QLabel(self.enable_tagger_scripts)
        self.label.setObjectName(u"label")
        self.label.setWordWrap(True)

        self.horizontalLayout_2.addWidget(self.label)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.scripting_options_splitter = QSplitter(self.enable_tagger_scripts)
        self.scripting_options_splitter.setObjectName(u"scripting_options_splitter")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scripting_options_splitter.sizePolicy().hasHeightForWidth())
        self.scripting_options_splitter.setSizePolicy(sizePolicy)
        self.scripting_options_splitter.setOrientation(Qt.Horizontal)
        self.scripting_options_splitter.setChildrenCollapsible(False)
        self.script_list = ScriptListWidget(self.scripting_options_splitter)
        self.script_list.setObjectName(u"script_list")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.script_list.sizePolicy().hasHeightForWidth())
        self.script_list.setSizePolicy(sizePolicy1)
        self.script_list.setMinimumSize(QSize(120, 0))
        self.scripting_options_splitter.addWidget(self.script_list)
        self.formWidget = QWidget(self.scripting_options_splitter)
        self.formWidget.setObjectName(u"formWidget")
        self.verticalLayout_2 = QVBoxLayout(self.formWidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.tagger_script = ScriptTextEdit(self.formWidget)
        self.tagger_script.setObjectName(u"tagger_script")
        self.tagger_script.setAcceptRichText(False)

        self.verticalLayout_2.addWidget(self.tagger_script)

        self.scripting_options_splitter.addWidget(self.formWidget)

        self.verticalLayout.addWidget(self.scripting_options_splitter)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.move_up_button = QToolButton(self.enable_tagger_scripts)
        self.move_up_button.setObjectName(u"move_up_button")
        icon = QIcon()
        iconThemeName = u":/images/16x16/go-up.png"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.move_up_button.setIcon(icon)

        self.horizontalLayout.addWidget(self.move_up_button)

        self.move_down_button = QToolButton(self.enable_tagger_scripts)
        self.move_down_button.setObjectName(u"move_down_button")
        icon1 = QIcon()
        iconThemeName = u":/images/16x16/go-down.png"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.move_down_button.setIcon(icon1)

        self.horizontalLayout.addWidget(self.move_down_button)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.add_button = QToolButton(self.enable_tagger_scripts)
        self.add_button.setObjectName(u"add_button")

        self.horizontalLayout.addWidget(self.add_button)

        self.remove_button = QToolButton(self.enable_tagger_scripts)
        self.remove_button.setObjectName(u"remove_button")

        self.horizontalLayout.addWidget(self.remove_button)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_3)

        self.import_button = QToolButton(self.enable_tagger_scripts)
        self.import_button.setObjectName(u"import_button")

        self.horizontalLayout.addWidget(self.import_button)

        self.export_button = QToolButton(self.enable_tagger_scripts)
        self.export_button.setObjectName(u"export_button")

        self.horizontalLayout.addWidget(self.export_button)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.scripting_documentation_button = QToolButton(self.enable_tagger_scripts)
        self.scripting_documentation_button.setObjectName(u"scripting_documentation_button")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.scripting_documentation_button.sizePolicy().hasHeightForWidth())
        self.scripting_documentation_button.setSizePolicy(sizePolicy2)

        self.horizontalLayout.addWidget(self.scripting_documentation_button)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.script_error = QLabel(self.enable_tagger_scripts)
        self.script_error.setObjectName(u"script_error")
        self.script_error.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.script_error)


        self.vboxLayout.addWidget(self.enable_tagger_scripts)

        QWidget.setTabOrder(self.enable_tagger_scripts, self.script_list)
        QWidget.setTabOrder(self.script_list, self.tagger_script)
        QWidget.setTabOrder(self.tagger_script, self.move_up_button)
        QWidget.setTabOrder(self.move_up_button, self.move_down_button)
        QWidget.setTabOrder(self.move_down_button, self.remove_button)

        self.retranslateUi(ScriptingOptionsPage)
        self.add_button.clicked.connect(self.script_list.add_script)
        self.tagger_script.textChanged.connect(ScriptingOptionsPage.live_update_and_check)
        self.script_list.itemSelectionChanged.connect(ScriptingOptionsPage.script_selected)
        self.remove_button.clicked.connect(self.script_list.remove_selected_script)
        self.enable_tagger_scripts.toggled.connect(ScriptingOptionsPage.enable_tagger_scripts_toggled)

        QMetaObject.connectSlotsByName(ScriptingOptionsPage)
    # setupUi

    def retranslateUi(self, ScriptingOptionsPage):
        self.enable_tagger_scripts.setTitle(_(u"Enable Tagger Script(s)"))
        self.label.setText(_(u"Tagger scripts that have been activated below will be executed automatically for each track of a release loaded from MusicBrainz."))
        self.tagger_script.setPlaceholderText(_(u"Enter your tagger script here."))
#if QT_CONFIG(tooltip)
        self.move_up_button.setToolTip(_(u"Move tagger script up"))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.move_down_button.setToolTip(_(u"Move tagger script down"))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.add_button.setToolTip(_(u"Add new tagger script"))
#endif // QT_CONFIG(tooltip)
        self.add_button.setText(_(u"Add new tagger script"))
#if QT_CONFIG(tooltip)
        self.remove_button.setToolTip(_(u"Remove the selected tagger script"))
#endif // QT_CONFIG(tooltip)
        self.remove_button.setText(_(u"Remove tagger script"))
        self.import_button.setText(_(u"Import"))
        self.export_button.setText(_(u"Export"))
        self.scripting_documentation_button.setText(_(u"Documentation"))
        self.script_error.setText("")
        pass
    # retranslateUi

