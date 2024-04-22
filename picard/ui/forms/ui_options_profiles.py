# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_profiles.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QDialogButtonBox,
    QGroupBox, QHBoxLayout, QHeaderView, QListWidgetItem,
    QSizePolicy, QSpacerItem, QSplitter, QToolButton,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from picard.ui.widgets.profilelistwidget import ProfileListWidget

from picard.i18n import gettext as _

class Ui_ProfileEditorDialog(object):
    def setupUi(self, ProfileEditorDialog):
        if not ProfileEditorDialog.objectName():
            ProfileEditorDialog.setObjectName(u"ProfileEditorDialog")
        ProfileEditorDialog.resize(430, 551)
        self.vboxLayout = QVBoxLayout(ProfileEditorDialog)
        self.vboxLayout.setSpacing(6)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.vboxLayout.setContentsMargins(9, 9, 9, 9)
        self.option_profiles_groupbox = QGroupBox(ProfileEditorDialog)
        self.option_profiles_groupbox.setObjectName(u"option_profiles_groupbox")
        self.option_profiles_groupbox.setCheckable(False)
        self.verticalLayout = QVBoxLayout(self.option_profiles_groupbox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.profile_editor_splitter = QSplitter(self.option_profiles_groupbox)
        self.profile_editor_splitter.setObjectName(u"profile_editor_splitter")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.profile_editor_splitter.sizePolicy().hasHeightForWidth())
        self.profile_editor_splitter.setSizePolicy(sizePolicy)
        self.profile_editor_splitter.setOrientation(Qt.Horizontal)
        self.profile_editor_splitter.setChildrenCollapsible(False)
        self.profile_list = ProfileListWidget(self.profile_editor_splitter)
        self.profile_list.setObjectName(u"profile_list")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.profile_list.sizePolicy().hasHeightForWidth())
        self.profile_list.setSizePolicy(sizePolicy1)
        self.profile_list.setMinimumSize(QSize(120, 0))
        self.profile_editor_splitter.addWidget(self.profile_list)
        self.settings_tree = QTreeWidget(self.profile_editor_splitter)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"1");
        self.settings_tree.setHeaderItem(__qtreewidgetitem)
        self.settings_tree.setObjectName(u"settings_tree")
        self.settings_tree.setSelectionMode(QAbstractItemView.MultiSelection)
        self.settings_tree.setColumnCount(1)
        self.profile_editor_splitter.addWidget(self.settings_tree)
        self.settings_tree.header().setVisible(True)

        self.verticalLayout.addWidget(self.profile_editor_splitter)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.move_up_button = QToolButton(self.option_profiles_groupbox)
        self.move_up_button.setObjectName(u"move_up_button")
        icon = QIcon()
        iconThemeName = u":/images/16x16/go-up.png"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.move_up_button.setIcon(icon)

        self.horizontalLayout.addWidget(self.move_up_button)

        self.move_down_button = QToolButton(self.option_profiles_groupbox)
        self.move_down_button.setObjectName(u"move_down_button")
        icon1 = QIcon()
        iconThemeName = u":/images/16x16/go-down.png"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.move_down_button.setIcon(icon1)

        self.horizontalLayout.addWidget(self.move_down_button)

        self.profile_list_buttonbox = QDialogButtonBox(self.option_profiles_groupbox)
        self.profile_list_buttonbox.setObjectName(u"profile_list_buttonbox")
        self.profile_list_buttonbox.setMinimumSize(QSize(0, 10))
        self.profile_list_buttonbox.setStandardButtons(QDialogButtonBox.NoButton)

        self.horizontalLayout.addWidget(self.profile_list_buttonbox)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.vboxLayout.addWidget(self.option_profiles_groupbox)


        self.retranslateUi(ProfileEditorDialog)

        QMetaObject.connectSlotsByName(ProfileEditorDialog)
    # setupUi

    def retranslateUi(self, ProfileEditorDialog):
        self.option_profiles_groupbox.setTitle(_(u"Option Profile(s)"))
#if QT_CONFIG(tooltip)
        self.move_up_button.setToolTip(_(u"Move profile up"))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.move_down_button.setToolTip(_(u"Move profile down"))
#endif // QT_CONFIG(tooltip)
        pass
    # retranslateUi

