# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_cover_processing.ui'
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
    QSizePolicy, QSpacerItem, QSpinBox, QVBoxLayout,
    QWidget)

from picard.i18n import gettext as _

class Ui_CoverProcessingOptionsPage(object):
    def setupUi(self, CoverProcessingOptionsPage):
        if not CoverProcessingOptionsPage.objectName():
            CoverProcessingOptionsPage.setObjectName(u"CoverProcessingOptionsPage")
        CoverProcessingOptionsPage.resize(518, 285)
        self.verticalLayout = QVBoxLayout(CoverProcessingOptionsPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.filtering = QGroupBox(CoverProcessingOptionsPage)
        self.filtering.setObjectName(u"filtering")
        self.filtering.setCheckable(True)
        self.filtering.setChecked(False)
        self.verticalLayout_2 = QVBoxLayout(self.filtering)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.filtering_width_widget = QWidget(self.filtering)
        self.filtering_width_widget.setObjectName(u"filtering_width_widget")
        self.horizontalLayout = QHBoxLayout(self.filtering_width_widget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.filtering_width_label = QLabel(self.filtering_width_widget)
        self.filtering_width_label.setObjectName(u"filtering_width_label")

        self.horizontalLayout.addWidget(self.filtering_width_label)

        self.filtering_width_value = QSpinBox(self.filtering_width_widget)
        self.filtering_width_value.setObjectName(u"filtering_width_value")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.filtering_width_value.sizePolicy().hasHeightForWidth())
        self.filtering_width_value.setSizePolicy(sizePolicy)
        self.filtering_width_value.setMaximum(9999)
        self.filtering_width_value.setValue(250)

        self.horizontalLayout.addWidget(self.filtering_width_value)

        self.px_label1 = QLabel(self.filtering_width_widget)
        self.px_label1.setObjectName(u"px_label1")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.px_label1.sizePolicy().hasHeightForWidth())
        self.px_label1.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.px_label1)


        self.verticalLayout_2.addWidget(self.filtering_width_widget)

        self.filtering_height_widget = QWidget(self.filtering)
        self.filtering_height_widget.setObjectName(u"filtering_height_widget")
        self.horizontalLayout_2 = QHBoxLayout(self.filtering_height_widget)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.filtering_height_label = QLabel(self.filtering_height_widget)
        self.filtering_height_label.setObjectName(u"filtering_height_label")

        self.horizontalLayout_2.addWidget(self.filtering_height_label)

        self.filtering_height_value = QSpinBox(self.filtering_height_widget)
        self.filtering_height_value.setObjectName(u"filtering_height_value")
        sizePolicy.setHeightForWidth(self.filtering_height_value.sizePolicy().hasHeightForWidth())
        self.filtering_height_value.setSizePolicy(sizePolicy)
        self.filtering_height_value.setMaximum(9999)
        self.filtering_height_value.setValue(250)

        self.horizontalLayout_2.addWidget(self.filtering_height_value)

        self.px_label2 = QLabel(self.filtering_height_widget)
        self.px_label2.setObjectName(u"px_label2")
        sizePolicy1.setHeightForWidth(self.px_label2.sizePolicy().hasHeightForWidth())
        self.px_label2.setSizePolicy(sizePolicy1)

        self.horizontalLayout_2.addWidget(self.px_label2)


        self.verticalLayout_2.addWidget(self.filtering_height_widget)


        self.verticalLayout.addWidget(self.filtering)

        self.resizing = QGroupBox(CoverProcessingOptionsPage)
        self.resizing.setObjectName(u"resizing")
        self.resizing.setCheckable(False)
        self.resizing.setChecked(False)
        self.horizontalLayout_7 = QHBoxLayout(self.resizing)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.save_to_tags = QGroupBox(self.resizing)
        self.save_to_tags.setObjectName(u"save_to_tags")
        self.save_to_tags.setCheckable(True)
        self.save_to_tags.setChecked(False)
        self.verticalLayout_3 = QVBoxLayout(self.save_to_tags)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.tags_resize_width_widget = QWidget(self.save_to_tags)
        self.tags_resize_width_widget.setObjectName(u"tags_resize_width_widget")
        self.horizontalLayout_5 = QHBoxLayout(self.tags_resize_width_widget)
        self.horizontalLayout_5.setSpacing(4)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.tags_resized_width_label = QLabel(self.tags_resize_width_widget)
        self.tags_resized_width_label.setObjectName(u"tags_resized_width_label")

        self.horizontalLayout_5.addWidget(self.tags_resized_width_label)

        self.tags_resized_width_value = QSpinBox(self.tags_resize_width_widget)
        self.tags_resized_width_value.setObjectName(u"tags_resized_width_value")
        sizePolicy.setHeightForWidth(self.tags_resized_width_value.sizePolicy().hasHeightForWidth())
        self.tags_resized_width_value.setSizePolicy(sizePolicy)
        self.tags_resized_width_value.setMaximum(9999)
        self.tags_resized_width_value.setValue(1000)

        self.horizontalLayout_5.addWidget(self.tags_resized_width_value)

        self.px_label5 = QLabel(self.tags_resize_width_widget)
        self.px_label5.setObjectName(u"px_label5")
        sizePolicy1.setHeightForWidth(self.px_label5.sizePolicy().hasHeightForWidth())
        self.px_label5.setSizePolicy(sizePolicy1)

        self.horizontalLayout_5.addWidget(self.px_label5)


        self.verticalLayout_3.addWidget(self.tags_resize_width_widget)

        self.tags_resize_height_widget = QWidget(self.save_to_tags)
        self.tags_resize_height_widget.setObjectName(u"tags_resize_height_widget")
        self.horizontalLayout_3 = QHBoxLayout(self.tags_resize_height_widget)
        self.horizontalLayout_3.setSpacing(4)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.tags_resized_height_label = QLabel(self.tags_resize_height_widget)
        self.tags_resized_height_label.setObjectName(u"tags_resized_height_label")

        self.horizontalLayout_3.addWidget(self.tags_resized_height_label)

        self.tags_resized_height_value = QSpinBox(self.tags_resize_height_widget)
        self.tags_resized_height_value.setObjectName(u"tags_resized_height_value")
        sizePolicy.setHeightForWidth(self.tags_resized_height_value.sizePolicy().hasHeightForWidth())
        self.tags_resized_height_value.setSizePolicy(sizePolicy)
        self.tags_resized_height_value.setMaximum(9999)
        self.tags_resized_height_value.setValue(1000)

        self.horizontalLayout_3.addWidget(self.tags_resized_height_value)

        self.px_label6 = QLabel(self.tags_resize_height_widget)
        self.px_label6.setObjectName(u"px_label6")
        sizePolicy1.setHeightForWidth(self.px_label6.sizePolicy().hasHeightForWidth())
        self.px_label6.setSizePolicy(sizePolicy1)

        self.horizontalLayout_3.addWidget(self.px_label6)


        self.verticalLayout_3.addWidget(self.tags_resize_height_widget)


        self.horizontalLayout_7.addWidget(self.save_to_tags)

        self.save_to_file = QGroupBox(self.resizing)
        self.save_to_file.setObjectName(u"save_to_file")
        self.save_to_file.setCheckable(True)
        self.save_to_file.setChecked(False)
        self.verticalLayout_4 = QVBoxLayout(self.save_to_file)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.file_resize_width_widget = QWidget(self.save_to_file)
        self.file_resize_width_widget.setObjectName(u"file_resize_width_widget")
        self.horizontalLayout_6 = QHBoxLayout(self.file_resize_width_widget)
        self.horizontalLayout_6.setSpacing(4)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.file_resized_width_label = QLabel(self.file_resize_width_widget)
        self.file_resized_width_label.setObjectName(u"file_resized_width_label")

        self.horizontalLayout_6.addWidget(self.file_resized_width_label)

        self.file_resized_width_value = QSpinBox(self.file_resize_width_widget)
        self.file_resized_width_value.setObjectName(u"file_resized_width_value")
        sizePolicy.setHeightForWidth(self.file_resized_width_value.sizePolicy().hasHeightForWidth())
        self.file_resized_width_value.setSizePolicy(sizePolicy)
        self.file_resized_width_value.setMaximum(9999)
        self.file_resized_width_value.setValue(1000)

        self.horizontalLayout_6.addWidget(self.file_resized_width_value)

        self.px_label3 = QLabel(self.file_resize_width_widget)
        self.px_label3.setObjectName(u"px_label3")
        sizePolicy1.setHeightForWidth(self.px_label3.sizePolicy().hasHeightForWidth())
        self.px_label3.setSizePolicy(sizePolicy1)

        self.horizontalLayout_6.addWidget(self.px_label3)


        self.verticalLayout_4.addWidget(self.file_resize_width_widget)

        self.file_resize_height_widget = QWidget(self.save_to_file)
        self.file_resize_height_widget.setObjectName(u"file_resize_height_widget")
        self.horizontalLayout_4 = QHBoxLayout(self.file_resize_height_widget)
        self.horizontalLayout_4.setSpacing(4)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.file_resized_height_label = QLabel(self.file_resize_height_widget)
        self.file_resized_height_label.setObjectName(u"file_resized_height_label")

        self.horizontalLayout_4.addWidget(self.file_resized_height_label)

        self.file_resized_height_value = QSpinBox(self.file_resize_height_widget)
        self.file_resized_height_value.setObjectName(u"file_resized_height_value")
        sizePolicy.setHeightForWidth(self.file_resized_height_value.sizePolicy().hasHeightForWidth())
        self.file_resized_height_value.setSizePolicy(sizePolicy)
        self.file_resized_height_value.setMaximum(9999)
        self.file_resized_height_value.setValue(1000)

        self.horizontalLayout_4.addWidget(self.file_resized_height_value)

        self.px_label4 = QLabel(self.file_resize_height_widget)
        self.px_label4.setObjectName(u"px_label4")
        sizePolicy1.setHeightForWidth(self.px_label4.sizePolicy().hasHeightForWidth())
        self.px_label4.setSizePolicy(sizePolicy1)

        self.horizontalLayout_4.addWidget(self.px_label4)


        self.verticalLayout_4.addWidget(self.file_resize_height_widget)


        self.horizontalLayout_7.addWidget(self.save_to_file)


        self.verticalLayout.addWidget(self.resizing)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.retranslateUi(CoverProcessingOptionsPage)

        QMetaObject.connectSlotsByName(CoverProcessingOptionsPage)
    # setupUi

    def retranslateUi(self, CoverProcessingOptionsPage):
        CoverProcessingOptionsPage.setWindowTitle(_(u"Form"))
        self.filtering.setTitle(_(u"Discard images if below the given size"))
        self.filtering_width_label.setText(_(u"Minimum width:"))
        self.px_label1.setText(_(u"px"))
        self.filtering_height_label.setText(_(u"Minimum height:"))
        self.px_label2.setText(_(u"px"))
        self.resizing.setTitle(_(u"Resize images if above the given size"))
        self.save_to_tags.setTitle(_(u"Resize images saved to tags "))
        self.tags_resized_width_label.setText(_(u"Maximum width:"))
        self.px_label5.setText(_(u"px"))
        self.tags_resized_height_label.setText(_(u"Maximum height:"))
        self.px_label6.setText(_(u"px"))
        self.save_to_file.setTitle(_(u"Resize images saved to files"))
        self.file_resized_width_label.setText(_(u"Maximum width:"))
        self.px_label3.setText(_(u"px"))
        self.file_resized_height_label.setText(_(u"Maximum height:"))
        self.px_label4.setText(_(u"px"))
    # retranslateUi

