# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'edittagdialog.ui'
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
    QDialog, QDialogButtonBox, QHBoxLayout, QListView,
    QListWidget, QListWidgetItem, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_EditTagDialog(object):
    def setupUi(self, EditTagDialog):
        if not EditTagDialog.objectName():
            EditTagDialog.setObjectName(u"EditTagDialog")
        EditTagDialog.setWindowModality(Qt.ApplicationModal)
        EditTagDialog.resize(400, 250)
        EditTagDialog.setFocusPolicy(Qt.StrongFocus)
        EditTagDialog.setModal(True)
        self.verticalLayout_2 = QVBoxLayout(EditTagDialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tag_names = QComboBox(EditTagDialog)
        self.tag_names.setObjectName(u"tag_names")
        self.tag_names.setEditable(True)

        self.verticalLayout_2.addWidget(self.tag_names)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.value_list = QListWidget(EditTagDialog)
        self.value_list.setObjectName(u"value_list")
        self.value_list.setFocusPolicy(Qt.StrongFocus)
        self.value_list.setTabKeyNavigation(False)
        self.value_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.value_list.setMovement(QListView.Free)

        self.horizontalLayout.addWidget(self.value_list)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.edit_value = QPushButton(EditTagDialog)
        self.edit_value.setObjectName(u"edit_value")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(100)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edit_value.sizePolicy().hasHeightForWidth())
        self.edit_value.setSizePolicy(sizePolicy)
        self.edit_value.setMinimumSize(QSize(100, 0))
        self.edit_value.setAutoDefault(False)

        self.verticalLayout.addWidget(self.edit_value)

        self.add_value = QPushButton(EditTagDialog)
        self.add_value.setObjectName(u"add_value")
        sizePolicy.setHeightForWidth(self.add_value.sizePolicy().hasHeightForWidth())
        self.add_value.setSizePolicy(sizePolicy)
        self.add_value.setMinimumSize(QSize(100, 0))
        self.add_value.setAutoDefault(False)

        self.verticalLayout.addWidget(self.add_value)

        self.remove_value = QPushButton(EditTagDialog)
        self.remove_value.setObjectName(u"remove_value")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(120)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.remove_value.sizePolicy().hasHeightForWidth())
        self.remove_value.setSizePolicy(sizePolicy1)
        self.remove_value.setMinimumSize(QSize(120, 0))
        self.remove_value.setAutoDefault(False)

        self.verticalLayout.addWidget(self.remove_value)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.move_value_up = QPushButton(EditTagDialog)
        self.move_value_up.setObjectName(u"move_value_up")
        icon = QIcon()
        iconThemeName = u":/images/16x16/go-up.png"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.move_value_up.setIcon(icon)

        self.verticalLayout.addWidget(self.move_value_up)

        self.move_value_down = QPushButton(EditTagDialog)
        self.move_value_down.setObjectName(u"move_value_down")
        icon1 = QIcon()
        iconThemeName = u":/images/16x16/go-down.png"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.move_value_down.setIcon(icon1)

        self.verticalLayout.addWidget(self.move_value_down)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.horizontalLayout.addLayout(self.verticalLayout)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.buttonbox = QDialogButtonBox(EditTagDialog)
        self.buttonbox.setObjectName(u"buttonbox")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(150)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.buttonbox.sizePolicy().hasHeightForWidth())
        self.buttonbox.setSizePolicy(sizePolicy2)
        self.buttonbox.setMinimumSize(QSize(150, 0))
        self.buttonbox.setOrientation(Qt.Horizontal)
        self.buttonbox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout_2.addWidget(self.buttonbox)

        QWidget.setTabOrder(self.tag_names, self.value_list)
        QWidget.setTabOrder(self.value_list, self.edit_value)
        QWidget.setTabOrder(self.edit_value, self.add_value)
        QWidget.setTabOrder(self.add_value, self.remove_value)
        QWidget.setTabOrder(self.remove_value, self.buttonbox)

        self.retranslateUi(EditTagDialog)
        self.buttonbox.accepted.connect(EditTagDialog.accept)
        self.buttonbox.rejected.connect(EditTagDialog.reject)
        self.move_value_up.clicked.connect(EditTagDialog.move_row_up)
        self.move_value_down.clicked.connect(EditTagDialog.move_row_down)
        self.edit_value.clicked.connect(EditTagDialog.edit_value)
        self.add_value.clicked.connect(EditTagDialog.add_value)
        self.value_list.itemChanged.connect(EditTagDialog.value_edited)
        self.remove_value.clicked.connect(EditTagDialog.remove_value)
        self.value_list.itemSelectionChanged.connect(EditTagDialog.value_selection_changed)
        self.tag_names.editTextChanged.connect(EditTagDialog.tag_changed)
        self.tag_names.activated.connect(EditTagDialog.tag_selected)

        QMetaObject.connectSlotsByName(EditTagDialog)
    # setupUi

    def retranslateUi(self, EditTagDialog):
        EditTagDialog.setWindowTitle(_(u"Edit Tag"))
        self.edit_value.setText(_(u"Edit value"))
        self.add_value.setText(_(u"Add value"))
        self.remove_value.setText(_(u"Remove value"))
#if QT_CONFIG(tooltip)
        self.move_value_up.setToolTip(_(u"Move selected value up"))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.move_value_up.setAccessibleDescription(_(u"Move selected value up"))
#endif // QT_CONFIG(accessibility)
        self.move_value_up.setText("")
#if QT_CONFIG(tooltip)
        self.move_value_down.setToolTip(_(u"Move selected value down"))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.move_value_down.setAccessibleDescription(_(u"Move selected value down"))
#endif // QT_CONFIG(accessibility)
        self.move_value_down.setText("")
    # retranslateUi

