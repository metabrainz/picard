# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'scripteditor.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QComboBox,
    QDialogButtonBox, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QSizePolicy, QSplitter, QTextEdit, QVBoxLayout,
    QWidget)

from picard.ui.widgets.scripttextedit import ScriptTextEdit

from picard.i18n import gettext as _

class Ui_ScriptEditor(object):
    def setupUi(self, ScriptEditor):
        if not ScriptEditor.objectName():
            ScriptEditor.setObjectName(u"ScriptEditor")
        ScriptEditor.resize(902, 729)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ScriptEditor.sizePolicy().hasHeightForWidth())
        ScriptEditor.setSizePolicy(sizePolicy)
        self.verticalLayout_3 = QVBoxLayout(ScriptEditor)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.layout_for_menubar = QHBoxLayout()
        self.layout_for_menubar.setSpacing(0)
        self.layout_for_menubar.setObjectName(u"layout_for_menubar")

        self.verticalLayout_3.addLayout(self.layout_for_menubar)

        self.content_layout = QVBoxLayout()
        self.content_layout.setObjectName(u"content_layout")
        self.content_layout.setContentsMargins(9, 0, 9, 9)
        self.splitter_between_editor_and_examples = QSplitter(ScriptEditor)
        self.splitter_between_editor_and_examples.setObjectName(u"splitter_between_editor_and_examples")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.splitter_between_editor_and_examples.sizePolicy().hasHeightForWidth())
        self.splitter_between_editor_and_examples.setSizePolicy(sizePolicy1)
        self.splitter_between_editor_and_examples.setMinimumSize(QSize(0, 0))
        self.splitter_between_editor_and_examples.setFrameShape(QFrame.NoFrame)
        self.splitter_between_editor_and_examples.setOrientation(Qt.Vertical)
        self.frame_4 = QFrame(self.splitter_between_editor_and_examples)
        self.frame_4.setObjectName(u"frame_4")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(5)
        sizePolicy2.setHeightForWidth(self.frame_4.sizePolicy().hasHeightForWidth())
        self.frame_4.setSizePolicy(sizePolicy2)
        self.frame_4.setMinimumSize(QSize(0, 250))
        self.frame_4.setFrameShape(QFrame.NoFrame)
        self.frame_4.setFrameShadow(QFrame.Raised)
        self.verticalLayout_5 = QVBoxLayout(self.frame_4)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 3, 0, 0)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(-1, -1, -1, 0)
        self.label = QLabel(self.frame_4)
        self.label.setObjectName(u"label")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy3)
        self.label.setMinimumSize(QSize(0, 0))
        self.label.setIndent(0)

        self.horizontalLayout_2.addWidget(self.label)

        self.preset_naming_scripts = QComboBox(self.frame_4)
        self.preset_naming_scripts.setObjectName(u"preset_naming_scripts")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.preset_naming_scripts.sizePolicy().hasHeightForWidth())
        self.preset_naming_scripts.setSizePolicy(sizePolicy4)
        self.preset_naming_scripts.setMinimumSize(QSize(200, 0))

        self.horizontalLayout_2.addWidget(self.preset_naming_scripts)


        self.verticalLayout_5.addLayout(self.horizontalLayout_2)

        self.frame = QFrame(self.frame_4)
        self.frame.setObjectName(u"frame")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy5)
        self.frame.setMinimumSize(QSize(0, 200))
        self.frame.setFrameShape(QFrame.NoFrame)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_8 = QVBoxLayout(self.frame)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.splitter_between_editor_and_documentation = QSplitter(self.frame)
        self.splitter_between_editor_and_documentation.setObjectName(u"splitter_between_editor_and_documentation")
        self.splitter_between_editor_and_documentation.setMinimumSize(QSize(0, 0))
        self.splitter_between_editor_and_documentation.setFrameShape(QFrame.NoFrame)
        self.splitter_between_editor_and_documentation.setOrientation(Qt.Horizontal)
        self.splitter_between_editor_and_documentation.setOpaqueResize(True)
        self.frame_5 = QFrame(self.splitter_between_editor_and_documentation)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setFrameShape(QFrame.NoFrame)
        self.frame_5.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame_5)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.label_2 = QLabel(self.frame_5)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout.addWidget(self.label_2)

        self.script_title = QLineEdit(self.frame_5)
        self.script_title.setObjectName(u"script_title")

        self.horizontalLayout.addWidget(self.script_title)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.file_naming_format = ScriptTextEdit(self.frame_5)
        self.file_naming_format.setObjectName(u"file_naming_format")
        self.file_naming_format.setEnabled(False)
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(5)
        sizePolicy6.setHeightForWidth(self.file_naming_format.sizePolicy().hasHeightForWidth())
        self.file_naming_format.setSizePolicy(sizePolicy6)
        self.file_naming_format.setMinimumSize(QSize(0, 50))
        self.file_naming_format.viewport().setProperty("cursor", QCursor(Qt.IBeamCursor))
        self.file_naming_format.setTabChangesFocus(False)
        self.file_naming_format.setLineWrapMode(QTextEdit.NoWrap)
        self.file_naming_format.setTabStopDistance(20.000000000000000)
        self.file_naming_format.setAcceptRichText(False)
        self.file_naming_format.setTextInteractionFlags(Qt.TextEditorInteraction)

        self.verticalLayout_2.addWidget(self.file_naming_format)

        self.splitter_between_editor_and_documentation.addWidget(self.frame_5)
        self.documentation_frame = QFrame(self.splitter_between_editor_and_documentation)
        self.documentation_frame.setObjectName(u"documentation_frame")
        self.documentation_frame.setMinimumSize(QSize(100, 0))
        self.documentation_frame.setFrameShape(QFrame.NoFrame)
        self.documentation_frame.setFrameShadow(QFrame.Raised)
        self.documentation_frame_layout = QVBoxLayout(self.documentation_frame)
        self.documentation_frame_layout.setObjectName(u"documentation_frame_layout")
        self.documentation_frame_layout.setContentsMargins(0, 0, 0, 0)
        self.splitter_between_editor_and_documentation.addWidget(self.documentation_frame)

        self.verticalLayout_8.addWidget(self.splitter_between_editor_and_documentation)


        self.verticalLayout_5.addWidget(self.frame)

        self.renaming_error = QLabel(self.frame_4)
        self.renaming_error.setObjectName(u"renaming_error")
        sizePolicy7 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.renaming_error.sizePolicy().hasHeightForWidth())
        self.renaming_error.setSizePolicy(sizePolicy7)
        self.renaming_error.setAlignment(Qt.AlignCenter)

        self.verticalLayout_5.addWidget(self.renaming_error)

        self.splitter_between_editor_and_examples.addWidget(self.frame_4)
        self.groupBox = QGroupBox(self.splitter_between_editor_and_examples)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy8 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy8.setHorizontalStretch(0)
        sizePolicy8.setVerticalStretch(1)
        sizePolicy8.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy8)
        self.groupBox.setMinimumSize(QSize(300, 150))
        self.groupBox.setMaximumSize(QSize(16777215, 400))
        self.groupBox.setBaseSize(QSize(0, 150))
        self.verticalLayout = QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(3, 3, 3, 3)
        self.splitter_between_before_and_after = QSplitter(self.groupBox)
        self.splitter_between_before_and_after.setObjectName(u"splitter_between_before_and_after")
        self.splitter_between_before_and_after.setOrientation(Qt.Horizontal)
        self.splitter_between_before_and_after.setOpaqueResize(True)
        self.frame_2 = QFrame(self.splitter_between_before_and_after)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.frame_2)
        self.verticalLayout_4.setSpacing(3)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.example_filename_before_label = QLabel(self.frame_2)
        self.example_filename_before_label.setObjectName(u"example_filename_before_label")

        self.verticalLayout_4.addWidget(self.example_filename_before_label)

        self.example_filename_before = QListWidget(self.frame_2)
        self.example_filename_before.setObjectName(u"example_filename_before")
        self.example_filename_before.setEditTriggers(QAbstractItemView.CurrentChanged|QAbstractItemView.DoubleClicked|QAbstractItemView.EditKeyPressed|QAbstractItemView.SelectedClicked)
        self.example_filename_before.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.verticalLayout_4.addWidget(self.example_filename_before)

        self.splitter_between_before_and_after.addWidget(self.frame_2)
        self.frame_3 = QFrame(self.splitter_between_before_and_after)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.NoFrame)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.frame_3)
        self.verticalLayout_6.setSpacing(3)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.example_filename_after_label = QLabel(self.frame_3)
        self.example_filename_after_label.setObjectName(u"example_filename_after_label")

        self.verticalLayout_6.addWidget(self.example_filename_after_label)

        self.example_filename_after = QListWidget(self.frame_3)
        self.example_filename_after.setObjectName(u"example_filename_after")
        self.example_filename_after.setEditTriggers(QAbstractItemView.CurrentChanged|QAbstractItemView.DoubleClicked|QAbstractItemView.EditKeyPressed|QAbstractItemView.SelectedClicked)
        self.example_filename_after.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.verticalLayout_6.addWidget(self.example_filename_after)

        self.splitter_between_before_and_after.addWidget(self.frame_3)

        self.verticalLayout.addWidget(self.splitter_between_before_and_after)

        self.splitter_between_editor_and_examples.addWidget(self.groupBox)

        self.content_layout.addWidget(self.splitter_between_editor_and_examples)

        self.buttonbox = QDialogButtonBox(ScriptEditor)
        self.buttonbox.setObjectName(u"buttonbox")

        self.content_layout.addWidget(self.buttonbox)


        self.verticalLayout_3.addLayout(self.content_layout)


        self.retranslateUi(ScriptEditor)

        QMetaObject.connectSlotsByName(ScriptEditor)
    # setupUi

    def retranslateUi(self, ScriptEditor):
        self.label.setText(_(u"Selected file naming script:"))
#if QT_CONFIG(tooltip)
        self.preset_naming_scripts.setToolTip(_(u"Select the file naming script to load into the editor"))
#endif // QT_CONFIG(tooltip)
        self.label_2.setText(_(u"Title:"))
        self.renaming_error.setText("")
        self.groupBox.setTitle(_(u"Files will be named like this:"))
        self.example_filename_before_label.setText(_(u"Before"))
        self.example_filename_after_label.setText(_(u"After"))
        pass
    # retranslateUi

