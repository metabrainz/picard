# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_interface.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_InterfaceOptionsPage(object):
    def setupUi(self, InterfaceOptionsPage):
        if not InterfaceOptionsPage.objectName():
            InterfaceOptionsPage.setObjectName(u"InterfaceOptionsPage")
        InterfaceOptionsPage.resize(466, 543)
        self.vboxLayout = QVBoxLayout(InterfaceOptionsPage)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.groupBox = QGroupBox(InterfaceOptionsPage)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_3 = QVBoxLayout(self.groupBox)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.toolbar_show_labels = QCheckBox(self.groupBox)
        self.toolbar_show_labels.setObjectName(u"toolbar_show_labels")

        self.verticalLayout_3.addWidget(self.toolbar_show_labels)

        self.show_menu_icons = QCheckBox(self.groupBox)
        self.show_menu_icons.setObjectName(u"show_menu_icons")

        self.verticalLayout_3.addWidget(self.show_menu_icons)

        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.verticalLayout_3.addWidget(self.label)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.ui_language = QComboBox(self.groupBox)
        self.ui_language.setObjectName(u"ui_language")

        self.horizontalLayout.addWidget(self.ui_language)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.label_theme = QLabel(self.groupBox)
        self.label_theme.setObjectName(u"label_theme")

        self.verticalLayout_3.addWidget(self.label_theme)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.ui_theme = QComboBox(self.groupBox)
        self.ui_theme.setObjectName(u"ui_theme")

        self.horizontalLayout_2.addWidget(self.ui_theme)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)


        self.verticalLayout_3.addLayout(self.horizontalLayout_2)


        self.vboxLayout.addWidget(self.groupBox)

        self.miscellaneous_box = QGroupBox(InterfaceOptionsPage)
        self.miscellaneous_box.setObjectName(u"miscellaneous_box")
        self.vboxLayout1 = QVBoxLayout(self.miscellaneous_box)
        self.vboxLayout1.setObjectName(u"vboxLayout1")
        self.allow_multi_dirs_selection = QCheckBox(self.miscellaneous_box)
        self.allow_multi_dirs_selection.setObjectName(u"allow_multi_dirs_selection")

        self.vboxLayout1.addWidget(self.allow_multi_dirs_selection)

        self.builtin_search = QCheckBox(self.miscellaneous_box)
        self.builtin_search.setObjectName(u"builtin_search")

        self.vboxLayout1.addWidget(self.builtin_search)

        self.use_adv_search_syntax = QCheckBox(self.miscellaneous_box)
        self.use_adv_search_syntax.setObjectName(u"use_adv_search_syntax")

        self.vboxLayout1.addWidget(self.use_adv_search_syntax)

        self.new_user_dialog = QCheckBox(self.miscellaneous_box)
        self.new_user_dialog.setObjectName(u"new_user_dialog")

        self.vboxLayout1.addWidget(self.new_user_dialog)

        self.quit_confirmation = QCheckBox(self.miscellaneous_box)
        self.quit_confirmation.setObjectName(u"quit_confirmation")

        self.vboxLayout1.addWidget(self.quit_confirmation)

        self.file_save_warning = QCheckBox(self.miscellaneous_box)
        self.file_save_warning.setObjectName(u"file_save_warning")

        self.vboxLayout1.addWidget(self.file_save_warning)

        self.filebrowser_horizontal_autoscroll = QCheckBox(self.miscellaneous_box)
        self.filebrowser_horizontal_autoscroll.setObjectName(u"filebrowser_horizontal_autoscroll")

        self.vboxLayout1.addWidget(self.filebrowser_horizontal_autoscroll)

        self.starting_directory = QCheckBox(self.miscellaneous_box)
        self.starting_directory.setObjectName(u"starting_directory")

        self.vboxLayout1.addWidget(self.starting_directory)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(2)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.starting_directory_path = QLineEdit(self.miscellaneous_box)
        self.starting_directory_path.setObjectName(u"starting_directory_path")
        self.starting_directory_path.setEnabled(False)

        self.horizontalLayout_4.addWidget(self.starting_directory_path)

        self.starting_directory_browse = QPushButton(self.miscellaneous_box)
        self.starting_directory_browse.setObjectName(u"starting_directory_browse")
        self.starting_directory_browse.setEnabled(False)

        self.horizontalLayout_4.addWidget(self.starting_directory_browse)


        self.vboxLayout1.addLayout(self.horizontalLayout_4)

        self.ui_theme_container = QWidget(self.miscellaneous_box)
        self.ui_theme_container.setObjectName(u"ui_theme_container")
        self.ui_theme_container.setEnabled(True)
        self.verticalLayout_2 = QVBoxLayout(self.ui_theme_container)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)

        self.vboxLayout1.addWidget(self.ui_theme_container)


        self.vboxLayout.addWidget(self.miscellaneous_box)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vboxLayout.addItem(self.verticalSpacer)

        QWidget.setTabOrder(self.toolbar_show_labels, self.show_menu_icons)
        QWidget.setTabOrder(self.show_menu_icons, self.ui_language)
        QWidget.setTabOrder(self.ui_language, self.ui_theme)
        QWidget.setTabOrder(self.ui_theme, self.allow_multi_dirs_selection)
        QWidget.setTabOrder(self.allow_multi_dirs_selection, self.builtin_search)
        QWidget.setTabOrder(self.builtin_search, self.use_adv_search_syntax)
        QWidget.setTabOrder(self.use_adv_search_syntax, self.new_user_dialog)
        QWidget.setTabOrder(self.new_user_dialog, self.quit_confirmation)
        QWidget.setTabOrder(self.quit_confirmation, self.file_save_warning)
        QWidget.setTabOrder(self.file_save_warning, self.filebrowser_horizontal_autoscroll)
        QWidget.setTabOrder(self.filebrowser_horizontal_autoscroll, self.starting_directory)
        QWidget.setTabOrder(self.starting_directory, self.starting_directory_path)
        QWidget.setTabOrder(self.starting_directory_path, self.starting_directory_browse)

        self.retranslateUi(InterfaceOptionsPage)

        QMetaObject.connectSlotsByName(InterfaceOptionsPage)
    # setupUi

    def retranslateUi(self, InterfaceOptionsPage):
        self.groupBox.setTitle(_(u"Appearance"))
        self.toolbar_show_labels.setText(_(u"Show text labels under icons"))
        self.show_menu_icons.setText(_(u"Show icons in menus"))
        self.label.setText(_(u"User interface language:"))
        self.label_theme.setText(_(u"User interface color theme:"))
        self.miscellaneous_box.setTitle(_(u"Miscellaneous"))
        self.allow_multi_dirs_selection.setText(_(u"Allow selection of multiple directories"))
        self.builtin_search.setText(_(u"Use builtin search rather than looking in browser"))
        self.use_adv_search_syntax.setText(_(u"Use advanced query syntax"))
        self.new_user_dialog.setText(_(u"Show the new user dialog when starting Picard"))
        self.quit_confirmation.setText(_(u"Show a quit confirmation dialog for unsaved changes"))
        self.file_save_warning.setText(_(u"Show a confirmation dialog when saving files"))
        self.filebrowser_horizontal_autoscroll.setText(_(u"Adjust horizontal position in file browser automatically"))
        self.starting_directory.setText(_(u"Begin browsing in the following directory:"))
        self.starting_directory_browse.setText(_(u"Browse\u2026"))
        pass
    # retranslateUi

