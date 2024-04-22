# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'scripting_documentation_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QSizePolicy, QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_ScriptingDocumentationDialog(object):
    def setupUi(self, ScriptingDocumentationDialog):
        if not ScriptingDocumentationDialog.objectName():
            ScriptingDocumentationDialog.setObjectName(u"ScriptingDocumentationDialog")
        ScriptingDocumentationDialog.resize(725, 457)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(ScriptingDocumentationDialog.sizePolicy().hasHeightForWidth())
        ScriptingDocumentationDialog.setSizePolicy(sizePolicy)
        ScriptingDocumentationDialog.setModal(False)
        self.verticalLayout = QVBoxLayout(ScriptingDocumentationDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.documentation_layout = QVBoxLayout()
        self.documentation_layout.setObjectName(u"documentation_layout")

        self.verticalLayout.addLayout(self.documentation_layout)

        self.buttonBox = QDialogButtonBox(ScriptingDocumentationDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(ScriptingDocumentationDialog)

        QMetaObject.connectSlotsByName(ScriptingDocumentationDialog)
    # setupUi

    def retranslateUi(self, ScriptingDocumentationDialog):
        ScriptingDocumentationDialog.setWindowTitle(_(u"Scripting Documentation"))
    # retranslateUi

