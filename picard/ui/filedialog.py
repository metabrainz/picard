from picard.ui import PicardDialog
from picard.ui.ui_filedialog import Ui_fileDialog
from picard.formats import supported_extensions
from PyQt5.QtWidgets import QFileSystemModel , QAbstractItemView
import os,sys

class FileDialog(PicardDialog):

    def __init__(self,parent=None):
        PicardDialog.__init__(self, parent)
        self.ui = Ui_fileDialog()
        self.ui.setupUi(self)
        self.showMaximized()
        self.files = []
        self.init_ui()
        if self.exec_():
            sys.close()

    def init_ui(self):
        self.extensions = ['*' + ext for ext in supported_extensions()]
        self.model = QFileSystemModel()
        self.model.setRootPath('/') #temporary
        self.model.setNameFilters(self.extensions)
        self.model.setNameFilterDisables(0)
        self.ui.fileTree.setModel(self.model)
        self.ui.fileTree.setRootIndex(self.model.index('/home/vishi')) #temporary
        self.ui.fileTree.setColumnWidth(0,.7*self.ui.fileTree.width())
        self.ui.fileTree.setColumnWidth(1,.1*self.ui.fileTree.width())
        self.ui.fileTree.setColumnWidth(2,.1*self.ui.fileTree.width())
        self.ui.fileTree.setColumnWidth(3,.1*self.ui.fileTree.width())
        self.ui.fileTree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.ui.formatsCb.addItem('All Supported Formats')
        self.ui.formatsCb.addItems(supported_extensions())
        self.ui.formatsCb.currentIndexChanged.connect(self.change_extension)
        self.ui.selectBtn.clicked.connect(self.get_files)

    def closeEvent(self,event):
        self.files.clear()
        self.close()

    def get_files(self):
        indexes = self.ui.fileTree.selectionModel().selectedIndexes()
        for indx in indexes:
            if os.path.isdir(self.model.filePath(indx)):
                self.add_directory_recursively(self.model.filePath(indx))
                pass
            else:
                self.files.append(self.model.filePath(indx))
        self.hide()
        return self.files

    def add_directory_recursively(self,path):
        for file in os.listdir(path):
            if os.path.isfile(os.path.join(path,file)):
                for exts in supported_extensions():
                    if file.endswith(exts):
                            self.files.append(os.path.join(path,file))
            elif os.path.isdir(os.path.join(path,file)):
                    self.add_directory_recursively(os.path.join(path,file))

    def change_extension(self,ext):
        self.extensions.clear()
        if self.ui.formatsCb.itemText(ext) == 'All Supported Formats':
            self.extensions = ['*' + ext for ext in supported_extensions()]
        else:
            self.extensions.append('*' + (self.ui.formatsCb.itemText(ext)))
        self.model.setNameFilters(self.extensions)

