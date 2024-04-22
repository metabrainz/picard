# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'scripteditor_details.ui'
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
    QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_ScriptDetails(object):
    def setupUi(self, ScriptDetails):
        if not ScriptDetails.objectName():
            ScriptDetails.setObjectName(u"ScriptDetails")
        ScriptDetails.setWindowModality(Qt.WindowModal)
        ScriptDetails.resize(700, 284)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(ScriptDetails.sizePolicy().hasHeightForWidth())
        ScriptDetails.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(ScriptDetails)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.script_version = QLineEdit(ScriptDetails)
        self.script_version.setObjectName(u"script_version")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.script_version.sizePolicy().hasHeightForWidth())
        self.script_version.setSizePolicy(sizePolicy1)
        self.script_version.setMinimumSize(QSize(100, 0))
        self.script_version.setMaximumSize(QSize(100, 16777215))
        self.script_version.setBaseSize(QSize(0, 0))

        self.horizontalLayout.addWidget(self.script_version)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.label_4 = QLabel(ScriptDetails)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout.addWidget(self.label_4)

        self.script_last_updated = QLineEdit(ScriptDetails)
        self.script_last_updated.setObjectName(u"script_last_updated")
        self.script_last_updated.setMinimumSize(QSize(200, 0))
        self.script_last_updated.setMaximumSize(QSize(200, 16777215))

        self.horizontalLayout.addWidget(self.script_last_updated)

        self.last_updated_now = QPushButton(ScriptDetails)
        self.last_updated_now.setObjectName(u"last_updated_now")

        self.horizontalLayout.addWidget(self.last_updated_now)


        self.gridLayout.addLayout(self.horizontalLayout, 2, 2, 1, 1)

        self.label_2 = QLabel(ScriptDetails)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.label_3 = QLabel(ScriptDetails)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)

        self.label_5 = QLabel(ScriptDetails)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 3, 0, 1, 1)

        self.label = QLabel(ScriptDetails)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.script_license = QLineEdit(ScriptDetails)
        self.script_license.setObjectName(u"script_license")

        self.gridLayout.addWidget(self.script_license, 3, 2, 1, 1)

        self.label_6 = QLabel(ScriptDetails)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.gridLayout.addWidget(self.label_6, 4, 0, 1, 1)

        self.script_description = QPlainTextEdit(ScriptDetails)
        self.script_description.setObjectName(u"script_description")

        self.gridLayout.addWidget(self.script_description, 4, 2, 1, 1)

        self.script_author = QLineEdit(ScriptDetails)
        self.script_author.setObjectName(u"script_author")

        self.gridLayout.addWidget(self.script_author, 1, 2, 1, 1)

        self.script_title = QLineEdit(ScriptDetails)
        self.script_title.setObjectName(u"script_title")

        self.gridLayout.addWidget(self.script_title, 0, 2, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout)

        self.buttonBox = QDialogButtonBox(ScriptDetails)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Close|QDialogButtonBox.Save)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(ScriptDetails)

        QMetaObject.connectSlotsByName(ScriptDetails)
    # setupUi

    def retranslateUi(self, ScriptDetails):
        ScriptDetails.setWindowTitle(_(u"File Naming Script Metadata"))
#if QT_CONFIG(tooltip)
        self.script_version.setToolTip(_(u"Version number of the file naming script."))
#endif // QT_CONFIG(tooltip)
        self.label_4.setText(_(u"Last Updated:"))
#if QT_CONFIG(tooltip)
        self.script_last_updated.setToolTip(_(u"Date and time the file naming script was last updated (UTC)."))
#endif // QT_CONFIG(tooltip)
        self.last_updated_now.setText(_(u"Now"))
        self.label_2.setText(_(u"Author:"))
        self.label_3.setText(_(u"Version:"))
        self.label_5.setText(_(u"License:"))
        self.label.setText(_(u"Title:"))
#if QT_CONFIG(tooltip)
        self.script_license.setToolTip(_(u"License under which the file naming script is available."))
#endif // QT_CONFIG(tooltip)
        self.label_6.setText(_(u"Description:"))
#if QT_CONFIG(tooltip)
        self.script_description.setToolTip(_(u"Brief description of the file naming script, including any required plugins."))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.script_author.setToolTip(_(u"The author of the file naming script."))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

