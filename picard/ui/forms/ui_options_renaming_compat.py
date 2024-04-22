# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_renaming_compat.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_RenamingCompatOptionsPage(object):
    def setupUi(self, RenamingCompatOptionsPage):
        if not RenamingCompatOptionsPage.objectName():
            RenamingCompatOptionsPage.setObjectName(u"RenamingCompatOptionsPage")
        RenamingCompatOptionsPage.setEnabled(True)
        RenamingCompatOptionsPage.resize(453, 332)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(RenamingCompatOptionsPage.sizePolicy().hasHeightForWidth())
        RenamingCompatOptionsPage.setSizePolicy(sizePolicy)
        self.verticalLayout_5 = QVBoxLayout(RenamingCompatOptionsPage)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.ascii_filenames = QCheckBox(RenamingCompatOptionsPage)
        self.ascii_filenames.setObjectName(u"ascii_filenames")

        self.verticalLayout_5.addWidget(self.ascii_filenames)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.windows_compatibility = QCheckBox(RenamingCompatOptionsPage)
        self.windows_compatibility.setObjectName(u"windows_compatibility")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.windows_compatibility.sizePolicy().hasHeightForWidth())
        self.windows_compatibility.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.windows_compatibility)

        self.btn_windows_compatibility_change = QPushButton(RenamingCompatOptionsPage)
        self.btn_windows_compatibility_change.setObjectName(u"btn_windows_compatibility_change")
        self.btn_windows_compatibility_change.setEnabled(False)

        self.horizontalLayout.addWidget(self.btn_windows_compatibility_change)


        self.verticalLayout_5.addLayout(self.horizontalLayout)

        self.windows_long_paths = QCheckBox(RenamingCompatOptionsPage)
        self.windows_long_paths.setObjectName(u"windows_long_paths")
        self.windows_long_paths.setEnabled(False)

        self.verticalLayout_5.addWidget(self.windows_long_paths)

        self.replace_spaces_with_underscores = QCheckBox(RenamingCompatOptionsPage)
        self.replace_spaces_with_underscores.setObjectName(u"replace_spaces_with_underscores")

        self.verticalLayout_5.addWidget(self.replace_spaces_with_underscores)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_replace_dir_separator = QLabel(RenamingCompatOptionsPage)
        self.label_replace_dir_separator.setObjectName(u"label_replace_dir_separator")
        sizePolicy.setHeightForWidth(self.label_replace_dir_separator.sizePolicy().hasHeightForWidth())
        self.label_replace_dir_separator.setSizePolicy(sizePolicy)

        self.horizontalLayout_2.addWidget(self.label_replace_dir_separator)

        self.replace_dir_separator = QLineEdit(RenamingCompatOptionsPage)
        self.replace_dir_separator.setObjectName(u"replace_dir_separator")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.replace_dir_separator.sizePolicy().hasHeightForWidth())
        self.replace_dir_separator.setSizePolicy(sizePolicy2)
        self.replace_dir_separator.setMaximumSize(QSize(20, 16777215))
        self.replace_dir_separator.setText(u"_")
        self.replace_dir_separator.setMaxLength(1)

        self.horizontalLayout_2.addWidget(self.replace_dir_separator)


        self.verticalLayout_5.addLayout(self.horizontalLayout_2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer)

        self.example_selection_note = QLabel(RenamingCompatOptionsPage)
        self.example_selection_note.setObjectName(u"example_selection_note")
        self.example_selection_note.setWordWrap(True)

        self.verticalLayout_5.addWidget(self.example_selection_note)

        QWidget.setTabOrder(self.ascii_filenames, self.windows_compatibility)
        QWidget.setTabOrder(self.windows_compatibility, self.btn_windows_compatibility_change)
        QWidget.setTabOrder(self.btn_windows_compatibility_change, self.windows_long_paths)
        QWidget.setTabOrder(self.windows_long_paths, self.replace_spaces_with_underscores)
        QWidget.setTabOrder(self.replace_spaces_with_underscores, self.replace_dir_separator)

        self.retranslateUi(RenamingCompatOptionsPage)
        self.windows_compatibility.toggled.connect(self.windows_long_paths.setEnabled)
        self.windows_compatibility.toggled.connect(self.btn_windows_compatibility_change.setEnabled)

        QMetaObject.connectSlotsByName(RenamingCompatOptionsPage)
    # setupUi

    def retranslateUi(self, RenamingCompatOptionsPage):
        self.ascii_filenames.setText(_(u"Replace non-ASCII characters"))
        self.windows_compatibility.setText(_(u"Windows compatibility"))
        self.btn_windows_compatibility_change.setText(_(u"Customize\u2026"))
        self.windows_long_paths.setText(_(u"Allow paths longer than 259 characters"))
        self.replace_spaces_with_underscores.setText(_(u"Replace spaces with underscores"))
        self.label_replace_dir_separator.setText(_(u"Replace directory separators with:"))
        self.example_selection_note.setText("")
        pass
    # retranslateUi

