# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_metadata.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_MetadataOptionsPage(object):
    def setupUi(self, MetadataOptionsPage):
        if not MetadataOptionsPage.objectName():
            MetadataOptionsPage.setObjectName(u"MetadataOptionsPage")
        MetadataOptionsPage.resize(423, 553)
        self.verticalLayout = QVBoxLayout(MetadataOptionsPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.metadata_groupbox = QGroupBox(MetadataOptionsPage)
        self.metadata_groupbox.setObjectName(u"metadata_groupbox")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.metadata_groupbox.sizePolicy().hasHeightForWidth())
        self.metadata_groupbox.setSizePolicy(sizePolicy)
        self.metadata_groupbox.setMinimumSize(QSize(397, 135))
        self.metadata_groupbox.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.verticalLayout_3 = QVBoxLayout(self.metadata_groupbox)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.translate_artist_names = QCheckBox(self.metadata_groupbox)
        self.translate_artist_names.setObjectName(u"translate_artist_names")

        self.verticalLayout_3.addWidget(self.translate_artist_names)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, -1, -1, 0)
        self.selected_locales = QLineEdit(self.metadata_groupbox)
        self.selected_locales.setObjectName(u"selected_locales")
        self.selected_locales.setReadOnly(True)

        self.horizontalLayout.addWidget(self.selected_locales)

        self.select_locales = QPushButton(self.metadata_groupbox)
        self.select_locales.setObjectName(u"select_locales")

        self.horizontalLayout.addWidget(self.select_locales)


        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.translate_artist_names_script_exception = QCheckBox(self.metadata_groupbox)
        self.translate_artist_names_script_exception.setObjectName(u"translate_artist_names_script_exception")

        self.verticalLayout_3.addWidget(self.translate_artist_names_script_exception)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(-1, -1, -1, 0)
        self.selected_scripts = QLineEdit(self.metadata_groupbox)
        self.selected_scripts.setObjectName(u"selected_scripts")
        self.selected_scripts.setReadOnly(True)

        self.horizontalLayout_4.addWidget(self.selected_scripts)

        self.select_scripts = QPushButton(self.metadata_groupbox)
        self.select_scripts.setObjectName(u"select_scripts")

        self.horizontalLayout_4.addWidget(self.select_scripts)


        self.verticalLayout_3.addLayout(self.horizontalLayout_4)

        self.standardize_artists = QCheckBox(self.metadata_groupbox)
        self.standardize_artists.setObjectName(u"standardize_artists")

        self.verticalLayout_3.addWidget(self.standardize_artists)

        self.standardize_instruments = QCheckBox(self.metadata_groupbox)
        self.standardize_instruments.setObjectName(u"standardize_instruments")

        self.verticalLayout_3.addWidget(self.standardize_instruments)

        self.convert_punctuation = QCheckBox(self.metadata_groupbox)
        self.convert_punctuation.setObjectName(u"convert_punctuation")

        self.verticalLayout_3.addWidget(self.convert_punctuation)

        self.release_ars = QCheckBox(self.metadata_groupbox)
        self.release_ars.setObjectName(u"release_ars")

        self.verticalLayout_3.addWidget(self.release_ars)

        self.track_ars = QCheckBox(self.metadata_groupbox)
        self.track_ars.setObjectName(u"track_ars")

        self.verticalLayout_3.addWidget(self.track_ars)

        self.guess_tracknumber_and_title = QCheckBox(self.metadata_groupbox)
        self.guess_tracknumber_and_title.setObjectName(u"guess_tracknumber_and_title")

        self.verticalLayout_3.addWidget(self.guess_tracknumber_and_title)


        self.verticalLayout.addWidget(self.metadata_groupbox)

        self.custom_fields_groupbox = QGroupBox(MetadataOptionsPage)
        self.custom_fields_groupbox.setObjectName(u"custom_fields_groupbox")
        sizePolicy.setHeightForWidth(self.custom_fields_groupbox.sizePolicy().hasHeightForWidth())
        self.custom_fields_groupbox.setSizePolicy(sizePolicy)
        self.custom_fields_groupbox.setMinimumSize(QSize(397, 0))
        self.gridLayout = QGridLayout(self.custom_fields_groupbox)
        self.gridLayout.setSpacing(2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_6 = QLabel(self.custom_fields_groupbox)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout.addWidget(self.label_6, 0, 0, 1, 2)

        self.label_7 = QLabel(self.custom_fields_groupbox)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout.addWidget(self.label_7, 2, 0, 1, 2)

        self.nat_name = QLineEdit(self.custom_fields_groupbox)
        self.nat_name.setObjectName(u"nat_name")

        self.gridLayout.addWidget(self.nat_name, 3, 0, 1, 1)

        self.nat_name_default = QPushButton(self.custom_fields_groupbox)
        self.nat_name_default.setObjectName(u"nat_name_default")

        self.gridLayout.addWidget(self.nat_name_default, 3, 1, 1, 1)

        self.va_name_default = QPushButton(self.custom_fields_groupbox)
        self.va_name_default.setObjectName(u"va_name_default")

        self.gridLayout.addWidget(self.va_name_default, 1, 1, 1, 1)

        self.va_name = QLineEdit(self.custom_fields_groupbox)
        self.va_name.setObjectName(u"va_name")

        self.gridLayout.addWidget(self.va_name, 1, 0, 1, 1)


        self.verticalLayout.addWidget(self.custom_fields_groupbox)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

#if QT_CONFIG(shortcut)
        self.label_6.setBuddy(self.va_name_default)
        self.label_7.setBuddy(self.nat_name_default)
#endif // QT_CONFIG(shortcut)
        QWidget.setTabOrder(self.translate_artist_names, self.selected_locales)
        QWidget.setTabOrder(self.selected_locales, self.select_locales)
        QWidget.setTabOrder(self.select_locales, self.translate_artist_names_script_exception)
        QWidget.setTabOrder(self.translate_artist_names_script_exception, self.selected_scripts)
        QWidget.setTabOrder(self.selected_scripts, self.select_scripts)
        QWidget.setTabOrder(self.select_scripts, self.standardize_artists)
        QWidget.setTabOrder(self.standardize_artists, self.standardize_instruments)
        QWidget.setTabOrder(self.standardize_instruments, self.convert_punctuation)
        QWidget.setTabOrder(self.convert_punctuation, self.release_ars)
        QWidget.setTabOrder(self.release_ars, self.track_ars)
        QWidget.setTabOrder(self.track_ars, self.guess_tracknumber_and_title)
        QWidget.setTabOrder(self.guess_tracknumber_and_title, self.va_name)
        QWidget.setTabOrder(self.va_name, self.va_name_default)
        QWidget.setTabOrder(self.va_name_default, self.nat_name)
        QWidget.setTabOrder(self.nat_name, self.nat_name_default)

        self.retranslateUi(MetadataOptionsPage)

        QMetaObject.connectSlotsByName(MetadataOptionsPage)
    # setupUi

    def retranslateUi(self, MetadataOptionsPage):
        self.metadata_groupbox.setTitle(_(u"Metadata"))
        self.translate_artist_names.setText(_(u"Translate artist names to these locales where possible:"))
        self.select_locales.setText(_(u"Select\u2026"))
        self.translate_artist_names_script_exception.setText(_(u"Ignore artist name translation for these language scripts:"))
        self.select_scripts.setText(_(u"Select\u2026"))
        self.standardize_artists.setText(_(u"Use standardized artist names"))
        self.standardize_instruments.setText(_(u"Use standardized instrument and vocal credits"))
        self.convert_punctuation.setText(_(u"Convert Unicode punctuation characters to ASCII"))
        self.release_ars.setText(_(u"Use release relationships"))
        self.track_ars.setText(_(u"Use track relationships"))
        self.guess_tracknumber_and_title.setText(_(u"Guess track number and title from filename if empty"))
        self.custom_fields_groupbox.setTitle(_(u"Custom Fields"))
        self.label_6.setText(_(u"Various artists:"))
        self.label_7.setText(_(u"Standalone recordings:"))
        self.nat_name_default.setText(_(u"Default"))
        self.va_name_default.setText(_(u"Default"))
        pass
    # retranslateUi

