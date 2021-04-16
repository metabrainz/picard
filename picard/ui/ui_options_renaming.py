# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_RenamingOptionsPage(object):
    def setupUi(self, RenamingOptionsPage):
        RenamingOptionsPage.setObjectName("RenamingOptionsPage")
        RenamingOptionsPage.setEnabled(True)
        RenamingOptionsPage.resize(453, 552)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(RenamingOptionsPage.sizePolicy().hasHeightForWidth())
        RenamingOptionsPage.setSizePolicy(sizePolicy)
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(RenamingOptionsPage)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.move_files = QtWidgets.QGroupBox(RenamingOptionsPage)
        self.move_files.setFlat(False)
        self.move_files.setCheckable(True)
        self.move_files.setChecked(False)
        self.move_files.setObjectName("move_files")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.move_files)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.label = QtWidgets.QLabel(self.move_files)
        self.label.setObjectName("label")
        self.verticalLayout_4.addWidget(self.label)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setSpacing(2)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.move_files_to = QtWidgets.QLineEdit(self.move_files)
        self.move_files_to.setEnabled(False)
        self.move_files_to.setObjectName("move_files_to")
        self.horizontalLayout_4.addWidget(self.move_files_to)
        self.move_files_to_browse = QtWidgets.QPushButton(self.move_files)
        self.move_files_to_browse.setEnabled(False)
        self.move_files_to_browse.setObjectName("move_files_to_browse")
        self.horizontalLayout_4.addWidget(self.move_files_to_browse)
        self.verticalLayout_4.addLayout(self.horizontalLayout_4)
        self.move_additional_files = QtWidgets.QCheckBox(self.move_files)
        self.move_additional_files.setEnabled(False)
        self.move_additional_files.setObjectName("move_additional_files")
        self.verticalLayout_4.addWidget(self.move_additional_files)
        self.move_additional_files_pattern = QtWidgets.QLineEdit(self.move_files)
        self.move_additional_files_pattern.setEnabled(False)
        self.move_additional_files_pattern.setObjectName("move_additional_files_pattern")
        self.verticalLayout_4.addWidget(self.move_additional_files_pattern)
        self.delete_empty_dirs = QtWidgets.QCheckBox(self.move_files)
        self.delete_empty_dirs.setEnabled(False)
        self.delete_empty_dirs.setObjectName("delete_empty_dirs")
        self.verticalLayout_4.addWidget(self.delete_empty_dirs)
        self.verticalLayout_5.addWidget(self.move_files)
        self.rename_files = QtWidgets.QCheckBox(RenamingOptionsPage)
        self.rename_files.setObjectName("rename_files")
        self.verticalLayout_5.addWidget(self.rename_files)
        self.ascii_filenames = QtWidgets.QCheckBox(RenamingOptionsPage)
        self.ascii_filenames.setObjectName("ascii_filenames")
        self.verticalLayout_5.addWidget(self.ascii_filenames)
        self.windows_compatibility = QtWidgets.QCheckBox(RenamingOptionsPage)
        self.windows_compatibility.setObjectName("windows_compatibility")
        self.verticalLayout_5.addWidget(self.windows_compatibility)
        self.groupBox = QtWidgets.QGroupBox(RenamingOptionsPage)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setContentsMargins(2, 0, 2, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.example_filename_before_label = QtWidgets.QLabel(self.groupBox)
        self.example_filename_before_label.setObjectName("example_filename_before_label")
        self.horizontalLayout_3.addWidget(self.example_filename_before_label)
        self.example_filename_after_label = QtWidgets.QLabel(self.groupBox)
        self.example_filename_after_label.setObjectName("example_filename_after_label")
        self.horizontalLayout_3.addWidget(self.example_filename_after_label)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.example_filename_before = QtWidgets.QListWidget(self.groupBox)
        self.example_filename_before.setObjectName("example_filename_before")
        self.horizontalLayout_2.addWidget(self.example_filename_before)
        self.example_filename_after = QtWidgets.QListWidget(self.groupBox)
        self.example_filename_after.setObjectName("example_filename_after")
        self.horizontalLayout_2.addWidget(self.example_filename_after)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.verticalLayout_5.addWidget(self.groupBox)
        self.label_2 = QtWidgets.QLabel(RenamingOptionsPage)
        self.label_2.setWordWrap(True)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_5.addWidget(self.label_2)
        self.renaming_error = QtWidgets.QLabel(RenamingOptionsPage)
        self.renaming_error.setText("")
        self.renaming_error.setAlignment(QtCore.Qt.AlignCenter)
        self.renaming_error.setObjectName("renaming_error")
        self.verticalLayout_5.addWidget(self.renaming_error)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.example_filename_sample_files_button = QtWidgets.QPushButton(RenamingOptionsPage)
        self.example_filename_sample_files_button.setObjectName("example_filename_sample_files_button")
        self.horizontalLayout.addWidget(self.example_filename_sample_files_button)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.open_script_editor = QtWidgets.QPushButton(RenamingOptionsPage)
        self.open_script_editor.setObjectName("open_script_editor")
        self.horizontalLayout.addWidget(self.open_script_editor)
        self.verticalLayout_5.addLayout(self.horizontalLayout)

        self.retranslateUi(RenamingOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(RenamingOptionsPage)
        RenamingOptionsPage.setTabOrder(self.move_files, self.move_files_to)
        RenamingOptionsPage.setTabOrder(self.move_files_to, self.move_files_to_browse)
        RenamingOptionsPage.setTabOrder(self.move_files_to_browse, self.move_additional_files)
        RenamingOptionsPage.setTabOrder(self.move_additional_files, self.move_additional_files_pattern)
        RenamingOptionsPage.setTabOrder(self.move_additional_files_pattern, self.delete_empty_dirs)

    def retranslateUi(self, RenamingOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.move_files.setTitle(_("Move files when saving"))
        self.label.setText(_("Destination directory:"))
        self.move_files_to_browse.setText(_("Browse..."))
        self.move_additional_files.setText(_("Move additional files (case insensitive):"))
        self.delete_empty_dirs.setText(_("Delete empty directories"))
        self.rename_files.setText(_("Rename files when saving"))
        self.ascii_filenames.setText(_("Replace non-ASCII characters"))
        self.windows_compatibility.setText(_("Windows compatibility"))
        self.groupBox.setTitle(_("Files will be named like this:"))
        self.example_filename_before_label.setText(_("Before"))
        self.example_filename_after_label.setText(_("After"))
        self.label_2.setText(_("If you select files from the Cluster pane or Album pane prior to opening the Options screen, up to 10 files will be randomly chosen from your selection as file naming examples.  If you have not selected any files, then some default examples will be provided."))
        self.example_filename_sample_files_button.setText(_("Reload examples"))
        self.open_script_editor.setText(_("Open the file naming script editor"))
