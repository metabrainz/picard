from picard import config
from picard.ui import PicardDialog
from picard.ui.ui_filedialog import Ui_fileDialog
from PyQt5 import QtWidgets
import sys

class FileDialog(PicardDialog):

    def __init__(self,parent=None):
        PicardDialog.__init__(self, parent)
        self.ui = Ui_fileDialog()
        self.ui.setupUi(self)
        self.showMaximized()
        sys.exit(self.exec_())

    def getfiles(self):
        """
        Yet to implement it
        """

app = QtWidgets.QApplication(sys.argv)
fi = FileDialog()
sys.exit(app.exec_())
