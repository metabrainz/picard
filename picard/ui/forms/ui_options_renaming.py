# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_renaming.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QSizePolicy,
    QSpacerItem, QSplitter, QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_RenamingOptionsPage(object):
    def setupUi(self, RenamingOptionsPage):
        if not RenamingOptionsPage.objectName():
            RenamingOptionsPage.setObjectName(u"RenamingOptionsPage")
        RenamingOptionsPage.setEnabled(True)
        RenamingOptionsPage.resize(453, 489)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(RenamingOptionsPage.sizePolicy().hasHeightForWidth())
        RenamingOptionsPage.setSizePolicy(sizePolicy)
        self.verticalLayout_5 = QVBoxLayout(RenamingOptionsPage)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.move_files = QGroupBox(RenamingOptionsPage)
        self.move_files.setObjectName(u"move_files")
        self.move_files.setFlat(False)
        self.move_files.setCheckable(True)
        self.move_files.setChecked(False)
        self.verticalLayout_4 = QVBoxLayout(self.move_files)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label = QLabel(self.move_files)
        self.label.setObjectName(u"label")

        self.verticalLayout_4.addWidget(self.label)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(2)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.move_files_to = QLineEdit(self.move_files)
        self.move_files_to.setObjectName(u"move_files_to")

        self.horizontalLayout_4.addWidget(self.move_files_to)

        self.move_files_to_browse = QPushButton(self.move_files)
        self.move_files_to_browse.setObjectName(u"move_files_to_browse")

        self.horizontalLayout_4.addWidget(self.move_files_to_browse)


        self.verticalLayout_4.addLayout(self.horizontalLayout_4)

        self.move_additional_files = QCheckBox(self.move_files)
        self.move_additional_files.setObjectName(u"move_additional_files")

        self.verticalLayout_4.addWidget(self.move_additional_files)

        self.move_additional_files_pattern = QLineEdit(self.move_files)
        self.move_additional_files_pattern.setObjectName(u"move_additional_files_pattern")

        self.verticalLayout_4.addWidget(self.move_additional_files_pattern)

        self.delete_empty_dirs = QCheckBox(self.move_files)
        self.delete_empty_dirs.setObjectName(u"delete_empty_dirs")

        self.verticalLayout_4.addWidget(self.delete_empty_dirs)


        self.verticalLayout_5.addWidget(self.move_files)

        self.rename_files = QCheckBox(RenamingOptionsPage)
        self.rename_files.setObjectName(u"rename_files")

        self.verticalLayout_5.addWidget(self.rename_files)

        self.label_2 = QLabel(RenamingOptionsPage)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout_5.addWidget(self.label_2)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.naming_script_selector = QComboBox(RenamingOptionsPage)
        self.naming_script_selector.setObjectName(u"naming_script_selector")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.naming_script_selector.sizePolicy().hasHeightForWidth())
        self.naming_script_selector.setSizePolicy(sizePolicy1)

        self.horizontalLayout_2.addWidget(self.naming_script_selector)

        self.open_script_editor = QPushButton(RenamingOptionsPage)
        self.open_script_editor.setObjectName(u"open_script_editor")

        self.horizontalLayout_2.addWidget(self.open_script_editor)


        self.verticalLayout_5.addLayout(self.horizontalLayout_2)

        self.groupBox = QGroupBox(RenamingOptionsPage)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy2)
        self.groupBox.setMinimumSize(QSize(0, 120))
        self.verticalLayout_6 = QVBoxLayout(self.groupBox)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(3, 3, 3, 3)
        self.renaming_options_examples_splitter = QSplitter(self.groupBox)
        self.renaming_options_examples_splitter.setObjectName(u"renaming_options_examples_splitter")
        self.renaming_options_examples_splitter.setOrientation(Qt.Horizontal)
        self.frame = QFrame(self.renaming_options_examples_splitter)
        self.frame.setObjectName(u"frame")
        self.frame.setMinimumSize(QSize(100, 0))
        self.frame.setFrameShape(QFrame.NoFrame)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout = QVBoxLayout(self.frame)
        self.verticalLayout.setSpacing(3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.example_filename_before_label = QLabel(self.frame)
        self.example_filename_before_label.setObjectName(u"example_filename_before_label")

        self.verticalLayout.addWidget(self.example_filename_before_label)

        self.example_filename_before = QListWidget(self.frame)
        self.example_filename_before.setObjectName(u"example_filename_before")

        self.verticalLayout.addWidget(self.example_filename_before)

        self.renaming_options_examples_splitter.addWidget(self.frame)
        self.frame_2 = QFrame(self.renaming_options_examples_splitter)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setMinimumSize(QSize(100, 0))
        self.frame_2.setFrameShape(QFrame.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frame_2)
        self.verticalLayout_3.setSpacing(3)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.example_filename_after_label = QLabel(self.frame_2)
        self.example_filename_after_label.setObjectName(u"example_filename_after_label")

        self.verticalLayout_3.addWidget(self.example_filename_after_label)

        self.example_filename_after = QListWidget(self.frame_2)
        self.example_filename_after.setObjectName(u"example_filename_after")

        self.verticalLayout_3.addWidget(self.example_filename_after)

        self.renaming_options_examples_splitter.addWidget(self.frame_2)

        self.verticalLayout_6.addWidget(self.renaming_options_examples_splitter)


        self.verticalLayout_5.addWidget(self.groupBox)

        self.example_selection_note = QLabel(RenamingOptionsPage)
        self.example_selection_note.setObjectName(u"example_selection_note")
        self.example_selection_note.setWordWrap(True)

        self.verticalLayout_5.addWidget(self.example_selection_note)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.example_filename_sample_files_button = QPushButton(RenamingOptionsPage)
        self.example_filename_sample_files_button.setObjectName(u"example_filename_sample_files_button")

        self.horizontalLayout.addWidget(self.example_filename_sample_files_button)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.verticalLayout_5.addLayout(self.horizontalLayout)

        QWidget.setTabOrder(self.move_files, self.move_files_to)
        QWidget.setTabOrder(self.move_files_to, self.move_files_to_browse)
        QWidget.setTabOrder(self.move_files_to_browse, self.move_additional_files)
        QWidget.setTabOrder(self.move_additional_files, self.move_additional_files_pattern)
        QWidget.setTabOrder(self.move_additional_files_pattern, self.delete_empty_dirs)
        QWidget.setTabOrder(self.delete_empty_dirs, self.rename_files)
        QWidget.setTabOrder(self.rename_files, self.naming_script_selector)
        QWidget.setTabOrder(self.naming_script_selector, self.open_script_editor)
        QWidget.setTabOrder(self.open_script_editor, self.example_filename_before)
        QWidget.setTabOrder(self.example_filename_before, self.example_filename_after)
        QWidget.setTabOrder(self.example_filename_after, self.example_filename_sample_files_button)

        self.retranslateUi(RenamingOptionsPage)

        QMetaObject.connectSlotsByName(RenamingOptionsPage)
    # setupUi

    def retranslateUi(self, RenamingOptionsPage):
        self.move_files.setTitle(_(u"Move files when saving"))
        self.label.setText(_(u"Destination directory:"))
        self.move_files_to_browse.setText(_(u"Browse\u2026"))
        self.move_additional_files.setText(_(u"Move additional files (case insensitive):"))
        self.delete_empty_dirs.setText(_(u"Delete empty directories"))
        self.rename_files.setText(_(u"Rename files when saving"))
        self.label_2.setText(_(u"Selected file naming script:"))
        self.open_script_editor.setText(_(u"Edit file naming script\u2026"))
        self.groupBox.setTitle(_(u"Files will be named like this:"))
        self.example_filename_before_label.setText(_(u"Before"))
        self.example_filename_after_label.setText(_(u"After"))
        self.example_selection_note.setText("")
        self.example_filename_sample_files_button.setText(_(u"Reload examples"))
        pass
    # retranslateUi

